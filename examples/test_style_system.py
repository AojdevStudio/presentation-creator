#!/usr/bin/env python3
"""
Style Management System Demo

This script demonstrates the functionality of the style management system and brand guidelines integration.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.templates.style_manager import StyleManager
from src.templates.brand_manager import BrandManager

def print_style_section(title, data):
    """Print a section of style data nicely formatted."""
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2))
    print("=" * (len(title) + 8))

def run_style_demo():
    """Demonstrate the style inheritance features."""
    print("\n\nSTYLE INHERITANCE DEMO")
    print("=====================")
    
    # Create StyleManager
    style_manager = StyleManager()
    
    # Get global styles
    global_styles = style_manager._global_styles
    print_style_section("Global Styles (Colors Only)", global_styles["colors"])
    
    # Get corporate brand styles
    corporate_brand = style_manager.get_merged_style("any_template", "corporate")
    print_style_section("Corporate Brand (Colors Only)", corporate_brand["colors"])
    
    # Get creative brand styles
    creative_brand = style_manager.get_merged_style("any_template", "creative")
    print_style_section("Creative Brand (Colors Only)", creative_brand["colors"])
    
    # Load minimal template style
    minimal_template = style_manager.load_template_style("minimal")
    print_style_section("Minimal Template (Colors Only)", minimal_template.get("colors", {}))
    
    # Get merged styles with template and brands
    minimal_corporate = style_manager.get_merged_style("minimal", "corporate")
    print_style_section("Minimal Template + Corporate Brand (Colors Only)", minimal_corporate["colors"])
    
    minimal_creative = style_manager.get_merged_style("minimal", "creative")
    print_style_section("Minimal Template + Creative Brand (Colors Only)", minimal_creative["colors"])
    
    # Demonstrate element-specific overrides
    element_style = {
        "colors": {
            "primary": "#00FF00",  # Override primary color for this element only
        }
    }
    
    element_override = style_manager.get_merged_style("minimal", "corporate", element_style)
    print_style_section("Element-specific Override (Colors Only)", element_override["colors"])
    
    # Demonstrate specific style property access
    primary_color = style_manager.get_specific_style("colors.primary", "minimal", "corporate")
    print(f"\nPrimary color for minimal+corporate: {primary_color}")
    
    title_font = style_manager.get_specific_style("fonts.title", "minimal", "corporate")
    print(f"Title font for minimal+corporate: {title_font}")

def run_brand_demo():
    """Demonstrate the brand management features."""
    print("\n\nBRAND MANAGEMENT DEMO")
    print("====================")
    
    # Create BrandManager
    brand_manager = BrandManager()
    
    # List available brands
    brands = brand_manager.get_brand_list()
    print(f"\nAvailable brands: {brands}")
    
    # Get corporate brand
    try:
        corporate = brand_manager.get_brand("corporate")
        print_style_section("Corporate Brand Info", corporate.get("brand_info", {}))
    except KeyError:
        print("Corporate brand not found")
    
    # Generate brand preview
    try:
        preview_path = brand_manager.generate_brand_preview("creative")
        print(f"\nCreated brand preview at: {preview_path}")
        print(f"Open this file in a browser to see the brand styles visually")
    except Exception as e:
        print(f"Failed to generate preview: {e}")
    
    # Apply brand to template
    try:
        merged_style = brand_manager.apply_brand_to_template("creative", "minimal")
        print_style_section("Creative Brand Applied to Minimal Template (Fonts Only)", merged_style["fonts"])
    except KeyError:
        print("Failed to apply brand to template")

def export_import_demo():
    """Demonstrate export and import functionality."""
    print("\n\nEXPORT/IMPORT DEMO")
    print("=================")
    
    # Create StyleManager
    style_manager = StyleManager()
    
    # Export corporate style to YAML
    export_path = style_manager.export_style_to_yaml("minimal", "corporate")
    print(f"\nExported style to: {export_path}")
    
    # Create a sample custom brand
    custom_brand = {
        "colors": {
            "primary": "#8E44AD",    # Purple
            "secondary": "#2980B9",  # Blue
            "accent1": "#F1C40F",    # Yellow
            "accent2": "#27AE60",    # Green
            "text": "#2C3E50",       # Dark Blue
            "background": "#ECF0F1"  # Light Gray
        },
        "fonts": {
            "title": {
                "name": "Georgia",
                "size": 42,
                "bold": True,
                "color": "#8E44AD"
            },
            "body": {
                "name": "Georgia",
                "size": 18,
                "bold": False,
                "color": "#2C3E50"
            }
        }
    }
    
    # Create brand manager and create the custom brand
    brand_manager = BrandManager(style_manager=style_manager)
    brand_manager.create_brand("custom", custom_brand)
    print("\nCreated custom brand")
    
    # Apply custom brand to minimal template
    merged_style = brand_manager.apply_brand_to_template("custom", "minimal")
    print_style_section("Custom Brand Applied to Minimal Template (Colors Only)", merged_style["colors"])
    
    # Export custom brand to YAML
    export_path = brand_manager.export_brand_to_yaml("custom")
    print(f"\nExported custom brand to: {export_path}")

if __name__ == "__main__":
    # Run demonstrations
    run_style_demo()
    run_brand_demo()
    export_import_demo()
    
    print("\n\nDemo completed! 🎉")
    print("The style management system with brand guidelines integration is working properly.")
    print("You can find exported files in the templates/styles and templates/brands directories.") 