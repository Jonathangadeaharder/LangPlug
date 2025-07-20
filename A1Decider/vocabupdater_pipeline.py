#!/usr/bin/env python3
"""
Refactored vocabulary updater using ProcessingPipeline architecture.
This script replaces the manual vocabupdater.py with a pipeline-based approach.
"""

import sys
from rich.console import Console
from rich.panel import Panel

# Import pipeline components
from processing_steps import ProcessingPipeline, ProcessingContext
from concrete_processing_steps import VocabularyUpdateStep
from shared_utils.model_utils import ModelManager
from config import get_config

console = Console()

def main():
    """Main function using ProcessingPipeline for vocabulary updates."""
    try:
        console.print(Panel(
            "[bold blue]Vocabulary Updater - Pipeline Version[/bold blue]\n"
            "This tool updates your vocabulary with missing lemmas from known words.",
            title="Vocabulary Updater",
            style="bold cyan"
        ))
        
        # Initialize model manager
        model_manager = ModelManager()
        
        # Create processing context
        context = ProcessingContext(
            video_file="",  # Not needed for vocabulary update
            model_manager=model_manager,
            language="de"
        )
        
        # Create pipeline with vocabulary update step
        pipeline = ProcessingPipeline([
            VocabularyUpdateStep()
        ])
        
        # Execute pipeline
        success = pipeline.execute(context)
        
        if success:
            console.print(Panel(
                "[bold green]Vocabulary update completed successfully![/bold green]",
                title="Success",
                style="bold green"
            ))
        else:
            console.print(Panel(
                "[bold red]Vocabulary update failed![/bold red]",
                title="Error",
                style="bold red"
            ))
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        sys.exit(1)
    finally:
        # Cleanup
        if 'model_manager' in locals():
            model_manager.cleanup_cuda_memory()

if __name__ == "__main__":
    main()