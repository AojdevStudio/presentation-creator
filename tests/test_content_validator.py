"""
Tests for the Content Validation System.

This module tests the functionality of the ContentValidator class,
including text extraction, spelling/grammar checking, consistency checks,
and report generation.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

from src.qa.content_validator import (
    ContentValidator, 
    ValidationIssue, 
    ValidationSeverity,
    validate_content
)

@pytest.fixture
def sample_presentation() -> Dict[str, Any]:
    """Create a sample presentation for testing validation."""
    return {
        "title": "Sample Presentation",
        "author": "Test User",
        "created_at": "2025-04-01T12:00:00Z",
        "slides": [
            {
                "title": "Introduction",
                "elements": [
                    {
                        "type": "text",
                        "content": "This is a sample presentation for testing the content validator.",
                        "style": {"fontSize": 16, "color": "#000000"}
                    },
                    {
                        "type": "bullet_list",
                        "content": [
                            "First point with a misspelled woord",
                            "Second point with duplicate duplicate word",
                            "Third point with proper grammar"
                        ],
                        "style": {"fontSize": 14, "color": "#000000"}
                    }
                ]
            },
            {
                "title": "key concepts",  # Inconsistent capitalization
                "elements": [
                    {
                        "type": "text",
                        "content": "Here we introduce some key concepts.",
                        "style": {"fontSize": 16, "color": "#000000"}
                    },
                    {
                        "type": "bullet_list",
                        "content": [
                            "The Key Concepts are important",  # Inconsistent term (key concepts vs Key Concepts)
                            "Understanding the key-concepts is essential",  # Inconsistent hyphenation
                            "Let's apply these key-concepts in practice"
                        ],
                        "style": {"fontSize": 14, "color": "#000000"}
                    }
                ]
            }
        ]
    }

@pytest.fixture
def custom_dictionary_path(tmp_path) -> Path:
    """Create a temporary custom dictionary file."""
    dict_path = tmp_path / "custom_dict.txt"
    with open(dict_path, 'w') as f:
        f.write("woord\n")  # Add the misspelled word to dictionary so it won't be flagged
        f.write("keyconceptsuniquename\n")
    
    return dict_path

def test_validation_issue_creation():
    """Test creating a ValidationIssue."""
    issue = ValidationIssue(
        issue_type="spelling",
        message="Misspelled word",
        location={"slide": 0, "element_id": 1},
        severity=ValidationSeverity.WARNING,
        suggestions=["correction"]
    )
    
    assert issue.issue_type == "spelling"
    assert issue.message == "Misspelled word"
    assert issue.location == {"slide": 0, "element_id": 1}
    assert issue.severity == ValidationSeverity.WARNING
    assert issue.suggestions == ["correction"]

def test_validation_issue_to_dict():
    """Test converting ValidationIssue to dictionary."""
    issue = ValidationIssue(
        issue_type="spelling",
        message="Misspelled word",
        location={"slide": 0, "element_id": 1},
        severity=ValidationSeverity.WARNING,
        suggestions=["correction"]
    )
    
    issue_dict = issue.to_dict()
    assert issue_dict["type"] == "spelling"
    assert issue_dict["message"] == "Misspelled word"
    assert issue_dict["location"] == {"slide": 0, "element_id": 1}
    assert issue_dict["severity"] == "WARNING"
    assert issue_dict["suggestions"] == ["correction"]

def test_content_validator_initialization():
    """Test initializing the ContentValidator."""
    validator = ContentValidator()
    assert validator.language == "en-US"
    assert isinstance(validator.custom_words, set)
    assert len(validator.custom_words) == 0

def test_content_validator_with_custom_dictionary(custom_dictionary_path):
    """Test initializing the ContentValidator with a custom dictionary."""
    validator = ContentValidator(custom_dictionary=custom_dictionary_path)
    assert "woord" in validator.custom_words
    assert "keyconceptsuniquename" in validator.custom_words

def test_extract_text_from_presentation(sample_presentation):
    """Test extracting text from a presentation."""
    validator = ContentValidator()
    extracted_text = validator.extract_text_from_presentation(sample_presentation)
    
    # Check that we have text from both slides
    assert 0 in extracted_text and 1 in extracted_text
    
    # Check slide titles are extracted
    assert any(element["element_type"] == "title" and element["text"] == "Introduction" 
               for element in extracted_text[0])
    assert any(element["element_type"] == "title" and element["text"] == "key concepts" 
               for element in extracted_text[1])
    
    # Check bullet points are extracted
    bullet_texts = []
    for slide_idx, elements in extracted_text.items():
        for element in elements:
            if "bullet_list" in element["element_type"]:
                bullet_texts.append(element["text"])
    
    assert "First point with a misspelled woord" in bullet_texts
    assert "Second point with duplicate duplicate word" in bullet_texts

def test_check_spelling_and_grammar():
    """Test checking spelling and grammar."""
    validator = ContentValidator()
    issues = validator.check_spelling_and_grammar(
        "This sentence has a misspeled word.",
        {"slide": 0, "element_type": "text", "element_id": 0}
    )
    
    # We should find at least one issue (the misspelled word)
    assert len(issues) > 0
    # At least one should be a spelling issue
    assert any(issue.issue_type == "spelling" for issue in issues)

def test_check_spelling_with_custom_dictionary(custom_dictionary_path):
    """Test that custom dictionary words are not flagged."""
    validator = ContentValidator(custom_dictionary=custom_dictionary_path)
    issues = validator.check_spelling_and_grammar(
        "This word 'woord' should not be flagged.",
        {"slide": 0, "element_type": "text", "element_id": 0}
    )
    
    # No issues should be found for "woord" since it's in the custom dictionary
    assert not any(issue.issue_type == "spelling" and "woord" in issue.message.lower() 
                   for issue in issues)

def test_check_consistency(sample_presentation):
    """Test checking terminology consistency."""
    print("\nSample presentation structure:")
    print(json.dumps(sample_presentation, indent=2))
    
    validator = ContentValidator()
    extracted_text = validator.extract_text_from_presentation(sample_presentation)
    print("\nExtracted text structure:")
    print(json.dumps(extracted_text, default=lambda x: str(x), indent=2))
    
    issues = validator.check_consistency(extracted_text)
    
    # Print issues for debugging
    print("\nIssues found in test:", [str(issue) for issue in issues])
    
    # Check that term variations are detected
    assert any("key concepts" in issue.message.lower() or "key-concepts" in issue.message.lower() 
               for issue in issues)

def test_check_capitalization(sample_presentation):
    """Test checking capitalization consistency."""
    validator = ContentValidator()
    extracted_text = validator.extract_text_from_presentation(sample_presentation)
    issues = validator.check_capitalization(extracted_text)
    
    # Check that capitalization inconsistencies are detected
    assert any("capitalization" in issue.message.lower() and "key concepts" in issue.message.lower() 
               for issue in issues)

def test_validate_presentation(sample_presentation):
    """Test validating an entire presentation."""
    validator = ContentValidator()
    issues = validator.validate_presentation(sample_presentation)
    
    # Should find multiple issues in our sample presentation
    assert len(issues) > 0
    
    # Issues should include spelling, consistency, and capitalization
    issue_types = {issue.issue_type for issue in issues}
    assert len(issue_types) >= 2  # At least 2 different types of issues
    
    # Check some specific issues
    assert any("duplicate" in issue.message.lower() for issue in issues)
    assert any("key concept" in issue.message.lower() for issue in issues)

def test_generate_validation_report_text(sample_presentation):
    """Test generating a text validation report."""
    validator = ContentValidator()
    issues = validator.validate_presentation(sample_presentation)
    report = validator.generate_validation_report(issues, output_format="text")
    
    # Report should contain issue information
    assert "Content Validation Report" in report
    assert "Found" in report and "issues in total" in report
    assert "WARNING" in report or "ERROR" in report or "INFO" in report

def test_generate_validation_report_json(sample_presentation):
    """Test generating a JSON validation report."""
    validator = ContentValidator()
    issues = validator.validate_presentation(sample_presentation)
    report = validator.generate_validation_report(issues, output_format="json")
    
    # Report should be a dictionary
    assert isinstance(report, dict)
    assert "status" in report
    assert "issue_count" in report
    assert "issues_by_severity" in report
    
    # Try converting to actual JSON
    json_str = json.dumps(report)
    assert isinstance(json_str, str)

def test_generate_validation_report_html(sample_presentation):
    """Test generating an HTML validation report."""
    validator = ContentValidator()
    issues = validator.validate_presentation(sample_presentation)
    report = validator.generate_validation_report(issues, output_format="html")
    
    # Report should be HTML
    assert "<h1>Content Validation Report</h1>" in report
    assert "<ul>" in report
    assert "<li>" in report
    assert "</ul>" in report

def test_validate_content_helper_function(sample_presentation):
    """Test the helper function for validating content."""
    # Test text format
    text_report = validate_content(sample_presentation)
    assert isinstance(text_report, str)
    assert "Content Validation Report" in text_report
    
    # Test JSON format
    json_report = validate_content(sample_presentation, output_format="json")
    assert isinstance(json_report, dict)
    assert "status" in json_report
    
    # Test HTML format
    html_report = validate_content(sample_presentation, output_format="html")
    assert isinstance(html_report, str)
    assert "<h1>Content Validation Report</h1>" in html_report

def test_empty_presentation():
    """Test validating an empty presentation."""
    empty_presentation = {"slides": []}
    validator = ContentValidator()
    issues = validator.validate_presentation(empty_presentation)
    
    # Should have no issues
    assert len(issues) == 0
    
    # Report should indicate success
    report = validator.generate_validation_report(issues)
    assert "No issues found" in report 