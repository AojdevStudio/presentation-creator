"""
Pipeline Error Handlers

This module implements specific error handlers and recovery strategies for
the presentation generation pipeline stages.
"""

import logging
import traceback
from typing import Any, Dict, Optional, List
from pathlib import Path
import json
import asyncio
from datetime import datetime

from .pipeline import PipelineContext

logger = logging.getLogger(__name__)

class ErrorRecoveryStrategy:
    """Base class for error recovery strategies."""
    
    async def can_recover(self, error: Exception, context: PipelineContext) -> bool:
        """Determine if this strategy can recover from the error."""
        return False
        
    async def recover(self, error: Exception, context: PipelineContext) -> Optional[Any]:
        """Attempt to recover from the error."""
        raise NotImplementedError

class RetryStrategy(ErrorRecoveryStrategy):
    """Strategy that retries the operation with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self._retry_counts: Dict[str, int] = {}
        
    async def can_recover(self, error: Exception, context: PipelineContext) -> bool:
        stage_name = context.get_data("current_stage_name")
        current_retries = self._retry_counts.get(stage_name, 0)
        return current_retries < self.max_retries
        
    async def recover(self, error: Exception, context: PipelineContext) -> Optional[Any]:
        stage_name = context.get_data("current_stage_name")
        current_retries = self._retry_counts.get(stage_name, 0)
        self._retry_counts[stage_name] = current_retries + 1
        
        delay = self.initial_delay * (2 ** current_retries)
        logger.info(f"Retrying {stage_name} after {delay}s (attempt {current_retries + 1}/{self.max_retries})")
        await asyncio.sleep(delay)
        
        # Make sure we have the stage input data for the retry
        input_data = context.get_data("stage_input_data")
        if input_data is None:
            logger.warning(f"No stage input data found for retry of {stage_name}")
            return None
            
        # Ensure we're setting up for a clean retry
        context.set_data("retry_attempt", current_retries + 1)
        context.set_data("recovery_strategy", self.__class__.__name__)
        
        return input_data

class FallbackContentStrategy(ErrorRecoveryStrategy):
    """Strategy that uses fallback content when content generation fails."""
    
    def __init__(self, fallback_templates_dir: Path):
        self.fallback_templates_dir = fallback_templates_dir
        
    async def can_recover(self, error: Exception, context: PipelineContext) -> bool:
        return (
            isinstance(error, (ConnectionError, TimeoutError)) and
            context.get_data("current_stage_name") == "Content Generation"
        )
        
    async def recover(self, error: Exception, context: PipelineContext) -> Optional[Dict[str, Any]]:
        topic = context.get_data("topic")
        template_path = self.fallback_templates_dir / f"{topic.lower().replace(' ', '_')}.json"
        
        if template_path.exists():
            logger.info(f"Using fallback template for topic: {topic}")
            return json.loads(template_path.read_text())
        return None

class AutoSaveStrategy(ErrorRecoveryStrategy):
    """Strategy that auto-saves progress and can resume from last checkpoint."""
    
    def __init__(self, checkpoints_dir: Path):
        self.checkpoints_dir = checkpoints_dir
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_checkpoint_path(self, context: PipelineContext) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.checkpoints_dir / f"checkpoint_{timestamp}.json"
        
    async def can_recover(self, error: Exception, context: PipelineContext) -> bool:
        # Can always try to save progress
        return True
        
    async def recover(self, error: Exception, context: PipelineContext) -> Optional[Any]:
        # Save current progress
        checkpoint_data = {
            "stage_name": context.get_data("current_stage_name"),
            "input_data": context.get_data("stage_input_data"),
            "partial_results": context.get_data("partial_results", {}),
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        checkpoint_path = self._get_checkpoint_path(context)
        checkpoint_path.write_text(json.dumps(checkpoint_data, indent=2))
        logger.info(f"Saved checkpoint to: {checkpoint_path}")
        
        # Return the input data so the pipeline can continue
        # This allows AutoSaveStrategy to be used alongside RetryStrategy
        # If RetryStrategy has already recovered, this won't be used
        return context.get_data("stage_input_data")

class ErrorHandler:
    """Main error handler that coordinates recovery strategies."""
    
    def __init__(self):
        self.strategies: List[ErrorRecoveryStrategy] = []
        
    def add_strategy(self, strategy: ErrorRecoveryStrategy) -> None:
        """Add a recovery strategy."""
        self.strategies.append(strategy)
        
    async def handle_error(self, error: Exception, context: PipelineContext) -> Optional[Any]:
        """
        Handle an error using available recovery strategies.
        
        Returns:
            Optional[Any]: Recovery data if successful, None if no recovery was possible
        """
        logger.error(f"Error in stage {context.get_data('current_stage_name')}: {error}")
        logger.error(f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
        
        recovery_result = None
        
        # Try each strategy in order
        for strategy in self.strategies:
            try:
                if await strategy.can_recover(error, context):
                    logger.info(f"Attempting recovery with {strategy.__class__.__name__}")
                    result = await strategy.recover(error, context)
                    
                    # If this is the first successful recovery, store the result
                    if result is not None and recovery_result is None:
                        recovery_result = result
                        logger.info(f"Recovery successful with {strategy.__class__.__name__}")
                        
                        # Remove the error from context upon successful recovery
                        if error in context.errors:
                            context.errors.remove(error)
                            logger.info(f"Removed error from context after successful recovery: {error}")
            except Exception as e:
                logger.error(f"Error in recovery strategy {strategy.__class__.__name__}: {e}")
        
        if recovery_result is None:
            logger.error("All recovery strategies failed")
            
        return recovery_result

# Create stage-specific error handlers
def create_input_validation_error_handler(checkpoints_dir: Path) -> ErrorHandler:
    """Create error handler for input validation stage."""
    handler = ErrorHandler()
    handler.add_strategy(RetryStrategy(max_retries=2))
    handler.add_strategy(AutoSaveStrategy(checkpoints_dir))
    return handler

def create_content_generation_error_handler(
    checkpoints_dir: Path,
    fallback_templates_dir: Path
) -> ErrorHandler:
    """Create error handler for content generation stage."""
    handler = ErrorHandler()
    handler.add_strategy(RetryStrategy(max_retries=3, initial_delay=2.0))
    handler.add_strategy(FallbackContentStrategy(fallback_templates_dir))
    handler.add_strategy(AutoSaveStrategy(checkpoints_dir))
    return handler

def create_slide_creation_error_handler(checkpoints_dir: Path) -> ErrorHandler:
    """Create error handler for slide creation stage."""
    handler = ErrorHandler()
    handler.add_strategy(RetryStrategy(max_retries=2))
    handler.add_strategy(AutoSaveStrategy(checkpoints_dir))
    return handler

def create_presentation_assembly_error_handler(checkpoints_dir: Path) -> ErrorHandler:
    """Create error handler for presentation assembly stage."""
    handler = ErrorHandler()
    handler.add_strategy(RetryStrategy(max_retries=2))
    handler.add_strategy(AutoSaveStrategy(checkpoints_dir))
    return handler 