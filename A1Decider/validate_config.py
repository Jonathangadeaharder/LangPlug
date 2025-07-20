#!/usr/bin/env python3
"""
Configuration Validation Script for A1Decider

This script validates the centralized configuration and provides
detailed information about the system setup.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text

try:
    from config import get_config, AppConfig
except ImportError:
    print("Error: Could not import config module. Make sure config.py is in the same directory.")
    sys.exit(1)

console = Console()

def check_file_exists(file_path: str) -> tuple[bool, str]:
    """Check if a file exists and return status with details."""
    if os.path.exists(file_path):
        try:
            size = os.path.getsize(file_path)
            return True, f"✓ ({size} bytes)"
        except OSError:
            return False, "✗ (access denied)"
    else:
        return False, "✗ (not found)"

def check_directory_exists(dir_path: str) -> tuple[bool, str]:
    """Check if a directory exists and return status with details."""
    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            try:
                items = len(os.listdir(dir_path))
                return True, f"✓ ({items} items)"
            except OSError:
                return True, "✓ (access denied)"
        else:
            return False, "✗ (not a directory)"
    else:
        return False, "✗ (not found)"

def validate_word_lists(config: AppConfig) -> None:
    """Validate word list files."""
    console.print("\n[bold blue]Word List Files Validation[/bold blue]")
    
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("File Type", style="cyan")
    table.add_column("File Path", style="white")
    table.add_column("Status", style="green")
    table.add_column("Word Count", style="yellow")
    
    word_lists = {
        "A1 Words": config.word_lists.a1_words,
        "Character Words": config.word_lists.charaktere_words,
        "Giulia Words": config.word_lists.giuliwords,
        "Brands": config.word_lists.brands,
        "Onomatopoeia": config.word_lists.onomatopoeia,
        "Interjections": config.word_lists.interjections
    }
    
    total_words = 0
    for file_type, file_path in word_lists.items():
        exists, status = check_file_exists(file_path)
        word_count = "N/A"
        
        if exists:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    words = [line.strip() for line in f if line.strip()]
                    word_count = str(len(words))
                    total_words += len(words)
            except Exception as e:
                word_count = f"Error: {e}"
        
        table.add_row(file_type, file_path, status, word_count)
    
    console.print(table)
    console.print(f"\n[bold green]Total words across all lists: {total_words}[/bold green]")

def validate_directories(config: AppConfig) -> None:
    """Validate directory structure."""
    console.print("\n[bold blue]Directory Structure Validation[/bold blue]")
    
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Directory Type", style="cyan")
    table.add_column("Directory Path", style="white")
    table.add_column("Status", style="green")
    
    directories = {
        "Base Directory": config.file_paths.base_dir,
        "Output Directory": config.file_paths.output_dir,
        "Temp Directory": config.file_paths.temp_dir
    }
    
    for dir_type, dir_path in directories.items():
        exists, status = check_directory_exists(dir_path)
        table.add_row(dir_type, dir_path, status)
    
    console.print(table)

def validate_models(config: AppConfig) -> None:
    """Validate model configuration and availability."""
    console.print("\n[bold blue]Model Configuration Validation[/bold blue]")
    
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Model Type", style="cyan")
    table.add_column("Model Name", style="white")
    table.add_column("Status", style="green")
    
    # Check spaCy model
    spacy_status = "✗ (not available)"
    try:
        import spacy
        try:
            nlp = spacy.load(config.models.spacy_model)
            spacy_status = "✓ (loaded successfully)"
        except OSError:
            spacy_status = "✗ (model not found)"
    except ImportError:
        spacy_status = "✗ (spaCy not installed)"
    
    table.add_row("spaCy NLP", config.models.spacy_model, spacy_status)
    
    # Check Whisper model
    whisper_status = "✗ (not available)"
    try:
        import whisper
        whisper_status = "✓ (Whisper available)"
    except ImportError:
        whisper_status = "✗ (Whisper not installed)"
    
    table.add_row("Whisper ASR", config.models.whisper_model, whisper_status)
    
    # Check translation model
    translation_status = "✗ (not available)"
    try:
        from transformers import pipeline
        translation_status = "✓ (Transformers available)"
    except ImportError:
        translation_status = "✗ (Transformers not installed)"
    
    table.add_row("Translation", config.models.translation_model, translation_status)
    
    console.print(table)

def validate_api_config(config: AppConfig) -> None:
    """Validate API configuration."""
    console.print("\n[bold blue]API Configuration[/bold blue]")
    
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="green")
    
    # Check host and port
    table.add_row("Host", config.api.host, "✓")
    table.add_row("Port", str(config.api.port), "✓")
    table.add_row("Debug Mode", str(config.api.debug), "✓")
    table.add_row("CORS Origins", str(len(config.api.cors_origins)), "✓")
    table.add_row("Max File Size", f"{config.api.max_file_size // (1024*1024)} MB", "✓")
    
    console.print(table)

def show_environment_variables() -> None:
    """Show relevant environment variables."""
    console.print("\n[bold blue]Environment Variables[/bold blue]")
    
    env_vars = {
        "A1_DECIDER_PATH": "Base path override",
        "API_HOST": "API host override",
        "API_PORT": "API port override",
        "API_DEBUG": "API debug mode override",
        "WHISPER_MODEL": "Whisper model override",
        "SPACY_MODEL": "spaCy model override",
        "DEVICE": "Device override (cpu/cuda)"
    }
    
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Variable", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Current Value", style="yellow")
    
    for var_name, description in env_vars.items():
        value = os.getenv(var_name, "[not set]")
        table.add_row(var_name, description, value)
    
    console.print(table)

def show_configuration_summary(config: AppConfig) -> None:
    """Show a summary of the current configuration."""
    console.print("\n[bold blue]Configuration Summary[/bold blue]")
    
    # Validation results
    validation = config.validate_config()
    
    # Count successful validations
    success_count = sum(1 for status in validation.values() if status)
    total_count = len(validation)
    
    # Create summary panel
    summary_text = Text()
    summary_text.append(f"Configuration Status: ", style="bold")
    
    if success_count == total_count:
        summary_text.append("✓ All components validated", style="bold green")
    else:
        summary_text.append(f"⚠ {success_count}/{total_count} components validated", style="bold yellow")
    
    summary_text.append(f"\n\nBase Directory: {config.file_paths.base_dir}")
    summary_text.append(f"\nWord Lists: {len(config.word_lists.get_all_files())} files configured")
    summary_text.append(f"\nAPI Endpoint: http://{config.api.host}:{config.api.port}")
    summary_text.append(f"\nProcessing Batch Size: {config.processing.batch_size}")
    
    panel = Panel(
        summary_text,
        title="A1Decider Configuration",
        border_style="blue",
        box=box.ROUNDED
    )
    
    console.print(panel)

def main():
    """Main validation function."""
    console.print("[bold magenta]A1Decider Configuration Validation[/bold magenta]")
    console.print("[italic]Validating centralized configuration system...[/italic]\n")
    
    try:
        # Load configuration
        config = get_config()
        
        # Show configuration summary
        show_configuration_summary(config)
        
        # Validate components
        validate_word_lists(config)
        validate_directories(config)
        validate_models(config)
        validate_api_config(config)
        show_environment_variables()
        
        # Final status
        validation_results = config.validate_config()
        failed_components = [name for name, status in validation_results.items() if not status]
        
        if not failed_components:
            console.print("\n[bold green]✓ All configuration components are valid![/bold green]")
            console.print("[green]The A1Decider system is ready to use.[/green]")
        else:
            console.print(f"\n[bold yellow]⚠ Configuration issues found:[/bold yellow]")
            for component in failed_components:
                console.print(f"  • {component}")
            console.print("\n[yellow]Please address these issues before running the system.[/yellow]")
    
    except Exception as e:
        console.print(f"\n[bold red]Error during validation: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()