"""
Tests for the BrandManager class.
"""

import pytest
import os
import tempfile
import json
import shutil
from pathlib import Path

from src.templates.brand_manager import BrandManager, BrandAssetError
from src.templates.style_manager import StyleManager

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def brand_manager(temp_dir):
    """Create a BrandManager instance with temporary directories."""
    brands_dir = temp_dir / "brands"
    assets_dir = temp_dir / "brands/assets"
    brands_dir.mkdir()
    assets_dir.mkdir()
    return BrandManager(brands_dir=brands_dir, assets_dir=assets_dir)

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
        },
        "brand_info": {
            "name": "Test Brand",
            "tagline": "This is a test brand",
            "copyright": "© 2023 Test Brand"
        }
    }

@pytest.fixture
def test_logo_file(temp_dir):
    """Create a test logo file."""
    logo_path = temp_dir / "test_logo.png"
    # Create a dummy PNG file
    with open(logo_path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    return logo_path

def test_create_brand(brand_manager, test_brand_data):
    """Test creating a brand."""
    brand_manager.create_brand("test_brand", test_brand_data)
    
    # Check if brand was created
    assert "test_brand" in brand_manager.get_brand_list()
    
    # Check if brand file was created
    brand_file = brand_manager.brands_dir / "test_brand.json"
    assert brand_file.exists()
    
    # Check if brand assets directory was created
    brand_assets_dir = brand_manager.assets_dir / "test_brand"
    assert brand_assets_dir.exists()

def test_create_brand_with_logo(brand_manager, test_brand_data, test_logo_file):
    """Test creating a brand with a logo."""
    brand_manager.create_brand("logo_brand", test_brand_data, logo_path=test_logo_file)
    
    # Check if brand was created
    assert "logo_brand" in brand_manager.get_brand_list()
    
    # Check if logo was copied to assets directory
    brand_assets_dir = brand_manager.assets_dir / "logo_brand"
    assert (brand_assets_dir / "test_logo.png").exists()
    
    # Check if logo path was added to brand data
    brand = brand_manager.get_brand("logo_brand")
    assert "logo" in brand

def test_get_brand(brand_manager, test_brand_data):
    """Test getting a brand by name."""
    brand_manager.create_brand("test_brand", test_brand_data)
    
    # Get brand
    brand = brand_manager.get_brand("test_brand")
    
    # Check if brand data is correct
    assert brand["colors"]["primary"] == "#FF0000"
    assert brand["brand_info"]["name"] == "Test Brand"
    
    # Test nonexistent brand
    with pytest.raises(KeyError):
        brand_manager.get_brand("nonexistent")

def test_get_brand_assets(brand_manager, test_brand_data, test_logo_file):
    """Test getting brand assets."""
    brand_manager.create_brand("asset_brand", test_brand_data, logo_path=test_logo_file)
    
    # Get brand assets
    assets = brand_manager.get_brand_assets("asset_brand")
    
    # Check if logo is in assets
    assert "logo" in assets
    
    # Test nonexistent brand
    with pytest.raises(KeyError):
        brand_manager.get_brand_assets("nonexistent")

def test_add_brand_asset(brand_manager, test_brand_data, test_logo_file):
    """Test adding an asset to a brand."""
    brand_manager.create_brand("asset_brand", test_brand_data)
    
    # Add logo asset
    asset_path = brand_manager.add_brand_asset("asset_brand", test_logo_file, asset_type="logo")
    
    # Check if asset was added
    assert Path(asset_path).exists()
    
    # Check if logo was added to brand data
    brand = brand_manager.get_brand("asset_brand")
    assert "logo" in brand
    
    # Test nonexistent brand
    with pytest.raises(KeyError):
        brand_manager.add_brand_asset("nonexistent", test_logo_file)
    
    # Test nonexistent asset file
    with pytest.raises(BrandAssetError):
        brand_manager.add_brand_asset("asset_brand", Path("nonexistent.png"))

def test_generate_brand_preview(brand_manager, test_brand_data):
    """Test generating a brand preview."""
    brand_manager.create_brand("preview_brand", test_brand_data)
    
    # Generate preview
    preview_path = brand_manager.generate_brand_preview("preview_brand")
    
    # Check if preview was created
    assert preview_path.exists()
    
    # Test nonexistent brand
    with pytest.raises(KeyError):
        brand_manager.generate_brand_preview("nonexistent")

def test_delete_brand(brand_manager, test_brand_data, test_logo_file):
    """Test deleting a brand."""
    brand_manager.create_brand("delete_brand", test_brand_data, logo_path=test_logo_file)
    
    # Check if brand exists
    assert "delete_brand" in brand_manager.get_brand_list()
    
    # Delete brand
    brand_manager.delete_brand("delete_brand")
    
    # Check if brand was deleted
    assert "delete_brand" not in brand_manager.get_brand_list()
    
    # Check if brand file was deleted
    brand_file = brand_manager.brands_dir / "delete_brand.json"
    assert not brand_file.exists()
    
    # Check if brand assets directory was deleted
    brand_assets_dir = brand_manager.assets_dir / "delete_brand"
    assert not brand_assets_dir.exists()
    
    # Test nonexistent brand
    with pytest.raises(KeyError):
        brand_manager.delete_brand("nonexistent")

def test_apply_brand_to_template(brand_manager, test_brand_data, temp_dir):
    """Test applying a brand to a template."""
    # Create style manager with a template
    styles_dir = temp_dir / "styles"
    styles_dir.mkdir()
    style_manager = StyleManager(styles_dir=styles_dir, brands_dir=brand_manager.brands_dir)
    
    # Replace brand_manager's style_manager with our test one
    brand_manager.style_manager = style_manager
    
    # Create a template
    template_style = {
        "colors": {
            "primary": "#0000FF",
            "accent1": "#FFFF00"
        }
    }
    style_manager.load_template_style("test_template", template_style)
    
    # Create a brand
    brand_manager.create_brand("apply_brand", test_brand_data)
    
    # Apply brand to template
    merged_style = brand_manager.apply_brand_to_template("apply_brand", "test_template")
    
    # Check if styles were merged correctly
    assert merged_style["colors"]["primary"] == "#0000FF"  # From template
    assert merged_style["colors"]["secondary"] == "#00FF00"  # From brand
    
    # Test nonexistent brand
    with pytest.raises(KeyError):
        brand_manager.apply_brand_to_template("nonexistent", "test_template") 