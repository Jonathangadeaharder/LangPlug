import os
import sys
import traceback
import argparse
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from rich.console import Console
from moviepy import VideoFileClip

# Add the parent directory to the system path to allow imports from shared_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_utils.model_utils import ModelManager
from processing_steps import ProcessingContext, ProcessingPipeline
from concrete_processing_steps import (
    PreviewTranscriptionStep,
    FullTranscriptionStep,
    A1FilterStep,
    TranslationStep,
    PreviewProcessingStep
)

# Rich Console initialization
console = Console()

# Legacy functions have been replaced by ProcessingStep classes
# See concrete_processing_steps.py for the new implementation

# All legacy functions have been replaced by ProcessingStep classes
# See concrete_processing_steps.py for the new modular implementation

def create_processing_pipeline(include_preview: bool = True) -> ProcessingPipeline:
    """Create and configure the processing pipeline.
    
    Args:
        include_preview: Whether to include preview processing steps
        
    Returns:
        ProcessingPipeline: Configured pipeline with processing steps
    """
    steps = []
    
    if include_preview:
        steps.append(PreviewTranscriptionStep())
        steps.append(PreviewProcessingStep())
    
    steps.extend([
        FullTranscriptionStep(),
        A1FilterStep(),
        TranslationStep()
    ])
    
    return ProcessingPipeline(steps)

def main():
    """Main function to orchestrate the subtitle processing pipeline."""
    parser = argparse.ArgumentParser(description='Unified Subtitle Processor')
    parser.add_argument('--no-preview', action='store_true', help='Skip creating 10-minute preview for long videos')
    parser.add_argument('--language', default='de', help='Source language for transcription (default: de)')
    parser.add_argument('--src-lang', default='de', help='Source language for translation (default: de)')
    parser.add_argument('--tgt-lang', default='es', help='Target language for translation (default: es)')
    args = parser.parse_args()
    
    console.print("[bold green]Welcome to the Unified Subtitle Processor![/bold green]")
    
    Tk().withdraw()
    video_files = askopenfilename(
        title="Select Video Files",
        filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv"), ("All Files", "*.* ")],
        multiple=True
    )
    
    if not video_files:
        console.print("[bold red]No video files selected. Exiting.[/bold red]")
        return
    
    # Initialize model manager
    model_manager = ModelManager()
    
    # Create processing pipeline
    pipeline = create_processing_pipeline(include_preview=not args.no_preview)
    
    # Process each video file
    for i, video_file in enumerate(video_files):
        console.print(f"\n[bold cyan]Processing ({i+1}/{len(video_files)}): {os.path.basename(video_file)}[/bold cyan]")
        
        try:
            # Create processing context
            context = ProcessingContext(
                video_file=video_file,
                model_manager=model_manager,
                language=args.language,
                src_lang=args.src_lang,
                tgt_lang=args.tgt_lang,
                no_preview=args.no_preview
            )
            
            # Execute pipeline
            success = pipeline.execute(context)
            
            if success:
                console.print(f"\n[bold green]All processing complete for: {os.path.basename(video_file)}[/bold green]")
            else:
                console.print(f"[bold red]Processing failed for: {os.path.basename(video_file)}[/bold red]")
            
        except Exception as e:
            console.print(f"[bold red]Error processing {video_file}: {e}[/bold red]")
            traceback.print_exc()
        
        # Clean up memory between videos
        if len(video_files) > 1 and i < len(video_files) - 1:
            console.print("\n[bold yellow]Cleaning up memory before next video...[/bold yellow]")
            model_manager.cleanup_cuda_memory()
    
    console.print("\n[bold green]All videos processed![/bold green]")
    model_manager.cleanup_all_models()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        traceback.print_exc()
        sys.exit(1)
