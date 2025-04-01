"""
Integration test for the end-to-end presentation generation pipeline.

This test verifies that all pipeline components work together correctly
to generate a presentation from user input.
"""

import pytest
import os
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.main import PresentationGenerator
from src.core.pipeline_factory import PipelineFactory
from src.core.pipeline import Pipeline, PipelineStageStatus, StageResult

# Sample test data
SAMPLE_INPUT = {
    "topic": "Test Presentation",
    "style": "professional",
    "num_slides": 5,
    "author": "Test Author",
    "company": "Test Company",
    "keywords": ["test", "presentation", "pipeline"]
}

SAMPLE_CONFIG = {
    "theme": "default",
    "output_format": "pptx",
    "max_retries": 2,
    "checkpoints_enabled": True,
    "fallback_templates_enabled": True
}

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def temp_config_file(temp_dir):
    """Create a temporary config file for testing."""
    import json
    config_path = temp_dir / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(SAMPLE_CONFIG, f)
    return config_path

@pytest.mark.asyncio
async def test_pipeline_factory_creates_valid_pipeline():
    """Test that PipelineFactory creates a valid pipeline with all stages."""
    factory = PipelineFactory()
    pipeline = await factory.create_pipeline(SAMPLE_CONFIG)
    
    # Verify pipeline structure
    assert pipeline is not None
    assert pipeline.initial_stage is not None
    
    # Check that all stages are connected
    stages = []
    current_stage = pipeline.initial_stage
    while current_stage:
        stages.append(current_stage)
        current_stage = current_stage._next_stages[0] if current_stage._next_stages else None
    
    # There should be input, content, slide, and assembly stages
    assert len(stages) == 4
    assert stages[0].name == "Input Validation"
    assert stages[1].name == "Content Generation"
    assert stages[2].name == "Slide Creation"
    assert stages[3].name == "Presentation Assembly"

class MockStage:
    """Mock pipeline stage for testing."""
    
    def __init__(self, name, result_data=None, status=PipelineStageStatus.COMPLETED):
        self.name = name
        self._next_stages = []
        self._error_handlers = []
        self.result_data = result_data
        self.status = status
    
    async def process(self, data, context):
        return StageResult(status=self.status, data=self.result_data)
    
    def add_next_stage(self, stage):
        self._next_stages.append(stage)
    
    def add_error_handler(self, handler):
        self._error_handlers.append(handler)

@pytest.mark.asyncio
async def test_presentation_generator_with_mock_pipeline():
    """Test PresentationGenerator with a mock pipeline."""
    # Create mock pipeline
    mock_output_path = Path("/mock/output/presentation.pptx")
    mock_stage = MockStage("Mock Stage", result_data=mock_output_path)
    mock_pipeline = Pipeline(mock_stage)
    
    # Mock factory to return our mock pipeline
    mock_factory = MagicMock()
    mock_factory.create_pipeline.return_value = mock_pipeline
    
    # Patch PipelineFactory to use our mock
    with patch('src.main.PipelineFactory', return_value=mock_factory):
        generator = PresentationGenerator()
        output_path = await generator.generate_presentation(SAMPLE_INPUT)
        
        # Verify results
        assert output_path == mock_output_path
        mock_factory.create_pipeline.assert_called_once()

@pytest.mark.asyncio
async def test_presentation_generator_with_config_file(temp_config_file):
    """Test PresentationGenerator with a configuration file."""
    # Mock pipeline execution
    mock_output_path = Path("/mock/output/presentation.pptx")
    
    # Create mock execute method
    async def mock_execute(data):
        context = MagicMock()
        context.errors = []
        context.get_data.return_value = mock_output_path
        return context
    
    # Create mock pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.execute = mock_execute
    
    # Mock factory to return our mock pipeline
    mock_factory = MagicMock()
    mock_factory.create_pipeline.return_value = mock_pipeline
    
    # Patch PipelineFactory to use our mock
    with patch('src.main.PipelineFactory', return_value=mock_factory):
        generator = PresentationGenerator(temp_config_file)
        output_path = await generator.generate_presentation(SAMPLE_INPUT)
        
        # Verify results
        assert output_path == mock_output_path
        mock_factory.create_pipeline.assert_called_once()

@pytest.mark.asyncio
async def test_pipeline_error_handling():
    """Test error handling in the pipeline."""
    # Create a pipeline with a stage that will fail
    error_stage = MockStage("Error Stage", status=PipelineStageStatus.FAILED)
    error_stage.process = MagicMock(side_effect=Exception("Test error"))
    
    pipeline = Pipeline(error_stage)
    
    # Mock error handler that successfully recovers
    async def mock_error_handler(error, context):
        return {"recovered": True}
    
    error_stage.handle_error = mock_error_handler
    
    # Execute pipeline and verify error handling
    context = await pipeline.execute(SAMPLE_INPUT)
    
    # Verify error was added to context
    assert len(context.errors) > 0
    assert isinstance(context.errors[0], Exception)

@pytest.mark.asyncio
async def test_integration_with_mocked_components(temp_dir):
    """Test end-to-end integration with mocked components."""
    # Setup mock output
    mock_output_path = temp_dir / "test_presentation.pptx"
    
    # Create mock for PresentationAssemblyStage's process method
    async def mock_assembly_process(data, context):
        # Create an empty file to simulate output
        with open(mock_output_path, 'w') as f:
            f.write("Mock presentation content")
        return StageResult(
            status=PipelineStageStatus.COMPLETED,
            data=mock_output_path
        )
    
    # Create patches for the core components
    patches = [
        # Mock slide content generation
        patch('src.core.slide_content_generator.SlideContentGenerator.generate_slide_contents',
              return_value=[{"title": "Slide 1", "content": "Test content"}]),
              
        # Mock slide creation
        patch('src.core.slide_generator.SlideGenerator.create_slide',
              return_value={"title": "Slide 1", "content": "Test content", "layout": "Title Slide"}),
              
        # Mock theme management
        patch('src.core.theme_manager.ThemeManager.get_theme',
              return_value=MagicMock(name="default")),
              
        # Mock presentation assembly - replace the entire process method
        patch('src.core.presentation_pipeline_stages.PresentationAssemblyStage.process',
              mock_assembly_process)
    ]
    
    # Apply all patches
    for p in patches:
        p.start()
    
    try:
        # Create generator and execute pipeline
        generator = PresentationGenerator()
        output_path = await generator.generate_presentation(SAMPLE_INPUT)
        
        # Verify the output
        assert output_path.exists()
        assert output_path == mock_output_path
        
    finally:
        # Stop all patches
        for p in patches:
            p.stop()

if __name__ == "__main__":
    asyncio.run(pytest.main([__file__])) 