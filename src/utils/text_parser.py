"""
Text parser module for converting user-provided content into structured presentation format.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextParser:
    """Parses user-provided text content into structured format for presentation slides."""
    
    def __init__(self, custom_patterns: Optional[Dict[str, str]] = None):
        """Initialize the text parser.
        
        Args:
            custom_patterns: Optional dictionary of custom regex patterns to use for parsing
        """
        # Default regex patterns for different content elements
        self.patterns = {
            # Headings - lines that are standalone and either all caps, 
            # numbered (1., 1.1), or end with newline
            'heading': r'^(?:\d+\.[\d\.]*\s+|#+\s+)?([A-Z0-9][\w\s\:\-\'\"]+)$',
            
            # Bullet points - lines starting with -, *, or •
            'bullet': r'^\s*[-*•]\s+(.+)$',
            
            # Numbered list items - lines starting with numbers followed by . or )
            'numbered': r'^\s*(\d+)[\.|\)]\s+(.+)$',
            
            # Paragraphs - blocks of text separated by blank lines
            # (handled separately in the parsing logic)
        }
        
        # Update with any custom patterns
        if custom_patterns:
            self.patterns.update(custom_patterns)
            
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse text content into structured format.
        
        Args:
            text: String containing user-provided content
            
        Returns:
            Dictionary with parsed content structure
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for parsing")
            return {"slides": []}
            
        # Split text into lines and normalize line endings
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        
        # Initialize result structure
        result = {
            "slides": []
        }
        
        # Track current slide being built
        current_slide = None
        current_element = None
        
        # Process each line
        for line in lines:
            line = line.rstrip()
            
            # Skip empty lines for basic parsing
            if not line:
                # If we have at least one parsed element, consider an empty line
                # as a slide separator (unless it's the beginning or already has content)
                if current_slide and len(current_slide["elements"]) > 0 and current_element:
                    current_element = None
                continue
            
            # Check if it's a heading
            heading_match = re.match(self.patterns['heading'], line)
            if heading_match:
                # New slide with this heading as title
                if current_slide:
                    result["slides"].append(current_slide)
                
                current_slide = {
                    "title": heading_match.group(1).strip(),
                    "elements": []
                }
                current_element = None
                continue
            
            # If we don't have a current slide yet, create one with default title
            if not current_slide:
                current_slide = {
                    "title": "Slide",
                    "elements": []
                }
            
            # Check for bullet points
            bullet_match = re.match(self.patterns['bullet'], line)
            if bullet_match:
                bullet_content = bullet_match.group(1).strip()
                
                # Check if we already have a bullet list element
                if current_element and current_element["type"] == "bullet_list":
                    current_element["content"].append(bullet_content)
                else:
                    # Create a new bullet list element
                    current_element = {
                        "type": "bullet_list",
                        "content": [bullet_content]
                    }
                    current_slide["elements"].append(current_element)
                continue
            
            # Check for numbered list items
            numbered_match = re.match(self.patterns['numbered'], line)
            if numbered_match:
                number = numbered_match.group(1)
                numbered_content = numbered_match.group(2).strip()
                
                # Check if we already have a numbered list element
                if current_element and current_element["type"] == "numbered_list":
                    current_element["content"].append(numbered_content)
                else:
                    # Create a new numbered list element
                    current_element = {
                        "type": "numbered_list",
                        "content": [numbered_content]
                    }
                    current_slide["elements"].append(current_element)
                continue
            
            # If no special formatting, treat as paragraph/text
            if current_element and current_element["type"] == "text":
                # Append to existing text with proper spacing
                if current_element["content"].endswith(" "):
                    current_element["content"] += line
                else:
                    current_element["content"] += " " + line
            else:
                # Create a new text element
                current_element = {
                    "type": "text",
                    "content": line
                }
                current_slide["elements"].append(current_element)
        
        # Add the last slide if it exists
        if current_slide:
            result["slides"].append(current_slide)
            
        # Post-process slides to improve structure
        result = self._post_process_slides(result)
            
        return result
    
    def _post_process_slides(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process the parsed slides to improve structure.
        
        Args:
            parsed_data: Dictionary with initial parsed content
            
        Returns:
            Dictionary with improved content structure
        """
        for slide in parsed_data["slides"]:
            # Merge adjacent text elements
            i = 0
            while i < len(slide["elements"]) - 1:
                if (slide["elements"][i]["type"] == "text" and 
                    slide["elements"][i + 1]["type"] == "text"):
                    # Merge with spacing
                    slide["elements"][i]["content"] += " " + slide["elements"][i + 1]["content"]
                    slide["elements"].pop(i + 1)
                else:
                    i += 1
                    
            # Check if the first element contains keywords suggesting it's a subtitle
            if (len(slide["elements"]) > 0 and 
                slide["elements"][0]["type"] == "text" and
                len(slide["elements"][0]["content"]) < 100):
                first_el = slide["elements"][0]["content"].lower()
                subtitle_keywords = ["overview", "introduction", "summary", "conclusion", "agenda"]
                if any(keyword in first_el for keyword in subtitle_keywords):
                    slide["subtitle"] = slide["elements"][0]["content"]
                    slide["elements"].pop(0)
                    
        return parsed_data
    
    def parse_markdown(self, markdown_text: str) -> Dict[str, Any]:
        """Parse markdown text into structured format.
        
        Args:
            markdown_text: String containing markdown-formatted content
            
        Returns:
            Dictionary with parsed content structure
        """
        # Enhanced patterns for markdown
        markdown_patterns = {
            # Markdown headings (# Heading)
            'md_heading': r'^(#{1,6})\s+(.+)$',
            
            # Markdown bullet points
            'md_bullet': r'^\s*[-*+]\s+(.+)$',
            
            # Markdown code blocks
            'md_code_start': r'^```(\w*)$',
            'md_code_end': r'^```$',
            
            # Markdown emphasis
            'md_bold': r'\*\*(.+?)\*\*',
            'md_italic': r'\*(.+?)\*',
        }
        
        # Initialize result structure
        result = {"slides": []}
        
        # Split text into lines
        lines = markdown_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        
        # Track current slide and current element
        current_slide = None
        current_element = None
        in_code_block = False
        code_content = []
        code_language = ""
        
        # Process each line
        for line in lines:
            line = line.rstrip()
            
            # Handle code blocks
            code_start_match = re.match(markdown_patterns['md_code_start'], line)
            if code_start_match:
                in_code_block = True
                code_content = []
                code_language = code_start_match.group(1)
                continue
                
            if in_code_block:
                if re.match(markdown_patterns['md_code_end'], line):
                    in_code_block = False
                    if not current_slide:
                        current_slide = {
                            "title": "Code Example",
                            "elements": []
                        }
                    current_element = {
                        "type": "code",
                        "language": code_language,
                        "content": "\n".join(code_content)
                    }
                    current_slide["elements"].append(current_element)
                    current_element = None
                else:
                    code_content.append(line)
                continue
            
            # Check for markdown headings
            heading_match = re.match(markdown_patterns['md_heading'], line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                # Level 1-2 headings create new slides
                if level <= 2:
                    if current_slide:
                        result["slides"].append(current_slide)
                    
                    current_slide = {
                        "title": title,
                        "elements": []
                    }
                    current_element = None
                # Level 3+ headings become subsections within slides
                else:
                    if not current_slide:
                        current_slide = {
                            "title": "Slide",
                            "elements": []
                        }
                    
                    current_element = {
                        "type": "subheading",
                        "level": level,
                        "content": title
                    }
                    current_slide["elements"].append(current_element)
                    current_element = None
                continue
            
            # Skip empty lines
            if not line:
                current_element = None
                continue
            
            # Ensure we have a current slide
            if not current_slide:
                current_slide = {
                    "title": "Slide",
                    "elements": []
                }
            
            # Check for markdown bullet points
            bullet_match = re.match(markdown_patterns['md_bullet'], line)
            if bullet_match:
                bullet_content = bullet_match.group(1).strip()
                
                # Process emphasis in content
                bullet_content = self._process_markdown_emphasis(bullet_content, markdown_patterns)
                
                if current_element and current_element["type"] == "bullet_list":
                    current_element["content"].append(bullet_content)
                else:
                    current_element = {
                        "type": "bullet_list",
                        "content": [bullet_content]
                    }
                    current_slide["elements"].append(current_element)
                continue
            
            # Check for numbered list items (same as in parse method)
            numbered_match = re.match(self.patterns['numbered'], line)
            if numbered_match:
                number = numbered_match.group(1)
                numbered_content = numbered_match.group(2).strip()
                
                # Process emphasis in content
                numbered_content = self._process_markdown_emphasis(numbered_content, markdown_patterns)
                
                if current_element and current_element["type"] == "numbered_list":
                    current_element["content"].append(numbered_content)
                else:
                    current_element = {
                        "type": "numbered_list",
                        "content": [numbered_content]
                    }
                    current_slide["elements"].append(current_element)
                continue
            
            # Process emphasis in regular text
            processed_line = self._process_markdown_emphasis(line, markdown_patterns)
            
            # Regular text
            if current_element and current_element["type"] == "text":
                if current_element["content"].endswith(" "):
                    current_element["content"] += processed_line
                else:
                    current_element["content"] += " " + processed_line
            else:
                current_element = {
                    "type": "text",
                    "content": processed_line
                }
                current_slide["elements"].append(current_element)
        
        # Add the last slide if it exists
        if current_slide:
            result["slides"].append(current_slide)
            
        # Post-process slides
        result = self._post_process_slides(result)
            
        return result
    
    def _process_markdown_emphasis(self, text: str, patterns: Dict[str, str]) -> str:
        """Process markdown emphasis (bold, italic) in text.
        
        Args:
            text: Text to process
            patterns: Dictionary of regex patterns
            
        Returns:
            Processed text with emphasis information
        """
        # This is a simplified implementation - in a real application,
        # we might want to preserve formatting information in a more structured way
        # For now, we'll just keep the emphasized text without the markdown markers
        text = re.sub(patterns['md_bold'], r'\1', text)
        text = re.sub(patterns['md_italic'], r'\1', text)
        return text
        
    def detect_format(self, content: str) -> str:
        """Detect the format of the provided content.
        
        Args:
            content: User-provided content
            
        Returns:
            Detected format: 'markdown', 'text', or 'unknown'
        """
        # Look for markdown-specific features
        markdown_indicators = [
            r'^#+\s+',  # Headings
            r'^[-*+]\s+',  # Bullet points
            r'[^\\]\*\*[^*]+\*\*',  # Bold
            r'[^\\]\*[^*]+\*',  # Italic
            r'^```',  # Code blocks
            r'\[.*?\]\(.*?\)'  # Links
        ]
        
        # Count the number of lines with markdown features
        markdown_count = 0
        total_lines = 0
        
        lines = content.split('\n')
        for line in lines:
            if line.strip():
                total_lines += 1
                if any(re.search(pattern, line) for pattern in markdown_indicators):
                    markdown_count += 1
        
        # If more than 15% of non-empty lines have markdown features, classify as markdown
        if total_lines > 0 and (markdown_count / total_lines) > 0.15:
            return 'markdown'
        else:
            return 'text'
            
    def parse_auto(self, content: str) -> Dict[str, Any]:
        """Automatically detect format and parse content accordingly.
        
        Args:
            content: User-provided content
            
        Returns:
            Dictionary with parsed content structure
        """
        format_type = self.detect_format(content)
        
        if format_type == 'markdown':
            return self.parse_markdown(content)
        else:
            return self.parse(content) 