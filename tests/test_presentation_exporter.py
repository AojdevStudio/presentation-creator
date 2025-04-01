"""
Tests for the presentation exporter module.
"""
import os
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from pptx import Presentation
from pptx.presentation import Presentation as PresentationType
from src.presentation.presentation_exporter import PresentationExporter

@pytest.fixture
def presentation() -> PresentationType:
    """Create a test presentation."""
    return Presentation()

@pytest.fixture
def exporter(presentation) -> PresentationExporter:
    """Create a test exporter."""
    return PresentationExporter(presentation)

@pytest.fixture
def temp_pptx(tmp_path) -> Path:
    """Create a temporary directory and file path for test presentations."""
    test_dir = tmp_path / "test_presentations"
    test_dir.mkdir()
    return test_dir / "test.pptx"

def test_export_new_file(exporter, temp_pptx):
    """Test exporting to a new file."""
    # Export presentation
    result_path = exporter.export(str(temp_pptx))
    
    # Verify file was created
    assert Path(result_path).exists()
    assert result_path == str(temp_pptx)
    
def test_export_existing_file_no_overwrite(exporter, temp_pptx):
    """Test exporting when file exists and overwrite is False."""
    # Create initial file
    temp_pptx.write_text("dummy content")
    
    # Try to export - should raise error
    with pytest.raises(FileExistsError):
        exporter.export(str(temp_pptx), {'overwrite': False})
        
def test_export_existing_file_with_backup(exporter, temp_pptx):
    """Test exporting with backup of existing file."""
    # Create initial file
    temp_pptx.write_text("original content")
    original_content = temp_pptx.read_text()
    
    # Export with backup
    result_path = exporter.export(str(temp_pptx), {
        'overwrite': True,
        'backup_existing': True
    })
    
    # Verify new file exists
    assert Path(result_path).exists()
    
    # Verify backup was created
    backup_path = temp_pptx.with_suffix(".bak.pptx")
    assert backup_path.exists()
    assert backup_path.read_text() == original_content
    
def test_export_create_directories(exporter, temp_pptx):
    """Test creating directories during export."""
    # Create deep path
    deep_path = temp_pptx.parent / "subdir1" / "subdir2" / "presentation.pptx"
    
    # Export presentation
    result_path = exporter.export(str(deep_path), {'create_dirs': True})
    
    # Verify directories and file were created
    assert Path(result_path).exists()
    assert deep_path.parent.exists()
    
def test_export_fail_no_permissions(exporter, temp_pptx, monkeypatch):
    """Test handling of permission errors during export."""
    def mock_save(*args):
        raise PermissionError("Access denied")
        
    # Mock the save method to raise error
    monkeypatch.setattr(exporter.presentation, 'save', mock_save)
    
    # Try to export - should raise error
    with pytest.raises(OSError) as exc_info:
        exporter.export(str(temp_pptx))
    assert "Access denied" in str(exc_info.value)
    
def test_get_file_info(exporter, temp_pptx):
    """Test getting file information."""
    # Export a file
    exporter.export(str(temp_pptx))
    
    # Get file info
    info = exporter.get_file_info(str(temp_pptx))
    
    # Verify info structure
    assert 'size' in info
    assert 'created' in info
    assert 'modified' in info
    assert 'is_backup' in info
    assert isinstance(info['size'], int)
    assert isinstance(info['created'], float)
    assert isinstance(info['modified'], float)
    assert isinstance(info['is_backup'], bool)
    assert not info['is_backup']  # Should not be a backup file
    
def test_get_file_info_backup(exporter, temp_pptx):
    """Test getting file information for backup file."""
    # Create initial file and backup
    exporter.export(str(temp_pptx))
    exporter.export(str(temp_pptx), {'overwrite': True, 'backup_existing': True})
    
    # Get info for backup file
    backup_path = temp_pptx.with_suffix(".bak.pptx")
    info = exporter.get_file_info(str(backup_path))
    
    assert info['is_backup']
    
def test_get_file_info_nonexistent(exporter, temp_pptx):
    """Test getting info for non-existent file."""
    with pytest.raises(FileNotFoundError):
        exporter.get_file_info(str(temp_pptx)) 