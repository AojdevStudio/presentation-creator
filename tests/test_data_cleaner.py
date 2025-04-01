"""
Tests for data cleaning and transformation utilities.
"""
import pytest
import pandas as pd
import numpy as np
from src.data_processing.data_cleaner import (
    clean_text,
    clean_list,
    format_bullet_points,
    clean_numerical_data,
    extract_key_points,
    format_section_title
)

def test_clean_text():
    """Test text cleaning functionality."""
    # Test basic cleaning
    text = "  This   is  a    test  "
    assert clean_text(text) == "This is a test"
    
    # Test special characters
    text = "Hello! This has (special) characters & symbols..."
    assert clean_text(text) == "Hello! This has special characters symbols"
    
    # Test quote normalization
    text = "This has "quotes" and 'apostrophes'"
    assert clean_text(text) == "This has quotes and apostrophes"
    
    # Test dash normalization
    text = "This is a test--with dashes"
    assert clean_text(text) == "This is a test—with dashes"

def test_clean_list():
    """Test list cleaning functionality."""
    items = [
        "  Item 1  ",
        "",  # Empty item
        "Item (2)",
        "  ",  # Whitespace only
        "Item 3!"
    ]
    
    expected = [
        "Item 1",
        "Item 2",
        "Item 3!"
    ]
    
    assert clean_list(items) == expected

def test_format_bullet_points():
    """Test bullet point formatting."""
    points = [
        "This is a short point",
        "This is a very long point that should be split into multiple lines because it exceeds the maximum length",
        "Another short point"
    ]
    
    formatted = format_bullet_points(points, max_length=30)
    
    assert len(formatted) > len(points)  # Long point should be split
    assert all(len(point) <= 30 for point in formatted)
    assert formatted[0] == "This is a short point"
    assert "This is a very long point" in formatted[1]
    assert formatted[-1] == "Another short point"

def test_clean_numerical_data():
    """Test numerical data cleaning."""
    # Test with dictionary input
    data = {
        "A": [1.0, 2.0, np.nan, 4.0],
        "B": [10.0, np.nan, 30.0, 40.0]
    }
    
    result = clean_numerical_data(data)
    
    assert "data" in result
    assert "metadata" in result
    assert len(result["data"]["A"]) == 4  # No rows should be dropped
    assert not any(pd.isna(x) for x in result["data"]["A"])  # No NaN values
    
    # Test with DataFrame input
    df = pd.DataFrame({
        "X": [1.234, 2.345, 3.456],
        "Y": [10.123, 20.234, 30.345]
    })
    
    result = clean_numerical_data(df)
    
    assert all(isinstance(x, float) for x in result["data"]["X"])
    assert all(round(x, 2) == x for x in result["data"]["X"])  # Values should be rounded
    assert "summary_stats" in result["metadata"]

def test_extract_key_points():
    """Test key point extraction."""
    text = """
    This is the main point of the text. Some additional context here.
    Another important point about the topic. This is just filler text.
    The third significant point is crucial. Finally, a conclusion.
    """
    
    points = extract_key_points(text, max_points=3)
    
    assert len(points) <= 3
    assert any("main point" in p.lower() for p in points)
    assert any("important" in p.lower() for p in points)
    assert any("significant" in p.lower() for p in points)

def test_format_section_title():
    """Test section title formatting."""
    # Test basic capitalization
    title = "this is a test title"
    assert format_section_title(title) == "This Is a Test Title"
    
    # Test with special characters
    title = "section 1: the main (topic)"
    assert format_section_title(title) == "Section 1 the Main Topic"
    
    # Test with already capitalized words
    title = "THIS IS ALL CAPS"
    assert format_section_title(title) == "This Is All Caps"
    
    # Test with prepositions and articles
    title = "the impact of artificial intelligence on society"
    assert format_section_title(title) == "The Impact of Artificial Intelligence on Society" 