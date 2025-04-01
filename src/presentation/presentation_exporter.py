"""
Module for handling presentation export and file output operations.
"""
from pathlib import Path
from typing import Dict, Any, Optional
from pptx.presentation import Presentation as PresentationType

class PresentationExporter:
    """Handles presentation export operations and file management."""
    
    def __init__(self, presentation: PresentationType):
        """
        Initialize the exporter with a presentation.
        
        Args:
            presentation: The presentation to export
        """
        self.presentation = presentation
        
    def export(self, output_path: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Export the presentation with specified options.
        
        Args:
            output_path: Path where to save the presentation
            options: Dictionary containing export options:
                    - overwrite: Whether to overwrite existing file (default: False)
                    - create_dirs: Whether to create missing directories (default: True)
                    - backup_existing: Whether to backup existing file (default: True)
        
        Returns:
            The actual path where the file was saved
        
        Raises:
            FileExistsError: If file exists and overwrite is False
            OSError: If directory creation fails or file cannot be saved
        """
        options = options or {}
        overwrite = options.get('overwrite', False)
        create_dirs = options.get('create_dirs', True)
        backup_existing = options.get('backup_existing', True)
        
        # Convert to Path object for easier manipulation
        path = Path(output_path)
        
        # Create directories if needed
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
            
        # Handle existing file
        if path.exists():
            if not overwrite:
                raise FileExistsError(f"File {path} already exists and overwrite=False")
            if backup_existing:
                backup_path = path.with_suffix(f".bak{path.suffix}")
                path.rename(backup_path)
                
        try:
            # Save the presentation
            self.presentation.save(str(path))
            return str(path)
        except Exception as e:
            # If backup exists and save failed, restore it
            if backup_existing and 'backup_path' in locals() and backup_path.exists():
                backup_path.rename(path)
            raise OSError(f"Failed to save presentation: {e}")
            
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get information about an exported presentation file.
        
        Args:
            path: Path to the presentation file
            
        Returns:
            Dictionary containing file information:
            - size: File size in bytes
            - created: Creation timestamp
            - modified: Last modified timestamp
            - is_backup: Whether this is a backup file
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File {path} not found")
            
        stats = file_path.stat()
        return {
            'size': stats.st_size,
            'created': stats.st_ctime,
            'modified': stats.st_mtime,
            'is_backup': file_path.suffix.endswith('.bak.pptx')
        } 