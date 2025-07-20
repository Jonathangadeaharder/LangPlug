#!/usr/bin/env python3
"""
LEGACY SCRIPT - DEPRECATED

This script has been refactored to use the ProcessingPipeline architecture.
Please use a1decider_pipeline.py instead.

This file is kept for backward compatibility but will redirect to the new implementation.
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel

# Rich Console initialization
console = Console()

def main():
    """Legacy main function - redirects to pipeline version."""
    console.print(Panel(
        "[bold yellow]DEPRECATED SCRIPT[/bold yellow]\n\n"
        "This script has been refactored to use the ProcessingPipeline architecture.\n"
        "Please use [bold cyan]a1decider_pipeline.py[/bold cyan] instead.\n\n"
        "Redirecting to the new pipeline version...",
        title="Legacy Script Notice",
        style="bold yellow"
    ))
    
    # Try to run the new pipeline version
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pipeline_script = os.path.join(script_dir, "a1decider_pipeline.py")
        
        if os.path.exists(pipeline_script):
            console.print("[bold green]Launching pipeline version...[/bold green]")
            os.system(f'python "{pipeline_script}"')
        else:
            console.print("[bold red]Pipeline version not found. Please run a1decider_pipeline.py manually.[/bold red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error launching pipeline version: {e}[/bold red]")
        console.print("[bold yellow]Please run a1decider_pipeline.py manually.[/bold yellow]")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
        sys.exit(1)
