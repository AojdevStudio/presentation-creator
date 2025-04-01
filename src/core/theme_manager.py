"""
Theme management for presentations.
"""
import logging
from typing import Dict, Any, Optional
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThemeManager:
    """Manages presentation themes and styling"""
    
    DEFAULT_THEME = {
        "colors": {
            "primary": RGBColor(0, 114, 198),    # Blue
            "secondary": RGBColor(0, 175, 100),   # Green
            "accent1": RGBColor(255, 140, 0),     # Orange
            "accent2": RGBColor(139, 0, 139),     # Purple
            "text": RGBColor(0, 0, 0),           # Black
            "background": RGBColor(255, 255, 255) # White
        },
        "fonts": {
            "title": {
                "name": "Calibri",
                "size": Pt(44),
                "bold": True,
                "color": RGBColor(0, 0, 0)
            },
            "subtitle": {
                "name": "Calibri",
                "size": Pt(32),
                "bold": False,
                "color": RGBColor(89, 89, 89)
            },
            "heading": {
                "name": "Calibri",
                "size": Pt(28),
                "bold": True,
                "color": RGBColor(0, 0, 0)
            },
            "body": {
                "name": "Calibri",
                "size": Pt(18),
                "bold": False,
                "color": RGBColor(0, 0, 0)
            },
            "caption": {
                "name": "Calibri",
                "size": Pt(14),
                "bold": False,
                "color": RGBColor(89, 89, 89)
            }
        },
        "spacing": {
            "paragraph": Pt(12),
            "line": Pt(1.2),
            "margins": {
                "top": Inches(0.5),
                "bottom": Inches(0.5),
                "left": Inches(0.5),
                "right": Inches(0.5)
            }
        },
        "alignment": {
            "title": PP_ALIGN.CENTER,
            "subtitle": PP_ALIGN.CENTER,
            "heading": PP_ALIGN.LEFT,
            "body": PP_ALIGN.LEFT,
            "caption": PP_ALIGN.LEFT
        }
    }
    
    def __init__(self, custom_theme: Optional[Dict[str, Any]] = None):
        """Initialize the theme manager.
        
        Args:
            custom_theme: Optional custom theme to override default settings
        """
        self.theme = self.DEFAULT_THEME.copy()
        if custom_theme:
            self._merge_theme(custom_theme)
            
    def _merge_theme(self, custom_theme: Dict[str, Any]) -> None:
        """Merge custom theme settings with default theme.
        
        Args:
            custom_theme: Custom theme settings to merge
        """
        for category, settings in custom_theme.items():
            if category in self.theme:
                if isinstance(settings, dict):
                    self.theme[category].update(settings)
                else:
                    self.theme[category] = settings
                    
    def apply_text_style(self, paragraph, style_type: str) -> None:
        """Apply text styling to a paragraph.
        
        Args:
            paragraph: The paragraph to style
            style_type: Type of style to apply (title, subtitle, heading, body, caption)
        """
        if style_type not in self.theme["fonts"]:
            logger.warning(f"Unknown style type: {style_type}")
            return
            
        font_settings = self.theme["fonts"][style_type]
        font = paragraph.font
        
        font.name = font_settings["name"]
        font.size = font_settings["size"]
        font.bold = font_settings["bold"]
        font.color.rgb = font_settings["color"]
        
        paragraph.alignment = self.theme["alignment"].get(style_type, PP_ALIGN.LEFT)
        paragraph.space_after = self.theme["spacing"]["paragraph"]
        paragraph.line_spacing = self.theme["spacing"]["line"]
        
    def get_color(self, color_type: str) -> RGBColor:
        """Get a theme color.
        
        Args:
            color_type: Type of color to get (primary, secondary, accent1, accent2, text, background)
            
        Returns:
            RGBColor object for the requested color
        """
        return self.theme["colors"].get(color_type, RGBColor(0, 0, 0))
        
    def get_margin(self, side: str) -> float:
        """Get margin setting.
        
        Args:
            side: Which margin to get (top, bottom, left, right)
            
        Returns:
            Margin value in inches
        """
        return self.theme["spacing"]["margins"].get(side, Inches(0.5)) 