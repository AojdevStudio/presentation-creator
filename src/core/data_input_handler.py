"""
Data input handlers for various file formats.
"""
import logging
import json
import csv
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataInputHandler:
    """Base class for handling data input from various file formats"""
    
    def __init__(self, input_path: Union[str, Path]):
        """Initialize the data input handler.
        
        Args:
            input_path: Path to the input file
        """
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
    def _validate_file_extension(self, expected_extensions: List[str]) -> None:
        """Validate that the file has the expected extension.
        
        Args:
            expected_extensions: List of valid file extensions (e.g., ['.txt', '.text'])
            
        Raises:
            ValueError: If file extension is not in expected_extensions
        """
        if self.input_path.suffix.lower() not in expected_extensions:
            raise ValueError(
                f"Invalid file extension. Expected one of {expected_extensions}, "
                f"got {self.input_path.suffix}"
            )
            
    def read(self) -> Dict[str, Any]:
        """Read and parse the input file.
        
        Returns:
            Dictionary containing the parsed data
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement read()")

class TextInputHandler(DataInputHandler):
    """Handler for text file input"""
    
    def read(self) -> Dict[str, Any]:
        """Read and parse a text file.
        
        Returns:
            Dictionary containing the parsed text data with sections
        """
        self._validate_file_extension(['.txt', '.text'])
        
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # First get all lines, removing empty ones
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            if not lines:
                raise ValueError("Empty text file")
                
            # First line is always the title
            title = lines[0]
            
            # Rest of the content is split into sections by double newlines
            remaining_content = '\n'.join(lines[1:])
            sections = [s.strip() for s in remaining_content.split('\n\n') if s.strip()]
            
            return {
                "type": "text",
                "title": title,
                "sections": sections,
                "metadata": {
                    "file_size": self.input_path.stat().st_size,
                    "line_count": len(lines),
                    "section_count": len(sections)
                }
            }
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            raise

class CSVInputHandler(DataInputHandler):
    """Handler for CSV file input"""
    
    def read(self) -> Dict[str, Any]:
        """Read and parse a CSV file.
        
        Returns:
            Dictionary containing the parsed CSV data with headers and rows
        """
        self._validate_file_extension(['.csv'])
        
        try:
            rows = []
            headers = []
            
            with open(self.input_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)  # First row as headers
                rows = list(reader)
                
            return {
                "type": "csv",
                "headers": headers,
                "rows": rows,
                "metadata": {
                    "file_size": self.input_path.stat().st_size,
                    "row_count": len(rows),
                    "column_count": len(headers)
                }
            }
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

class JSONInputHandler(DataInputHandler):
    """Handler for JSON file input"""
    
    def read(self) -> Dict[str, Any]:
        """Read and parse a JSON file.
        
        Returns:
            Dictionary containing the parsed JSON data
        """
        self._validate_file_extension(['.json'])
        
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Add metadata about the structure
            metadata = {
                "file_size": self.input_path.stat().st_size,
                "is_array": isinstance(data, list),
                "top_level_keys": list(data.keys()) if isinstance(data, dict) else None,
                "array_length": len(data) if isinstance(data, list) else None
            }
            
            return {
                "type": "json",
                "data": data,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            raise

def create_input_handler(input_path: Union[str, Path]) -> DataInputHandler:
    """Factory function to create the appropriate input handler based on file extension.
    
    Args:
        input_path: Path to the input file
        
    Returns:
        An instance of the appropriate DataInputHandler subclass
        
    Raises:
        ValueError: If file extension is not supported
    """
    path = Path(input_path)
    extension = path.suffix.lower()
    
    handlers = {
        '.txt': TextInputHandler,
        '.text': TextInputHandler,
        '.csv': CSVInputHandler,
        '.json': JSONInputHandler
    }
    
    if extension not in handlers:
        raise ValueError(
            f"Unsupported file extension: {extension}. "
            f"Supported extensions: {list(handlers.keys())}"
        )
        
    return handlers[extension](input_path) 