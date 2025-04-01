"""
Module for managing file paths, names, and overwrite protection for presentation exports.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Set

class FilePathManager:
    """Handles file path operations, name generation, and overwrite protection."""
    
    # Windows reserved names (case-insensitive)
    WINDOWS_RESERVED_NAMES: Set[str] = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }
    
    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the file path manager.
        
        Args:
            base_dir: Optional base directory for file operations. Defaults to current directory.
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing invalid characters and handling security concerns.
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            Sanitized filename
        """
        # Handle empty or dot-only filenames first
        if not filename or all(c == '.' for c in filename):
            return 'presentation'
            
        # Replace path traversal patterns with underscores
        # Replace each '../' or '..\\' with '___'
        sanitized = re.sub(r'\.\.[/\\]', '___', filename)
        # Replace remaining path separators
        sanitized = re.sub(r'[/\\]', '_', sanitized)
        
        # Remove any remaining path-like components
        sanitized = os.path.basename(sanitized)
        
        # Replace other invalid characters
        invalid_chars = r'[<>:"|?*]'
        sanitized = re.sub(invalid_chars, '_', sanitized)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        
        # Check again for empty or dot-only filename after sanitization
        if not sanitized or all(c == '.' for c in sanitized):
            return 'presentation'
            
        # Handle Windows reserved names
        name_parts = sanitized.split('.')
        name_base = name_parts[0].lower()
        if name_base in self.WINDOWS_RESERVED_NAMES:
            if len(name_parts) > 1:
                sanitized = f"_{name_parts[0]}.{'.'.join(name_parts[1:])}"
            else:
                sanitized = f"_{sanitized}"
            
        return sanitized
        
    def generate_timestamped_filename(self, base_name: str, extension: str = '.pptx') -> str:
        """
        Generate a timestamped filename.
        
        Args:
            base_name: Base name for the file
            extension: File extension (default: .pptx)
            
        Returns:
            Timestamped filename
        """
        # Sanitize base name
        base_name = self.sanitize_filename(base_name)
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Ensure extension starts with dot
        if not extension.startswith('.'):
            extension = f'.{extension}'
            
        return f"{base_name}_{timestamp}{extension}"
        
    def get_unique_filepath(self, filepath: Union[str, Path], strategy: str = 'timestamp') -> Path:
        """
        Get a unique filepath using the specified strategy to handle existing files.
        
        Args:
            filepath: The desired filepath
            strategy: Strategy to use ('timestamp' or 'increment')
            
        Returns:
            A unique Path object
        
        Raises:
            ValueError: If strategy is invalid
        """
        if strategy not in ('timestamp', 'increment'):
            raise ValueError("Strategy must be 'timestamp' or 'increment'")
            
        filepath = Path(filepath)
        
        # If file doesn't exist, return as is
        if not filepath.exists():
            return filepath
            
        if strategy == 'timestamp':
            # Add timestamp before extension
            stem = filepath.stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return filepath.with_name(f"{stem}_{timestamp}{filepath.suffix}")
        else:  # increment
            counter = 1
            while True:
                new_filepath = filepath.with_name(f"{filepath.stem}_{counter}{filepath.suffix}")
                if not new_filepath.exists():
                    return new_filepath
                counter += 1
                
    def validate_filepath(self, filepath: Union[str, Path]) -> None:
        """
        Validate a filepath for writing.
        
        Args:
            filepath: The filepath to validate
            
        Raises:
            ValueError: If path is invalid
            PermissionError: If path is not writable
            OSError: If path is too long
        """
        filepath = Path(filepath)
        
        # Check if parent directory exists or can be created
        parent = filepath.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True)
            except OSError as e:
                raise ValueError(f"Cannot create directory {parent}: {e}")
                
        # Check if path is too long (Windows has 260 char limit by default)
        try:
            filepath.resolve()
        except OSError as e:
            raise OSError(f"Path too long or invalid: {e}")
            
        # Check write permissions by trying to create a temp file
        if filepath.exists():
            if not os.access(filepath, os.W_OK):
                raise PermissionError(f"No write permission for {filepath}")
        else:
            try:
                filepath.touch()
                filepath.unlink()
            except OSError as e:
                raise PermissionError(f"Cannot write to {filepath}: {e}")
                
    def resolve_filepath(self, filename: str, create_dirs: bool = True) -> Path:
        """
        Resolve a filename to a full filepath in the base directory.
        
        Args:
            filename: The filename to resolve
            create_dirs: Whether to create parent directories
            
        Returns:
            Resolved Path object
            
        Raises:
            ValueError: If filename is invalid
        """
        # Split path into components and sanitize each part
        parts = Path(filename).parts
        sanitized_parts = [self.sanitize_filename(part) for part in parts]
        sanitized_path = Path(*sanitized_parts)
        
        # Create full path
        filepath = self.base_dir / sanitized_path
        
        # Create parent directories only if requested
        if create_dirs and not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)
                
        return filepath.resolve() 