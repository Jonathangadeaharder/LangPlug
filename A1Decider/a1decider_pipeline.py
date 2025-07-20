#!/usr/bin/env python3
"""
Refactored A1 Decider using ProcessingPipeline architecture.
This script replaces the manual a1decider.py with a pipeline-based approach.
"""

import sys
from rich.console import Console
from rich.panel import Panel

# Import pipeline components
from processing_steps import ProcessingPipeline, ProcessingContext
from concrete_processing_steps import A1DeciderStep
from shared_utils.model_utils import ModelManager
from config import get_config

console = Console()

def main():
    """Main function using ProcessingPipeline for A1 decision making."""
    try:
        console.print(Panel(
            "[bold blue]A1 Decider - Pipeline Version[/bold blue]\n"
            "Interactive vocabulary game to decide which words you know.\n"
            "Use arrow keys: ← (Don't know) / → (Know) / ↑ (Undo) / ↓ (Finish)",
            title="A1 Decider",
            style="bold cyan"
        ))
        
        # Initialize model manager
        model_manager = ModelManager()
        
        # Create processing context
        context = ProcessingContext(
            video_file="",  # Will be selected in the step if needed
            model_manager=model_manager,
            language="de"
        )
        
        # Create pipeline with A1 decider step
        pipeline = ProcessingPipeline([
            A1DeciderStep()
        ])
        
        # Execute pipeline
        success = pipeline.execute(context)
        
        if success:
            console.print(Panel(
                "[bold green]A1 decision session completed successfully![/bold green]",
                title="Success",
                style="bold green"
            ))
        else:
            console.print(Panel(
                "[bold red]A1 decision session failed![/bold red]",
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