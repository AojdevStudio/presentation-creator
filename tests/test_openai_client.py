"""
Tests for the OpenAI Assistants API client wrapper.
"""
import os
import pytest
from unittest.mock import Mock, patch
from src.core.openai_client import AssistantsAPIClient, OpenAIRateLimiter, ResponseCache
import openai

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    with patch('src.core.openai_client.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        yield mock_client

@pytest.fixture
def api_client(mock_openai_client):
    """Create an API client instance with a mock OpenAI client"""
    return AssistantsAPIClient(api_key="test-key")

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

def test_rate_limiter():
    """Test rate limiter functionality"""
    limiter = OpenAIRateLimiter(max_requests=2, time_window=1)
    
    # First two requests should not wait
    limiter.wait_if_needed()
    limiter.wait_if_needed()
    
    # Third request should trigger wait
    with patch('time.sleep') as mock_sleep:
        limiter.wait_if_needed()
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

def test_create_assistant(api_client, mock_openai_client):
    """Test creating an assistant"""
    mock_response = Mock()
    mock_openai_client.beta.assistants.create.return_value = mock_response
    
    response = api_client.create_assistant(
        name="Test Assistant",
        instructions="Test instructions"
    )
    
    assert response == mock_response
    mock_openai_client.beta.assistants.create.assert_called_once_with(
        name="Test Assistant",
        instructions="Test instructions",
        model="gpt-4-turbo-preview"
    )

def test_create_thread(api_client, mock_openai_client):
    """Test creating a thread"""
    mock_response = Mock()
    mock_openai_client.beta.threads.create.return_value = mock_response
    
    response = api_client.create_thread()
    
    assert response == mock_response
    mock_openai_client.beta.threads.create.assert_called_once()

def test_add_message(api_client, mock_openai_client):
    """Test adding a message to a thread"""
    mock_response = Mock()
    mock_openai_client.beta.threads.messages.create.return_value = mock_response
    
    response = api_client.add_message(
        thread_id="test-thread",
        content="test message"
    )
    
    assert response == mock_response
    mock_openai_client.beta.threads.messages.create.assert_called_once_with(
        thread_id="test-thread",
        role="user",
        content="test message"
    )

def test_run_assistant(api_client, mock_openai_client):
    """Test running an assistant"""
    mock_response = Mock()
    mock_openai_client.beta.threads.runs.create.return_value = mock_response
    
    response = api_client.run_assistant(
        thread_id="test-thread",
        assistant_id="test-assistant"
    )
    
    assert response == mock_response
    mock_openai_client.beta.threads.runs.create.assert_called_once_with(
        thread_id="test-thread",
        assistant_id="test-assistant"
    )

def test_get_run_status(api_client, mock_openai_client):
    """Test getting run status"""
    mock_response = Mock()
    mock_openai_client.beta.threads.runs.retrieve.return_value = mock_response
    
    response = api_client.get_run_status(
        thread_id="test-thread",
        run_id="test-run"
    )
    
    assert response == mock_response
    mock_openai_client.beta.threads.runs.retrieve.assert_called_once_with(
        thread_id="test-thread",
        run_id="test-run"
    )

def test_get_messages(api_client, mock_openai_client):
    """Test getting messages from a thread"""
    mock_response = Mock()
    mock_openai_client.beta.threads.messages.list.return_value = mock_response
    
    response = api_client.get_messages(thread_id="test-thread")
    
    assert response == mock_response
    mock_openai_client.beta.threads.messages.list.assert_called_once_with(
        thread_id="test-thread"
    )

def test_token_usage_tracking(api_client, mock_openai_client):
    """Test token usage tracking"""
    # Create mock response with usage information
    mock_response = Mock()
    mock_response.usage.total_tokens = 100
    mock_openai_client.beta.threads.create.return_value = mock_response
    
    # Make an API call
    api_client.create_thread()
    
    # Check token usage tracking
    usage = api_client.get_token_usage()
    assert usage["total_tokens"] == 100
    assert usage["total_api_calls"] == 1

@pytest.mark.parametrize("error_class", [
    openai.RateLimitError,
    openai.APIError,
    Exception
])
def test_error_handling(api_client, mock_openai_client, error_class):
    """Test error handling for different types of errors"""
    mock_openai_client.beta.threads.create.side_effect = error_class("Test error")
    
    with pytest.raises(error_class):
        api_client.create_thread() 