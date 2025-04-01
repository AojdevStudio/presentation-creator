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
from typing import Dict, Any, Optional, List
from datetime import datetime

from .core.pipeline_factory import PipelineFactory
from .core.pipeline import StageResult, PipelineStageStatus
from .core.file_path_manager import FilePathManager
from .core.presentation_builder import PresentationBuilder
from dotenv import load_dotenv

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

# Load environment variables from .env file
load_dotenv()

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

async def generate_presentation(
    topic: str, 
    style: str = "professional", 
    num_slides: int = 10, 
    presenter: str = "", 
    company: str = "",
    output: str = "output.pptx"
) -> Dict[str, Any]:
    """Generate a presentation on a given topic.
    
    Args:
        topic: The presentation topic
        style: Style of the presentation (professional, casual, academic)
        num_slides: Number of slides to generate
        presenter: Name of the presenter
        company: Name of the company
        output: Output file path
        
    Returns:
        Dictionary containing generation results
    """
    # Initialize the presentation builder
    builder = PresentationBuilder()
    await builder.initialize()
    
    # Determine current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Create an outline for the presentation
    outline = [
        {
            "title": "Introduction",
            "content": [
                {
                    "title": "Overview",
                    "points": [f"Introduction to {topic}", "Why this matters", "What we'll cover"],
                    "context": f"Setting the stage for our discussion on {topic}"
                }
            ],
            "key_takeaway": "Understanding the importance of this topic"
        }
    ]
    
    # Add main content sections based on the requested number of slides
    # Allocate slides to sections (roughly 1 title, 1 summary, and the rest distributed)
    content_slides = num_slides - 2  # Accounting for title and summary slides
    
    # Basic distribution: 1/3 for background, 2/3 for main points
    background_section = {
        "title": "Background",
        "content": [
            {
                "title": "Context & History",
                "points": [f"Evolution of {topic}", "Key developments", "Current landscape"],
                "context": f"Historical perspective on {topic}"
            }
        ],
        "key_takeaway": "Historical context is essential to understanding the topic"
    }
    outline.append(background_section)
    
    main_points_section = {
        "title": "Key Points",
        "content": [
            {
                "title": "Main Considerations",
                "points": ["Important aspect 1", "Important aspect 2", "Important aspect 3"],
                "context": f"Critical elements of {topic} to consider"
            },
            {
                "title": "Practical Applications",
                "points": ["Application 1", "Application 2", "Application 3"],
                "context": f"How {topic} is applied in practice"
            }
        ],
        "key_takeaway": "These key points provide a foundation for working with this topic"
    }
    outline.append(main_points_section)
    
    # For larger presentations, add more detail sections
    if num_slides > 6:
        challenges_section = {
            "title": "Challenges & Solutions",
            "content": [
                {
                    "title": "Common Challenges",
                    "points": ["Challenge 1", "Challenge 2", "Challenge 3"],
                    "context": f"Obstacles often encountered with {topic}"
                },
                {
                    "title": "Effective Solutions",
                    "points": ["Solution approach 1", "Solution approach 2", "Solution approach 3"],
                    "context": f"Proven strategies to address challenges in {topic}"
                }
            ],
            "key_takeaway": "Anticipating and solving challenges is key to success"
        }
        outline.append(challenges_section)
    
    # For very detailed presentations, add future trends
    if num_slides > 8:
        future_section = {
            "title": "Future Outlook",
            "content": [
                {
                    "title": "Emerging Trends",
                    "points": ["Trend 1", "Trend 2", "Trend 3"],
                    "context": f"Where {topic} is heading in the future"
                }
            ],
            "key_takeaway": "Staying ahead of trends ensures continued relevance"
        }
        outline.append(future_section)
    
    # Generate the presentation from the outline
    result = await builder.build_presentation_from_outline(
        title=f"{topic}",
        outline=outline,
        presenter=presenter if presenter else "Presenter Name",
        date=current_date,
        output_path=output
    )
    
    return result

async def generate_presentation_from_text(
    text: str,
    format_type: Optional[str] = None,
    presenter: str = "",
    date: str = "",
    content_density: str = "medium",
    output: str = "output.pptx"
) -> Dict[str, Any]:
    """Generate a presentation from user-provided text.
    
    Args:
        text: User-provided text content
        format_type: Optional format type ('text', 'markdown', or None for auto-detection)
        presenter: Name of the presenter
        date: Presentation date
        content_density: Density of content per slide (low, medium, high)
        output: Output file path
        
    Returns:
        Dictionary containing generation results
    """
    # Initialize the presentation builder
    builder = PresentationBuilder()
    await builder.initialize()
    
    # Use current date if not provided
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Generate the presentation from text
    result = await builder.build_presentation_from_text(
        text=text,
        presenter=presenter,
        date=date,
        format_type=format_type,
        content_density=content_density,
        output_path=output
    )
    
    return result

async def generate_presentation_from_text_file(
    file_path: str,
    format_type: Optional[str] = None,
    presenter: str = "",
    date: str = "",
    content_density: str = "medium",
    output: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a presentation from a text file.
    
    Args:
        file_path: Path to the text file
        format_type: Optional format type ('text', 'markdown', or None for auto-detection)
        presenter: Name of the presenter
        date: Presentation date
        content_density: Density of content per slide (low, medium, high)
        output: Output file path
        
    Returns:
        Dictionary containing generation results
    """
    # Initialize the presentation builder
    builder = PresentationBuilder()
    await builder.initialize()
    
    # Use current date if not provided
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Generate the presentation from the text file
    result = await builder.build_presentation_from_text_file(
        file_path=file_path,
        presenter=presenter,
        date=date,
        format_type=format_type,
        content_density=content_density,
        output_path=output
    )
    
    return result

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Generate PowerPoint presentations automatically")
    
    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Parser for AI-generated content
    ai_parser = subparsers.add_parser("ai", help="Generate presentation with AI content")
    ai_parser.add_argument("topic", help="Presentation topic")
    ai_parser.add_argument("--style", choices=["professional", "casual", "academic"], 
                        default="professional", help="Presentation style")
    ai_parser.add_argument("--num-slides", type=int, default=10, help="Number of slides to generate")
    ai_parser.add_argument("--presenter", help="Presenter name")
    ai_parser.add_argument("--company", help="Company name")
    ai_parser.add_argument("--output", default="output.pptx", help="Output file path")
    
    # Parser for text input
    text_parser = subparsers.add_parser("text", help="Generate presentation from text input")
    text_parser.add_argument("--text", help="Direct text input for slide generation")
    text_parser.add_argument("--file", help="Path to text file for slide generation")
    text_parser.add_argument("--format", choices=["text", "markdown", "auto"], 
                          default="auto", help="Format of the input text")
    text_parser.add_argument("--presenter", help="Presenter name")
    text_parser.add_argument("--date", help="Presentation date (YYYY-MM-DD)")
    text_parser.add_argument("--density", choices=["low", "medium", "high"], 
                          default="medium", help="Density of content per slide")
    text_parser.add_argument("--output", help="Output file path")
    
    return parser

async def main_async(args: Optional[List[str]] = None) -> int:
    """Asynchronous main function that processes command-line arguments.
    
    Args:
        args: Command-line arguments (if None, sys.argv is used)
        
    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    try:
        if parsed_args.command == "ai":
            # Generate presentation with AI content
            result = await generate_presentation(
                topic=parsed_args.topic,
                style=parsed_args.style,
                num_slides=parsed_args.num_slides,
                presenter=parsed_args.presenter or "",
                company=parsed_args.company or "",
                output=parsed_args.output
            )
            
            print(f"Presentation generated successfully at {result['path']}")
        elif parsed_args.command == "text":
            # Determine if we're using file or direct text input
            if parsed_args.file:
                # Format handling
                format_type = parsed_args.format
                if format_type == "auto":
                    format_type = None  # Let the system auto-detect
                
                # Generate from file
                result = await generate_presentation_from_text_file(
                    file_path=parsed_args.file,
                    format_type=format_type,
                    presenter=parsed_args.presenter or "",
                    date=parsed_args.date or "",
                    content_density=parsed_args.density,
                    output=parsed_args.output
                )
                
                print(f"Presentation generated successfully at {result['path']}")
            elif parsed_args.text:
                # Format handling
                format_type = parsed_args.format
                if format_type == "auto":
                    format_type = None  # Let the system auto-detect
                
                # Generate from direct text
                result = await generate_presentation_from_text(
                    text=parsed_args.text,
                    format_type=format_type,
                    presenter=parsed_args.presenter or "",
                    date=parsed_args.date or "",
                    content_density=parsed_args.density,
                    output=parsed_args.output or "output.pptx"
                )
                
                print(f"Presentation generated successfully at {result['path']}")
            else:
                print("Error: Either --text or --file must be provided")
                return 1
                
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

def main() -> int:
    """Entry point for the command-line interface.
    
    Returns:
        Exit code
    """
    return asyncio.run(main_async())

if __name__ == "__main__":
    sys.exit(main()) 