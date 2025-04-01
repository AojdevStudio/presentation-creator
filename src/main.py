"""
Presentation Generation Pipeline - Main Entry Point

This module provides the main entry point for the end-to-end presentation generation
pipeline, integrating all components and providing a command-line interface for users.
"""

import argparse
import asyncio
import logging
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .core.pipeline_factory import PipelineFactory
from .core.pipeline import StageResult, PipelineStageStatus
from .core.file_path_manager import FilePathManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('presentation_pipeline.log')
    ]
)

logger = logging.getLogger(__name__)

class PresentationGenerator:
    """Main class for orchestrating the presentation generation process."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the presentation generator.
        
        Args:
            config_path: Optional path to a JSON configuration file
        """
        self.config = self._load_config(config_path) if config_path else {}
        self.file_path_manager = FilePathManager()
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}
    
    async def generate_presentation(self, input_data: Dict[str, Any]) -> Path:
        """
        Generate a presentation based on the provided input data.
        
        Args:
            input_data: Dictionary containing presentation requirements
            
        Returns:
            Path to the generated presentation file
        """
        start_time = time.time()
        logger.info("Starting presentation generation")
        
        try:
            # Create pipeline factory
            base_dir = Path(self.config.get("base_dir", os.getcwd()))
            factory = PipelineFactory(base_dir=base_dir)
            
            # Create and configure pipeline
            pipeline = await factory.create_pipeline(self.config)
            
            # Add progress tracking
            self._setup_progress_tracking(pipeline)
            
            # Execute pipeline
            pipeline.context.set_data("start_time", start_time)
            context = await pipeline.execute(input_data)
            
            # Check for errors
            if context.errors:
                for error in context.errors:
                    logger.error(f"Pipeline error: {error}")
                raise RuntimeError("Presentation generation failed. Check logs for details.")
            
            # Get output path from context
            output_path = context.get_data("output_path")
            if not output_path:
                output_path = context.get_data("stage_input_data")
                
            # Log performance metrics
            self._log_performance_metrics(context, start_time)
            
            logger.info(f"Presentation generation completed successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate presentation: {e}")
            end_time = time.time()
            logger.info(f"Total execution time: {end_time - start_time:.2f} seconds")
            raise
    
    def _setup_progress_tracking(self, pipeline: Any) -> None:
        """Set up progress tracking for the pipeline."""
        total_stages = len(pipeline._get_all_stages(pipeline))
        completed_stages = 0
        
        async def progress_observer(stage: Any, result: StageResult, context: Any) -> None:
            nonlocal completed_stages
            if result.status == PipelineStageStatus.COMPLETED:
                completed_stages += 1
                progress = (completed_stages / total_stages) * 100
                logger.info(f"Progress: {progress:.2f}% - Completed stage: {stage.name}")
                context.set_data("progress", progress)
                
        pipeline.add_observer(progress_observer)
    
    def _log_performance_metrics(self, context: Any, start_time: float) -> None:
        """Log performance metrics for the pipeline execution."""
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"Performance Metrics:")
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        
        # Log stage-specific metrics if available
        stages = ["input_validation", "content_generation", "slide_creation", "assembly"]
        for stage in stages:
            stage_time = context.get_data(f"{stage}_time")
            if stage_time:
                logger.info(f"  - {stage.replace('_', ' ').title()} time: {stage_time}")

async def process_args(args: argparse.Namespace) -> None:
    """Process command-line arguments and execute the pipeline."""
    # Create input data dictionary from arguments
    input_data = {
        "topic": args.topic,
        "style": args.style,
        "num_slides": args.num_slides
    }
    
    # Add optional arguments if provided
    if args.author:
        input_data["author"] = args.author
    if args.company:
        input_data["company"] = args.company
    if args.keywords:
        input_data["keywords"] = args.keywords.split(",")
    
    # Create configuration
    config = {
        "theme": args.theme,
        "output_format": args.output_format,
        "max_retries": args.max_retries,
        "checkpoints_enabled": not args.no_checkpoints,
        "fallback_templates_enabled": not args.no_fallback
    }
    
    # Create generator and generate presentation
    config_path = Path(args.config) if args.config else None
    generator = PresentationGenerator(config_path)
    
    try:
        output_path = await generator.generate_presentation(input_data)
        print(f"✓ Presentation generated successfully: {output_path}")
    except Exception as e:
        print(f"✗ Failed to generate presentation: {e}")
        exit(1)

def main():
    """Main entry point for the presentation generation pipeline."""
    parser = argparse.ArgumentParser(description="Generate PowerPoint presentations automatically")
    
    # Required arguments
    parser.add_argument("topic", help="The topic of the presentation")
    
    # Optional arguments
    parser.add_argument("--style", default="professional", help="Presentation style (professional, casual, academic)")
    parser.add_argument("--num-slides", type=int, default=10, help="Number of slides to generate")
    parser.add_argument("--theme", default="default", help="Presentation theme name")
    parser.add_argument("--output-format", default="pptx", choices=["pptx", "pdf"], help="Output format")
    parser.add_argument("--author", help="Author name")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--keywords", help="Comma-separated keywords")
    parser.add_argument("--config", help="Path to JSON configuration file")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries for failed stages")
    parser.add_argument("--no-checkpoints", action="store_true", help="Disable checkpointing")
    parser.add_argument("--no-fallback", action="store_true", help="Disable fallback templates")
    
    args = parser.parse_args()
    
    # Run the asyncio event loop
    asyncio.run(process_args(args))

if __name__ == "__main__":
    main() 