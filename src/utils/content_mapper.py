"""
Content mapper module for transforming parsed text into internal slide representation format.
"""
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentMapper:
    """Maps parsed text structures into slide objects compatible with the slide generator."""
    
    def __init__(self, 
                max_bullets_per_slide: int = 6, 
                max_text_length_per_slide: int = 400,
                content_density: str = "medium"):
        """Initialize the content mapper.
        
        Args:
            max_bullets_per_slide: Maximum number of bullet points per slide
            max_text_length_per_slide: Maximum text length per slide in characters
            content_density: Density of content per slide (low, medium, high)
        """
        self.max_bullets_per_slide = max_bullets_per_slide
        self.max_text_length_per_slide = max_text_length_per_slide
        
        # Adjust settings based on content density
        if content_density == "low":
            self.max_bullets_per_slide = min(self.max_bullets_per_slide, 4)
            self.max_text_length_per_slide = min(self.max_text_length_per_slide, 300)
        elif content_density == "high":
            self.max_bullets_per_slide = max(self.max_bullets_per_slide, 8)
            self.max_text_length_per_slide = max(self.max_text_length_per_slide, 500)
            
    def map_to_slide_specs(self, parsed_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map parsed content to slide specifications.
        
        Args:
            parsed_content: Parsed content from TextParser
            
        Returns:
            List of slide specifications compatible with PresentationBuilder
        """
        if not parsed_content or "slides" not in parsed_content:
            logger.warning("Invalid parsed content format")
            return []
            
        slide_specs = []
        slides = parsed_content["slides"]
        
        # Title slide handling
        if slides and len(slides) > 0:
            first_slide = slides[0]
            # Generate title slide
            title_slide = {
                "template_type": "title",
                "variables": {
                    "title": first_slide["title"],
                    "subtitle": first_slide.get("subtitle", ""),
                    "presenter": "",  # Can be passed separately
                    "date": ""  # Can be passed separately
                }
            }
            slide_specs.append(title_slide)
            
            # Process the content of the first slide if it has non-title content
            if len(first_slide["elements"]) > 0:
                content_slides = self._map_slide_content(first_slide)
                slide_specs.extend(content_slides)
        
        # Process the rest of the slides
        for slide in slides[1:]:
            # For section transitions, we can use the section_transition template
            if any(keyword in slide["title"].lower() for keyword in ["section", "part", "chapter"]):
                transition_slide = {
                    "template_type": "section_transition",
                    "variables": {
                        "title": slide["title"],
                        "subtitle": slide.get("subtitle", "")
                    }
                }
                slide_specs.append(transition_slide)
            
            # Map the slide content
            content_slides = self._map_slide_content(slide)
            slide_specs.extend(content_slides)
            
        # Generate summary slide if appropriate
        if slides and any("summary" in slide["title"].lower() or "conclusion" in slide["title"].lower() for slide in slides[-2:]):
            summary_slide = self._generate_summary_slide(slides)
            if summary_slide:
                slide_specs.append(summary_slide)
                
        return slide_specs
        
    def _map_slide_content(self, slide: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map a single slide's content to slide specifications.
        
        Args:
            slide: Single slide dictionary from parsed content
            
        Returns:
            List of slide specifications for this content
        """
        result_slides = []
        elements = slide["elements"]
        
        # If there are no elements, skip this slide
        if not elements:
            return result_slides
            
        # Group elements by type for better organization
        bullet_lists = []
        text_blocks = []
        numbered_lists = []
        code_blocks = []
        subheadings = []
        
        for element in elements:
            element_type = element["type"]
            if element_type == "bullet_list":
                bullet_lists.append(element)
            elif element_type == "numbered_list":
                numbered_lists.append(element)
            elif element_type == "text":
                text_blocks.append(element)
            elif element_type == "code":
                code_blocks.append(element)
            elif element_type == "subheading":
                subheadings.append(element)
                
        # Process bullet and numbered lists (these make good content slides)
        all_lists = bullet_lists + numbered_lists
        if all_lists:
            for list_element in all_lists:
                # Split large lists into multiple slides if needed
                content_chunks = self._chunk_list_items(list_element["content"])
                
                for i, chunk in enumerate(content_chunks):
                    context = ""
                    
                    # If this is the first chunk and there are text blocks, 
                    # use the first text block as context
                    if i == 0 and text_blocks:
                        context = text_blocks[0]["content"]
                        
                    # If there are subheadings, include them in the title
                    title_parts = [slide["title"]]
                    if subheadings and i < len(subheadings):
                        title_parts.append(subheadings[i]["content"])
                    
                    # Create the content slide
                    content_slide = {
                        "template_type": "content",
                        "variables": {
                            "title": " - ".join(title_parts),
                            "key_points": chunk,
                            "context": context
                        }
                    }
                    result_slides.append(content_slide)
        
        # Process text blocks if no lists were processed
        elif text_blocks:
            # Combine text blocks
            combined_text = " ".join(block["content"] for block in text_blocks)
            
            # Split text into manageable chunks
            text_chunks = self._chunk_text(combined_text)
            
            for i, chunk in enumerate(text_chunks):
                # If there are subheadings, include them in the title
                title_parts = [slide["title"]]
                if subheadings and i < len(subheadings):
                    title_parts.append(subheadings[i]["content"])
                
                content_slide = {
                    "template_type": "content",
                    "variables": {
                        "title": " - ".join(title_parts),
                        "key_points": [chunk],  # Single point with the text chunk
                        "context": ""
                    }
                }
                result_slides.append(content_slide)
        
        # Process code blocks if present
        for code_block in code_blocks:
            # Create a special content slide for code
            code_slide = {
                "template_type": "content",
                "variables": {
                    "title": f"{slide['title']} - Code Example",
                    "key_points": ["Code example:"],
                    "context": code_block["content"],
                    "is_code": True  # Flag to indicate this is code content
                }
            }
            result_slides.append(code_slide)
            
        return result_slides
        
    def _chunk_list_items(self, items: List[str]) -> List[List[str]]:
        """Split a list of items into smaller chunks for multiple slides.
        
        Args:
            items: List of content items (e.g., bullet points)
            
        Returns:
            List of lists, each representing items for one slide
        """
        chunks = []
        current_chunk = []
        
        for item in items:
            current_chunk.append(item)
            
            # If we've reached the maximum bullets per slide, create a new chunk
            if len(current_chunk) >= self.max_bullets_per_slide:
                chunks.append(current_chunk)
                current_chunk = []
                
        # Add any remaining items
        if current_chunk:
            chunks.append(current_chunk)
            
        # If no chunks were created (empty input), return empty list
        if not chunks:
            chunks = [[]]
            
        return chunks
        
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into smaller chunks for multiple slides.
        
        Args:
            text: Text content
            
        Returns:
            List of text chunks, each for one slide
        """
        # If text is already small enough for one slide, return it as is
        if len(text) <= self.max_text_length_per_slide:
            return [text]
            
        chunks = []
        
        # Try to split by sentences or paragraphs
        import re
        
        # First try to split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.max_text_length_per_slide:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # If adding this paragraph would exceed the limit,
                # save the current chunk and start a new one
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If a single paragraph is too long, split it by sentences
                if len(para) > self.max_text_length_per_slide:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) <= self.max_text_length_per_slide:
                            if current_chunk:
                                current_chunk += " " + sentence
                            else:
                                current_chunk = sentence
                        else:
                            chunks.append(current_chunk)
                            current_chunk = sentence
                else:
                    current_chunk = para
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def _generate_summary_slide(self, slides: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate a summary slide based on the content of all slides.
        
        Args:
            slides: List of all slides from parsed content
            
        Returns:
            Summary slide specification or None
        """
        # Extract main topics from slide titles
        main_topics = [slide["title"] for slide in slides if "title" in slide]
        
        # Extract key takeaways from the last slide if it's labeled as summary or conclusion
        key_takeaways = []
        if slides and (
            "summary" in slides[-1]["title"].lower() or 
            "conclusion" in slides[-1]["title"].lower()
        ):
            for element in slides[-1]["elements"]:
                if element["type"] in ["bullet_list", "numbered_list"]:
                    key_takeaways.extend(element["content"])
        
        # If no explicit takeaways, generate some from the first bullet point of each slide
        if not key_takeaways:
            for slide in slides:
                for element in slide["elements"]:
                    if element["type"] in ["bullet_list", "numbered_list"] and element["content"]:
                        key_takeaways.append(element["content"][0])
                        break
        
        # Limit to a reasonable number of takeaways
        key_takeaways = key_takeaways[:5]
        
        # Only create a summary slide if we have enough content
        if len(main_topics) >= 2 or len(key_takeaways) >= 2:
            return {
                "template_type": "summary",
                "variables": {
                    "title": "Summary",
                    "main_topics": main_topics[:5],  # Limit to 5 topics
                    "key_takeaways": key_takeaways
                }
            }
        
        return None
        
    def set_metadata(self, slide_specs: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Set metadata for slides (presenter, date, etc).
        
        Args:
            slide_specs: List of slide specifications
            metadata: Dictionary of metadata to set
            
        Returns:
            Updated list of slide specifications
        """
        # Find the title slide and update it with metadata
        for slide in slide_specs:
            if slide["template_type"] == "title":
                # Update the variables with metadata
                for key, value in metadata.items():
                    if key in slide["variables"]:
                        slide["variables"][key] = value
                break
                
        return slide_specs
        
    def generate_slide_specs_from_text(self, 
                                      text: str, 
                                      parsed_content: Dict[str, Any],
                                      metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate slide specifications directly from parsed text.
        
        Args:
            text: Original text content
            parsed_content: Parsed content structure
            metadata: Optional metadata (presenter, date, etc.)
            
        Returns:
            List of slide specifications
        """
        # Map the parsed content to slide specs
        slide_specs = self.map_to_slide_specs(parsed_content)
        
        # Apply metadata if provided
        if metadata:
            slide_specs = self.set_metadata(slide_specs, metadata)
            
        return slide_specs 