"""
Tests for slide generation functionality.
"""
import os
import pytest
from pathlib import Path
from src.core.slide_generator import SlideGenerator

@pytest.fixture
def temp_pptx(tmp_path):
    """Create a temporary directory for test presentations."""
    return tmp_path / "test.pptx"

@pytest.fixture
def slide_generator():
    """Create a slide generator instance."""
    return SlideGenerator()

def test_create_title_slide(slide_generator, temp_pptx):
    """Test creating a title slide."""
    content = {
        "title": "Test Presentation",
        "subtitle": "Testing Slide Generation",
        "presenter": "Test User",
        "date": "2024-03-31"
    }
    
    slide_generator.create_title_slide(content)
    slide_generator.save(temp_pptx)
    
    assert temp_pptx.exists()
    # Note: We can't easily verify the content of the PPTX file
    # but we can verify it was created successfully

def test_create_content_slide(slide_generator, temp_pptx):
    """Test creating a content slide."""
    content = {
        "title": "Content Slide",
        "key_points": [
            "First key point",
            "Second key point",
            "Third key point"
        ],
        "context": "Additional context information"
    }
    
    slide_generator.create_content_slide(content)
    slide_generator.save(temp_pptx)
    
    assert temp_pptx.exists()

def test_create_section_transition(slide_generator, temp_pptx):
    """Test creating a section transition slide."""
    content = {
        "current_section": "Current Section",
        "next_section": "Next Section"
    }
    
    slide_generator.create_section_transition(content)
    slide_generator.save(temp_pptx)
    
    assert temp_pptx.exists()

def test_create_summary_slide(slide_generator, temp_pptx):
    """Test creating a summary slide."""
    content = {
        "main_topics": [
            "Topic 1",
            "Topic 2",
            "Topic 3"
        ],
        "key_takeaways": [
            "Takeaway 1",
            "Takeaway 2",
            "Takeaway 3"
        ]
    }
    
    slide_generator.create_summary_slide(content)
    slide_generator.save(temp_pptx)
    
    assert temp_pptx.exists()

def test_multiple_slides(slide_generator, temp_pptx):
    """Test creating multiple slides in a presentation."""
    # Create title slide
    title_content = {
        "title": "Test Presentation",
        "subtitle": "Testing Multiple Slides",
        "presenter": "Test User",
        "date": "2024-03-31"
    }
    slide_generator.create_title_slide(title_content)
    
    # Create content slide
    content_slide = {
        "title": "Content Slide",
        "key_points": [
            "Point 1",
            "Point 2",
            "Point 3"
        ],
        "context": "Additional context"
    }
    slide_generator.create_content_slide(content_slide)
    
    # Create section transition
    transition = {
        "current_section": "First Section",
        "next_section": "Second Section"
    }
    slide_generator.create_section_transition(transition)
    
    # Create summary slide
    summary = {
        "main_topics": ["Topic 1", "Topic 2"],
        "key_takeaways": ["Takeaway 1", "Takeaway 2"]
    }
    slide_generator.create_summary_slide(summary)
    
    # Save and verify
    slide_generator.save(temp_pptx)
    assert temp_pptx.exists()

def test_template_loading(tmp_path):
    """Test loading a template file."""
    # This test will be skipped if no template file is available
    template_path = "templates/default.pptx"
    if not os.path.exists(template_path):
        pytest.skip("Template file not available")
        
    generator = SlideGenerator(template_path=template_path)
    output_path = tmp_path / "from_template.pptx"
    
    content = {
        "title": "Template Test",
        "subtitle": "Testing Template Loading",
        "presenter": "Test User",
        "date": "2024-03-31"
    }
    
    generator.create_title_slide(content)
    generator.save(output_path)
    
    assert output_path.exists()

def test_invalid_content(slide_generator):
    """Test handling of invalid content."""
    invalid_content = {
        "wrong_key": "This should fail"
    }
    
    with pytest.raises(KeyError):
        slide_generator.create_title_slide(invalid_content)

def test_invalid_save_path(slide_generator):
    """Test handling of invalid save path."""
    with pytest.raises(Exception):
        slide_generator.save("/invalid/path/presentation.pptx") 