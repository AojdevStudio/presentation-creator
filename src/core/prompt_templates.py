"""
Prompt templates for slide content generation using OpenAI Assistants API.
"""
from typing import Dict, List, Optional

class PromptTemplate:
    """Base class for prompt templates"""
    def __init__(self, template: str):
        self.template = template
        
    def format(self, **kwargs) -> str:
        """Format the template with provided variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable in prompt template: {e}")

class SlidePrompts:
    """Collection of prompt templates for slide generation"""
    
    TITLE_SLIDE = PromptTemplate("""
    Create a title slide with the following information:
    Title: {title}
    Subtitle: {subtitle}
    Presenter: {presenter}
    Date: {date}
    
    Format the content professionally and ensure it follows presentation best practices.
    """)
    
    CONTENT_SLIDE = PromptTemplate("""
    Create a content slide with the following requirements:
    Title: {title}
    Key Points:
    {key_points}
    
    Additional Context: {context}
    
    Format the content to be clear, concise, and visually appealing. Use bullet points where appropriate.
    Ensure the content follows the presentation's style guide and maintains consistency.
    """)
    
    DATA_VISUALIZATION_SLIDE = PromptTemplate("""
    Create a data visualization slide using the following data:
    Title: {title}
    Data: {data}
    Chart Type: {chart_type}
    
    Additional Requirements:
    - Include clear axis labels and legend
    - Use appropriate color scheme
    - Add brief annotations to highlight key insights
    - Keep the visualization clean and easy to understand
    """)
    
    SECTION_TRANSITION = PromptTemplate("""
    Create a transition slide for the following section:
    Current Section: {current_section}
    Next Section: {next_section}
    
    Create a smooth transition that maintains the presentation flow and prepares the audience
    for the upcoming content. Include a brief overview of what's coming next.
    """)
    
    SUMMARY_SLIDE = PromptTemplate("""
    Create a summary slide for the following content:
    Main Topics: {main_topics}
    Key Takeaways: {key_takeaways}
    
    Format the summary to be concise yet comprehensive. Highlight the most important points
    and ensure they align with the presentation's objectives.
    """)

    @staticmethod
    def get_template(template_type: str) -> PromptTemplate:
        """Get a specific prompt template by type"""
        templates = {
            'title': SlidePrompts.TITLE_SLIDE,
            'content': SlidePrompts.CONTENT_SLIDE,
            'data_viz': SlidePrompts.DATA_VISUALIZATION_SLIDE,
            'transition': SlidePrompts.SECTION_TRANSITION,
            'summary': SlidePrompts.SUMMARY_SLIDE
        }
        
        if template_type not in templates:
            raise ValueError(f"Unknown template type: {template_type}")
        
        return templates[template_type]

def generate_slide_prompt(template_type: str, **kwargs) -> str:
    """
    Generate a formatted prompt for slide content generation.
    
    Args:
        template_type: Type of slide template to use
        **kwargs: Variables to format the template with
        
    Returns:
        Formatted prompt string
    """
    template = SlidePrompts.get_template(template_type)
    return template.format(**kwargs) 