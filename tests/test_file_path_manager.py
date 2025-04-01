"""
Tests for the file path manager module.

Example:
    >>> manager = FilePathManager()
    >>> manager.sanitize_filename('test<>:"/\\|?*file.txt')
    'test_________file.txt'
    >>> manager.generate_timestamped_filename('test')
    'test_20240401_123456.pptx'  # timestamp will vary
"""
import os
import re
import pytest
from pathlib import Path
from datetime import datetime
from src.core.file_path_manager import FilePathManager

@pytest.fixture
def manager():
    """Create a test file path manager."""
    return FilePathManager()

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for file operations."""
    return tmp_path

def test_init_default(manager):
    """Test default initialization."""
    assert isinstance(manager.base_dir, Path), "base_dir should be a Path object"
    assert manager.base_dir == Path.cwd(), "Default base_dir should be current working directory"

def test_init_with_base_dir(temp_dir):
    """Test initialization with base directory."""
    manager = FilePathManager(temp_dir)
    assert manager.base_dir == temp_dir, "base_dir should match provided directory"

@pytest.mark.parametrize("input_filename,expected", [
    ('test<>:"/\\|?*file.txt', 'test_________file.txt'),
    (' .test. ', 'test'),
    ('', 'presentation'),
    ('...', 'presentation'),
    ('test-file.txt', 'test-file.txt'),
    ('../../etc/passwd', '______etc_passwd'),  # Security test
    ('con.txt', '_con.txt'),  # Windows reserved name
    ('file....txt', 'file....txt'),
])
def test_sanitize_filename(manager, input_filename, expected):
    """Test filename sanitization with various inputs."""
    result = manager.sanitize_filename(input_filename)
    assert result == expected, f"Failed to sanitize '{input_filename}' correctly"

def test_generate_timestamped_filename(manager):
    """Test timestamped filename generation."""
    # Test basic filename
    filename = manager.generate_timestamped_filename('test')
    assert filename.startswith('test_'), "Filename should start with base name"
    assert filename.endswith('.pptx'), "Default extension should be .pptx"
    assert re.match(r'test_\d{8}_\d{6}\.pptx', filename), "Filename should contain timestamp"
    
    # Test with custom extension
    filename = manager.generate_timestamped_filename('test', '.txt')
    assert filename.endswith('.txt'), "Should use provided extension"
    
    # Test with invalid characters
    filename = manager.generate_timestamped_filename('test/file')
    assert 'test_file_' in filename, "Should sanitize invalid characters"
    assert '/' not in filename, "Should not contain path separators"

@pytest.mark.parametrize("strategy,expected_pattern", [
    ('timestamp', r'test_\d{8}_\d{6}\.pptx$'),
    ('increment', r'test_1\.pptx$'),
])
def test_get_unique_filepath_strategies(manager, temp_dir, strategy, expected_pattern):
    """Test different strategies for generating unique filepaths."""
    base_path = temp_dir / 'test.pptx'
    base_path.touch()
    
    unique_path = manager.get_unique_filepath(base_path, strategy)
    assert unique_path != base_path, "Should generate different path when file exists"
    assert re.match(expected_pattern, str(unique_path.name)), f"Invalid pattern for {strategy} strategy"

def test_get_unique_filepath_increment_sequence(manager, temp_dir):
    """Test incremental numbering of duplicate files."""
    base_path = temp_dir / 'test.pptx'
    base_path.touch()
    
    # Create test_1.pptx
    first_path = manager.get_unique_filepath(base_path, 'increment')
    first_path.touch()
    assert first_path.name == 'test_1.pptx'
    
    # Create test_2.pptx
    second_path = manager.get_unique_filepath(base_path, 'increment')
    assert second_path.name == 'test_2.pptx'

def test_get_unique_filepath_invalid_strategy(manager, temp_dir):
    """Test error handling for invalid strategy."""
    with pytest.raises(ValueError, match="Strategy must be 'timestamp' or 'increment'"):
        manager.get_unique_filepath(temp_dir / 'test.pptx', 'invalid')

@pytest.mark.skipif(os.name != 'posix', reason="Permission tests only run on POSIX systems")
def test_validate_filepath_permissions(manager, temp_dir):
    """Test filepath validation with different permissions."""
    read_only_dir = temp_dir / 'readonly'
    read_only_dir.mkdir()
    read_only_dir.chmod(0o444)  # Read-only
    
    with pytest.raises(PermissionError, match="Cannot write to"):
        manager.validate_filepath(read_only_dir / 'test.pptx')

def test_validate_filepath_creation(manager, temp_dir):
    """Test filepath validation with directory creation."""
    nested_path = temp_dir / 'nested' / 'path' / 'test.pptx'
    manager.validate_filepath(nested_path)
    assert nested_path.parent.exists(), "Should create parent directories"

@pytest.mark.parametrize("input_path,expected_exists", [
    ('test.pptx', True),
    ('subdir/test.pptx', True),
    ('nested/path/test.pptx', False),
])
def test_resolve_filepath(manager, temp_dir, input_path, expected_exists):
    """Test filepath resolution with different inputs."""
    manager = FilePathManager(temp_dir)
    path = manager.resolve_filepath(input_path, create_dirs=expected_exists)
    
    assert path.is_absolute(), "Should return absolute path"
    assert path.parent.exists() == expected_exists, "Directory existence should match expected"
    assert str(path).startswith(str(temp_dir)), "Path should be under temp_dir" 