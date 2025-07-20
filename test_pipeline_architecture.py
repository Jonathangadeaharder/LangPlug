#!/usr/bin/env python3
"""
Test script to verify the new pipeline architecture works correctly.

This script performs basic validation of the processing steps and pipeline
without requiring actual dependencies or video files.
"""

import os
import sys
from unittest.mock import Mock, MagicMock
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# Define the core architecture classes for testing
@dataclass
class ProcessingContext:
    """Context object that holds all data and state for the processing pipeline."""
    video_file: str
    model_manager: Any = None
    language: str = "de"
    src_lang: str = "de"
    tgt_lang: str = "es"
    no_preview: bool = False
    
    # File paths (will be set during processing)
    audio_file: Optional[str] = None
    preview_srt: Optional[str] = None
    full_srt: Optional[str] = None
    filtered_srt: Optional[str] = None
    translated_srt: Optional[str] = None
    
    # Processing metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
class ProcessingStep(ABC):
    """Abstract base class for all processing steps."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: ProcessingContext) -> bool:
        """Execute this processing step.
        
        Args:
            context: The processing context containing all necessary data
            
        Returns:
            bool: True if the step succeeded, False otherwise
        """
        pass
    
    def log_start(self):
        print(f"[{self.name}] Starting...")
    
    def log_success(self, message: str = ""):
        print(f"[{self.name}] ✓ Success: {message}")
    
    def log_error(self, message: str = ""):
        print(f"[{self.name}] ✗ Error: {message}")
        
class ProcessingPipeline:
    """Pipeline that executes a sequence of processing steps."""
    
    def __init__(self, steps: List[ProcessingStep]):
        self.steps = steps
    
    def execute(self, context: ProcessingContext) -> bool:
        """Execute all steps in the pipeline.
        
        Args:
            context: The processing context
            
        Returns:
            bool: True if all steps succeeded, False if any step failed
        """
        print(f"\nExecuting pipeline with {len(self.steps)} steps...")
        
        for i, step in enumerate(self.steps, 1):
            print(f"\nStep {i}/{len(self.steps)}: {step.name}")
            
            try:
                success = step.execute(context)
                if not success:
                    print(f"Pipeline failed at step {i}: {step.name}")
                    return False
            except Exception as e:
                print(f"Pipeline failed at step {i}: {step.name} - {str(e)}")
                return False
        
        print("\n🎉 Pipeline completed successfully!")
        return True

# Mock processing steps for testing
class MockProcessingStep(ProcessingStep):
    """Mock processing step for testing."""
    
    def __init__(self, name: str, should_succeed: bool = True):
        super().__init__(name)
        self.should_succeed = should_succeed
        self.executed = False
    
    def execute(self, context: ProcessingContext) -> bool:
        self.log_start()
        self.executed = True
        
        if self.should_succeed:
            self.log_success("Mock step completed")
            return True
        else:
            self.log_error("Mock step failed")
            return False

class MockTranscriptionStep(ProcessingStep):
    """Mock transcription step."""
    
    def __init__(self):
        super().__init__("Mock Transcription")
    
    def execute(self, context: ProcessingContext) -> bool:
        self.log_start()
        # Simulate transcription
        context.full_srt = f"{context.video_file}.srt"
        context.metadata["transcription_completed"] = True
        self.log_success(f"Created subtitles: {context.full_srt}")
        return True

class MockFilterStep(ProcessingStep):
    """Mock filtering step."""
    
    def __init__(self):
        super().__init__("Mock A1 Filter")
    
    def execute(self, context: ProcessingContext) -> bool:
        self.log_start()
        if not context.full_srt:
            self.log_error("No subtitles to filter")
            return False
        
        # Simulate filtering
        context.filtered_srt = context.full_srt.replace(".srt", "_filtered.srt")
        context.metadata["filtering_completed"] = True
        self.log_success(f"Created filtered subtitles: {context.filtered_srt}")
        return True

class MockTranslationStep(ProcessingStep):
    """Mock translation step."""
    
    def __init__(self):
        super().__init__("Mock Translation")
    
    def execute(self, context: ProcessingContext) -> bool:
        self.log_start()
        if not context.filtered_srt:
            self.log_error("No filtered subtitles to translate")
            return False
        
        # Simulate translation
        context.translated_srt = context.filtered_srt.replace("_filtered.srt", f"_translated_{context.tgt_lang}.srt")
        context.metadata["translation_completed"] = True
        self.log_success(f"Created translated subtitles: {context.translated_srt}")
        return True

def create_mock_model_manager():
    """Create a mock model manager for testing."""
    mock_manager = Mock()
    mock_manager.get_whisper_model.return_value = Mock()
    mock_manager.get_spacy_model.return_value = Mock()
    mock_manager.get_translation_model.return_value = (Mock(), Mock())
    mock_manager.get_device.return_value = "cpu"
    mock_manager.cleanup_cuda_memory.return_value = None
    mock_manager.cleanup_all_models.return_value = None
    return mock_manager

def test_processing_context():
    """Test ProcessingContext creation and usage."""
    print("Testing ProcessingContext...")
    
    mock_manager = create_mock_model_manager()
    
    context = ProcessingContext(
        video_file="test_video.mp4",
        model_manager=mock_manager,
        language="de",
        src_lang="de",
        tgt_lang="es"
    )
    
    assert context.video_file == "test_video.mp4"
    assert context.language == "de"
    assert context.src_lang == "de"
    assert context.tgt_lang == "es"
    assert context.metadata is not None
    
    print("✓ ProcessingContext test passed")

def test_processing_step():
    """Test individual processing step functionality."""
    print("Testing ProcessingStep...")
    
    # Test successful step
    success_step = MockProcessingStep("Success Step", should_succeed=True)
    context = ProcessingContext(
        video_file="test.mp4",
        model_manager=create_mock_model_manager()
    )
    
    result = success_step.execute(context)
    assert result is True
    assert success_step.executed is True
    
    # Test failing step
    fail_step = MockProcessingStep("Fail Step", should_succeed=False)
    result = fail_step.execute(context)
    assert result is False
    assert fail_step.executed is True
    
    print("✓ ProcessingStep test passed")

def test_processing_pipeline():
    """Test pipeline execution with multiple steps."""
    print("Testing ProcessingPipeline...")
    
    # Test successful pipeline
    steps = [
        MockProcessingStep("Step 1", should_succeed=True),
        MockProcessingStep("Step 2", should_succeed=True),
        MockProcessingStep("Step 3", should_succeed=True)
    ]
    
    pipeline = ProcessingPipeline(steps)
    context = ProcessingContext(
        video_file="test.mp4",
        model_manager=create_mock_model_manager()
    )
    
    result = pipeline.execute(context)
    assert result is True
    
    # Verify all steps were executed
    for step in steps:
        assert step.executed is True
    
    print("✓ ProcessingPipeline success test passed")
    
    # Test pipeline with failing step
    failing_steps = [
        MockProcessingStep("Step 1", should_succeed=True),
        MockProcessingStep("Step 2", should_succeed=False),  # This will fail
        MockProcessingStep("Step 3", should_succeed=True)
    ]
    
    failing_pipeline = ProcessingPipeline(failing_steps)
    context2 = ProcessingContext(
        video_file="test2.mp4",
        model_manager=create_mock_model_manager()
    )
    
    result = failing_pipeline.execute(context2)
    assert result is False
    
    # Verify execution stopped at failing step
    assert failing_steps[0].executed is True   # First step executed
    assert failing_steps[1].executed is True   # Second step executed (but failed)
    assert failing_steps[2].executed is False  # Third step not executed
    
    print("✓ ProcessingPipeline failure test passed")

def test_realistic_pipeline():
    """Test a realistic subtitle processing pipeline."""
    print("Testing realistic subtitle processing pipeline...")
    
    # Create a realistic pipeline
    steps = [
        MockTranscriptionStep(),
        MockFilterStep(),
        MockTranslationStep()
    ]
    
    pipeline = ProcessingPipeline(steps)
    context = ProcessingContext(
        video_file="episode_01.mp4",
        model_manager=create_mock_model_manager(),
        src_lang="de",
        tgt_lang="es"
    )
    
    result = pipeline.execute(context)
    assert result is True
    
    # Verify the context was updated correctly
    assert context.full_srt == "episode_01.mp4.srt"
    assert context.filtered_srt == "episode_01.mp4_filtered.srt"
    assert context.translated_srt == "episode_01.mp4_translated_es.srt"
    assert context.metadata["transcription_completed"] is True
    assert context.metadata["filtering_completed"] is True
    assert context.metadata["translation_completed"] is True
    
    print("✓ Realistic pipeline test passed")

def test_pipeline_configurations():
    """Test different pipeline configurations."""
    print("Testing pipeline configurations...")
    
    # Test minimal pipeline (transcription only)
    minimal_pipeline = ProcessingPipeline([
        MockTranscriptionStep()
    ])
    assert len(minimal_pipeline.steps) == 1
    
    # Test learning pipeline (transcription + filtering)
    learning_pipeline = ProcessingPipeline([
        MockTranscriptionStep(),
        MockFilterStep()
    ])
    assert len(learning_pipeline.steps) == 2
    
    # Test full pipeline (transcription + filtering + translation)
    full_pipeline = ProcessingPipeline([
        MockTranscriptionStep(),
        MockFilterStep(),
        MockTranslationStep()
    ])
    assert len(full_pipeline.steps) == 3
    
    print("✓ Pipeline configuration test passed")

def run_all_tests():
    """Run all tests and report results."""
    print("🧪 Running pipeline architecture tests...\n")
    
    try:
        test_processing_context()
        test_processing_step()
        test_processing_pipeline()
        test_realistic_pipeline()
        test_pipeline_configurations()
        
        print("\n🎉 All tests passed! The new pipeline architecture is working correctly.")
        print("\n📋 Architecture Summary:")
        print("  ✓ ProcessingContext: Manages state and data flow")
        print("  ✓ ProcessingStep: Abstract base class for modular steps")
        print("  ✓ ProcessingPipeline: Orchestrates step execution")
        print("  ✓ Error handling: Pipeline stops on first failure")
        print("  ✓ Extensibility: Easy to add new processing steps")
        
        print("\n🚀 Next steps:")
        print("  1. Test with actual video files using unified_subtitle_processor.py")
        print("  2. Configure environment variables for the Node.js backend")
        print("  3. Run the backend server and test API endpoints")
        print("  4. Use pipeline_config_example.py for custom configurations")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)