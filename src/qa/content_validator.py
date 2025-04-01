"""
Content Validation System for Presentations.

This module provides functionality to validate presentation content,
including spelling, grammar, and consistency checks across slides.
"""

import re
import logging
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from pathlib import Path
import json

# Setup logging
logger = logging.getLogger(__name__)

def load_word_list(filename: str = None) -> Set[str]:
    """Load a list of words from a file or use a default word list."""
    logger.info(f"Loading word list from: {filename if filename else 'default list'}")
    if filename and Path(filename).exists():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return set(word.strip().lower() for word in f if word.strip())
        except Exception as e:
            logger.error(f"Failed to load word list from {filename}: {e}")
            # Fall back to default word list
    
    # Fallback to a very small set of common words if no file is provided or file loading fails
    logger.info("Using default word list for basic spell checking")
    return {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it',
        'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
        'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or',
        'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
        'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me'
    }

# Try to import language-check if available, otherwise use a simple spelling checker
LANGUAGE_TOOL_AVAILABLE = True
_language_tool_instance = None
try:
    import language_tool_python
except ImportError:
    LANGUAGE_TOOL_AVAILABLE = False
    logger.warning("language_tool_python not found. Grammar/style checking will be disabled.")
except Exception as e:
    LANGUAGE_TOOL_AVAILABLE = False
    logger.error(f"Error initializing language_tool_python: {e}", exc_info=True)

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class ValidationIssue:
    """Represents a validation issue found in the content."""
    
    def __init__(
        self, 
        issue_type: str, 
        message: str, 
        location: Dict[str, Any],
        severity: ValidationSeverity = ValidationSeverity.WARNING,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize a validation issue.
        
        Args:
            issue_type: Type of the issue (e.g., 'spelling', 'grammar', 'consistency')
            message: Description of the issue
            location: Location of the issue (e.g., {slide: 1, element: 'title'})
            severity: Severity level of the issue
            suggestions: Optional list of suggested corrections
        """
        self.issue_type = issue_type
        self.message = message
        self.location = location
        self.severity = severity
        self.suggestions = suggestions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to a dictionary representation."""
        return {
            'type': self.issue_type,
            'message': self.message,
            'location': self.location,
            'severity': self.severity.name,
            'suggestions': self.suggestions
        }
    
    def __str__(self) -> str:
        """Get string representation of the issue."""
        loc_str = ", ".join(f"{k}: {v}" for k, v in self.location.items())
        sugg_str = f" Suggestions: {', '.join(self.suggestions)}" if self.suggestions else ""
        return f"[{self.severity.name}] {self.issue_type}: {self.message} at {loc_str}.{sugg_str}"

class ContentValidator:
    """
    Validates presentation content for quality issues.
    
    Supports:
    - Spelling and grammar checks
    - Terminology consistency
    - Capitalization patterns
    - Formatting consistency
    """
    
    def __init__(self, language: str = 'en-US', custom_dictionary: Optional[str] = None):
        """
        Initialize a content validator.
        
        Args:
            language: Language code to use for validation 
            custom_dictionary: Path to a custom dictionary file
        """
        # Declare intent to use the global variable before any reference or assignment
        global LANGUAGE_TOOL_AVAILABLE
        global _language_tool_instance
        
        self.language = language
        self.custom_words = set()
        self.lang_tool = None
        self.perform_grammar_check = LANGUAGE_TOOL_AVAILABLE
        
        if custom_dictionary:
            try:
                with open(custom_dictionary, 'r', encoding='utf-8') as f:
                    self.custom_words = {word.strip().lower() for word in f if word.strip()}
            except Exception as e:
                logger.warning(f"Failed to load custom dictionary: {e}")
        
        # Initialize the language tool if available
        if self.perform_grammar_check:
            try:
                if _language_tool_instance is None:
                    _language_tool_instance = language_tool_python.LanguageTool(language)
                self.lang_tool = _language_tool_instance
                
                # Add custom words to the language tool
                for word in self.custom_words:
                    self.lang_tool.add_to_dictionary(word)
                    
                logger.info("LanguageTool initialized successfully for ContentValidator.")
            except Exception as e:
                logger.error(f"Error initializing LanguageTool: {e}")
                self.lang_tool = None
                self.perform_grammar_check = False
                LANGUAGE_TOOL_AVAILABLE = False  # Update global flag if initialization fails
        else:
            logger.warning("Grammar check requested but LanguageTool is not available.")
        
        # Fallback to word list if LanguageTool isn't available
        if not self.perform_grammar_check:
            self.word_list = load_word_list()
            self.word_list.update(self.custom_words)
    
    def extract_text_from_presentation(self, presentation: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all text content from a presentation.
        
        Args:
            presentation: The presentation data structure
            
        Returns:
            Dictionary mapping slide indices to lists of text elements
        """
        extracted_text = {}
        
        for slide_idx, slide in enumerate(presentation.get('slides', [])):
            texts = []
            
            # Extract from slide title
            if 'title' in slide:
                texts.append({
                    'text': slide['title'],
                    'element_type': 'title',
                    'element_id': 'title'
                })
            
            # Extract from slide content elements
            for elem_id, element in enumerate(slide.get('elements', [])):
                # Skip non-text elements
                if element.get('type') not in ['text', 'title', 'subtitle', 'bullet_list', 'paragraph']:
                    continue
                
                if isinstance(element.get('content'), str):
                    texts.append({
                        'text': element['content'],
                        'element_type': element.get('type'),
                        'element_id': elem_id
                    })
                elif isinstance(element.get('content'), list):
                    # For bullet lists or other list-type content
                    for item_idx, item in enumerate(element['content']):
                        if isinstance(item, str):
                            texts.append({
                                'text': item,
                                'element_type': element.get('type'),
                                'element_id': f"{elem_id}_{item_idx}"
                            })
                        elif isinstance(item, dict) and 'text' in item:
                            texts.append({
                                'text': item['text'],
                                'element_type': element.get('type'),
                                'element_id': f"{elem_id}_{item_idx}"
                            })
            
            extracted_text[slide_idx] = texts
        
        return extracted_text

    def check_spelling_and_grammar(self, text: str, location: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Check text for spelling and grammar issues.
        
        Args:
            text: Text to validate
            location: Location information for the text
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        if not text or not text.strip():
            return issues
        
        if self.perform_grammar_check and self.lang_tool:
            # Use LanguageTool for comprehensive checking
            try:
                matches = self.lang_tool.check(text)
                
                for match in matches:
                    # Skip spelling issues for words in custom dictionary
                    if match.ruleId.startswith('MORFOLOGIK_RULE') and match.matchedText.lower() in self.custom_words:
                        continue
                    
                    issue_type = 'grammar' if match.ruleId.startswith('GRAMMAR') else 'spelling'
                    
                    issues.append(ValidationIssue(
                        issue_type=issue_type,
                        message=match.message,
                        location={**location, 'offset': match.offset, 'length': match.errorLength},
                        severity=ValidationSeverity.WARNING,
                        suggestions=match.replacements[:5]  # Limit to top 5 suggestions
                    ))
            except Exception as e:
                logger.error(f"Error during LanguageTool check: {e}", exc_info=True)
                # Don't disable future checks just because one check failed
        else:
            # Use simple word list for basic spell checking
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            for word in words:
                if len(word) > 2 and word not in self.word_list and word not in self.custom_words:
                    issues.append(ValidationIssue(
                        issue_type='spelling',
                        message=f"Potential spelling error: '{word}'",
                        location=location,
                        severity=ValidationSeverity.INFO
                    ))
        
        return issues

    def check_consistency(self, presentation_text: Dict[str, List[Dict[str, Any]]]) -> List[ValidationIssue]:
        """
        Check for terminology and capitalization consistency across slides.
        
        Args:
            presentation_text: Dictionary of extracted text elements
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Track term variations
        term_variations = {}
        multi_word_variations = {}
        
        # First pass: collect all terms and their variations
        for slide_idx, elements in presentation_text.items():
            for element in elements:
                text = element['text']
                
                # Extract single words and hyphenated terms
                words = re.findall(r'\b[a-zA-Z][a-zA-Z\-]+\b', text)
                
                # Extract multi-word terms (2-3 words) and hyphenated versions of the same concepts
                multi_words = re.findall(r'\b[a-zA-Z][a-zA-Z\-]+(?:\s+|\-)[a-zA-Z][a-zA-Z\-]+(?:(?:\s+|\-)[a-zA-Z][a-zA-Z\-]+)?\b', text)
                
                # Process single words
                for word in words:
                    key = word.lower()
                    if key not in term_variations:
                        term_variations[key] = {}
                    
                    if word not in term_variations[key]:
                        term_variations[key][word] = []
                    
                    term_variations[key][word].append({
                        'slide': slide_idx,
                        'element_type': element['element_type'],
                        'element_id': element['element_id']
                    })
                
                # Process multi-word terms
                for phrase in multi_words:
                    # Create a normalized key (lowercase, no hyphens)
                    normalized_key = phrase.lower().replace('-', ' ')
                    
                    if normalized_key not in multi_word_variations:
                        multi_word_variations[normalized_key] = {}
                    
                    if phrase not in multi_word_variations[normalized_key]:
                        multi_word_variations[normalized_key][phrase] = []
                    
                    multi_word_variations[normalized_key][phrase].append({
                        'slide': slide_idx,
                        'element_type': element['element_type'],
                        'element_id': element['element_id']
                    })
        
        # Second pass: find inconsistencies in single words
        for term, variations in term_variations.items():
            if len(variations) > 1:
                # Found multiple variations of the same term
                dominant_form = max(variations.items(), key=lambda x: len(x[1]))[0]
                
                for variation, locations in variations.items():
                    if variation != dominant_form:
                        for location in locations:
                            issues.append(ValidationIssue(
                                issue_type='terminology_consistency',
                                message=f"Inconsistent term usage: '{variation}' vs dominant form '{dominant_form}'",
                                location=location,
                                severity=ValidationSeverity.WARNING,
                                suggestions=[dominant_form]
                            ))
        
        # Third pass: find inconsistencies in multi-word terms
        for normalized_term, variations in multi_word_variations.items():
            if len(variations) > 1:
                # Found multiple variations of the same multi-word term
                dominant_form = max(variations.items(), key=lambda x: len(x[1]))[0]
                
                for variation, locations in variations.items():
                    if variation != dominant_form:
                        for location in locations:
                            issues.append(ValidationIssue(
                                issue_type='terminology_consistency',
                                message=f"Inconsistent multi-word term usage: '{variation}' vs '{dominant_form}' for the concept '{normalized_term}'",
                                location=location,
                                severity=ValidationSeverity.WARNING,
                                suggestions=[dominant_form]
                            ))
        
        # Special handling for hyphenated variations vs space-separated variations
        # This ensures we catch things like "key concepts" vs "key-concepts"
        for normalized_term, variations in multi_word_variations.items():
            # If the normalized term has a space, check if there's a hyphenated version
            if ' ' in normalized_term:
                hyphenated_term = normalized_term.replace(' ', '-')
                
                # Find all phrases that match either version
                spaced_phrases = []
                hyphenated_phrases = []
                
                for variation in variations.keys():
                    if ' ' in variation:
                        spaced_phrases.append(variation)
                    elif '-' in variation:
                        hyphenated_phrases.append(variation)
                
                # If we found both versions, report this as an inconsistency
                if spaced_phrases and hyphenated_phrases:
                    for spaced_phrase in spaced_phrases:
                        for location in variations[spaced_phrase]:
                            issues.append(ValidationIssue(
                                issue_type='terminology_consistency',
                                message=f"Inconsistent use of spaces vs hyphens: '{spaced_phrase}' (with spaces) vs '{hyphenated_phrases[0]}' (with hyphens)",
                                location=location,
                                severity=ValidationSeverity.WARNING,
                                suggestions=[spaced_phrase, hyphenated_phrases[0]]
                            ))
        
        return issues

    def check_capitalization(self, presentation_text: Dict[str, List[Dict[str, Any]]]) -> List[ValidationIssue]:
        """
        Check for consistent capitalization in titles and headings.
        
        Args:
            presentation_text: Dictionary of extracted text elements
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        title_case_pattern = re.compile(r'^([A-Z][a-z]*\s)*[A-Z][a-z]*$')
        sentence_case_pattern = re.compile(r'^[A-Z][a-z\s]*')
        
        # Track capitalization styles in titles
        title_capitalization = {
            'title_case': 0,
            'sentence_case': 0
        }
        
        # First pass: determine dominant capitalization style for titles
        for slide_idx, elements in presentation_text.items():
            for element in elements:
                if element['element_type'] in ['title', 'subtitle']:
                    text = element['text']
                    
                    if title_case_pattern.match(text):
                        title_capitalization['title_case'] += 1
                    elif sentence_case_pattern.match(text):
                        title_capitalization['sentence_case'] += 1
        
        # Determine dominant style
        dominant_style = max(title_capitalization.items(), key=lambda x: x[1])[0]
        
        # Second pass: check for inconsistencies
        for slide_idx, elements in presentation_text.items():
            for element in elements:
                if element['element_type'] in ['title', 'subtitle']:
                    text = element['text']
                    
                    if dominant_style == 'title_case' and not title_case_pattern.match(text):
                        # Should be title case but isn't
                        issues.append(ValidationIssue(
                            issue_type='capitalization_consistency',
                            message=f"Inconsistent capitalization: Expected title case for '{text}'",
                            location={
                                'slide': slide_idx,
                                'element_type': element['element_type'],
                                'element_id': element['element_id']
                            },
                            severity=ValidationSeverity.INFO,
                            suggestions=[' '.join(word.capitalize() for word in text.split())]
                        ))
                    elif dominant_style == 'sentence_case' and not sentence_case_pattern.match(text):
                        # Should be sentence case but isn't
                        suggestion = text[0].upper() + text[1:].lower() if text else ""
                        issues.append(ValidationIssue(
                            issue_type='capitalization_consistency',
                            message=f"Inconsistent capitalization: Expected sentence case for '{text}'",
                            location={
                                'slide': slide_idx,
                                'element_type': element['element_type'],
                                'element_id': element['element_id']
                            },
                            severity=ValidationSeverity.INFO,
                            suggestions=[suggestion]
                        ))
        
        return issues

    def validate_presentation(self, presentation: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Perform full validation on a presentation.
        
        Args:
            presentation: The presentation data structure
            
        Returns:
            List of all validation issues found
        """
        issues = []
        
        # Extract text from presentation
        presentation_text = self.extract_text_from_presentation(presentation)
        
        # Validate each text element
        for slide_idx, elements in presentation_text.items():
            for element in elements:
                text = element['text']
                location = {
                    'slide': slide_idx,
                    'element_type': element['element_type'],
                    'element_id': element['element_id']
                }
                
                # Check spelling and grammar
                issues.extend(self.check_spelling_and_grammar(text, location))
        
        # Check for consistency across the presentation
        issues.extend(self.check_consistency(presentation_text))
        issues.extend(self.check_capitalization(presentation_text))
        
        return issues

    def generate_validation_report(self, issues: List[ValidationIssue], output_format: str = 'text') -> Union[str, Dict]:
        """
        Generate a report from validation issues.
        
        Args:
            issues: List of validation issues
            output_format: Format of the report ('text', 'json', or 'html')
            
        Returns:
            Report in the specified format
        """
        if not issues:
            if output_format == 'json':
                return {'status': 'success', 'issues': []}
            elif output_format == 'html':
                return "<h1>Content Validation Report</h1><p>No issues found. Content is valid.</p>"
            else:
                return "Content Validation Report\n=========================\nNo issues found. Content is valid."
        
        # Group issues by severity
        issues_by_severity = {}
        for severity in ValidationSeverity:
            issues_by_severity[severity] = [issue for issue in issues if issue.severity == severity]
        
        # Generate report in the requested format
        if output_format == 'json':
            return {
                'status': 'issues_found',
                'issue_count': len(issues),
                'issues_by_severity': {
                    severity.name: [issue.to_dict() for issue in issues_by_severity[severity]]
                    for severity in ValidationSeverity
                }
            }
        
        elif output_format == 'html':
            html = ["<h1>Content Validation Report</h1>"]
            html.append(f"<p>Found {len(issues)} issues in total.</p>")
            
            for severity in ValidationSeverity:
                if issues_by_severity[severity]:
                    html.append(f"<h2>{severity.name} Issues ({len(issues_by_severity[severity])})</h2>")
                    html.append("<ul>")
                    for issue in issues_by_severity[severity]:
                        html.append(f"<li><strong>{issue.issue_type}:</strong> {issue.message} ")
                        loc_str = ", ".join(f"{k}: {v}" for k, v in issue.location.items())
                        html.append(f"at {loc_str}. ")
                        if issue.suggestions:
                            html.append(f"Suggestions: {', '.join(issue.suggestions)}")
                        html.append("</li>")
                    html.append("</ul>")
            
            return "".join(html)
        
        else:  # text format
            report = ["Content Validation Report", "========================="]
            report.append(f"Found {len(issues)} issues in total.\n")
            
            for severity in ValidationSeverity:
                if issues_by_severity[severity]:
                    report.append(f"{severity.name} Issues ({len(issues_by_severity[severity])}):")
                    report.append("-" * (len(severity.name) + 9))
                    for issue in issues_by_severity[severity]:
                        report.append(f"- {issue}")
                    report.append("")
            
            return "\n".join(report)

def validate_content(presentation: Dict[str, Any], language: str = 'en-US', 
                    custom_dictionary: Optional[str] = None, output_format: str = 'text') -> Union[str, Dict]:
    """
    Validate the content of a presentation.
    
    Args:
        presentation: The presentation data structure
        language: Language code to use for validation
        custom_dictionary: Path to a custom dictionary file
        output_format: Format of the report ('text', 'json', or 'html')
        
    Returns:
        Validation report in the specified format
    """
    validator = ContentValidator(language, custom_dictionary)
    issues = validator.validate_presentation(presentation)
    return validator.generate_validation_report(issues, output_format)

def cli_validate_content(presentation_file: str, output: Optional[str] = None, format: str = 'text', 
                     custom_dict: Optional[str] = None) -> None:
    """
    CLI function to validate presentation content.
    
    Args:
        presentation_file: Path to the presentation JSON file
        output: Optional path to write the report to
        format: Output format (text, json, html)
        custom_dict: Optional path to a custom dictionary file
    """
    try:
        # Load presentation data
        with open(presentation_file, 'r', encoding='utf-8') as f:
            try:
                presentation_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from {presentation_file}")
                return
        
        # Create validator
        validator = ContentValidator(custom_dictionary=custom_dict)
        
        # Run validation
        issues = validator.validate_presentation(presentation_data)
        
        # Generate report
        report = validator.generate_validation_report(issues, output_format=format)
        
        # Output or save the report
        if output:
            # If report is a dictionary, convert to string
            if isinstance(report, dict):
                report = json.dumps(report, indent=2)
                
            with open(output, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Validation report written to {output}")
        else:
            # Print to console
            if isinstance(report, dict):
                print(json.dumps(report, indent=2))
            else:
                print(report)
    
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate presentation content")
    parser.add_argument("presentation_file", help="Path to the presentation JSON file")
    parser.add_argument("--output", "-o", help="Path to write the report to")
    parser.add_argument("--format", "-f", choices=['text', 'json', 'html'], default='text',
                        help="Output format (text, json, html)")
    parser.add_argument("--custom-dict", "-d", help="Path to a custom dictionary file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging based on verbose flag
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    cli_validate_content(
        args.presentation_file,
        output=args.output,
        format=args.format,
        custom_dict=args.custom_dict
    ) 