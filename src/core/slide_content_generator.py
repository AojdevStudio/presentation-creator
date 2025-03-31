"""
Slide content generator using OpenAI Assistants API.
"""
import logging
from typing import Dict, List, Optional, Any
from .openai_client import AssistantsAPIClient
from .prompt_templates import generate_slide_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlideContentGenerator:
    """Generates slide content using OpenAI Assistants API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the slide content generator.
        
        Args:
            api_key: Optional OpenAI API key. If not provided, will use environment variable.
        """
        self.client = AssistantsAPIClient(api_key=api_key)
        self.assistant = None
        self.thread = None
        
    async def initialize(self) -> None:
        """Initialize the assistant and thread for slide generation."""
        # Create a specialized assistant for slide content generation
        self.assistant = await self.client.create_assistant(
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
        self.thread = await self.client.create_thread()
        
    async def generate_slide_content(self, 
                                   template_type: str, 
                                   variables: Dict[str, Any],
                                   max_retries: int = 3) -> Dict[str, Any]:
        """Generate content for a slide using the specified template.
        
        Args:
            template_type: Type of slide template to use (e.g., 'title', 'content')
            variables: Dictionary of variables to format the template with
            max_retries: Maximum number of retries for content generation
            
        Returns:
            Dictionary containing the generated slide content
        """
        if not self.assistant or not self.thread:
            raise RuntimeError("SlideContentGenerator not initialized. Call initialize() first.")
            
        # Generate the prompt using the template
        prompt = generate_slide_prompt(template_type, **variables)
        
        # Add the prompt as a message to the thread
        await self.client.add_message(
            thread_id=self.thread.id,
            content=prompt
        )
        
        # Run the assistant
        run = await self.client.run_assistant(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id
        )
        
        # Wait for completion and get the response
        status = await self.client.get_run_status(
            thread_id=self.thread.id,
            run_id=run.id
        )
        
        if status.status == "completed":
            # Get the assistant's response
            messages = await self.client.get_messages(thread_id=self.thread.id)
            latest_message = messages.data[0]  # Get the most recent message
            
            # Extract and return the content
            return {
                "content": latest_message.content[0].text.value,
                "type": template_type,
                "variables": variables
            }
        else:
            raise RuntimeError(f"Assistant run failed with status: {status.status}")
            
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