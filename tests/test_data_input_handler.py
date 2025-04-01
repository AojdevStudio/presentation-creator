"""
Tests for data input handlers.
"""
import pytest
import json
import csv
from pathlib import Path
from src.core.data_input_handler import (
    DataInputHandler,
    TextInputHandler,
    CSVInputHandler,
    JSONInputHandler,
    create_input_handler
)

@pytest.fixture
def temp_text_file(tmp_path):
    """Create a temporary text file for testing."""
    content = """Sample Presentation
    
This is the first section.
It has multiple lines.

This is the second section.
Another multi-line section.
"""
    file_path = tmp_path / "test.txt"
    file_path.write_text(content)
    return file_path

@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing."""
    content = [
        ["Name", "Age", "City"],
        ["John", "30", "New York"],
        ["Alice", "25", "London"],
        ["Bob", "35", "Paris"]
    ]
    file_path = tmp_path / "test.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(content)
    return file_path

@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    data = {
        "title": "Sample Presentation",
        "sections": [
            {
                "title": "Introduction",
                "content": ["Point 1", "Point 2"]
            },
            {
                "title": "Main Content",
                "content": ["Point 3", "Point 4"]
            }
        ]
    }
    file_path = tmp_path / "test.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def test_base_handler_init():
    """Test base handler initialization with invalid path."""
    with pytest.raises(FileNotFoundError):
        DataInputHandler("nonexistent.txt")

def test_base_handler_read():
    """Test base handler read method raises NotImplementedError."""
    class TestHandler(DataInputHandler):
        pass
        
    with pytest.raises(NotImplementedError):
        handler = TestHandler(__file__)
        handler.read()

def test_text_handler(temp_text_file):
    """Test text file handler."""
    handler = TextInputHandler(temp_text_file)
    result = handler.read()
    
    assert result["type"] == "text"
    assert result["title"] == "Sample Presentation"
    assert len(result["sections"]) == 2
    assert "This is the first section" in result["sections"][0]
    assert "This is the second section" in result["sections"][1]
    assert result["metadata"]["line_count"] > 0
    assert result["metadata"]["section_count"] == 3  # Title + 2 content sections

def test_csv_handler(temp_csv_file):
    """Test CSV file handler."""
    handler = CSVInputHandler(temp_csv_file)
    result = handler.read()
    
    assert result["type"] == "csv"
    assert result["headers"] == ["Name", "Age", "City"]
    assert len(result["rows"]) == 3
    assert result["rows"][0] == ["John", "30", "New York"]
    assert result["metadata"]["row_count"] == 3
    assert result["metadata"]["column_count"] == 3

def test_json_handler(temp_json_file):
    """Test JSON file handler."""
    handler = JSONInputHandler(temp_json_file)
    result = handler.read()
    
    assert result["type"] == "json"
    assert result["data"]["title"] == "Sample Presentation"
    assert len(result["data"]["sections"]) == 2
    assert result["metadata"]["is_array"] is False
    assert "title" in result["metadata"]["top_level_keys"]
    assert result["metadata"]["array_length"] is None

def test_create_input_handler(temp_text_file, temp_csv_file, temp_json_file):
    """Test input handler factory function."""
    # Test text handler creation
    handler = create_input_handler(temp_text_file)
    assert isinstance(handler, TextInputHandler)
    
    # Test CSV handler creation
    handler = create_input_handler(temp_csv_file)
    assert isinstance(handler, CSVInputHandler)
    
    # Test JSON handler creation
    handler = create_input_handler(temp_json_file)
    assert isinstance(handler, JSONInputHandler)
    
    # Test invalid extension
    with pytest.raises(ValueError):
        create_input_handler("invalid.xyz")

def test_invalid_file_extensions():
    """Test handling of invalid file extensions."""
    # Test text handler with invalid extension
    with pytest.raises(ValueError):
        handler = TextInputHandler(__file__)  # Using the test file itself
        handler.read()
        
    # Test CSV handler with invalid extension
    with pytest.raises(ValueError):
        handler = CSVInputHandler(__file__)
        handler.read()
        
    # Test JSON handler with invalid extension
    with pytest.raises(ValueError):
        handler = JSONInputHandler(__file__)
        handler.read()

def test_malformed_files(tmp_path):
    """Test handling of malformed files."""
    # Test malformed JSON
    json_file = tmp_path / "malformed.json"
    json_file.write_text("{invalid json")
    with pytest.raises(Exception):
        handler = JSONInputHandler(json_file)
        handler.read()
        
    # Test malformed CSV
    csv_file = tmp_path / "malformed.csv"
    csv_file.write_text("header1,header2\ninvalid,too,many,columns")
    handler = CSVInputHandler(csv_file)
    result = handler.read()
    assert len(result["headers"]) == 2  # Should still get headers
    
    # Test empty files
    for ext in [".txt", ".csv", ".json"]:
        empty_file = tmp_path / f"empty{ext}"
        empty_file.touch()
        handler = create_input_handler(empty_file)
        with pytest.raises(Exception):
            handler.read() 