"""
Tests for slide content generation functionality.
"""
import os
import pytest
from unittest.mock import AsyncMock, patch
from src.core.slide_content_generator import SlideContentGenerator

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    with patch('src.core.slide_content_generator.AssistantsAPIClient') as mock_client:
        # Create mock assistant and thread responses
        mock_assistant = AsyncMock()
        mock_assistant.id = "test_assistant_id"
        
        mock_thread = AsyncMock()
        mock_thread.id = "test_thread_id"
        
        mock_run = AsyncMock()
        mock_run.id = "test_run_id"
        
        mock_status = AsyncMock()
        mock_status.status = "completed"
        
        mock_message = AsyncMock()
        mock_message.content = [AsyncMock()]
        mock_message.content[0].text.value = "Generated slide content"
        
        mock_messages = AsyncMock()
        mock_messages.data = [mock_message]
        
        # Configure the client's mock methods
        client_instance = mock_client.return_value
        client_instance.create_assistant = AsyncMock(return_value=mock_assistant)
        client_instance.create_thread = AsyncMock(return_value=mock_thread)
        client_instance.add_message = AsyncMock()
        client_instance.run_assistant = AsyncMock(return_value=mock_run)
        client_instance.get_run_status = AsyncMock(return_value=mock_status)
        client_instance.get_messages = AsyncMock(return_value=mock_messages)
        
        yield client_instance

@pytest.mark.asyncio
async def test_initialize(mock_openai_client):
    """Test initialization of the slide content generator."""
    generator = SlideContentGenerator()
    await generator.initialize()
    
    # Verify that assistant and thread were created
    mock_openai_client.create_assistant.assert_called_once()
    mock_openai_client.create_thread.assert_called_once()
    
    assert generator.assistant is not None
    assert generator.thread is not None

@pytest.mark.asyncio
async def test_generate_slide_content(mock_openai_client):
    """Test generating content for a single slide."""
    generator = SlideContentGenerator()
    await generator.initialize()
    
    variables = {
        "title": "Test Slide",
        "subtitle": "Testing slide generation",
        "presenter": "Test User",
        "date": "2024-03-31"
    }
    
    result = await generator.generate_slide_content("title", variables)
    
    # Verify API calls
    mock_openai_client.add_message.assert_called_once()
    mock_openai_client.run_assistant.assert_called_once()
    mock_openai_client.get_run_status.assert_called_once()
    mock_openai_client.get_messages.assert_called_once()
    
    # Verify result structure
    assert result["content"] == "Generated slide content"
    assert result["type"] == "title"
    assert result["variables"] == variables

@pytest.mark.asyncio
async def test_generate_multiple_slides(mock_openai_client):
    """Test generating content for multiple slides."""
    generator = SlideContentGenerator()
    await generator.initialize()
    
    slide_specs = [
        {
            "template_type": "title",
            "variables": {
                "title": "Presentation Title",
                "subtitle": "Subtitle",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        },
        {
            "template_type": "content",
            "variables": {
                "title": "Content Slide",
                "key_points": ["Point 1", "Point 2"],
                "context": "Additional context"
            }
        }
    ]
    
    results = await generator.generate_multiple_slides(slide_specs)
    
    # Verify number of API calls (2 slides = 2 sets of calls)
    assert mock_openai_client.add_message.call_count == 2
    assert mock_openai_client.run_assistant.call_count == 2
    assert mock_openai_client.get_run_status.call_count == 2
    assert mock_openai_client.get_messages.call_count == 2
    
    # Verify results
    assert len(results) == 2
    for result, spec in zip(results, slide_specs):
        assert result["content"] == "Generated slide content"
        assert result["type"] == spec["template_type"]
        assert result["variables"] == spec["variables"]

@pytest.mark.asyncio
async def test_error_handling(mock_openai_client):
    """Test error handling during content generation."""
    generator = SlideContentGenerator()
    await generator.initialize()
    
    # Configure mock to raise an exception
    mock_openai_client.add_message.side_effect = Exception("API Error")
    
    variables = {
        "title": "Test Slide",
        "subtitle": "Testing error handling",
        "presenter": "Test User",
        "date": "2024-03-31"
    }
    
    # Test single slide error handling
    with pytest.raises(Exception):
        await generator.generate_slide_content("title", variables)
    
    # Test multiple slides error handling
    slide_specs = [
        {
            "template_type": "title",
            "variables": variables
        }
    ]
    
    results = await generator.generate_multiple_slides(slide_specs)
    assert len(results) == 1
    assert "error" in results[0]
    assert results[0]["type"] == "title"
    assert results[0]["variables"] == variables

@pytest.mark.asyncio
async def test_uninitialized_error():
    """Test error when trying to generate content without initialization."""
    generator = SlideContentGenerator()
    
    with pytest.raises(RuntimeError, match="SlideContentGenerator not initialized"):
        await generator.generate_slide_content("title", {}) 