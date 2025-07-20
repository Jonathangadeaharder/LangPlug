#!/usr/bin/env python3
"""
Example pipeline configurations for the unified subtitle processor.

This file demonstrates how to create custom processing pipelines
for different use cases using the new modular architecture.
"""

from processing_steps import ProcessingContext, ProcessingPipeline
from concrete_processing_steps import (
    PreviewTranscriptionStep,
    FullTranscriptionStep,
    A1FilterStep,
    TranslationStep,
    PreviewProcessingStep
)
from shared_utils.model_utils import ModelManager

def create_quick_pipeline() -> ProcessingPipeline:
    """Create a quick pipeline for fast transcription only.
    
    Use case: When you only need basic subtitles without filtering or translation.
    """
    steps = [
        FullTranscriptionStep()
    ]
    return ProcessingPipeline(steps)

def create_learning_pipeline() -> ProcessingPipeline:
    """Create a pipeline focused on language learning.
    
    Use case: Extract vocabulary for German language learners.
    """
    steps = [
        FullTranscriptionStep(),
        A1FilterStep()  # Only filter, no translation
    ]
    return ProcessingPipeline(steps)

def create_full_pipeline() -> ProcessingPipeline:
    """Create a complete pipeline with all processing steps.
    
    Use case: Full subtitle processing with preview, filtering, and translation.
    """
    steps = [
        PreviewTranscriptionStep(),
        PreviewProcessingStep(),
        FullTranscriptionStep(),
        A1FilterStep(),
        TranslationStep()
    ]
    return ProcessingPipeline(steps)

def create_translation_only_pipeline() -> ProcessingPipeline:
    """Create a pipeline for translating existing subtitles.
    
    Use case: When you already have subtitles and only need translation.
    Note: This would require a different context setup with existing subtitle files.
    """
    steps = [
        TranslationStep()
    ]
    return ProcessingPipeline(steps)

def create_batch_processing_pipeline() -> ProcessingPipeline:
    """Create a pipeline optimized for batch processing multiple videos.
    
    Use case: Processing many videos efficiently without preview steps.
    """
    steps = [
        FullTranscriptionStep(),
        A1FilterStep(),
        TranslationStep()
    ]
    return ProcessingPipeline(steps)

def example_usage():
    """Example of how to use custom pipeline configurations."""
    
    # Initialize model manager
    model_manager = ModelManager()
    
    # Example video file
    video_file = "/path/to/your/video.mp4"
    
    # Create processing context
    context = ProcessingContext(
        video_file=video_file,
        model_manager=model_manager,
        language="de",  # German
        src_lang="de",
        tgt_lang="es",  # Translate to Spanish
        no_preview=False
    )
    
    # Choose your pipeline based on needs
    pipeline_configs = {
        "quick": create_quick_pipeline(),
        "learning": create_learning_pipeline(),
        "full": create_full_pipeline(),
        "batch": create_batch_processing_pipeline()
    }
    
    # Select pipeline (change this based on your needs)
    selected_pipeline = "full"  # or "quick", "learning", "batch"
    
    pipeline = pipeline_configs[selected_pipeline]
    
    print(f"Executing {selected_pipeline} pipeline...")
    success = pipeline.execute(context)
    
    if success:
        print("Pipeline completed successfully!")
        print(f"Results:")
        print(f"  - Full subtitles: {context.full_srt}")
        print(f"  - Filtered subtitles: {context.filtered_srt}")
        print(f"  - Translated subtitles: {context.translated_srt}")
    else:
        print("Pipeline execution failed.")
    
    # Cleanup
    model_manager.cleanup_all_models()

if __name__ == "__main__":
    example_usage()