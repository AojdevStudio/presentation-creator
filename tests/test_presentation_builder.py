"""
Tests for presentation builder functionality.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from src.core.presentation_builder import PresentationBuilder

@pytest.fixture
def temp_pptx(tmp_path):
    """Create a temporary directory for test presentations."""
    return tmp_path / "test.pptx"

@pytest.fixture
async def presentation_builder():
    """Create a presentation builder instance with mocked dependencies."""
    with patch('src.core.presentation_builder.SlideContentGenerator') as mock_content_gen, \
         patch('src.core.presentation_builder.SlideGenerator') as mock_slide_gen:
        
        # Configure content generator mock
        content_gen_instance = mock_content_gen.return_value
        content_gen_instance.initialize = AsyncMock()
        content_gen_instance.generate_multiple_slides = AsyncMock()
        
        # Configure slide generator mock
        slide_gen_instance = mock_slide_gen.return_value
        slide_gen_instance.create_title_slide = MagicMock()
        slide_gen_instance.create_content_slide = MagicMock()
        slide_gen_instance.create_section_transition = MagicMock()
        slide_gen_instance.create_summary_slide = MagicMock()
        slide_gen_instance.save = MagicMock()
        
        builder = PresentationBuilder()
        await builder.initialize()
        
        yield builder

@pytest.mark.asyncio
async def test_build_presentation(presentation_builder, temp_pptx):
    """Test building a presentation from slide specifications."""
    slide_specs = [
        {
            "template_type": "title",
            "variables": {
                "title": "Test Presentation",
                "subtitle": "Testing Builder",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        },
        {
            "template_type": "content",
            "variables": {
                "title": "Content Slide",
                "key_points": ["Point 1", "Point 2"],
                "context": "Test context"
            }
        }
    ]
    
    # Configure mock response
    presentation_builder.content_generator.generate_multiple_slides.return_value = [
        {
            "type": "title",
            "content": {
                "title": "Generated Title",
                "subtitle": "Generated Subtitle",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        },
        {
            "type": "content",
            "content": {
                "title": "Generated Content",
                "key_points": ["Generated Point 1", "Generated Point 2"],
                "context": "Generated context"
            }
        }
    ]
    
    await presentation_builder.build_presentation(slide_specs, temp_pptx)
    
    # Verify content generation was called
    presentation_builder.content_generator.generate_multiple_slides.assert_called_once_with(
        slide_specs, max_retries=3
    )
    
    # Verify slide creation methods were called
    presentation_builder.slide_generator.create_title_slide.assert_called_once()
    presentation_builder.slide_generator.create_content_slide.assert_called_once()
    presentation_builder.slide_generator.save.assert_called_once_with(temp_pptx)

@pytest.mark.asyncio
async def test_build_presentation_from_outline(presentation_builder, temp_pptx):
    """Test building a presentation from an outline."""
    outline = [
        {
            "title": "Section 1",
            "content": [
                {
                    "title": "Topic 1",
                    "points": ["Point 1", "Point 2"],
                    "context": "Context 1"
                }
            ],
            "key_takeaway": "Takeaway 1"
        },
        {
            "title": "Section 2",
            "content": [
                {
                    "title": "Topic 2",
                    "points": ["Point 3", "Point 4"],
                    "context": "Context 2"
                }
            ],
            "key_takeaway": "Takeaway 2"
        }
    ]
    
    # Configure mock response
    presentation_builder.content_generator.generate_multiple_slides.return_value = [
        {
            "type": "title",
            "content": {"title": "Test Title", "subtitle": "Generated", "presenter": "Test", "date": "2024"}
        },
        {
            "type": "section_transition",
            "content": {"current_section": "Section 1", "next_section": "Section 2"}
        },
        {
            "type": "content",
            "content": {"title": "Topic 1", "key_points": ["Point 1", "Point 2"], "context": "Context 1"}
        },
        {
            "type": "section_transition",
            "content": {"current_section": "Section 2", "next_section": "Summary"}
        },
        {
            "type": "content",
            "content": {"title": "Topic 2", "key_points": ["Point 3", "Point 4"], "context": "Context 2"}
        },
        {
            "type": "summary",
            "content": {"main_topics": ["Section 1", "Section 2"], "key_takeaways": ["Takeaway 1", "Takeaway 2"]}
        }
    ]
    
    await presentation_builder.build_presentation_from_outline(
        "Test Presentation",
        outline,
        "Test User",
        "2024-03-31",
        temp_pptx
    )
    
    # Verify content generation was called
    presentation_builder.content_generator.generate_multiple_slides.assert_called_once()
    
    # Verify all slide types were created
    assert presentation_builder.slide_generator.create_title_slide.call_count == 1
    assert presentation_builder.slide_generator.create_section_transition.call_count == 2
    assert presentation_builder.slide_generator.create_content_slide.call_count == 2
    assert presentation_builder.slide_generator.create_summary_slide.call_count == 1
    presentation_builder.slide_generator.save.assert_called_once_with(temp_pptx)

@pytest.mark.asyncio
async def test_error_handling(presentation_builder, temp_pptx):
    """Test error handling during presentation building."""
    slide_specs = [
        {
            "template_type": "title",
            "variables": {
                "title": "Test Presentation",
                "subtitle": "Testing Error Handling",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        }
    ]
    
    # Configure mock to return an error
    presentation_builder.content_generator.generate_multiple_slides.return_value = [
        {
            "error": "Content generation failed",
            "type": "title",
            "variables": slide_specs[0]["variables"]
        }
    ]
    
    await presentation_builder.build_presentation(slide_specs, temp_pptx)
    
    # Verify no slides were created due to error
    presentation_builder.slide_generator.create_title_slide.assert_not_called()
    # But save should still be called
    presentation_builder.slide_generator.save.assert_called_once_with(temp_pptx)

def test_get_template_info(presentation_builder):
    """Test getting template information."""
    # Configure mock slide layouts
    mock_layout = MagicMock()
    mock_layout.name = "Title Slide"
    presentation_builder.slide_generator.prs.slide_layouts = [mock_layout]
    presentation_builder.slide_generator.prs.slide_masters = [MagicMock()]
    
    info = presentation_builder.get_template_info()
    
    assert info["slide_layouts"] == 1
    assert info["slide_masters"] == 1
    assert info["available_layouts"] == ["Title Slide"]

@pytest.mark.asyncio
async def test_save_error_handling(presentation_builder, temp_pptx):
    """Test handling of save errors."""
    slide_specs = [
        {
            "template_type": "title",
            "variables": {
                "title": "Test Presentation",
                "subtitle": "Testing Save Error",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        }
    ]
    
    # Configure mock to succeed in content generation
    presentation_builder.content_generator.generate_multiple_slides.return_value = [
        {
            "type": "title",
            "content": slide_specs[0]["variables"]
        }
    ]
    
    # Configure save to raise an exception
    presentation_builder.slide_generator.save.side_effect = Exception("Save failed")
    
    with pytest.raises(Exception, match="Save failed"):
        await presentation_builder.build_presentation(slide_specs, temp_pptx) 