"""
Core Pipeline Architecture for Presentation Generation

This module implements the core pipeline architecture that orchestrates the entire
presentation generation process. It defines the stage interfaces and provides the
main pipeline implementation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum, auto
import logging
import asyncio
from typing_extensions import Protocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variables for generic pipeline data
T = TypeVar('T')
U = TypeVar('U')

class PipelineStageStatus(Enum):
    """Status of a pipeline stage execution."""
    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()

@dataclass
class StageResult(Generic[T]):
    """Result of a pipeline stage execution."""
    status: PipelineStageStatus
    data: Optional[T] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class PipelineContext:
    """Context object passed through the pipeline stages."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self._data: Dict[str, Any] = {}
        self.errors: List[Exception] = []
        
    def set_data(self, key: str, value: Any) -> None:
        """Store data in the context."""
        self._data[key] = value
        
    def get_data(self, key: str, default: Any = None) -> Any:
        """Retrieve data from the context."""
        return self._data.get(key, default)
    
    def add_error(self, error: Exception) -> None:
        """Add an error to the context."""
        self.errors.append(error)

class PipelineStage(Generic[T, U], ABC):
    """Abstract base class for pipeline stages."""
    
    def __init__(self, name: str):
        self.name = name
        self._next_stages: List['PipelineStage'] = []
        self._error_handlers: List[callable] = []
        self._last_result = None
        
    @abstractmethod
    async def process(self, data: T, context: PipelineContext) -> StageResult[U]:
        """Process the input data and return a result."""
        pass
    
    def add_next_stage(self, stage: 'PipelineStage') -> None:
        """Add a stage to be executed after this one."""
        self._next_stages.append(stage)
        
    def add_error_handler(self, handler: callable) -> None:
        """Add an error handler for this stage."""
        self._error_handlers.append(handler)
        
    async def handle_error(self, error: Exception, context: PipelineContext) -> Optional[Any]:
        """Handle an error that occurred during processing.
        
        Returns:
            Optional[Any]: Recovery data if successful, None if no recovery was possible
        """
        for handler in self._error_handlers:
            try:
                recovery_data = await handler(error, context)
                if recovery_data is not None:
                    return recovery_data
            except Exception as e:
                logger.error(f"Error in error handler for stage {self.name}: {e}")
        return None

class Pipeline:
    """Main pipeline implementation that orchestrates stage execution."""
    
    def __init__(self, initial_stage: PipelineStage):
        self.initial_stage = initial_stage
        self.context = PipelineContext()
        self._observers: List[callable] = []
        
    def add_observer(self, observer: callable) -> None:
        """Add an observer to monitor pipeline execution."""
        self._observers.append(observer)
        
    async def _notify_observers(self, stage: PipelineStage, result: StageResult) -> None:
        """Notify observers of stage completion."""
        for observer in self._observers:
            try:
                await observer(stage, result, self.context)
            except Exception as e:
                logger.error(f"Error in pipeline observer: {e}")
                
    async def execute(self, initial_data: Any) -> PipelineContext:
        """Execute the pipeline with the given initial data."""
        self.context = PipelineContext()
        current_stage = self.initial_stage
        current_data = initial_data
        
        try:
            while current_stage is not None:
                logger.info(f"Executing pipeline stage: {current_stage.name}")
                
                try:
                    # Store current data in context for potential recovery
                    self.context.set_data("stage_input_data", current_data)
                    self.context.set_data("current_stage_name", current_stage.name)
                    
                    result = await current_stage.process(current_data, self.context)
                    # Store the result for later reference
                    current_stage._last_result = result
                    await self._notify_observers(current_stage, result)
                    
                    if result.status == PipelineStageStatus.FAILED:
                        recovery_data = await current_stage.handle_error(result.error, self.context)
                        if recovery_data is not None:
                            # If recovery was successful, retry with the recovered data
                            logger.info(f"Retrying stage {current_stage.name} with recovered data")
                            current_data = recovery_data
                            continue  # Retry the current stage
                        break  # No recovery, so we stop
                        
                    current_data = result.data
                    
                    # Move to the next stage if available
                    if current_stage._next_stages:
                        current_stage = current_stage._next_stages[0]
                    else:
                        current_stage = None
                        
                except Exception as e:
                    logger.error(f"Error in pipeline stage {current_stage.name}: {e}")
                    self.context.add_error(e)
                    
                    # Try to handle the error
                    recovery_data = await current_stage.handle_error(e, self.context)
                    
                    # If recovery was successful, retry the current stage
                    if recovery_data is not None:
                        logger.info(f"Stage {current_stage.name} recovered, retrying with recovered data")
                        current_data = recovery_data
                        continue  # Retry the current stage
                    else:
                        # Recovery failed, stop the pipeline
                        logger.error(f"Failed to recover from error in stage {current_stage.name}")
                        break
                    
        except Exception as e:
            logger.error(f"Critical pipeline error: {e}")
            self.context.add_error(e)
            
        return self.context

# Example stage implementations
class DataValidationStage(PipelineStage[Dict[str, Any], Dict[str, Any]]):
    """Example stage that validates input data."""
    
    async def process(self, data: Dict[str, Any], context: PipelineContext) -> StageResult[Dict[str, Any]]:
        try:
            # Implement validation logic here
            return StageResult(
                status=PipelineStageStatus.COMPLETED,
                data=data,
                metadata={"validated": True}
            )
        except Exception as e:
            return StageResult(
                status=PipelineStageStatus.FAILED,
                error=e,
                metadata={"validation_error": str(e)}
            )

class DataTransformationStage(PipelineStage[Dict[str, Any], Dict[str, Any]]):
    """Example stage that transforms data."""
    
    async def process(self, data: Dict[str, Any], context: PipelineContext) -> StageResult[Dict[str, Any]]:
        try:
            # Implement transformation logic here
            transformed_data = data  # Add actual transformation
            return StageResult(
                status=PipelineStageStatus.COMPLETED,
                data=transformed_data,
                metadata={"transformed": True}
            )
        except Exception as e:
            return StageResult(
                status=PipelineStageStatus.FAILED,
                error=e,
                metadata={"transformation_error": str(e)}
            ) 