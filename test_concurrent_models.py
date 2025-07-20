#!/usr/bin/env python3
"""
Test script to verify concurrency-safe ModelManager implementation.

This script tests the thread-safe model access methods and ensures
that multiple threads can safely access models without race conditions.
"""

import threading
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add A1Decider to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'A1Decider'))

from shared_utils.model_utils import ModelManager
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def test_whisper_model_access(thread_id: int, iterations: int = 3):
    """Test thread-safe Whisper model access."""
    manager = ModelManager()
    results = []
    
    for i in range(iterations):
        try:
            with manager.get_whisper_model_safe() as model:
                console.print(f"[green]Thread {thread_id}: Got Whisper model (iteration {i+1})[/green]")
                # Simulate some work
                time.sleep(0.5)
                results.append(f"Thread {thread_id} - Whisper iteration {i+1}: SUCCESS")
        except Exception as e:
            results.append(f"Thread {thread_id} - Whisper iteration {i+1}: ERROR - {e}")
            console.print(f"[red]Thread {thread_id}: Error accessing Whisper model: {e}[/red]")
    
    return results

def test_spacy_model_access(thread_id: int, iterations: int = 3):
    """Test thread-safe SpaCy model access."""
    manager = ModelManager()
    results = []
    
    for i in range(iterations):
        try:
            with manager.get_spacy_model_safe() as nlp:
                console.print(f"[blue]Thread {thread_id}: Got SpaCy model (iteration {i+1})[/blue]")
                # Test basic functionality
                doc = nlp("test sentence")
                tokens = [token.text for token in doc]
                time.sleep(0.3)
                results.append(f"Thread {thread_id} - SpaCy iteration {i+1}: SUCCESS - {len(tokens)} tokens")
        except Exception as e:
            results.append(f"Thread {thread_id} - SpaCy iteration {i+1}: ERROR - {e}")
            console.print(f"[red]Thread {thread_id}: Error accessing SpaCy model: {e}[/red]")
    
    return results

def test_translation_model_access(thread_id: int, iterations: int = 2):
    """Test thread-safe translation model access."""
    manager = ModelManager()
    results = []
    
    for i in range(iterations):
        try:
            with manager.get_translation_model_safe("de", "es") as (model, tokenizer):
                console.print(f"[yellow]Thread {thread_id}: Got translation model (iteration {i+1})[/yellow]")
                # Simulate some work
                time.sleep(0.4)
                results.append(f"Thread {thread_id} - Translation iteration {i+1}: SUCCESS")
        except Exception as e:
            results.append(f"Thread {thread_id} - Translation iteration {i+1}: ERROR - {e}")
            console.print(f"[red]Thread {thread_id}: Error accessing translation model: {e}[/red]")
    
    return results

def test_model_usage_stats():
    """Test model usage statistics."""
    manager = ModelManager()
    
    console.print("\n[bold cyan]Testing model usage statistics...[/bold cyan]")
    
    # Get initial stats
    stats = manager.get_model_usage_stats()
    console.print(f"Initial stats: {stats}")
    
    # Test concurrent access and stats
    def access_model_and_check_stats(model_type: str):
        if model_type == "whisper":
            with manager.get_whisper_model_safe() as model:
                stats = manager.get_model_usage_stats()
                console.print(f"During Whisper access: {stats['current_usage']}")
                time.sleep(1)
        elif model_type == "spacy":
            with manager.get_spacy_model_safe() as nlp:
                stats = manager.get_model_usage_stats()
                console.print(f"During SpaCy access: {stats['current_usage']}")
                time.sleep(1)
    
    # Run concurrent access
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(access_model_and_check_stats, "whisper"),
            executor.submit(access_model_and_check_stats, "spacy")
        ]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                console.print(f"[red]Error in stats test: {e}[/red]")
    
    # Final stats
    final_stats = manager.get_model_usage_stats()
    console.print(f"Final stats: {final_stats}")

def test_exclusive_access():
    """Test exclusive model access."""
    manager = ModelManager()
    
    console.print("\n[bold magenta]Testing exclusive model access...[/bold magenta]")
    
    def try_exclusive_access(thread_id: int):
        try:
            console.print(f"Thread {thread_id}: Requesting exclusive access...")
            with manager.exclusive_model_access("whisper", timeout=5):
                console.print(f"[green]Thread {thread_id}: Got exclusive access![/green]")
                time.sleep(2)
                console.print(f"[green]Thread {thread_id}: Releasing exclusive access[/green]")
        except Exception as e:
            console.print(f"[red]Thread {thread_id}: Failed to get exclusive access: {e}[/red]")
    
    # Test with multiple threads trying to get exclusive access
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(try_exclusive_access, i) for i in range(3)]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                console.print(f"[red]Error in exclusive access test: {e}[/red]")

def main():
    """Run all concurrency tests."""
    console.print("[bold green]Starting ModelManager Concurrency Tests[/bold green]\n")
    
    # Test 1: Concurrent model access
    console.print("[bold cyan]Test 1: Concurrent Model Access[/bold cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running concurrent model tests...", total=None)
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit various model access tests
            futures = []
            
            # Whisper tests
            for i in range(2):
                futures.append(executor.submit(test_whisper_model_access, f"W{i}", 2))
            
            # SpaCy tests
            for i in range(2):
                futures.append(executor.submit(test_spacy_model_access, f"S{i}", 2))
            
            # Translation tests
            for i in range(2):
                futures.append(executor.submit(test_translation_model_access, f"T{i}", 1))
            
            # Collect results
            all_results = []
            for future in as_completed(futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    console.print(f"[red]Thread execution error: {e}[/red]")
        
        progress.update(task, completed=True)
    
    # Print results summary
    console.print("\n[bold cyan]Test Results Summary:[/bold cyan]")
    for result in all_results:
        if "ERROR" in result:
            console.print(f"[red]{result}[/red]")
        else:
            console.print(f"[green]{result}[/green]")
    
    # Test 2: Model usage statistics
    test_model_usage_stats()
    
    # Test 3: Exclusive access
    test_exclusive_access()
    
    console.print("\n[bold green]All concurrency tests completed![/bold green]")

if __name__ == "__main__":
    main()