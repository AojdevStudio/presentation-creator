"""
Template Management System

This module provides a comprehensive template management system that allows
for creating, saving, loading, and previewing presentation templates.
"""

import os
import json
import logging
import shutil
import yaml
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from enum import Enum
from copy import deepcopy

from .style_manager import StyleManager
from .brand_manager import BrandManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """Types of templates supported by the system"""
    TITLE = "title"
    CONTENT = "content"
    DATA_VISUALIZATION = "data_viz"
    SECTION_TRANSITION = "transition"
    SUMMARY = "summary"
    CUSTOM = "custom"

class TemplateValidationError(Exception):
    """Exception raised for template validation errors"""
    pass

class TemplateManager:
    """
    Manages presentation templates with support for creation, saving, loading, and preview.
    
    The TemplateManager works with StyleManager and BrandManager to integrate
    styles and brand guidelines into templates.
    """
    
    def __init__(self, 
                 templates_dir: Optional[Path] = None,
                 previews_dir: Optional[Path] = None,
                 style_manager: Optional[StyleManager] = None,
                 brand_manager: Optional[BrandManager] = None):
        """
        Initialize the TemplateManager.
        
        Args:
            templates_dir: Directory for template definitions
            previews_dir: Directory for template previews
            style_manager: Optional StyleManager instance to use for style integration
            brand_manager: Optional BrandManager instance to use for brand integration
        """
        self.templates_dir = templates_dir or Path("templates/base")
        self.previews_dir = previews_dir or Path("templates/previews")
        self.style_manager = style_manager or StyleManager()
        self.brand_manager = brand_manager or BrandManager(style_manager=self.style_manager)
        
        # Create directories if they don't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize templates dict
        self._templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all templates from templates directory.
        
        Returns:
            Dictionary of template configurations by name
        """
        templates = {}
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    template_name = template_file.stem
                    templates[template_name] = template_data
                    logger.info(f"Loaded template: {template_name}")
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")
                
        return templates
        
    def create_template(self, name: str, template_data: Dict[str, Any], 
                      force_overwrite: bool = False) -> Dict[str, Any]:
        """
        Create a new template or update an existing one.
        
        Args:
            name: Template name
            template_data: Template configuration
            force_overwrite: Whether to overwrite existing template
            
        Returns:
            Template configuration
            
        Raises:
            ValueError: If template already exists and force_overwrite is False
            TemplateValidationError: If template data is invalid
        """
        if name in self._templates and not force_overwrite:
            raise ValueError(f"Template '{name}' already exists. Use force_overwrite=True to replace.")
            
        # Validate template data
        self._validate_template(template_data)
        
        # Save template
        template_path = self.templates_dir / f"{name}.json"
        with open(template_path, 'w') as f:
            json.dump(template_data, f, indent=2)
            
        # Update in-memory cache
        self._templates[name] = template_data
        
        logger.info(f"Created/updated template: {name}")
        return template_data
        
    def _validate_template(self, template_data: Dict[str, Any]) -> None:
        """
        Validate template data structure.
        
        Args:
            template_data: Template configuration to validate
            
        Raises:
            TemplateValidationError: If template is invalid
        """
        required_fields = ["type", "layout", "elements"]
        
        for field in required_fields:
            if field not in template_data:
                raise TemplateValidationError(f"Missing required field: {field}")
                
        # Validate template type
        template_type = template_data["type"]
        valid_types = [t.value for t in TemplateType]
        if template_type not in valid_types:
            raise TemplateValidationError(
                f"Invalid template type: {template_type}. Valid types: {', '.join(valid_types)}"
            )
            
        # Validate elements
        if not isinstance(template_data["elements"], dict):
            raise TemplateValidationError("Elements must be a dictionary")
            
        for element_id, element in template_data["elements"].items():
            if not isinstance(element, dict):
                raise TemplateValidationError(f"Element '{element_id}' must be a dictionary")
                
            if "type" not in element:
                raise TemplateValidationError(f"Element '{element_id}' is missing required field: type")
                
    def get_template(self, name: str) -> Dict[str, Any]:
        """
        Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template configuration
            
        Raises:
            KeyError: If template not found
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' not found")
            
        return deepcopy(self._templates[name])
        
    def get_template_list(self) -> List[str]:
        """
        Get list of available templates.
        
        Returns:
            List of template names
        """
        return list(self._templates.keys())
        
    def delete_template(self, name: str) -> None:
        """
        Delete a template.
        
        Args:
            name: Template name
            
        Raises:
            KeyError: If template not found
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' not found")
            
        # Remove template file
        template_path = self.templates_dir / f"{name}.json"
        if template_path.exists():
            template_path.unlink()
            
        # Remove preview if exists
        preview_path = self.previews_dir / f"{name}_preview.html"
        if preview_path.exists():
            preview_path.unlink()
            
        # Remove from in-memory cache
        del self._templates[name]
        
        logger.info(f"Deleted template: {name}")
        
    def generate_template_preview(self, template_name: str, brand_name: Optional[str] = None,
                                output_dir: Optional[Path] = None) -> Path:
        """
        Generate a preview of a template with optional brand styling.
        
        Args:
            template_name: Template name
            brand_name: Optional brand name to apply
            output_dir: Optional output directory
            
        Returns:
            Path to the generated HTML preview
            
        Raises:
            KeyError: If template or brand not found
        """
        if template_name not in self._templates:
            raise KeyError(f"Template '{template_name}' not found")
            
        if brand_name and brand_name not in self.brand_manager.get_brand_list():
            raise KeyError(f"Brand '{brand_name}' not found")
            
        if not output_dir:
            output_dir = self.previews_dir
            output_dir.mkdir(exist_ok=True)
            
        template_data = self._templates[template_name]
        style = self.style_manager.get_merged_style(template_name, brand_name)
        
        # Generate preview filename
        brand_suffix = f"_{brand_name}" if brand_name else ""
        preview_path = output_dir / f"{template_name}{brand_suffix}_preview.html"
        
        # Generate HTML preview
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{template_name} Template Preview</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; padding: 20px; }",
            ".preview-container { border: 1px solid #ccc; padding: 20px; margin: 20px auto; max-width: 800px; }",
            ".element { border: 1px dashed #aaa; margin: 10px; padding: 10px; position: relative; }",
            ".element-label { position: absolute; top: 0; right: 0; background: #f0f0f0; padding: 2px 5px; font-size: 12px; }",
            ".text-element { font-family: Arial, sans-serif; }",
            ".title { font-size: 24px; font-weight: bold; }",
            ".subtitle { font-size: 18px; }",
            ".bullet-list { list-style-type: disc; padding-left: 20px; }",
            ".image-placeholder { background: #eee; text-align: center; padding: 20px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{template_name} Template Preview</h1>"
        ]
        
        # Add brand info if provided
        if brand_name:
            html_content.append(f"<p><strong>Brand:</strong> {brand_name}</p>")
            
        # Add template type info
        html_content.append(f"<p><strong>Type:</strong> {template_data['type']}</p>")
        
        # Add style info
        html_content.append("<h2>Applied Style</h2>")
        html_content.append("<pre style='max-height: 200px; overflow: auto; background: #f5f5f5; padding: 10px;'>")
        html_content.append(json.dumps(style, indent=2))
        html_content.append("</pre>")
        
        # Add template preview
        html_content.append("<h2>Template Layout</h2>")
        html_content.append("<div class='preview-container'>")
        
        # Render elements based on their type and position
        for element_id, element in template_data["elements"].items():
            element_type = element["type"]
            element_style = element.get("style", {})
            
            # Convert element style to inline CSS
            css_props = []
            if "position" in element_style:
                position = element_style["position"]
                css_props.append(f"position: absolute")
                css_props.append(f"left: {position.get('x', 0)}px")
                css_props.append(f"top: {position.get('y', 0)}px")
            if "width" in element_style:
                css_props.append(f"width: {element_style['width']}px")
            if "height" in element_style:
                css_props.append(f"height: {element_style['height']}px")
                
            style_attr = f" style='{'; '.join(css_props)}'" if css_props else ""
            
            html_content.append(f"<div class='element'{style_attr}>")
            html_content.append(f"<div class='element-label'>{element_id}: {element_type}</div>")
            
            # Render element content based on type
            if element_type == "text":
                font_size = element_style.get("fontSize", 16)
                font_weight = "bold" if element_style.get("bold", False) else "normal"
                text_align = element_style.get("textAlign", "left")
                
                html_content.append(f"<div class='text-element' style='font-size: {font_size}px; font-weight: {font_weight}; text-align: {text_align};'>")
                html_content.append(element.get("placeholder", "Text content"))
                html_content.append("</div>")
                
            elif element_type == "title":
                html_content.append("<div class='title'>")
                html_content.append(element.get("placeholder", "Slide Title"))
                html_content.append("</div>")
                
            elif element_type == "subtitle":
                html_content.append("<div class='subtitle'>")
                html_content.append(element.get("placeholder", "Slide Subtitle"))
                html_content.append("</div>")
                
            elif element_type == "bullet_list":
                html_content.append("<ul class='bullet-list'>")
                placeholder_items = element.get("placeholder", ["Item 1", "Item 2", "Item 3"])
                for item in placeholder_items:
                    html_content.append(f"<li>{item}</li>")
                html_content.append("</ul>")
                
            elif element_type == "image":
                html_content.append("<div class='image-placeholder'>")
                html_content.append("[Image Placeholder]")
                html_content.append("</div>")
                
            else:
                html_content.append(f"<div>[{element_type} Element]</div>")
                
            html_content.append("</div>")
            
        html_content.append("</div>")
        
        # Close HTML
        html_content.append("</body>")
        html_content.append("</html>")
        
        # Write to file
        with open(preview_path, 'w') as f:
            f.write("\n".join(html_content))
            
        logger.info(f"Generated template preview: {preview_path}")
        return preview_path
        
    def apply_style_to_template(self, template_name: str, style_data: Dict[str, Any], 
                              save_as: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply a style to a template and optionally save as a new template.
        
        Args:
            template_name: Source template name
            style_data: Style data to apply
            save_as: Name to save the styled template as (None to modify in place)
            
        Returns:
            Updated template data
            
        Raises:
            KeyError: If template not found
        """
        if template_name not in self._templates:
            raise KeyError(f"Template '{template_name}' not found")
            
        # Get template and apply style
        template_data = deepcopy(self._templates[template_name])
        
        # Update base style reference
        template_data["style"] = style_data
        
        # Update element styles
        for element_id, element in template_data["elements"].items():
            if "style" in element:
                # Merge specific style properties from the global style based on element type
                element_type = element["type"]
                if element_type in style_data.get("elements", {}):
                    element["style"] = {**style_data["elements"][element_type], **element["style"]}
        
        # Save as new template or update existing
        target_name = save_as or template_name
        return self.create_template(target_name, template_data, force_overwrite=True)
        
    def duplicate_template(self, source_name: str, new_name: str) -> Dict[str, Any]:
        """
        Duplicate an existing template with a new name.
        
        Args:
            source_name: Source template name
            new_name: New template name
            
        Returns:
            Duplicated template data
            
        Raises:
            KeyError: If source template not found
            ValueError: If new template name already exists
        """
        if source_name not in self._templates:
            raise KeyError(f"Template '{source_name}' not found")
            
        if new_name in self._templates:
            raise ValueError(f"Template '{new_name}' already exists")
            
        # Duplicate template
        template_data = deepcopy(self._templates[source_name])
        return self.create_template(new_name, template_data)
        
    def export_template_to_yaml(self, template_name: str, output_path: Optional[Path] = None) -> Path:
        """
        Export a template to YAML format.
        
        Args:
            template_name: Template name
            output_path: Optional output file path
            
        Returns:
            Path to the exported file
            
        Raises:
            KeyError: If template not found
        """
        if template_name not in self._templates:
            raise KeyError(f"Template '{template_name}' not found")
            
        template_data = self._templates[template_name]
        
        if not output_path:
            output_path = self.templates_dir / f"export_{template_name}.yaml"
            
        with open(output_path, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False)
            
        logger.info(f"Exported template to {output_path}")
        return output_path
        
    def import_template_from_yaml(self, yaml_path: Path, template_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Import a template from a YAML file.
        
        Args:
            yaml_path: Path to YAML file
            template_name: Optional name to save the template as (defaults to filename without extension)
            
        Returns:
            Imported template data
            
        Raises:
            FileNotFoundError: If YAML file not found
            TemplateValidationError: If template data is invalid
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")
            
        # Load template data from YAML
        with open(yaml_path, 'r') as f:
            try:
                template_data = yaml.safe_load(f)
            except Exception as e:
                raise TemplateValidationError(f"Invalid YAML file: {e}")
                
        # Validate template data
        self._validate_template(template_data)
        
        # Save template
        name = template_name or yaml_path.stem
        return self.create_template(name, template_data) 