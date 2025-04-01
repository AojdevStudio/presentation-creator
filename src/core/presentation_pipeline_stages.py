"""
Presentation Generation Pipeline Stages

This module implements the specific pipeline stages for presentation generation,
building upon the core pipeline architecture.
"""

from typing import Dict, Any, List
import logging
from pathlib import Path

from .pipeline import PipelineStage, StageResult, PipelineStageStatus, PipelineContext
from .data_input_handler import DataInputHandler
from .openai_client import OpenAIClient
from .slide_content_generator import SlideContentGenerator
from .slide_generator import SlideGenerator
from .theme_manager import ThemeManager
from .presentation_builder import PresentationBuilder
from ..presentation.presentation_finalizer import PresentationFinalizer
from ..presentation.presentation_exporter import PresentationExporter

logger = logging.getLogger(__name__)

class InputValidationStage(PipelineStage[Dict[str, Any], Dict[str, Any]]):
    """Validates and processes the initial user input."""
    
    def __init__(self, input_handler: DataInputHandler):
        super().__init__("Input Validation")
        self.input_handler = input_handler
        
    async def process(self, data: Dict[str, Any], context: PipelineContext) -> StageResult[Dict[str, Any]]:
        try:
            # Validate and process input data
            validated_data = await self.input_handler.validate_input(data)
            context.set_data("input_validation_time", context.get_data("current_time"))
            
            return StageResult(
                status=PipelineStageStatus.COMPLETED,
                data=validated_data,
                metadata={"input_fields": list(validated_data.keys())}
            )
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return StageResult(
                status=PipelineStageStatus.FAILED,
                error=e,
                metadata={"validation_error": str(e)}
            )

class ContentGenerationStage(PipelineStage[Dict[str, Any], List[Dict[str, Any]]]):
    """Generates slide content using OpenAI."""
    
    def __init__(self, openai_client: OpenAIClient, content_generator: SlideContentGenerator):
        super().__init__("Content Generation")
        self.openai_client = openai_client
        self.content_generator = content_generator
        
    async def process(self, data: Dict[str, Any], context: PipelineContext) -> StageResult[List[Dict[str, Any]]]:
        try:
            # Generate content for each slide
            slide_contents = await self.content_generator.generate_slide_contents(
                topic=data["topic"],
                style=data.get("style", "professional"),
                num_slides=data.get("num_slides", 10)
            )
            
            context.set_data("content_generation_time", context.get_data("current_time"))
            
            return StageResult(
                status=PipelineStageStatus.COMPLETED,
                data=slide_contents,
                metadata={"num_slides": len(slide_contents)}
            )
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return StageResult(
                status=PipelineStageStatus.FAILED,
                error=e,
                metadata={"generation_error": str(e)}
            )

class SlideCreationStage(PipelineStage[List[Dict[str, Any]], List[Dict[str, Any]]]):
    """Creates individual slides with proper formatting and layout."""
    
    def __init__(self, slide_generator: SlideGenerator, theme_manager: ThemeManager):
        super().__init__("Slide Creation")
        self.slide_generator = slide_generator
        self.theme_manager = theme_manager
        
    async def process(self, data: List[Dict[str, Any]], context: PipelineContext) -> StageResult[List[Dict[str, Any]]]:
        try:
            # Apply theme and create slides
            theme = await self.theme_manager.get_theme(context.get_data("theme_name", "default"))
            slides = []
            
            for slide_content in data:
                slide = await self.slide_generator.create_slide(
                    content=slide_content,
                    theme=theme
                )
                slides.append(slide)
                
            context.set_data("slide_creation_time", context.get_data("current_time"))
            
            return StageResult(
                status=PipelineStageStatus.COMPLETED,
                data=slides,
                metadata={"theme_used": theme.name}
            )
        except Exception as e:
            logger.error(f"Slide creation failed: {e}")
            return StageResult(
                status=PipelineStageStatus.FAILED,
                error=e,
                metadata={"creation_error": str(e)}
            )

class PresentationAssemblyStage(PipelineStage[List[Dict[str, Any]], Path]):
    """Assembles the final presentation."""
    
    def __init__(self, presentation_builder: PresentationBuilder):
        super().__init__("Presentation Assembly")
        self.presentation_builder = presentation_builder
        
    async def process(self, data: List[Dict[str, Any]], context: PipelineContext) -> StageResult[Path]:
        try:
            # Build presentation
            presentation = await self.presentation_builder.build_presentation(data)
            
            # Create and use finalizer with the presentation
            presentation_finalizer = PresentationFinalizer(presentation)
            
            # Finalize presentation (add transitions, animations, etc.)
            metadata = {
                "title": context.get_data("title", "Untitled Presentation"),
                "author": context.get_data("author", "Unknown"),
                "company": context.get_data("company", ""),
                "keywords": context.get_data("keywords", ""),
                "comments": context.get_data("comments", ""),
                "footer": context.get_data("footer", "")
            }
            presentation_finalizer.finalize(metadata)
            
            # Create exporter and export to file
            presentation_exporter = PresentationExporter(presentation)
            output_path = await presentation_exporter.export(
                format=context.get_data("output_format", "pptx")
            )
            
            context.set_data("assembly_time", context.get_data("current_time"))
            
            return StageResult(
                status=PipelineStageStatus.COMPLETED,
                data=output_path,
                metadata={
                    "output_format": context.get_data("output_format", "pptx"),
                    "file_size": output_path.stat().st_size
                }
            )
        except Exception as e:
            logger.error(f"Presentation assembly failed: {e}")
            return StageResult(
                status=PipelineStageStatus.FAILED,
                error=e,
                metadata={"assembly_error": str(e)}
            ) 