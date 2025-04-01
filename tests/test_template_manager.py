"""
Tests for the Template Management System.

This module tests the functionality of the TemplateManager class,
including template creation, validation, preview generation, and YAML import/export.
"""

import pytest
import os
import tempfile
import json
import yaml
import shutil
from pathlib import Path

from src.templates.template_manager import TemplateManager, TemplateType, TemplateValidationError
from src.templates.style_manager import StyleManager
from src.templates.brand_manager import BrandManager

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def templates_dir(temp_dir):
    """Create a temporary templates directory"""
    templates_dir = temp_dir / "templates" / "base"
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir

@pytest.fixture
def previews_dir(temp_dir):
    """Create a temporary previews directory"""
    previews_dir = temp_dir / "templates" / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)
    return previews_dir

@pytest.fixture
def style_manager(temp_dir):
    """Create a StyleManager instance for testing"""
    styles_dir = temp_dir / "templates" / "styles"
    brands_dir = temp_dir / "templates" / "brands"
    
    styles_dir.mkdir(parents=True, exist_ok=True)
    brands_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal global style
    with open(styles_dir / "globals.json", 'w') as f:
        json.dump({
            "colors": {
                "primary": "#0078D7",
                "secondary": "#444444",
                "background": "#FFFFFF"
            },
            "fonts": {
                "title": {"name": "Arial", "size": 32},
                "body": {"name": "Arial", "size": 16}
            }
        }, f)
    
    return StyleManager(styles_dir=styles_dir, brands_dir=brands_dir)

@pytest.fixture
def brand_manager(temp_dir, style_manager):
    """Create a BrandManager instance for testing"""
    brands_dir = temp_dir / "templates" / "brands"
    assets_dir = temp_dir / "templates" / "brands" / "assets"
    
    brands_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    return BrandManager(brands_dir=brands_dir, assets_dir=assets_dir, style_manager=style_manager)

@pytest.fixture
def template_manager(templates_dir, previews_dir, style_manager, brand_manager):
    """Create a TemplateManager instance for testing"""
    return TemplateManager(
        templates_dir=templates_dir,
        previews_dir=previews_dir,
        style_manager=style_manager,
        brand_manager=brand_manager
    )

@pytest.fixture
def test_template_data():
    """Create sample template data for testing"""
    return {
        "type": "title",
        "layout": "standard",
        "elements": {
            "title": {
                "type": "title",
                "placeholder": "Presentation Title",
                "style": {
                    "fontSize": 32,
                    "bold": True,
                    "position": {"x": 50, "y": 150},
                    "width": 700,
                    "textAlign": "center"
                }
            },
            "subtitle": {
                "type": "subtitle",
                "placeholder": "Subtitle goes here",
                "style": {
                    "fontSize": 24,
                    "position": {"x": 50, "y": 250},
                    "width": 700,
                    "textAlign": "center"
                }
            },
            "presenter": {
                "type": "text",
                "placeholder": "Presenter Name",
                "style": {
                    "fontSize": 16,
                    "position": {"x": 50, "y": 350},
                    "width": 700,
                    "textAlign": "center"
                }
            },
            "date": {
                "type": "text",
                "placeholder": "Presentation Date",
                "style": {
                    "fontSize": 14,
                    "position": {"x": 50, "y": 400},
                    "width": 700,
                    "textAlign": "center"
                }
            }
        }
    }

@pytest.fixture
def test_brand_data(brand_manager):
    """Create a test brand for testing"""
    brand_data = {
        "name": "Test Brand",
        "colors": {
            "primary": "#FF0000",
            "secondary": "#00FF00",
            "accent": "#0000FF"
        },
        "fonts": {
            "title": {"name": "Helvetica", "size": 36, "bold": True},
            "subtitle": {"name": "Helvetica", "size": 24},
            "body": {"name": "Arial", "size": 16}
        }
    }
    
    brand_manager.create_brand("test_brand", brand_data)
    return brand_data

def test_create_template(template_manager, test_template_data):
    """Test creating a template"""
    template = template_manager.create_template("test_template", test_template_data)
    
    assert template == test_template_data
    assert "test_template" in template_manager.get_template_list()
    
    # Check if file was created
    template_path = template_manager.templates_dir / "test_template.json"
    assert template_path.exists()
    
    # Check file content
    with open(template_path, 'r') as f:
        saved_data = json.load(f)
        assert saved_data == test_template_data

def test_create_template_with_validation_error(template_manager):
    """Test creating a template with invalid data"""
    # Missing required fields
    invalid_template = {
        "type": "title",
        # Missing "layout" and "elements"
    }
    
    with pytest.raises(TemplateValidationError) as excinfo:
        template_manager.create_template("invalid_template", invalid_template)
    
    assert "Missing required field" in str(excinfo.value)
    
    # Invalid template type
    invalid_template = {
        "type": "invalid_type",
        "layout": "standard",
        "elements": {}
    }
    
    with pytest.raises(TemplateValidationError) as excinfo:
        template_manager.create_template("invalid_template", invalid_template)
    
    assert "Invalid template type" in str(excinfo.value)

def test_get_template(template_manager, test_template_data):
    """Test getting a template"""
    template_manager.create_template("test_template", test_template_data)
    
    template = template_manager.get_template("test_template")
    assert template == test_template_data
    
    # Test getting non-existent template
    with pytest.raises(KeyError) as excinfo:
        template_manager.get_template("non_existent")
    
    assert "not found" in str(excinfo.value)

def test_get_template_list(template_manager, test_template_data):
    """Test getting the list of templates"""
    # Initially empty
    assert template_manager.get_template_list() == []
    
    # Add a template
    template_manager.create_template("test_template1", test_template_data)
    assert template_manager.get_template_list() == ["test_template1"]
    
    # Add another template
    template_manager.create_template("test_template2", test_template_data)
    template_list = template_manager.get_template_list()
    assert len(template_list) == 2
    assert "test_template1" in template_list
    assert "test_template2" in template_list

def test_delete_template(template_manager, test_template_data):
    """Test deleting a template"""
    template_manager.create_template("test_template", test_template_data)
    
    # Generate a preview first
    template_manager.generate_template_preview("test_template")
    
    # Now delete the template
    template_manager.delete_template("test_template")
    
    # Check it's removed from the list
    assert "test_template" not in template_manager.get_template_list()
    
    # Check files are deleted
    template_path = template_manager.templates_dir / "test_template.json"
    preview_path = template_manager.previews_dir / "test_template_preview.html"
    
    assert not template_path.exists()
    assert not preview_path.exists()
    
    # Test deleting non-existent template
    with pytest.raises(KeyError) as excinfo:
        template_manager.delete_template("non_existent")
    
    assert "not found" in str(excinfo.value)

def test_generate_template_preview(template_manager, test_template_data, temp_dir):
    """Test generating a template preview"""
    template_manager.create_template("test_template", test_template_data)
    
    # Generate preview
    preview_path = template_manager.generate_template_preview("test_template")
    
    # Check preview file exists
    assert preview_path.exists()
    
    # Check content (basic check)
    with open(preview_path, 'r') as f:
        content = f.read()
        assert "test_template Template Preview" in content
        assert "Presentation Title" in content
        assert "Subtitle goes here" in content
    
    # Test with custom output directory
    custom_dir = temp_dir / "custom_previews"
    custom_dir.mkdir(exist_ok=True)
    
    custom_preview_path = template_manager.generate_template_preview(
        "test_template", output_dir=custom_dir
    )
    
    assert custom_preview_path.exists()
    assert custom_dir in custom_preview_path.parents

def test_generate_template_preview_with_brand(template_manager, test_template_data, test_brand_data):
    """Test generating a template preview with brand styling"""
    template_manager.create_template("test_template", test_template_data)
    
    # Generate preview with brand
    preview_path = template_manager.generate_template_preview("test_template", brand_name="test_brand")
    
    # Check preview file exists
    assert preview_path.exists()
    
    # Check content includes brand info
    with open(preview_path, 'r') as f:
        content = f.read()
        assert "test_template_test_brand_preview.html" in str(preview_path)
        assert '<strong>Brand:</strong> test_brand' in content
        assert "FF0000" in content  # Brand primary color

def test_apply_style_to_template(template_manager, test_template_data):
    """Test applying a style to a template"""
    template_manager.create_template("test_template", test_template_data)
    
    style_data = {
        "colors": {
            "primary": "#FF0000",
            "secondary": "#00FF00"
        },
        "elements": {
            "title": {
                "fontSize": 40,
                "textAlign": "left"
            }
        }
    }
    
    # Apply style and save as new template
    updated_template = template_manager.apply_style_to_template(
        "test_template", style_data, save_as="styled_template"
    )
    
    # Check the style was applied
    assert updated_template["style"] == style_data
    assert updated_template["elements"]["title"]["style"]["fontSize"] == 40
    assert updated_template["elements"]["title"]["style"]["textAlign"] == "left"
    
    # Check original template is unchanged
    original = template_manager.get_template("test_template")
    assert "style" not in original
    assert original["elements"]["title"]["style"]["fontSize"] == 32
    assert original["elements"]["title"]["style"]["textAlign"] == "center"
    
    # Apply style in place
    template_manager.apply_style_to_template("test_template", style_data)
    
    # Check original template was updated
    original = template_manager.get_template("test_template")
    assert original["style"] == style_data

def test_duplicate_template(template_manager, test_template_data):
    """Test duplicating a template"""
    template_manager.create_template("test_template", test_template_data)
    
    # Duplicate the template
    duplicate = template_manager.duplicate_template("test_template", "duplicate_template")
    
    # Check duplicate is the same as original
    original = template_manager.get_template("test_template")
    assert duplicate == original
    
    # Check duplicate is in the list
    assert "duplicate_template" in template_manager.get_template_list()
    
    # Check duplicate file exists
    duplicate_path = template_manager.templates_dir / "duplicate_template.json"
    assert duplicate_path.exists()
    
    # Test duplicating to an existing name
    with pytest.raises(ValueError) as excinfo:
        template_manager.duplicate_template("test_template", "duplicate_template")
    
    assert "already exists" in str(excinfo.value)
    
    # Test duplicating a non-existent template
    with pytest.raises(KeyError) as excinfo:
        template_manager.duplicate_template("non_existent", "new_template")
    
    assert "not found" in str(excinfo.value)

def test_export_template_to_yaml(template_manager, test_template_data, temp_dir):
    """Test exporting a template to YAML"""
    template_manager.create_template("test_template", test_template_data)
    
    # Export to default location
    export_path = template_manager.export_template_to_yaml("test_template")
    
    # Check file exists
    assert export_path.exists()
    assert export_path.name == "export_test_template.yaml"
    
    # Check content
    with open(export_path, 'r') as f:
        exported_data = yaml.safe_load(f)
        assert exported_data == test_template_data
    
    # Export to custom location
    custom_path = temp_dir / "custom_export.yaml"
    export_path = template_manager.export_template_to_yaml("test_template", custom_path)
    
    assert export_path.exists()
    assert export_path == custom_path
    
    # Test exporting a non-existent template
    with pytest.raises(KeyError) as excinfo:
        template_manager.export_template_to_yaml("non_existent")
    
    assert "not found" in str(excinfo.value)

def test_import_template_from_yaml(template_manager, test_template_data, temp_dir):
    """Test importing a template from YAML"""
    # Create a YAML file
    yaml_path = temp_dir / "template.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(test_template_data, f)
    
    # Import the template
    imported = template_manager.import_template_from_yaml(yaml_path)
    
    # Check the template was imported
    assert "template" in template_manager.get_template_list()
    assert imported == test_template_data
    
    # Import with custom name
    imported = template_manager.import_template_from_yaml(yaml_path, "custom_name")
    
    assert "custom_name" in template_manager.get_template_list()
    
    # Test importing from non-existent file
    non_existent = temp_dir / "non_existent.yaml"
    with pytest.raises(FileNotFoundError) as excinfo:
        template_manager.import_template_from_yaml(non_existent)
    
    assert "not found" in str(excinfo.value)
    
    # Test importing invalid YAML
    invalid_yaml = temp_dir / "invalid.yaml"
    with open(invalid_yaml, 'w') as f:
        f.write("invalid: yaml: content:")
    
    with pytest.raises(TemplateValidationError) as excinfo:
        template_manager.import_template_from_yaml(invalid_yaml)
    
    assert "Invalid" in str(excinfo.value)

def test_template_manager_initialization(temp_dir):
    """Test template manager initialization with default directories"""
    # Use a non-standard location as base
    os.environ["PWD"] = str(temp_dir)
    
    # Initialize without explicit paths
    template_manager = TemplateManager()
    
    # Check directories were created
    assert Path("templates/base").exists()
    assert Path("templates/previews").exists()
    
    # Clean up
    shutil.rmtree("templates") 