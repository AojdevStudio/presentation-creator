"""
Tests for the prompt templates module.
"""
import pytest
from src.core.prompt_templates import PromptTemplate, SlidePrompts, generate_slide_prompt

def test_prompt_template_format():
    """Test basic prompt template formatting"""
    template = PromptTemplate("Hello {name}!")
    result = template.format(name="World")
    assert result == "Hello World!"

def test_prompt_template_missing_variable():
    """Test prompt template with missing variable"""
    template = PromptTemplate("Hello {name}!")
    with pytest.raises(ValueError):
        template.format()

def test_title_slide_template():
    """Test title slide template formatting"""
    variables = {
        'title': 'Test Presentation',
        'subtitle': 'A Test Subtitle',
        'presenter': 'John Doe',
        'date': '2024-03-31'
    }
    
    prompt = generate_slide_prompt('title', **variables)
    
    assert 'Test Presentation' in prompt
    assert 'A Test Subtitle' in prompt
    assert 'John Doe' in prompt
    assert '2024-03-31' in prompt

def test_content_slide_template():
    """Test content slide template formatting"""
    variables = {
        'title': 'Key Features',
        'key_points': '- Point 1\n- Point 2\n- Point 3',
        'context': 'Additional information about the features'
    }
    
    prompt = generate_slide_prompt('content', **variables)
    
    assert 'Key Features' in prompt
    assert 'Point 1' in prompt
    assert 'Additional information about the features' in prompt

def test_data_visualization_slide_template():
    """Test data visualization slide template formatting"""
    variables = {
        'title': 'Sales Data',
        'data': '[{"month": "Jan", "sales": 100}, {"month": "Feb", "sales": 150}]',
        'chart_type': 'bar'
    }
    
    prompt = generate_slide_prompt('data_viz', **variables)
    
    assert 'Sales Data' in prompt
    assert 'chart_type' in prompt.lower()
    assert 'bar' in prompt

def test_section_transition_template():
    """Test section transition slide template formatting"""
    variables = {
        'current_section': 'Features',
        'next_section': 'Implementation'
    }
    
    prompt = generate_slide_prompt('transition', **variables)
    
    assert 'Features' in prompt
    assert 'Implementation' in prompt

def test_summary_slide_template():
    """Test summary slide template formatting"""
    variables = {
        'main_topics': '- Topic 1\n- Topic 2\n- Topic 3',
        'key_takeaways': '- Takeaway 1\n- Takeaway 2'
    }
    
    prompt = generate_slide_prompt('summary', **variables)
    
    assert 'Topic 1' in prompt
    assert 'Takeaway 1' in prompt

def test_invalid_template_type():
    """Test handling of invalid template type"""
    with pytest.raises(ValueError):
        generate_slide_prompt('invalid_type', title='Test') 