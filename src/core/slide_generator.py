"""
Slide generation functions using python-pptx.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlideGenerator:
    """Generates different types of slides using python-pptx"""
    
    def __init__(self, template_path: Optional[str] = None):
        """Initialize the slide generator.
        
        Args:
            template_path: Optional path to a PowerPoint template file
        """
        self.prs = Presentation(template_path) if template_path else Presentation()
        
    def _add_text_box(self, slide, left: float, top: float, width: float, height: float,
                     text: str, font_size: int = 18, bold: bool = False, 
                     alignment: PP_ALIGN = PP_ALIGN.LEFT) -> None:
        """Add a text box to a slide.
        
        Args:
            slide: The slide to add the text box to
            left: Left position in inches
            top: Top position in inches
            width: Width in inches
            height: Height in inches
            text: Text content
            font_size: Font size in points
            bold: Whether the text should be bold
            alignment: Text alignment
        """
        txBox = slide.shapes.add_textbox(
            Inches(left), Inches(top), Inches(width), Inches(height)
        )
        tf = txBox.text_frame
        tf.text = text
        p = tf.paragraphs[0]
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.alignment = alignment
        
    def create_title_slide(self, content: Dict[str, Any]) -> None:
        """Create a title slide.
        
        Args:
            content: Dictionary containing title, subtitle, presenter, and date
        """
        slide_layout = self.prs.slide_layouts[0]  # Title slide layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title
        title = slide.shapes.title
        title.text = content["title"]
        title.text_frame.paragraphs[0].font.size = Pt(44)
        
        # Add subtitle
        subtitle = slide.placeholders[1]
        subtitle.text = content["subtitle"]
        subtitle.text_frame.paragraphs[0].font.size = Pt(32)
        
        # Add presenter and date
        self._add_text_box(slide, 0.5, 5.0, 4.0, 0.5, 
                          f"Presenter: {content['presenter']}", 
                          font_size=16)
        self._add_text_box(slide, 8.5, 5.0, 2.0, 0.5, 
                          content['date'], 
                          font_size=16, 
                          alignment=PP_ALIGN.RIGHT)
        
    def create_content_slide(self, content: Dict[str, Any]) -> None:
        """Create a content slide with bullet points.
        
        Args:
            content: Dictionary containing title and key points
        """
        slide_layout = self.prs.slide_layouts[1]  # Content slide layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title
        title = slide.shapes.title
        title.text = content["title"]
        
        # Add bullet points
        body = slide.placeholders[1]
        tf = body.text_frame
        tf.text = ""  # Clear default text
        
        for point in content["key_points"]:
            p = tf.add_paragraph()
            p.text = point
            p.level = 0  # Top level bullet
            p.font.size = Pt(18)
            
        # Add context if provided
        if "context" in content:
            self._add_text_box(slide, 0.5, 5.0, 9.0, 0.75,
                             content["context"],
                             font_size=14,
                             alignment=PP_ALIGN.LEFT)
            
    def create_section_transition(self, content: Dict[str, Any]) -> None:
        """Create a section transition slide.
        
        Args:
            content: Dictionary containing current and next section info
        """
        slide_layout = self.prs.slide_layouts[2]  # Section header layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add current section
        title = slide.shapes.title
        title.text = content["current_section"]
        title.text_frame.paragraphs[0].font.size = Pt(40)
        
        # Add next section preview
        subtitle = slide.placeholders[1]
        subtitle.text = f"Coming Up: {content['next_section']}"
        subtitle.text_frame.paragraphs[0].font.size = Pt(32)
        
    def create_summary_slide(self, content: Dict[str, Any]) -> None:
        """Create a summary slide.
        
        Args:
            content: Dictionary containing main topics and key takeaways
        """
        slide_layout = self.prs.slide_layouts[1]  # Content slide layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title
        title = slide.shapes.title
        title.text = "Summary"
        
        # Add main topics and takeaways
        body = slide.placeholders[1]
        tf = body.text_frame
        tf.text = ""  # Clear default text
        
        # Add main topics
        p = tf.add_paragraph()
        p.text = "Main Topics:"
        p.font.bold = True
        p.font.size = Pt(20)
        
        for topic in content["main_topics"]:
            p = tf.add_paragraph()
            p.text = topic
            p.level = 1
            p.font.size = Pt(18)
            
        # Add space between sections
        p = tf.add_paragraph()
        p.text = ""
            
        # Add key takeaways
        p = tf.add_paragraph()
        p.text = "Key Takeaways:"
        p.font.bold = True
        p.font.size = Pt(20)
        
        for takeaway in content["key_takeaways"]:
            p = tf.add_paragraph()
            p.text = takeaway
            p.level = 1
            p.font.size = Pt(18)
            
    def save(self, output_path: str) -> None:
        """Save the presentation.
        
        Args:
            output_path: Path where to save the presentation
        """
        self.prs.save(output_path) 