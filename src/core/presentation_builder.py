"""
Presentation builder that combines slide content generation and slide creation.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from .slide_content_generator import SlideContentGenerator
from .slide_generator import SlideGenerator
from .theme_manager import ThemeManager
from ..presentation.presentation_exporter import PresentationExporter
from .openai_client import OpenAIClient
from ..utils.text_parser import TextParser
from ..utils.content_mapper import ContentMapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PresentationBuilder:
    """Builds complete presentations by combining content generation and slide creation."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None, api_key: Optional[str] = None,
                 template_path: Optional[str] = None, custom_theme: Optional[Dict[str, Any]] = None):
        """Initialize the presentation builder.
        
        Args:
            openai_client: Optional OpenAIClient instance. If not provided, one will be created.
            api_key: Optional OpenAI API key. If not provided and openai_client is None,
                    will use environment variable.
            template_path: Optional path to PowerPoint template
            custom_theme: Optional custom theme settings
        """
        self.content_generator = SlideContentGenerator(openai_client=openai_client, api_key=api_key)
        self.slide_generator = SlideGenerator(template_path=template_path, custom_theme=custom_theme)
        self.text_parser = TextParser()
        self.content_mapper = ContentMapper()
        
    async def initialize(self) -> None:
        """Initialize the content generator."""
        await self.content_generator.initialize()
        
    async def build_presentation(self, 
                               slide_specs: List[Dict[str, Any]], 
                               output_path: str,
                               export_options: Optional[Dict[str, Any]] = None,
                               max_retries: int = 3) -> Dict[str, Any]:
        """Build a complete presentation.
        
        Args:
            slide_specs: List of dictionaries containing template_type and variables for each slide
            output_path: Path where to save the presentation
            export_options: Optional dictionary with export settings (overwrite, backup, etc.)
            max_retries: Maximum number of retries for content generation
            
        Returns:
            Dictionary containing:
            - path: Path where presentation was saved
            - file_info: Information about the saved file
        """
        # Generate content for all slides
        generated_contents = await self.content_generator.generate_multiple_slides(
            slide_specs, max_retries=max_retries
        )
        
        # Create slides using the generated content
        for content in generated_contents:
            if "error" in content:
                logger.error(f"Error in slide content generation: {content['error']}")
                continue
                
            try:
                # Map template types to slide creation methods
                template_type = content["type"]
                if template_type == "title":
                    self.slide_generator.create_title_slide(content["content"])
                elif template_type == "content":
                    self.slide_generator.create_content_slide(content["content"])
                elif template_type == "section_transition":
                    self.slide_generator.create_section_transition(content["content"])
                elif template_type == "summary":
                    self.slide_generator.create_summary_slide(content["content"])
                else:
                    logger.warning(f"Unknown template type: {template_type}")
            except Exception as e:
                logger.error(f"Error creating slide: {e}")
                
        # Export the presentation
        try:
            exporter = PresentationExporter(self.slide_generator.prs)
            actual_path = exporter.export(output_path, export_options)
            file_info = exporter.get_file_info(actual_path)
            logger.info(f"Presentation saved to {actual_path}")
            return {
                'path': actual_path,
                'file_info': file_info
            }
        except Exception as e:
            logger.error(f"Error exporting presentation: {e}")
            raise
            
    async def build_presentation_from_outline(self,
                                            title: str,
                                            outline: List[Dict[str, Any]],
                                            presenter: str,
                                            date: str,
                                            output_path: str,
                                            export_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a presentation from a high-level outline.
        
        Args:
            title: Presentation title
            outline: List of sections with their content
            presenter: Presenter name
            date: Presentation date
            output_path: Path where to save the presentation
            export_options: Optional dictionary with export settings
            
        Returns:
            Dictionary containing:
            - path: Path where presentation was saved
            - file_info: Information about the saved file
        """
        slide_specs = []
        
        # Add title slide
        slide_specs.append({
            "template_type": "title",
            "variables": {
                "title": title,
                "subtitle": "Generated Presentation",
                "presenter": presenter,
                "date": date
            }
        })
        
        # Process each section
        for i, section in enumerate(outline):
            # Add section transition if not first section
            if i > 0:
                slide_specs.append({
                    "template_type": "section_transition",
                    "variables": {
                        "current_section": section["title"],
                        "next_section": outline[i + 1]["title"] if i + 1 < len(outline) else "Summary"
                    }
                })
                
            # Add content slides for the section
            for content in section["content"]:
                slide_specs.append({
                    "template_type": "content",
                    "variables": {
                        "title": content["title"],
                        "key_points": content["points"],
                        "context": content.get("context", "")
                    }
                })
                
        # Add summary slide
        slide_specs.append({
            "template_type": "summary",
            "variables": {
                "main_topics": [section["title"] for section in outline],
                "key_takeaways": [section["key_takeaway"] for section in outline if "key_takeaway" in section]
            }
        })
        
        # Build the presentation
        return await self.build_presentation(slide_specs, output_path, export_options)
    
    async def build_presentation_from_text(self,
                                         text: str,
                                         presenter: str = "",
                                         date: str = "",
                                         format_type: Optional[str] = None,
                                         content_density: str = "medium",
                                         output_path: str = "output.pptx",
                                         export_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a presentation from user-provided text content.
        
        Args:
            text: User-provided text content for the presentation
            presenter: Presenter name
            date: Presentation date
            format_type: Optional format type ('text', 'markdown', or None for auto-detection)
            content_density: Density of content per slide (low, medium, high)
            output_path: Path where to save the presentation
            export_options: Optional dictionary with export settings
            
        Returns:
            Dictionary containing:
            - path: Path where presentation was saved
            - file_info: Information about the saved file
        """
        # Initialize the content mapper with the specified density
        self.content_mapper = ContentMapper(content_density=content_density)
        
        # Parse the text content
        if format_type is None:
            # Auto-detect format
            parsed_content = self.text_parser.parse_auto(text)
        elif format_type.lower() == 'markdown':
            parsed_content = self.text_parser.parse_markdown(text)
        else:
            parsed_content = self.text_parser.parse(text)
            
        # Create metadata for the presentation
        metadata = {
            "presenter": presenter,
            "date": date
        }
        
        # Map the parsed content to slide specifications
        slide_specs = self.content_mapper.generate_slide_specs_from_text(
            text=text,
            parsed_content=parsed_content,
            metadata=metadata
        )
        
        # If no slides were generated, provide a helpful message
        if not slide_specs:
            logger.warning("No slides could be generated from the provided text")
            raise ValueError("The provided text could not be parsed into presentation slides. "
                            "Please ensure the text includes headings, bullet points, or paragraphs.")
        
        # Build the presentation
        return await self.build_presentation(slide_specs, output_path, export_options)
    
    async def build_presentation_from_text_file(self,
                                              file_path: str,
                                              presenter: str = "",
                                              date: str = "",
                                              format_type: Optional[str] = None,
                                              content_density: str = "medium",
                                              output_path: Optional[str] = None,
                                              export_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a presentation from a text file.
        
        Args:
            file_path: Path to the text file
            presenter: Presenter name
            date: Presentation date
            format_type: Optional format type ('text', 'markdown', or None for auto-detection)
            content_density: Density of content per slide (low, medium, high)
            output_path: Path where to save the presentation (defaults to input filename with .pptx extension)
            export_options: Optional dictionary with export settings
            
        Returns:
            Dictionary containing:
            - path: Path where presentation was saved
            - file_info: Information about the saved file
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is empty or cannot be parsed
        """
        try:
            # Check if file exists
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # If text is empty, raise error
            if not text.strip():
                raise ValueError(f"File is empty: {file_path}")
                
            # Determine output path if not provided
            if output_path is None:
                output_path = str(file_path_obj.with_suffix('.pptx'))
                
            # Detect format type based on file extension if not provided
            if format_type is None:
                extension = file_path_obj.suffix.lower()
                if extension in ['.md', '.markdown']:
                    format_type = 'markdown'
                else:
                    format_type = 'text'
                    
            # Build presentation from the text content
            return await self.build_presentation_from_text(
                text=text,
                presenter=presenter,
                date=date,
                format_type=format_type,
                content_density=content_density,
                output_path=output_path,
                export_options=export_options
            )
            
        except Exception as e:
            logger.error(f"Error building presentation from file: {e}")
            raise
        
    def get_template_info(self) -> Dict[str, Any]:
        """Get information about the current template and theme.
        
        Returns:
            Dictionary containing template and theme information
        """
        theme_info = {
            "colors": list(self.slide_generator.theme_manager.theme["colors"].keys()),
            "font_styles": list(self.slide_generator.theme_manager.theme["fonts"].keys()),
            "spacing": self.slide_generator.theme_manager.theme["spacing"],
            "alignments": {k: str(v) for k, v in self.slide_generator.theme_manager.theme["alignment"].items()}
        }
        
        return {
            "slide_layouts": len(self.slide_generator.prs.slide_layouts),
            "slide_masters": len(self.slide_generator.prs.slide_masters),
            "available_layouts": [
                layout.name for layout in self.slide_generator.prs.slide_layouts
            ],
            "theme": theme_info
        } 