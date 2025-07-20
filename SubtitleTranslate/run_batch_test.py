#!/usr/bin/env python3
"""
Quick runner script for batch speed testing
This script runs the batch speed test with predefined settings
"""

import os
import sys
from batch_speed_test import BatchSpeedTester
from rich.console import Console

console = Console()

def quick_test():
    """Run a quick batch speed test with smaller batch sizes"""
    subtitle_path = r"c:\Users\Jonandrop\IdeaProjects\SubtitleTranslate\Episode 1 Staffel 1 von Call the Midwife - Ruf des Lebens S to -.srt"
    
    console.print("[bold blue]Quick Batch Speed Test - German to Spanish[/bold blue]")
    
    # Check if file exists
    if not os.path.exists(subtitle_path):
        console.print(f"[bold red]File not found: {subtitle_path}[/bold red]")
        return
    
    # Initialize tester
    tester = BatchSpeedTester('de', 'es')
    
    # Load model
    if not tester.load_model():
        console.print("[bold red]Failed to load model[/bold red]")
        return
    
    # Quick test with smaller batch sizes
    batch_sizes = [1, 2, 4, 8, 16]
    num_runs = 2
    
    console.print(f"[bold yellow]Testing batch sizes: {batch_sizes}[/bold yellow]")
    console.print(f"[bold yellow]Number of runs per batch: {num_runs}[/bold yellow]")
    
    # Run test
    results = tester.run_speed_test(subtitle_path, batch_sizes, num_runs)
    
    if results:
        # Display results
        tester.display_results(results)
        optimal_batch = tester.find_optimal_batch_size(results)
        
        # Create simple plot
        plot_path = os.path.join(os.path.dirname(subtitle_path), "quick_batch_test.png")
        tester.plot_results(results, plot_path)
        
        console.print(f"\n[bold green]Quick test completed! Optimal batch size: {optimal_batch}[/bold green]")
    else:
        console.print("[bold red]No results obtained[/bold red]")

def comprehensive_test():
    """Run a comprehensive batch speed test"""
    subtitle_path = r"c:\Users\Jonandrop\IdeaProjects\SubtitleTranslate\Episode 1 Staffel 1 von Call the Midwife - Ruf des Lebens S to -.srt"
    
    console.print("[bold blue]Comprehensive Batch Speed Test - German to Spanish[/bold blue]")
    
    # Check if file exists
    if not os.path.exists(subtitle_path):
        console.print(f"[bold red]File not found: {subtitle_path}[/bold red]")
        return
    
    # Initialize tester
    tester = BatchSpeedTester('de', 'es')
    
    # Load model
    if not tester.load_model():
        console.print("[bold red]Failed to load model[/bold red]")
        return
    
    # Comprehensive test with more batch sizes
    batch_sizes = [1, 2, 4, 8, 16, 32, 64, 128]
    num_runs = 3
    
    console.print(f"[bold yellow]Testing batch sizes: {batch_sizes}[/bold yellow]")
    console.print(f"[bold yellow]Number of runs per batch: {num_runs}[/bold yellow]")
    
    # Run test
    results = tester.run_speed_test(subtitle_path, batch_sizes, num_runs)
    
    if results:
        # Display results
        tester.display_results(results)
        optimal_batch = tester.find_optimal_batch_size(results)
        
        # Create detailed plot
        plot_path = os.path.join(os.path.dirname(subtitle_path), "comprehensive_batch_test.png")
        tester.plot_results(results, plot_path)
        
        # Save detailed results
        results_path = os.path.join(os.path.dirname(subtitle_path), "comprehensive_results.txt")
        with open(results_path, 'w', encoding='utf-8') as f:
            f.write("Comprehensive Batch Speed Test Results\n")
            f.write("=" * 40 + "\n\n")
            
            baseline_time = results[1]['avg_time'] if 1 in results else None
            
            for batch_size in sorted(results.keys()):
                data = results[batch_size]
                speedup = baseline_time / data['avg_time'] if baseline_time else 1.0
                f.write(f"Batch Size {batch_size}:\n")
                f.write(f"  Average Time: {data['avg_time']:.2f}s\n")
                f.write(f"  Standard Deviation: {data['std_time']:.2f}s\n")
                f.write(f"  Throughput: {data['texts_per_second']:.2f} texts/second\n")
                f.write(f"  Speedup: {speedup:.2f}x\n\n")
            
            f.write(f"Optimal Batch Size: {optimal_batch}\n")
        
        console.print(f"\n[bold green]Comprehensive test completed!\nOptimal batch size: {optimal_batch}\nResults saved to: {results_path}[/bold green]")
    else:
        console.print("[bold red]No results obtained[/bold red]")

def main():
    """Main function with user choice"""
    console.print("[bold cyan]Batch Speed Test Runner[/bold cyan]")
    console.print("\nChoose test type:")
    console.print("1. Quick test (batch sizes 1-16, 2 runs each)")
    console.print("2. Comprehensive test (batch sizes 1-128, 3 runs each)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == '1':
            quick_test()
        elif choice == '2':
            comprehensive_test()
        else:
            console.print("[bold red]Invalid choice. Running quick test by default.[/bold red]")
            quick_test()
            
    except KeyboardInterrupt:
        console.print("\n[bold red]Test cancelled by user.[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    main()