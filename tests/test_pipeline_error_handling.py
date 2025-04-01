"""
Tests for pipeline error handling functionality.
"""

import pytest
import asyncio
from pathlib import Path
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.core.pipeline import Pipeline, PipelineStage, StageResult, PipelineStageStatus, PipelineContext
from src.core.pipeline_error_handlers import (
    ErrorRecoveryStrategy,
    RetryStrategy,
    FallbackContentStrategy,
    AutoSaveStrategy,
    ErrorHandler
)
from src.core.pipeline_factory import PipelineFactory

# Test data
TEST_DATA = {
    "topic": "Test Presentation",
    "style": "professional",
    "num_slides": 5
}

# Mock OpenAI API key for testing
@pytest.fixture(autouse=True)
def mock_openai_client():
    """Mock OpenAIClient for all tests."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}), \
         patch('src.core.openai_client.OpenAIClient') as mock_client:
        # Configure the mock
        mock_client.return_value = AsyncMock()
        mock_client.return_value.create_assistant = AsyncMock(return_value=Mock(id="test-assistant"))
        mock_client.return_value.create_thread = AsyncMock(return_value=Mock(id="test-thread"))
        mock_client.return_value.add_message = AsyncMock()
        mock_client.return_value.run_assistant = AsyncMock(return_value=Mock(id="test-run"))
        mock_client.return_value.get_run_status = AsyncMock(return_value=Mock(status="completed"))
        mock_client.return_value.get_messages = AsyncMock(return_value=Mock(
            data=[Mock(content=[Mock(text=Mock(value="Test content"))])]
        ))
        
        yield mock_client

class MockFailingStage(PipelineStage):
    """A stage that fails for testing error handling."""
    
    def __init__(self, name: str, fail_times: int = 1):
        super().__init__(name)
        self.fail_times = fail_times
        self.attempt = 0
        
    async def process(self, data: dict, context: PipelineContext) -> StageResult:
        self.attempt += 1
        if self.attempt <= self.fail_times:
            error = ConnectionError("Simulated failure")
            # Don't add error to context here, let Pipeline.execute handle it
            raise error
            
        return StageResult(
            status=PipelineStageStatus.COMPLETED,
            data=data
        )

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    checkpoints_dir = tmp_path / "checkpoints"
    fallback_dir = tmp_path / "templates" / "fallback"
    checkpoints_dir.mkdir(parents=True)
    fallback_dir.mkdir(parents=True)
    
    # Create a fallback template
    template = {
        "slides": [
            {"title": "Fallback Title", "content": "Fallback Content"}
        ]
    }
    template_path = fallback_dir / "test_presentation.json"
    template_path.write_text(json.dumps(template))
    
    # Create a test input file
    input_data = {
        "title": "Test Presentation",
        "sections": [
            "Introduction",
            "Main Content",
            "Conclusion"
        ]
    }
    input_file = tmp_path / "test_input.json"
    input_file.write_text(json.dumps(input_data))
    
    return {
        "base": tmp_path,
        "checkpoints": checkpoints_dir,
        "fallback": fallback_dir,
        "input_file": input_file
    }

@pytest.mark.asyncio
async def test_retry_strategy():
    """Test that retry strategy works with exponential backoff."""
    strategy = RetryStrategy(max_retries=2, initial_delay=0.1)
    context = PipelineContext()
    context.set_data("current_stage_name", "test_stage")
    context.set_data("stage_input_data", TEST_DATA)
    
    # First attempt should be possible
    assert await strategy.can_recover(Exception(), context)
    
    # Simulate first retry
    await strategy.recover(Exception(), context)
    assert await strategy.can_recover(Exception(), context)
    
    # Simulate second retry
    await strategy.recover(Exception(), context)
    # Should not allow more retries
    assert not await strategy.can_recover(Exception(), context)

@pytest.mark.asyncio
async def test_fallback_content_strategy(temp_dirs):
    """Test that fallback content strategy works when content generation fails."""
    strategy = FallbackContentStrategy(temp_dirs["fallback"])
    context = PipelineContext()
    context.set_data("current_stage_name", "Content Generation")
    context.set_data("topic", "Test Presentation")
    
    # Should recover from connection errors
    assert await strategy.can_recover(ConnectionError(), context)
    result = await strategy.recover(ConnectionError(), context)
    assert result is not None
    assert "slides" in result
    
    # Should not recover from other errors
    assert not await strategy.can_recover(ValueError(), context)

@pytest.mark.asyncio
async def test_auto_save_strategy(temp_dirs):
    """Test that auto-save strategy properly saves checkpoints."""
    strategy = AutoSaveStrategy(temp_dirs["checkpoints"])
    context = PipelineContext()
    context.set_data("current_stage_name", "test_stage")
    context.set_data("stage_input_data", TEST_DATA)
    
    # Should always be able to save
    assert await strategy.can_recover(Exception(), context)
    
    # Should save checkpoint
    await strategy.recover(Exception(), context)
    
    # Verify checkpoint was saved
    checkpoints = list(temp_dirs["checkpoints"].glob("checkpoint_*.json"))
    assert len(checkpoints) == 1
    
    # Verify checkpoint content
    checkpoint_data = json.loads(checkpoints[0].read_text())
    assert checkpoint_data["stage_name"] == "test_stage"
    assert checkpoint_data["input_data"] == TEST_DATA

@pytest.mark.asyncio
async def test_error_handler_recovery():
    """Test that error handler properly coordinates recovery strategies."""
    handler = ErrorHandler()
    
    # Add mock strategies
    mock_strategy1 = Mock(spec=ErrorRecoveryStrategy)
    mock_strategy1.can_recover = AsyncMock(return_value=False)
    mock_strategy1.recover = AsyncMock(return_value=None)
    
    mock_strategy2 = Mock(spec=ErrorRecoveryStrategy)
    mock_strategy2.can_recover = AsyncMock(return_value=True)
    mock_strategy2.recover = AsyncMock(return_value=TEST_DATA)
    
    handler.add_strategy(mock_strategy1)
    handler.add_strategy(mock_strategy2)
    
    # Test recovery
    context = PipelineContext()
    result = await handler.handle_error(Exception("Test error"), context)
    
    # Verify strategies were tried in order
    mock_strategy1.can_recover.assert_called_once()
    mock_strategy2.can_recover.assert_called_once()
    mock_strategy1.recover.assert_not_called()
    mock_strategy2.recover.assert_called_once()
    
    assert result == TEST_DATA

@pytest.mark.asyncio
async def test_pipeline_error_recovery(temp_dirs):
    """Test end-to-end pipeline error recovery."""
    # Create a pipeline with a failing stage
    factory = PipelineFactory(base_dir=temp_dirs["base"], input_path=temp_dirs["input_file"])
    failing_stage = MockFailingStage("Content Generation", fail_times=1)
    
    # Add error handler to the stage
    handler = ErrorHandler()
    # Add RetryStrategy first as it's the primary recovery mechanism
    handler.add_strategy(RetryStrategy(max_retries=2, initial_delay=0.1))
    # Add AutoSaveStrategy as the secondary recovery mechanism
    handler.add_strategy(AutoSaveStrategy(temp_dirs["checkpoints"]))
    
    async def error_handler(error, context):
        # Ensure required data is in context for error recovery
        context.set_data("current_stage_name", failing_stage.name)
        if context.get_data("stage_input_data") is None:
            context.set_data("stage_input_data", TEST_DATA)
        
        # Try to handle the error
        result = await handler.handle_error(error, context)
        
        # If recovery was successful, ensure error is removed from context
        if result is not None and error in context.errors:
            context.errors.remove(error)
            
        return result
    
    failing_stage.add_error_handler(error_handler)
    
    # Create and execute pipeline
    pipeline = Pipeline(failing_stage)
    context = await pipeline.execute(TEST_DATA)
    
    # Verify that the pipeline recovered and completed
    assert len(context.errors) == 0, f"Expected no errors, but found: {context.errors}"
    assert failing_stage.attempt == 2, "Stage should have attempted twice (one failure + one success)"
    assert context.get_data("stage_input_data") == TEST_DATA, "Input data should be preserved after retry"
    assert context.get_data("current_stage_name") == failing_stage.name, "Stage name should be preserved"
    
    # Verify stage completed successfully
    assert failing_stage._last_result is not None, "Stage should have produced a result"
    assert failing_stage._last_result.status == PipelineStageStatus.COMPLETED, "Stage should have completed successfully"
    assert failing_stage._last_result.data == TEST_DATA, "Stage should have processed the test data"
    
    # Verify checkpoint was created by AutoSaveStrategy
    checkpoints = list(temp_dirs["checkpoints"].glob("checkpoint_*.json"))
    assert len(checkpoints) == 1, "One checkpoint should have been created"
    
    # Verify checkpoint content
    checkpoint_data = json.loads(checkpoints[0].read_text())
    assert checkpoint_data["stage_name"] == failing_stage.name, "Checkpoint should record correct stage name"
    assert checkpoint_data["input_data"] == TEST_DATA, "Checkpoint should contain original input data"

@pytest.mark.asyncio
async def test_pipeline_factory_error_handling(temp_dirs):
    """Test that pipeline factory properly configures error handling."""
    factory = PipelineFactory(base_dir=temp_dirs["base"], input_path=temp_dirs["input_file"])
    
    config = {
        "max_retries": 3,
        "checkpoints_enabled": True,
        "fallback_templates_enabled": True,
        "theme": "modern",
        "output_format": "pptx"
    }
    
    pipeline = await factory.create_pipeline(config)
    
    # Verify configuration was applied
    assert pipeline.context.get_data("max_retries") == 3
    assert pipeline.context.get_data("checkpoints_enabled") is True
    assert pipeline.context.get_data("fallback_templates_enabled") is True
    
    # Verify error handlers were added to stages
    for stage in factory._get_all_stages(pipeline):
        assert len(stage._error_handlers) > 0 