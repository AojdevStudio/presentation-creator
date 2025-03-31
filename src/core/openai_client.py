"""
OpenAI Assistants API client wrapper with error handling, rate limiting, and caching.
"""
import os
import time
import json
import logging
from typing import Any, Dict, Optional
from functools import wraps
from pathlib import Path
import openai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIRateLimiter:
    """Rate limiter for OpenAI API calls"""
    def __init__(self, max_requests: int = 50, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def wait_if_needed(self):
        """Wait if rate limit is reached"""
        now = time.time()
        # Remove old requests
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Waiting {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
            self.requests = self.requests[1:]
        
        self.requests.append(now)

class ResponseCache:
    """Cache for API responses"""
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, prompt: str) -> str:
        """Generate a cache key from the prompt"""
        return str(hash(prompt))

    def get(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get cached response for a prompt"""
        cache_key = self._get_cache_key(prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
                return None
        return None

    def set(self, prompt: str, response: Dict[str, Any]):
        """Cache a response for a prompt"""
        cache_key = self._get_cache_key(prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(response, f)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

class AssistantsAPIClient:
    """OpenAI Assistants API client with error handling, rate limiting, and caching"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 max_retries: int = 3,
                 cache_enabled: bool = True):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
            
        self.client = OpenAI(api_key=self.api_key)
        self.rate_limiter = OpenAIRateLimiter()
        self.cache = ResponseCache() if cache_enabled else None
        self.max_retries = max_retries
        
        # Track token usage
        self.total_tokens_used = 0
        self.total_api_calls = 0

    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_api_call(self, func, *args, **kwargs):
        """Make an API call with retry logic"""
        try:
            await self.rate_limiter.wait_if_needed()
            response = await func(*args, **kwargs)
            self.total_api_calls += 1
            # Update token usage if available in response
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            return response
        except openai.RateLimitError:
            logger.warning("Rate limit exceeded, retrying after exponential backoff")
            raise
        except openai.APIError as e:
            logger.error(f"API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def create_assistant(self, name: str, instructions: str, model: str = "gpt-4-turbo-preview") -> Any:
        """Create a new assistant"""
        return await self._make_api_call(
            self.client.beta.assistants.create,
            name=name,
            instructions=instructions,
            model=model
        )

    async def create_thread(self) -> Any:
        """Create a new thread"""
        return await self._make_api_call(
            self.client.beta.threads.create
        )

    async def add_message(self, thread_id: str, content: str, role: str = "user") -> Any:
        """Add a message to a thread"""
        return await self._make_api_call(
            self.client.beta.threads.messages.create,
            thread_id=thread_id,
            role=role,
            content=content
        )

    async def run_assistant(self, thread_id: str, assistant_id: str) -> Any:
        """Run an assistant on a thread"""
        return await self._make_api_call(
            self.client.beta.threads.runs.create,
            thread_id=thread_id,
            assistant_id=assistant_id
        )

    async def get_run_status(self, thread_id: str, run_id: str) -> Any:
        """Get the status of a run"""
        return await self._make_api_call(
            self.client.beta.threads.runs.retrieve,
            thread_id=thread_id,
            run_id=run_id
        )

    async def get_messages(self, thread_id: str) -> Any:
        """Get messages from a thread"""
        return await self._make_api_call(
            self.client.beta.threads.messages.list,
            thread_id=thread_id
        )

    def get_token_usage(self) -> Dict[str, int]:
        """Get token usage statistics"""
        return {
            "total_tokens": self.total_tokens_used,
            "total_api_calls": self.total_api_calls
        } 