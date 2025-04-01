"""
Slide content generator using OpenAI Assistants API.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from .openai_client import OpenAIClient
from .prompt_templates import generate_slide_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlideContentGenerator:
    """Generates slide content using OpenAI Assistants API"""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None, api_key: Optional[str] = None):
        """Initialize the slide content generator.
        
        Args:
            openai_client: Optional OpenAIClient instance. If not provided, one will be created.
            api_key: Optional OpenAI API key. If not provided and openai_client is None,
                    will use environment variable.
        """
        self.client = openai_client or OpenAIClient(api_key=api_key)
        self.assistant_id = None
        self.thread_id = None
        
    async def initialize(self) -> None:
        """Initialize the assistant and thread for slide generation."""
        # Create a specialized assistant for slide content generation
        assistant = await self.client.create_assistant(
            name="Slide Content Generator",
            instructions="""You are a professional presentation content generator. 
            Your role is to create clear, concise, and engaging slide content that follows
            best practices for presentations. Focus on:
            
            1. Clear and concise messaging
            2. Proper content hierarchy
            3. Consistent formatting
            4. Engaging and professional tone
            5. Appropriate content density per slide
            
            Generate content that can be directly used in presentation slides.""",
            model="gpt-4-turbo-preview"
        )
        
        # Create a new thread for the conversation
        thread = await self.client.create_thread()
        
        # Store the IDs
        self.assistant_id = assistant.id
        self.thread_id = thread.id
        
    async def generate_slide_content(self, 
                                   template_type: str, 
                                   variables: Dict[str, Any],
                                   max_retries: int = 3,
                                   timeout: float = 30.0) -> Dict[str, Any]:
        """Generate content for a slide using the specified template.
        
        Args:
            template_type: Type of slide template to use (e.g., 'title', 'content')
            variables: Dictionary of variables to format the template with
            max_retries: Maximum number of retries for content generation
            timeout: Maximum time to wait for completion in seconds
            
        Returns:
            Dictionary containing the generated slide content
            
        Raises:
            RuntimeError: If generator not initialized or run fails
            TimeoutError: If run completion takes longer than timeout
            ValueError: If template variables are missing
        """
        if not self.assistant_id or not self.thread_id:
            raise RuntimeError("SlideContentGenerator not initialized. Call initialize() first.")
            
        # Generate the prompt using the template
        prompt = generate_slide_prompt(template_type, **variables)
        
        # Add the prompt as a message to the thread
        await self.client.add_message(
            thread_id=self.thread_id,
            content=prompt
        )
        
        # Run the assistant
        run = await self.client.run_assistant(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )
        
        # Wait for completion with timeout
        start_time = asyncio.get_event_loop().time()
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Assistant run timed out")
                
            status = await self.client.get_run_status(
                thread_id=self.thread_id,
                run_id=run.id
            )
            
            if status.status == "completed":
                break
            elif status.status == "failed":
                error = status.get("last_error", {})
                raise RuntimeError(f"Assistant run failed: {error.get('message', 'Unknown error')}")
                
            await asyncio.sleep(1)  # Wait before checking again
        
        # Get the assistant's response
        messages = await self.client.get_messages(thread_id=self.thread_id)
        latest_message = messages.data[0]  # Get the most recent message
        
        try:
            # Extract and return the content
            return {
                "content": latest_message.content[0].text.value,
                "type": template_type,
                "variables": variables
            }
        except (AttributeError, IndexError) as e:
            raise ValueError("Invalid response format from assistant") from e
            
    async def generate_multiple_slides(self, 
                                     slide_specs: List[Dict[str, Any]],
                                     max_retries: int = 3) -> List[Dict[str, Any]]:
        """Generate content for multiple slides.
        
        Args:
            slide_specs: List of dictionaries containing template_type and variables for each slide
            max_retries: Maximum number of retries for content generation
            
        Returns:
            List of dictionaries containing the generated slide content
        """
        results = []
        for spec in slide_specs:
            try:
                content = await self.generate_slide_content(
                    template_type=spec["template_type"],
                    variables=spec["variables"],
                    max_retries=max_retries
                )
                results.append(content)
            except Exception as e:
                logger.error(f"Error generating slide content: {e}")
                # Add error information to results
                results.append({
                    "error": str(e),
                    "type": spec["template_type"],
                    "variables": spec["variables"]
                })
        return results 