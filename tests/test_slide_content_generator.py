"""
Tests for slide content generation functionality.
"""
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.core.slide_content_generator import SlideContentGenerator

@pytest_asyncio.fixture
async def content_generator():
    """Create a slide content generator with mocked OpenAI client."""
    with patch('src.core.slide_content_generator.AssistantsAPIClient') as mock_client:
        # Create mock instance
        mock_api = AsyncMock()
        mock_client.return_value = mock_api
        
        # Configure mock responses
        mock_api.create_assistant.return_value = MagicMock(id="test-assistant")
        mock_api.create_thread.return_value = MagicMock(id="test-thread")
        mock_api.add_message.return_value = MagicMock(id="test-message")
        mock_api.run_assistant.return_value = MagicMock(id="test-run")
        mock_api.get_run_status.return_value = MagicMock(status="completed")
        mock_api.get_messages.return_value = MagicMock(
            data=[
                MagicMock(
                    content=[
                        MagicMock(
                            text=MagicMock(
                                value='{"type": "title", "content": {"title": "Test Title", "subtitle": "Test Subtitle"}}'
                            )
                        )
                    ]
                )
            ]
        )
        
        generator = SlideContentGenerator(api_key="test-key")
        generator.api_client = mock_api
        yield generator

@pytest.mark.asyncio
async def test_initialize(content_generator):
    """Test initialization of the content generator."""
    await content_generator.initialize()
    
    content_generator.api_client.create_assistant.assert_called_once()
    content_generator.api_client.create_thread.assert_called_once()
    assert content_generator.assistant_id == "test-assistant"
    assert content_generator.thread_id == "test-thread"

@pytest.mark.asyncio
async def test_generate_slide_content(content_generator):
    """Test generating slide content."""
    await content_generator.initialize()
    
    variables = {
        "title": "Test Title",
        "subtitle": "Test Subtitle",
        "presenter": "Test User",
        "date": "2024-03-31"
    }
    
    result = await content_generator.generate_slide_content("title", variables)
    
    assert "content" in result
    assert result["type"] == "title"
    assert result["variables"] == variables

@pytest.mark.asyncio
async def test_generate_multiple_slides(content_generator):
    """Test generating multiple slides."""
    await content_generator.initialize()
    
    slides = [
        {
            "template_type": "title",
            "variables": {
                "title": "Test Presentation",
                "subtitle": "Testing Multiple Slides",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        },
        {
            "template_type": "content",
            "variables": {
                "title": "Test Content",
                "subtitle": "Content Details",
                "key_points": ["Point 1", "Point 2"],
                "context": "Test context"
            }
        }
    ]
    
    results = await content_generator.generate_multiple_slides(slides)
    
    assert len(results) == len(slides)
    for result in results:
        assert "content" in result
        assert "type" in result
        assert "variables" in result

@pytest.mark.asyncio
async def test_error_handling(content_generator):
    """Test error handling in content generation."""
    await content_generator.initialize()
    
    # Configure mock to simulate API error
    content_generator.api_client.add_message.side_effect = Exception("API Error")
    
    with pytest.raises(Exception) as exc_info:
        await content_generator.generate_slide_content(
            "title",
            {
                "title": "Test Title",
                "subtitle": "Test Subtitle",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        )
    assert str(exc_info.value) == "API Error"

@pytest.mark.asyncio
async def test_run_completion_timeout(content_generator):
    """Test handling of run completion timeout."""
    await content_generator.initialize()
    
    # Configure mock to simulate timeout
    content_generator.api_client.get_run_status.return_value = MagicMock(status="in_progress")
    
    with pytest.raises(TimeoutError):
        await content_generator.generate_slide_content(
            "title",
            {
                "title": "Test Title",
                "subtitle": "Test Subtitle",
                "presenter": "Test User",
                "date": "2024-03-31"
            },
            timeout=0.1
        )

@pytest.mark.asyncio
async def test_run_completion_error(content_generator):
    """Test handling of run completion error."""
    await content_generator.initialize()
    
    # Configure mock to simulate run failure
    content_generator.api_client.get_run_status.return_value = MagicMock(
        status="failed",
        last_error={"code": "error_code", "message": "Run failed"},
        get=lambda x, y=None: {"code": "error_code", "message": "Run failed"} if x == "last_error" else y
    )
    
    with pytest.raises(RuntimeError) as exc_info:
        await content_generator.generate_slide_content(
            "title",
            {
                "title": "Test Title",
                "subtitle": "Test Subtitle",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        )
    assert "Run failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_invalid_response_format(content_generator):
    """Test handling of invalid response format."""
    await content_generator.initialize()
    
    # Configure mock to return invalid response format
    content_generator.api_client.get_messages.return_value = MagicMock(
        data=[
            MagicMock(
                content=[
                    MagicMock(
                        # Return None for text to trigger AttributeError
                        text=None
                    )
                ]
            )
        ]
    )
    
    with pytest.raises(ValueError) as exc_info:
        await content_generator.generate_slide_content(
            "title",
            {
                "title": "Test Title",
                "subtitle": "Test Subtitle",
                "presenter": "Test User",
                "date": "2024-03-31"
            }
        )
    assert "Invalid response format" in str(exc_info.value)

@pytest.mark.asyncio
async def test_uninitialized_error():
    """Test error when using uninitialized generator."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        generator = SlideContentGenerator(api_key="test-key")
        
        with pytest.raises(RuntimeError) as exc_info:
            await generator.generate_slide_content("title", {"title": "Test"})
        
        assert "not initialized" in str(exc_info.value) 