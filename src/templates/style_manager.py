"""
Style Management System

This module provides a comprehensive style management system that handles inheritance,
overriding, and brand guideline integration for presentation templates.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from enum import Enum
from copy import deepcopy
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StyleLevel(Enum):
    """Hierarchy levels for style inheritance"""
    GLOBAL = 1
    BRAND = 2
    TEMPLATE = 3
    ELEMENT = 4


class StyleValidationError(Exception):
    """Exception raised for style validation errors"""
    pass


class StyleManager:
    """
    Manages style definitions with inheritance support and brand guideline integration.
    
    The StyleManager implements a 4-level inheritance hierarchy:
    1. Global styles (base defaults)
    2. Brand styles (from brand guidelines)
    3. Template styles (specific to a template)
    4. Element styles (specific to a slide element)
    
    Properties at each level can override those defined in higher levels.
    """
    
    def __init__(self, 
                 styles_dir: Optional[Path] = None,
                 brands_dir: Optional[Path] = None):
        """
        Initialize the StyleManager.
        
        Args:
            styles_dir: Directory for style definitions
            brands_dir: Directory for brand guidelines
        """
        self.styles_dir = styles_dir or Path("templates/styles")
        self.brands_dir = brands_dir or Path("templates/brands")
        
        # Create directories if they don't exist
        self.styles_dir.mkdir(parents=True, exist_ok=True)
        self.brands_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize style hierarchy
        self._global_styles = self._load_global_styles()
        self._brand_styles: Dict[str, Dict[str, Any]] = {}
        self._template_styles: Dict[str, Dict[str, Any]] = {}
        self._active_style_cache: Dict[str, Any] = {}
        
        # Load available brands
        self._load_available_brands()
        
    def _load_global_styles(self) -> Dict[str, Any]:
        """
        Load global base styles.
        
        Returns:
            Dictionary of global styles
        """
        global_styles_path = self.styles_dir / "global.json"
        
        # Create default global styles if not exists
        if not global_styles_path.exists():
            default_styles = {
                "colors": {
                    "primary": "#0072C6",    # Blue
                    "secondary": "#00AF64",  # Green
                    "accent1": "#FF8C00",    # Orange
                    "accent2": "#8B008B",    # Purple
                    "text": "#000000",       # Black
                    "background": "#FFFFFF", # White
                },
                "fonts": {
                    "title": {
                        "name": "Calibri",
                        "size": 44,
                        "bold": True,
                        "color": "#000000"
                    },
                    "subtitle": {
                        "name": "Calibri",
                        "size": 32,
                        "bold": False,
                        "color": "#595959"
                    },
                    "heading": {
                        "name": "Calibri",
                        "size": 28,
                        "bold": True,
                        "color": "#000000"
                    },
                    "body": {
                        "name": "Calibri",
                        "size": 18,
                        "bold": False,
                        "color": "#000000"
                    },
                    "caption": {
                        "name": "Calibri",
                        "size": 14,
                        "bold": False,
                        "color": "#595959"
                    }
                },
                "spacing": {
                    "paragraph": 12,
                    "line": 1.2,
                    "margins": {
                        "top": 0.5,
                        "bottom": 0.5,
                        "left": 0.5,
                        "right": 0.5
                    }
                },
                "alignment": {
                    "title": "center",
                    "subtitle": "center",
                    "heading": "left",
                    "body": "left",
                    "caption": "left"
                },
                "slide_layouts": {
                    "title": {
                        "title": {
                            "x": 0.5,
                            "y": 0.3,
                            "width": 9.0,
                            "height": 1.5
                        },
                        "subtitle": {
                            "x": 0.5,
                            "y": 2.0,
                            "width": 9.0,
                            "height": 1.0
                        }
                    },
                    "content": {
                        "title": {
                            "x": 0.5,
                            "y": 0.3,
                            "width": 9.0,
                            "height": 0.8
                        },
                        "content": {
                            "x": 0.5,
                            "y": 1.5,
                            "width": 9.0,
                            "height": 5.0
                        }
                    },
                    "two_column": {
                        "title": {
                            "x": 0.5,
                            "y": 0.3,
                            "width": 9.0,
                            "height": 0.8
                        },
                        "left_column": {
                            "x": 0.5,
                            "y": 1.5,
                            "width": 4.3,
                            "height": 5.0
                        },
                        "right_column": {
                            "x": 5.2,
                            "y": 1.5,
                            "width": 4.3,
                            "height": 5.0
                        }
                    }
                }
            }
            
            # Save default styles
            with open(global_styles_path, 'w') as f:
                json.dump(default_styles, f, indent=2)
                
            return default_styles
        
        # Load existing global styles
        try:
            with open(global_styles_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load global styles: {e}")
            return {}
            
    def _load_available_brands(self) -> None:
        """Load all available brand definitions from the brands directory."""
        if not self.brands_dir.exists():
            return
            
        for brand_file in self.brands_dir.glob("*.json"):
            brand_name = brand_file.stem
            try:
                with open(brand_file, 'r') as f:
                    brand_data = json.load(f)
                    self._brand_styles[brand_name] = brand_data
                    logger.info(f"Loaded brand definition: {brand_name}")
            except Exception as e:
                logger.error(f"Failed to load brand {brand_name}: {e}")
                
    def create_brand(self, name: str, brand_data: Dict[str, Any]) -> None:
        """
        Create or update a brand definition.
        
        Args:
            name: Brand name
            brand_data: Brand definition data
        """
        # Validate brand data
        self._validate_brand_data(brand_data)
        
        # Save brand data
        brand_path = self.brands_dir / f"{name}.json"
        with open(brand_path, 'w') as f:
            json.dump(brand_data, f, indent=2)
            
        # Add to in-memory storage
        self._brand_styles[name] = brand_data
        logger.info(f"Created/updated brand: {name}")
        
        # Clear cache
        self._active_style_cache = {}
        
    def _validate_brand_data(self, brand_data: Dict[str, Any]) -> None:
        """
        Validate brand data structure.
        
        Args:
            brand_data: Brand definition data to validate
            
        Raises:
            StyleValidationError: If validation fails
        """
        required_sections = ["colors", "fonts"]
        
        for section in required_sections:
            if section not in brand_data:
                raise StyleValidationError(f"Missing required section in brand data: {section}")
                
        # Validate colors
        if "colors" in brand_data:
            for color_name, color_value in brand_data["colors"].items():
                if not isinstance(color_value, str) or not color_value.startswith("#"):
                    raise StyleValidationError(f"Invalid color format for {color_name}: {color_value}")
                    
        # Validate fonts
        if "fonts" in brand_data:
            for font_type, font_props in brand_data["fonts"].items():
                if not isinstance(font_props, dict):
                    raise StyleValidationError(f"Invalid font definition for {font_type}")
                if "name" not in font_props:
                    raise StyleValidationError(f"Missing font name for {font_type}")
                    
    def get_brand_list(self) -> List[str]:
        """
        Get list of available brands.
        
        Returns:
            List of brand names
        """
        return list(self._brand_styles.keys())
        
    def load_template_style(self, template_name: str, style_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load or create a template style.
        
        Args:
            template_name: Template identifier
            style_data: Optional style data to save
            
        Returns:
            Template style data
        """
        if style_data:
            # Save new template style
            self._template_styles[template_name] = style_data
            template_path = self.styles_dir / f"template_{template_name}.json"
            with open(template_path, 'w') as f:
                json.dump(style_data, f, indent=2)
            return style_data
            
        # Try to load existing template style
        template_path = self.styles_dir / f"template_{template_name}.json"
        if template_path.exists():
            try:
                with open(template_path, 'r') as f:
                    style_data = json.load(f)
                    self._template_styles[template_name] = style_data
                    return style_data
            except Exception as e:
                logger.error(f"Failed to load template style {template_name}: {e}")
                
        # Return empty dict if no style exists
        self._template_styles[template_name] = {}
        return {}
        
    def get_merged_style(self, template_name: str, brand_name: Optional[str] = None, 
                        element_style: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get fully merged style by applying inheritance hierarchy.
        
        Args:
            template_name: Template identifier
            brand_name: Optional brand to apply
            element_style: Optional element-specific style overrides
            
        Returns:
            Merged style dictionary with all inheritance applied
        """
        # Check cache first
        cache_key = f"{template_name}:{brand_name or 'default'}"
        if cache_key in self._active_style_cache and not element_style:
            return deepcopy(self._active_style_cache[cache_key])
            
        # Build style through inheritance
        result = deepcopy(self._global_styles)
        
        # Apply brand styles if specified
        if brand_name and brand_name in self._brand_styles:
            result = self._deep_merge(result, self._brand_styles[brand_name])
            
        # Apply template styles
        if template_name not in self._template_styles:
            self.load_template_style(template_name)
            
        if self._template_styles[template_name]:
            result = self._deep_merge(result, self._template_styles[template_name])
            
        # Cache template+brand combination
        if not element_style:
            self._active_style_cache[cache_key] = deepcopy(result)
            
        # Apply element-specific styles
        if element_style:
            result = self._deep_merge(result, element_style)
            
        return result
        
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge dictionaries with proper overriding.
        
        Args:
            base: Base dictionary
            override: Override dictionary with higher precedence
            
        Returns:
            Merged dictionary
        """
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
                
        return result
        
    def get_specific_style(self, style_path: str, template_name: str, 
                          brand_name: Optional[str] = None,
                          element_style: Optional[Dict[str, Any]] = None) -> Any:
        """
        Get a specific style property using dot notation path.
        
        Args:
            style_path: Dot notation path to style property (e.g., "colors.primary")
            template_name: Template identifier
            brand_name: Optional brand to apply
            element_style: Optional element-specific style overrides
            
        Returns:
            Style property value or None if not found
        """
        style = self.get_merged_style(template_name, brand_name, element_style)
        
        # Navigate through the path
        parts = style_path.split('.')
        current = style
        
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
            
        return current
        
    def export_style_to_yaml(self, template_name: str, brand_name: Optional[str] = None,
                           output_path: Optional[Path] = None) -> Path:
        """
        Export the merged style for a template to YAML format.
        
        Args:
            template_name: Template identifier
            brand_name: Optional brand to apply
            output_path: Optional output file path
            
        Returns:
            Path to the exported file
        """
        style = self.get_merged_style(template_name, brand_name)
        
        if not output_path:
            brand_suffix = f"_{brand_name}" if brand_name else ""
            output_path = self.styles_dir / f"export_{template_name}{brand_suffix}.yaml"
            
        with open(output_path, 'w') as f:
            yaml.dump(style, f, default_flow_style=False)
            
        logger.info(f"Exported style to {output_path}")
        return output_path
        
    def import_style_from_yaml(self, file_path: Path, as_template: Optional[str] = None,
                             as_brand: Optional[str] = None) -> Dict[str, Any]:
        """
        Import a style from YAML file.
        
        Args:
            file_path: Path to YAML file
            as_template: Optional template name to save as
            as_brand: Optional brand name to save as
            
        Returns:
            The imported style data
            
        Raises:
            StyleValidationError: If the imported style is invalid
        """
        try:
            with open(file_path, 'r') as f:
                style_data = yaml.safe_load(f)
                
            # Save as template if specified
            if as_template:
                self.load_template_style(as_template, style_data)
                
            # Save as brand if specified
            if as_brand:
                self._validate_brand_data(style_data)
                self.create_brand(as_brand, style_data)
                
            return style_data
            
        except Exception as e:
            logger.error(f"Failed to import style: {e}")
            raise StyleValidationError(f"Failed to import style: {e}")
            
    def reset_cache(self) -> None:
        """Reset the style cache."""
        self._active_style_cache = {} 