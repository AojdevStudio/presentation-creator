"""
Tests for the StyleManager class.
"""

import pytest
import os
import tempfile
import json
from pathlib import Path

from src.templates.style_manager import StyleManager, StyleValidationError

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def style_manager(temp_dir):
    """Create a StyleManager instance with temporary directories."""
    styles_dir = temp_dir / "styles"
    brands_dir = temp_dir / "brands"
    styles_dir.mkdir()
    brands_dir.mkdir()
    return StyleManager(styles_dir=styles_dir, brands_dir=brands_dir)

@pytest.fixture
def test_brand_data():
    """Sample brand data for testing."""
    return {
        "colors": {
            "primary": "#FF0000",
            "secondary": "#00FF00",
            "text": "#000000",
            "background": "#FFFFFF"
        },
        "fonts": {
            "title": {
                "name": "Test Font",
                "size": 24,
                "bold": True,
                "color": "#FF0000"
            },
            "body": {
                "name": "Test Font",
                "size": 12,
                "bold": False,
                "color": "#000000"
            }
        }
    }

@pytest.fixture
def test_template_style():
    """Sample template style for testing."""
    return {
        "colors": {
            "primary": "#0000FF",
            "accent1": "#FFFF00"
        },
        "fonts": {
            "title": {
                "size": 36
            }
        }
    }

def test_load_global_styles(style_manager):
    """Test loading global styles."""
    global_styles = style_manager._global_styles
    
    # Verify essential sections exist in global styles
    assert "colors" in global_styles
    assert "fonts" in global_styles
    assert "spacing" in global_styles
    
    # Check default colors
    assert "primary" in global_styles["colors"]
    assert "secondary" in global_styles["colors"]
    
    # Check default fonts
    assert "title" in global_styles["fonts"]
    assert "body" in global_styles["fonts"]

def test_create_brand(style_manager, test_brand_data):
    """Test creating a brand."""
    style_manager.create_brand("test_brand", test_brand_data)
    
    # Check if brand file was created
    brand_file = style_manager.brands_dir / "test_brand.json"
    assert brand_file.exists()
    
    # Verify brand data was saved correctly
    with open(brand_file, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data["colors"]["primary"] == "#FF0000"
    assert saved_data["fonts"]["title"]["name"] == "Test Font"

def test_load_template_style(style_manager, test_template_style):
    """Test loading a template style."""
    # Save a template style
    loaded_style = style_manager.load_template_style("test_template", test_template_style)
    
    # Check if template file was created
    template_file = style_manager.styles_dir / "template_test_template.json"
    assert template_file.exists()
    
    # Verify template data was saved and returned correctly
    assert loaded_style["colors"]["primary"] == "#0000FF"
    
    # Test loading existing template style
    loaded_style = style_manager.load_template_style("test_template")
    assert loaded_style["colors"]["primary"] == "#0000FF"

def test_get_merged_style(style_manager, test_brand_data, test_template_style):
    """Test merging styles from different levels."""
    # Create a brand and template style
    style_manager.create_brand("test_brand", test_brand_data)
    style_manager.load_template_style("test_template", test_template_style)
    
    # Get merged style (global + brand + template)
    merged_style = style_manager.get_merged_style("test_template", "test_brand")
    
    # Check colors (template overrides brand, brand overrides global)
    assert merged_style["colors"]["primary"] == "#0000FF"  # From template
    assert merged_style["colors"]["secondary"] == "#00FF00"  # From brand
    
    # Check fonts (template partially overrides brand)
    assert merged_style["fonts"]["title"]["name"] == "Test Font"  # From brand
    assert merged_style["fonts"]["title"]["size"] == 36  # From template
    assert merged_style["fonts"]["title"]["bold"] is True  # From brand

def test_get_merged_style_with_element(style_manager, test_brand_data, test_template_style):
    """Test merging styles with element-specific overrides."""
    # Create a brand and template style
    style_manager.create_brand("test_brand", test_brand_data)
    style_manager.load_template_style("test_template", test_template_style)
    
    # Define element-specific overrides
    element_style = {
        "colors": {
            "primary": "#PURPLE",
            "text": "#ELEMENT"
        }
    }
    
    # Get merged style with element overrides
    merged_style = style_manager.get_merged_style("test_template", "test_brand", element_style)
    
    # Check colors (element overrides template, brand, and global)
    assert merged_style["colors"]["primary"] == "#PURPLE"  # From element
    assert merged_style["colors"]["text"] == "#ELEMENT"  # From element
    assert merged_style["colors"]["secondary"] == "#00FF00"  # From brand

def test_validation(style_manager):
    """Test validation of brand data."""
    # Invalid brand data (missing required section)
    invalid_data = {
        "colors": {
            "primary": "#FF0000"
        }
        # Missing fonts section
    }
    
    # Valid brand data
    valid_data = {
        "colors": {
            "primary": "#FF0000"
        },
        "fonts": {
            "title": {
                "name": "Test Font"
            }
        }
    }
    
    # Invalid color format
    invalid_color_data = {
        "colors": {
            "primary": "not-a-color"
        },
        "fonts": {
            "title": {
                "name": "Test Font"
            }
        }
    }
    
    # Test validation
    with pytest.raises(StyleValidationError):
        style_manager.create_brand("invalid_brand", invalid_data)
    
    with pytest.raises(StyleValidationError):
        style_manager.create_brand("invalid_color_brand", invalid_color_data)
        
    # Valid data should not raise
    style_manager.create_brand("valid_brand", valid_data)

def test_get_specific_style(style_manager, test_brand_data, test_template_style):
    """Test getting a specific style property using dot notation."""
    # Create a brand and template style
    style_manager.create_brand("test_brand", test_brand_data)
    style_manager.load_template_style("test_template", test_template_style)
    
    # Get specific properties
    primary_color = style_manager.get_specific_style("colors.primary", "test_template", "test_brand")
    font_name = style_manager.get_specific_style("fonts.title.name", "test_template", "test_brand")
    font_size = style_manager.get_specific_style("fonts.title.size", "test_template", "test_brand")
    
    assert primary_color == "#0000FF"  # From template
    assert font_name == "Test Font"  # From brand
    assert font_size == 36  # From template
    
    # Nonexistent property
    nonexistent = style_manager.get_specific_style("nonexistent.path", "test_template", "test_brand")
    assert nonexistent is None 