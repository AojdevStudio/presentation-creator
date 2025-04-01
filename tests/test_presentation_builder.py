"""
Tests for presentation builder functionality.
"""
import os
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from src.core.presentation_builder import PresentationBuilder

@pytest_asyncio.fixture
async def temp_pptx(tmp_path):
    """Create a temporary directory for test presentations."""
    test_dir = tmp_path / "test_presentations"
    test_dir.mkdir()
    return test_dir / "test.pptx"

@pytest.fixture
def presentation_builder():
    """Create a mock presentation builder."""
    builder = PresentationBuilder()
    builder.content_generator = MagicMock()
    builder.content_generator.generate_multiple_slides = AsyncMock()
    builder.slide_generator = MagicMock()
    builder.slide_generator.prs = MagicMock()
    return builder

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

    # Configure mock response for content generation
    presentation_builder.content_generator.generate_multiple_slides = AsyncMock(return_value=[
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
    ])

    # Configure mock response for file info
    mock_file_info = {
        'size': 12345,
        'created': 1234567890.0,
        'modified': 1234567890.0,
        'is_backup': False
    }

    # Build presentation
    with patch('src.presentation.presentation_exporter.PresentationExporter') as MockExporter:
        mock_exporter = MockExporter.return_value
        mock_exporter.export.return_value = str(temp_pptx)
        mock_exporter.get_file_info.return_value = mock_file_info

        result = await presentation_builder.build_presentation(
            slide_specs, 
            temp_pptx,
            {'overwrite': True}
        )

    # Verify calls
    presentation_builder.content_generator.generate_multiple_slides.assert_called_once_with(
        slide_specs,
        max_retries=3
    )
    assert presentation_builder.slide_generator.create_title_slide.call_count == 1
    assert presentation_builder.slide_generator.create_content_slide.call_count == 1
    
    # Verify export was called with correct options
    MockExporter.assert_called_once_with(presentation_builder.slide_generator.prs)
    mock_exporter.export.assert_called_once_with(temp_pptx, {'overwrite': True})
    
    # Verify result structure
    assert result['path'] == str(temp_pptx)
    assert result['file_info'] == mock_file_info

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

    # Configure mock response for content generation
    presentation_builder.content_generator.generate_multiple_slides = AsyncMock(return_value=[
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
    ])

    # Configure mock response for file info
    mock_file_info = {
        'size': 12345,
        'created': 1234567890.0,
        'modified': 1234567890.0,
        'is_backup': False
    }

    # Build presentation
    with patch('src.presentation.presentation_exporter.PresentationExporter') as MockExporter:
        mock_exporter = MockExporter.return_value
        mock_exporter.export.return_value = str(temp_pptx)
        mock_exporter.get_file_info.return_value = mock_file_info

        result = await presentation_builder.build_presentation_from_outline(
            title="Test Presentation",
            outline=outline,
            presenter="Test User",
            date="2024-03-31",
            output_path=temp_pptx,
            export_options={'create_dirs': True}
        )

    # Verify calls
    presentation_builder.content_generator.generate_multiple_slides.assert_called_once()
    assert presentation_builder.slide_generator.create_title_slide.call_count == 1
    assert presentation_builder.slide_generator.create_section_transition.call_count == 2
    assert presentation_builder.slide_generator.create_content_slide.call_count == 2
    assert presentation_builder.slide_generator.create_summary_slide.call_count == 1
    
    # Verify export was called with correct options
    MockExporter.assert_called_once_with(presentation_builder.slide_generator.prs)
    mock_exporter.export.assert_called_once_with(temp_pptx, {'create_dirs': True})
    
    # Verify result structure
    assert result['path'] == str(temp_pptx)
    assert result['file_info'] == mock_file_info

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
    presentation_builder.content_generator.generate_multiple_slides = AsyncMock(
        side_effect=Exception("Content generation failed")
    )

    # Build presentation should handle the error
    with pytest.raises(Exception) as exc_info:
        await presentation_builder.build_presentation(slide_specs, temp_pptx)
    
    assert str(exc_info.value) == "Content generation failed"
    
@pytest.mark.asyncio
async def test_export_error_handling(presentation_builder, temp_pptx):
    """Test handling of export errors."""
    slide_specs = [
        {
            "template_type": "title",
            "variables": {
                "title": "Test Presentation",
                "subtitle": "Testing Export Error",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        }
    ]

    # Configure mock to succeed in content generation but fail on export
    presentation_builder.content_generator.generate_multiple_slides = AsyncMock(return_value=[
        {
            "type": "title",
            "content": slide_specs[0]["variables"]
        }
    ])

    with patch('src.presentation.presentation_exporter.PresentationExporter') as MockExporter:
        mock_exporter = MockExporter.return_value
        mock_exporter.export.side_effect = OSError("Export failed")

        # Build presentation should handle the export error
        with pytest.raises(OSError) as exc_info:
            await presentation_builder.build_presentation(slide_specs, temp_pptx)
        
        assert str(exc_info.value) == "Export failed"
        mock_exporter.export.assert_called_once_with(temp_pptx, None)

def test_get_template_info(presentation_builder):
    """Test getting template information."""
    info = presentation_builder.get_template_info()

    assert isinstance(info, dict)
    assert info["slide_layouts"] == 1
    assert info["slide_masters"] == 1
    assert "Title Slide" in info["available_layouts"]

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

    # Configure mock to succeed in content generation but fail on save
    presentation_builder.content_generator.generate_multiple_slides = AsyncMock(return_value=[
        {
            "type": "title",
            "content": slide_specs[0]["variables"]
        }
    ])
    presentation_builder.slide_generator.save.side_effect = Exception("Save failed")

    # Build presentation should handle the save error
    with pytest.raises(Exception) as exc_info:
        await presentation_builder.build_presentation(slide_specs, temp_pptx)
    
    assert str(exc_info.value) == "Save failed"
    presentation_builder.slide_generator.save.assert_called_once_with(temp_pptx) 