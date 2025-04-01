"""
Tests for the OpenAI Assistants API client wrapper.
"""
import os
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.core.openai_client import AssistantsAPIClient, OpenAIRateLimiter, ResponseCache
import openai
import tenacity

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    with patch('src.core.openai_client.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        yield mock_client

@pytest_asyncio.fixture
async def api_client():
    """Create an API client with mocked OpenAI client."""
    with patch('openai.OpenAI') as mock_openai:
        # Create mock instance
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Create and return client
        client = AssistantsAPIClient(api_key="test-key")
        client.client = mock_client
        yield client

def test_client_initialization():
    """Test client initialization with API key"""
    # Test with explicit API key
    client = AssistantsAPIClient(api_key="test-key")
    assert client.api_key == "test-key"
    
    # Test with environment variable
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
        client = AssistantsAPIClient()
        assert client.api_key == "env-key"
    
    # Test missing API key
    with pytest.raises(ValueError):
        AssistantsAPIClient(api_key=None)

@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter functionality"""
    limiter = OpenAIRateLimiter(max_requests=2, time_window=1)
    
    # First two requests should not wait
    await limiter.wait_if_needed()
    await limiter.wait_if_needed()
    
    # Third request should trigger wait
    with patch('asyncio.sleep') as mock_sleep:
        await limiter.wait_if_needed()
        mock_sleep.assert_called_once()

def test_response_cache(tmp_path):
    """Test response cache functionality"""
    cache = ResponseCache(cache_dir=str(tmp_path))
    
    # Test cache miss
    assert cache.get("test_prompt") is None
    
    # Test cache set and hit
    test_response = {"content": "test response"}
    cache.set("test_prompt", test_response)
    cached = cache.get("test_prompt")
    assert cached == test_response

@pytest.mark.asyncio
async def test_create_assistant(api_client):
    """Test creating an assistant"""
    mock_response = MagicMock()
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 100
    api_client.client.beta.assistants.create = AsyncMock(return_value=mock_response)
    
    response = await api_client.create_assistant(
        name="Test Assistant",
        instructions="Test instructions"
    )
    
    assert response == mock_response
    api_client.client.beta.assistants.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_thread(api_client):
    """Test creating a thread"""
    mock_response = MagicMock()
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 50
    api_client.client.beta.threads.create = AsyncMock(return_value=mock_response)
    
    response = await api_client.create_thread()
    
    assert response == mock_response
    api_client.client.beta.threads.create.assert_called_once()

@pytest.mark.asyncio
async def test_add_message(api_client):
    """Test adding a message to a thread"""
    mock_response = MagicMock()
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 75
    api_client.client.beta.threads.messages.create = AsyncMock(return_value=mock_response)
    
    response = await api_client.add_message(
        thread_id="test-thread",
        content="test message"
    )
    
    assert response == mock_response
    api_client.client.beta.threads.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_run_assistant(api_client):
    """Test running an assistant"""
    mock_response = MagicMock()
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 25
    api_client.client.beta.threads.runs.create = AsyncMock(return_value=mock_response)
    
    response = await api_client.run_assistant(
        thread_id="test-thread",
        assistant_id="test-assistant"
    )
    
    assert response == mock_response
    api_client.client.beta.threads.runs.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_run_status(api_client):
    """Test getting run status"""
    mock_response = MagicMock()
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 10
    api_client.client.beta.threads.runs.retrieve = AsyncMock(return_value=mock_response)
    
    response = await api_client.get_run_status(
        thread_id="test-thread",
        run_id="test-run"
    )
    
    assert response == mock_response
    api_client.client.beta.threads.runs.retrieve.assert_called_once()

@pytest.mark.asyncio
async def test_get_messages(api_client):
    """Test getting messages from a thread"""
    mock_response = MagicMock()
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 30
    api_client.client.beta.threads.messages.list = AsyncMock(return_value=mock_response)
    
    response = await api_client.get_messages(thread_id="test-thread")
    
    assert response == mock_response
    api_client.client.beta.threads.messages.list.assert_called_once()

@pytest.mark.asyncio
async def test_token_usage_tracking(api_client):
    """Test token usage tracking"""
    # Create mock response with usage information
    mock_response = MagicMock()
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 100
    api_client.client.beta.threads.create = AsyncMock(return_value=mock_response)
    
    # Make an API call
    await api_client.create_thread()
    
    # Check token usage tracking
    usage = api_client.get_token_usage()
    assert usage["total_tokens"] == 100

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for different types of errors"""
    mock_client = AsyncMock()
    with patch('openai.OpenAI', return_value=mock_client):
        client = AssistantsAPIClient(api_key="test-key")

        # Test rate limit error using APIStatusError
        mock_client.beta.threads.create = AsyncMock(
            side_effect=openai.APIStatusError(
                message="Rate limit exceeded",
                response=Mock(status_code=429),
                body={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}}
            )
        )

        # Should trigger retry and eventually raise RetryError
        with pytest.raises(tenacity.RetryError):
            await client.create_thread()

        # Test API error using APIConnectionError (simpler constructor)
        mock_client.beta.threads.create = AsyncMock(
            side_effect=openai.APIConnectionError(message="Connection error")
        )

        # Should also trigger retry and eventually raise RetryError
        with pytest.raises(tenacity.RetryError):
            await client.create_thread()

        # Verify token usage is properly tracked even with errors
        assert client.get_token_usage()["total_api_calls"] > 0 