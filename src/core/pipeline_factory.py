"""
Pipeline Factory

This module provides a factory class for constructing the presentation generation
pipeline with all its stages properly configured and connected.
"""

from typing import Optional, Dict, Any
import logging
from pathlib import Path

from .pipeline import Pipeline
from .presentation_pipeline_stages import (
    InputValidationStage,
    ContentGenerationStage,
    SlideCreationStage,
    PresentationAssemblyStage
)
from .pipeline_error_handlers import (
    create_input_validation_error_handler,
    create_content_generation_error_handler,
    create_slide_creation_error_handler,
    create_presentation_assembly_error_handler
)
from .data_input_handler import DataInputHandler
from .openai_client import OpenAIClient
from .slide_content_generator import SlideContentGenerator
from .slide_generator import SlideGenerator
from .theme_manager import ThemeManager
from .presentation_builder import PresentationBuilder
from ..presentation.presentation_finalizer import PresentationFinalizer

logger = logging.getLogger(__name__)

class PipelineFactory:
    """Factory class for creating presentation generation pipelines."""
    
    def __init__(self, base_dir: Optional[Path] = None, input_path: Optional[Path] = None):
        # Initialize component instances
        self.input_handler = DataInputHandler(input_path) if input_path else None
        self.openai_client = OpenAIClient()
        self.content_generator = SlideContentGenerator(openai_client=self.openai_client)
        self.slide_generator = SlideGenerator()
        self.theme_manager = ThemeManager()
        self.presentation_builder = PresentationBuilder(openai_client=self.openai_client)
        
        # Set up error handling directories
        self.base_dir = base_dir or Path.cwd()
        self.checkpoints_dir = self.base_dir / "checkpoints"
        self.fallback_templates_dir = self.base_dir / "templates" / "fallback"
        
        # Create directories if they don't exist
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.fallback_templates_dir.mkdir(parents=True, exist_ok=True)
        
    async def create_pipeline(self, config: Optional[Dict[str, Any]] = None) -> Pipeline:
        """
        Create and configure a presentation generation pipeline.
        
        Args:
            config: Optional configuration dictionary for customizing the pipeline
            
        Returns:
            A configured Pipeline instance ready for execution
        """
        # Create pipeline stages
        input_stage = InputValidationStage(self.input_handler)
        content_stage = ContentGenerationStage(self.openai_client, self.content_generator)
        slide_stage = SlideCreationStage(self.slide_generator, self.theme_manager)
        assembly_stage = PresentationAssemblyStage(
            self.presentation_builder
        )
        
        # Connect stages
        input_stage.add_next_stage(content_stage)
        content_stage.add_next_stage(slide_stage)
        slide_stage.add_next_stage(assembly_stage)
        
        # Create pipeline
        pipeline = Pipeline(input_stage)
        
        # Add stage-specific error handlers
        self._add_error_handlers(pipeline)
        
        # Add performance monitoring
        self._add_performance_monitoring(pipeline)
        
        # Apply custom configuration if provided
        if config:
            self._apply_configuration(pipeline, config)
        
        return pipeline
    
    def _add_error_handlers(self, pipeline: Pipeline) -> None:
        """Add stage-specific error handlers to all stages."""
        stages = self._get_all_stages(pipeline)
        
        # Create error handlers for each stage
        handlers = {
            "Input Validation": create_input_validation_error_handler(self.checkpoints_dir),
            "Content Generation": create_content_generation_error_handler(
                self.checkpoints_dir,
                self.fallback_templates_dir
            ),
            "Slide Creation": create_slide_creation_error_handler(self.checkpoints_dir),
            "Presentation Assembly": create_presentation_assembly_error_handler(self.checkpoints_dir)
        }
        
        # Add error handlers to stages
        for stage in stages:
            if stage.name in handlers:
                async def create_handler(stage_handler):
                    async def error_handler(error: Exception, context: Any) -> None:
                        context.set_data("current_stage_name", stage.name)
                        result = await stage_handler.handle_error(error, context)
                        if result is not None:
                            context.set_data("stage_input_data", result)
                    return error_handler
                
                stage.add_error_handler(create_handler(handlers[stage.name]))
    
    def _add_performance_monitoring(self, pipeline: Pipeline) -> None:
        """Add performance monitoring to the pipeline."""
        async def performance_observer(stage: Any, result: Any, context: Any) -> None:
            stage_time = context.get_data(f"{stage.name.lower()}_time")
            if stage_time:
                logger.info(f"Stage {stage.name} completed at {stage_time}")
                
        pipeline.add_observer(performance_observer)
    
    def _apply_configuration(self, pipeline: Pipeline, config: Dict[str, Any]) -> None:
        """Apply custom configuration to the pipeline."""
        # Pipeline configuration
        if "theme" in config:
            pipeline.context.set_data("theme_name", config["theme"])
        if "output_format" in config:
            pipeline.context.set_data("output_format", config["output_format"])
            
        # Error handling configuration
        if "max_retries" in config:
            pipeline.context.set_data("max_retries", config["max_retries"])
        if "checkpoints_enabled" in config:
            pipeline.context.set_data("checkpoints_enabled", config["checkpoints_enabled"])
        if "fallback_templates_enabled" in config:
            pipeline.context.set_data("fallback_templates_enabled", config["fallback_templates_enabled"])
    
    def _get_all_stages(self, pipeline: Pipeline) -> list:
        """Get all stages in the pipeline."""
        stages = []
        current = pipeline.initial_stage
        while current:
            stages.append(current)
            current = current._next_stages[0] if current._next_stages else None
        return stages

# Example usage:
async def create_default_pipeline() -> Pipeline:
    """Create a pipeline with default configuration."""
    factory = PipelineFactory()
    return await factory.create_pipeline()

async def create_custom_pipeline(config: Dict[str, Any]) -> Pipeline:
    """Create a pipeline with custom configuration."""
    factory = PipelineFactory()
    return await factory.create_pipeline(config) 