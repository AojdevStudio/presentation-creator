"""
Brand Guidelines Manager

This module provides functionality for managing brand guidelines and integrating
them with presentation templates.
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from .style_manager import StyleManager, StyleValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrandAssetError(Exception):
    """Exception raised for brand asset errors."""
    pass

class BrandManager:
    """
    Manages brand guidelines and assets for presentation templates.
    
    The BrandManager works with StyleManager to integrate brand guidelines into templates,
    including colors, fonts, and logos.
    """
    
    def __init__(self, 
                 brands_dir: Optional[Path] = None,
                 assets_dir: Optional[Path] = None,
                 style_manager: Optional[StyleManager] = None):
        """
        Initialize the BrandManager.
        
        Args:
            brands_dir: Directory for brand definitions
            assets_dir: Directory for brand assets (logos, images)
            style_manager: Optional StyleManager instance to use for style integration
        """
        self.brands_dir = brands_dir or Path("templates/brands")
        self.assets_dir = assets_dir or Path("templates/brands/assets")
        self.style_manager = style_manager or StyleManager(brands_dir=self.brands_dir)
        
        # Create directories if they don't exist
        self.brands_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize brands list
        self._brands = self._load_brands()
        
    def _load_brands(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all available brand definitions.
        
        Returns:
            Dictionary of brand definitions
        """
        brands = {}
        
        if not self.brands_dir.exists():
            return brands
            
        for brand_file in self.brands_dir.glob("*.json"):
            brand_name = brand_file.stem
            try:
                with open(brand_file, 'r') as f:
                    brand_data = json.load(f)
                    brands[brand_name] = brand_data
                    logger.info(f"Loaded brand definition: {brand_name}")
            except Exception as e:
                logger.error(f"Failed to load brand {brand_name}: {e}")
                
        return brands
        
    def create_brand(self, name: str, brand_data: Dict[str, Any], 
                    logo_path: Optional[Path] = None) -> None:
        """
        Create or update a brand definition.
        
        Args:
            name: Brand name
            brand_data: Brand definition data
            logo_path: Optional path to brand logo
            
        Raises:
            StyleValidationError: If brand data is invalid
        """
        # Create brand assets directory
        brand_assets_dir = self.assets_dir / name
        brand_assets_dir.mkdir(exist_ok=True)
        
        # Handle logo if provided
        if logo_path and logo_path.exists():
            logo_dest = brand_assets_dir / logo_path.name
            shutil.copy(logo_path, logo_dest)
            brand_data["logo"] = str(logo_dest.relative_to(Path.cwd()))
            
        # Create or update brand via StyleManager
        self.style_manager.create_brand(name, brand_data)
        
        # Update local cache
        self._brands[name] = brand_data
        
    def get_brand(self, name: str) -> Dict[str, Any]:
        """
        Get brand definition by name.
        
        Args:
            name: Brand name
            
        Returns:
            Brand definition data
            
        Raises:
            KeyError: If brand not found
        """
        if name not in self._brands:
            raise KeyError(f"Brand '{name}' not found")
            
        return self._brands[name]
        
    def get_brand_list(self) -> List[str]:
        """
        Get list of available brands.
        
        Returns:
            List of brand names
        """
        return list(self._brands.keys())
        
    def get_brand_assets(self, name: str) -> Dict[str, str]:
        """
        Get all assets for a brand.
        
        Args:
            name: Brand name
            
        Returns:
            Dictionary of asset paths by type
            
        Raises:
            KeyError: If brand not found
        """
        if name not in self._brands:
            raise KeyError(f"Brand '{name}' not found")
            
        assets = {}
        brand_assets_dir = self.assets_dir / name
        
        if not brand_assets_dir.exists():
            return assets
            
        # Get logo if exists
        if "logo" in self._brands[name]:
            assets["logo"] = self._brands[name]["logo"]
            
        # Get all other assets in directory
        for asset_file in brand_assets_dir.glob("*.*"):
            asset_type = asset_file.suffix.lower()[1:]  # Remove the dot
            if asset_type in ["png", "jpg", "jpeg", "svg", "gif"]:
                assets[f"image_{asset_file.stem}"] = str(asset_file)
                
        return assets
        
    def add_brand_asset(self, brand_name: str, asset_path: Path, 
                       asset_type: Optional[str] = None) -> str:
        """
        Add an asset to a brand.
        
        Args:
            brand_name: Brand name
            asset_path: Path to asset file
            asset_type: Optional asset type (logo, background, etc.)
            
        Returns:
            Path to the copied asset
            
        Raises:
            KeyError: If brand not found
            BrandAssetError: If asset file is invalid
        """
        if brand_name not in self._brands:
            raise KeyError(f"Brand '{brand_name}' not found")
            
        if not asset_path.exists():
            raise BrandAssetError(f"Asset file not found: {asset_path}")
            
        # Determine asset type if not provided
        if not asset_type:
            asset_ext = asset_path.suffix.lower()
            if asset_ext in [".png", ".jpg", ".jpeg", ".svg", ".gif"]:
                asset_type = "image"
            else:
                asset_type = "other"
                
        # Create brand assets directory if needed
        brand_assets_dir = self.assets_dir / brand_name
        brand_assets_dir.mkdir(exist_ok=True)
        
        # Copy asset to brand directory
        asset_dest = brand_assets_dir / asset_path.name
        shutil.copy(asset_path, asset_dest)
        
        # Update brand definition if this is a logo
        if asset_type == "logo":
            self._brands[brand_name]["logo"] = str(asset_dest.relative_to(Path.cwd()))
            
            # Update the brand on disk
            brand_path = self.brands_dir / f"{brand_name}.json"
            with open(brand_path, 'w') as f:
                json.dump(self._brands[brand_name], f, indent=2)
                
        return str(asset_dest)
        
    def generate_brand_preview(self, brand_name: str, output_dir: Optional[Path] = None) -> Path:
        """
        Generate a preview of brand styles.
        
        Args:
            brand_name: Brand name
            output_dir: Optional output directory
            
        Returns:
            Path to the generated HTML preview
            
        Raises:
            KeyError: If brand not found
        """
        if brand_name not in self._brands:
            raise KeyError(f"Brand '{brand_name}' not found")
            
        if not output_dir:
            output_dir = self.brands_dir / "previews"
            output_dir.mkdir(exist_ok=True)
            
        brand_data = self._brands[brand_name]
        preview_path = output_dir / f"{brand_name}_preview.html"
        
        # Generate HTML preview
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{brand_name} Brand Preview</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; padding: 20px; }",
            ".preview-section { margin-bottom: 30px; }",
            ".color-swatch { width: 100px; height: 100px; display: inline-block; margin: 10px; text-align: center; line-height: 100px; color: #fff; text-shadow: 0 0 2px #000; }",
            ".font-preview { margin: 10px 0; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{brand_name} Brand Preview</h1>"
        ]
        
        # Add color swatches
        html_content.append("<div class='preview-section'>")
        html_content.append("<h2>Colors</h2>")
        
        if "colors" in brand_data:
            for color_name, color_value in brand_data["colors"].items():
                html_content.append(f"<div class='color-swatch' style='background-color: {color_value};'>{color_name}<br>{color_value}</div>")
        
        html_content.append("</div>")
        
        # Add font previews
        html_content.append("<div class='preview-section'>")
        html_content.append("<h2>Typography</h2>")
        
        if "fonts" in brand_data:
            for font_type, font_props in brand_data["fonts"].items():
                font_name = font_props.get("name", "Arial")
                font_size = font_props.get("size", 16)
                font_weight = "bold" if font_props.get("bold", False) else "normal"
                font_color = font_props.get("color", "#000000")
                
                html_content.append(f"<div class='font-preview' style='font-family: {font_name}; font-size: {font_size}px; font-weight: {font_weight}; color: {font_color};'>")
                html_content.append(f"<p>{font_type}: {font_name}, {font_size}px</p>")
                html_content.append("<p>The quick brown fox jumps over the lazy dog.</p>")
                html_content.append("</div>")
        
        html_content.append("</div>")
        
        # Add logo if available
        if "logo" in brand_data:
            html_content.append("<div class='preview-section'>")
            html_content.append("<h2>Logo</h2>")
            html_content.append(f"<img src='../../{brand_data['logo']}' style='max-width: 300px; max-height: 200px;'>")
            html_content.append("</div>")
        
        # Close HTML
        html_content.append("</body>")
        html_content.append("</html>")
        
        # Write to file
        with open(preview_path, 'w') as f:
            f.write("\n".join(html_content))
            
        logger.info(f"Generated brand preview: {preview_path}")
        return preview_path
        
    def export_brand_to_yaml(self, brand_name: str, output_path: Optional[Path] = None) -> Path:
        """
        Export a brand definition to YAML format.
        
        Args:
            brand_name: Brand name
            output_path: Optional output file path
            
        Returns:
            Path to the exported file
            
        Raises:
            KeyError: If brand not found
        """
        if brand_name not in self._brands:
            raise KeyError(f"Brand '{brand_name}' not found")
            
        brand_data = self._brands[brand_name]
        
        if not output_path:
            output_path = self.brands_dir / f"{brand_name}.yaml"
            
        with open(output_path, 'w') as f:
            yaml.dump(brand_data, f, default_flow_style=False)
            
        logger.info(f"Exported brand to {output_path}")
        return output_path
        
    def import_brand_from_yaml(self, file_path: Path, brand_name: Optional[str] = None) -> str:
        """
        Import a brand definition from YAML.
        
        Args:
            file_path: Path to YAML file
            brand_name: Optional brand name (uses filename if not provided)
            
        Returns:
            Name of the imported brand
            
        Raises:
            StyleValidationError: If imported data is invalid
        """
        try:
            with open(file_path, 'r') as f:
                brand_data = yaml.safe_load(f)
                
            # Use filename as brand name if not provided
            if not brand_name:
                brand_name = file_path.stem
                
            # Create brand
            self.create_brand(brand_name, brand_data)
            
            return brand_name
            
        except Exception as e:
            logger.error(f"Failed to import brand: {e}")
            raise StyleValidationError(f"Failed to import brand: {e}")
            
    def delete_brand(self, brand_name: str) -> None:
        """
        Delete a brand and its assets.
        
        Args:
            brand_name: Brand name
            
        Raises:
            KeyError: If brand not found
        """
        if brand_name not in self._brands:
            raise KeyError(f"Brand '{brand_name}' not found")
            
        # Remove brand definition file
        brand_path = self.brands_dir / f"{brand_name}.json"
        if brand_path.exists():
            brand_path.unlink()
            
        # Remove brand assets directory
        brand_assets_dir = self.assets_dir / brand_name
        if brand_assets_dir.exists():
            shutil.rmtree(brand_assets_dir)
            
        # Remove from in-memory cache
        del self._brands[brand_name]
        
        logger.info(f"Deleted brand: {brand_name}")
        
    def apply_brand_to_template(self, brand_name: str, template_name: str) -> Dict[str, Any]:
        """
        Apply brand guidelines to a template.
        
        Args:
            brand_name: Brand name
            template_name: Template name
            
        Returns:
            Merged style dictionary with brand applied
            
        Raises:
            KeyError: If brand not found
        """
        if brand_name not in self._brands:
            raise KeyError(f"Brand '{brand_name}' not found")
            
        # Get merged style using StyleManager
        merged_style = self.style_manager.get_merged_style(template_name, brand_name)
        
        return merged_style 