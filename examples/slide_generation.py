"""
Example script demonstrating how to use the OpenAI client and prompt templates for slide generation.
"""
import os
import json
from dotenv import load_dotenv
from src.core.openai_client import AssistantsAPIClient
from src.core.prompt_templates import generate_slide_prompt

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the OpenAI client
    client = AssistantsAPIClient()
    
    # Create an assistant for slide generation
    assistant = client.create_assistant(
        name="Slide Generator",
        instructions="""
        You are an expert presentation creator. Your task is to generate professional,
        engaging, and well-structured slide content based on the provided prompts.
        Follow these guidelines:
        1. Keep content concise and impactful
        2. Use clear and professional language
        3. Maintain consistency in tone and style
        4. Structure information logically
        5. Highlight key points effectively
        """
    )
    
    # Example presentation structure
    presentation = {
        'title': {
            'title': 'AI-Powered Presentations',
            'subtitle': 'The Future of Content Creation',
            'presenter': 'John Doe',
            'date': '2024-03-31'
        },
        'content': {
            'title': 'Key Benefits',
            'key_points': '''
            - Automated content generation
            - Professional formatting
            - Time-saving workflow
            - Consistent quality
            ''',
            'context': 'Focus on the transformative impact on presentation creation.'
        },
        'data_viz': {
            'title': 'Efficiency Gains',
            'data': json.dumps({
                'manual_time': 120,
                'automated_time': 15,
                'quality_score_manual': 85,
                'quality_score_automated': 95
            }),
            'chart_type': 'bar'
        }
    }
    
    try:
        # Create a new thread for the conversation
        thread = client.create_thread()
        
        # Generate content for each slide type
        for slide_type, variables in presentation.items():
            # Generate the prompt using our templates
            prompt = generate_slide_prompt(slide_type, **variables)
            
            # Add the prompt to the thread
            client.add_message(thread.id, prompt)
            
            # Run the assistant to generate content
            run = client.run_assistant(thread.id, assistant.id)
            
            # Wait for completion and get the response
            while True:
                status = client.get_run_status(thread.id, run.id)
                if status.status == 'completed':
                    break
            
            # Get the assistant's response
            messages = client.get_messages(thread.id)
            latest_message = messages.data[0]  # Most recent message
            
            # Print the generated content
            print(f"\n=== {slide_type.upper()} SLIDE ===")
            print(latest_message.content[0].text.value)
            print("\n")
        
        # Print usage statistics
        usage = client.get_token_usage()
        print("=== USAGE STATISTICS ===")
        print(f"Total tokens used: {usage['total_tokens']}")
        print(f"Total API calls: {usage['total_api_calls']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 