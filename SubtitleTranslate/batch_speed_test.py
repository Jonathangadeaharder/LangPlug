import os
import sys
import time
import torch
import pysrt
from transformers import MarianMTModel, MarianTokenizer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple

console = Console()

class BatchSpeedTester:
    def __init__(self, src_lang: str = 'de', tgt_lang: str = 'es'):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.model = None
        self.tokenizer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
    def load_model(self):
        """Load the translation model"""
        try:
            model_name = f'Helsinki-NLP/opus-mt-tc-big-{self.src_lang}-{self.tgt_lang}'
            console.print(f"[bold blue]Loading model: {model_name}[/bold blue]")
            
            self.tokenizer = MarianTokenizer.from_pretrained(model_name)
            self.model = MarianMTModel.from_pretrained(model_name).to(self.device)
            
            console.print(f"[bold green]Model loaded successfully on {self.device}[/bold green]")
            return True
        except Exception as e:
            console.print(f"[bold red]Error loading model: {e}[/bold red]")
            return False
    
    def load_subtitle_texts(self, subtitle_path: str) -> List[str]:
        """Load subtitle texts from SRT file"""
        try:
            subs = pysrt.open(subtitle_path, encoding='utf-8')
            texts = [sub.text.strip() for sub in subs if sub.text.strip()]
            console.print(f"[bold blue]Loaded {len(texts)} subtitle entries[/bold blue]")
            return texts
        except Exception as e:
            console.print(f"[bold red]Error loading subtitle file: {e}[/bold red]")
            return []
    
    def translate_batch(self, texts: List[str], batch_size: int) -> Tuple[List[str], float]:
        """Translate texts in batches and return translations with timing"""
        translations = []
        start_time = time.time()
        
        # Process texts in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch_texts, 
                return_tensors='pt', 
                padding=True, 
                truncation=True,
                max_length=512
            ).to(self.device)
            
            # Generate translations
            with torch.no_grad():
                translated = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True
                )
            
            # Decode translations
            batch_translations = self.tokenizer.batch_decode(
                translated, 
                skip_special_tokens=True
            )
            
            translations.extend(batch_translations)
        
        total_time = time.time() - start_time
        return translations, total_time
    
    def run_speed_test(self, subtitle_path: str, batch_sizes: List[int] = None, num_runs: int = 3) -> dict:
        """Run speed tests with different batch sizes"""
        if batch_sizes is None:
            batch_sizes = [1, 2, 4, 8, 16, 32, 64]
        
        # Load subtitle texts
        texts = self.load_subtitle_texts(subtitle_path)
        if not texts:
            return {}
        
        # Limit to first 100 subtitles for testing (adjust as needed)
        test_texts = texts[:100]
        console.print(f"[bold yellow]Testing with {len(test_texts)} subtitle entries[/bold yellow]")
        
        results = {}
        
        with Progress() as progress:
            main_task = progress.add_task("[green]Running batch tests...", total=len(batch_sizes))
            
            for batch_size in batch_sizes:
                console.print(f"\n[bold cyan]Testing batch size: {batch_size}[/bold cyan]")
                
                batch_times = []
                
                # Run multiple times for average
                for run in range(num_runs):
                    console.print(f"  Run {run + 1}/{num_runs}")
                    
                    # Clear GPU cache
                    if self.device == 'cuda':
                        torch.cuda.empty_cache()
                    
                    translations, elapsed_time = self.translate_batch(test_texts, batch_size)
                    batch_times.append(elapsed_time)
                    
                    console.print(f"    Time: {elapsed_time:.2f}s")
                
                # Calculate statistics
                avg_time = np.mean(batch_times)
                std_time = np.std(batch_times)
                texts_per_second = len(test_texts) / avg_time
                
                results[batch_size] = {
                    'avg_time': avg_time,
                    'std_time': std_time,
                    'texts_per_second': texts_per_second,
                    'all_times': batch_times
                }
                
                console.print(f"  [bold green]Average time: {avg_time:.2f}±{std_time:.2f}s[/bold green]")
                console.print(f"  [bold green]Texts/second: {texts_per_second:.2f}[/bold green]")
                
                progress.update(main_task, advance=1)
        
        return results
    
    def display_results(self, results: dict):
        """Display results in a formatted table"""
        table = Table(title="Batch Size Performance Results")
        table.add_column("Batch Size", style="cyan")
        table.add_column("Avg Time (s)", style="green")
        table.add_column("Std Dev (s)", style="yellow")
        table.add_column("Texts/Second", style="magenta")
        table.add_column("Speedup vs Batch=1", style="red")
        
        baseline_time = results[1]['avg_time'] if 1 in results else None
        
        for batch_size in sorted(results.keys()):
            data = results[batch_size]
            speedup = f"{baseline_time / data['avg_time']:.2f}x" if baseline_time else "N/A"
            
            table.add_row(
                str(batch_size),
                f"{data['avg_time']:.2f}",
                f"{data['std_time']:.2f}",
                f"{data['texts_per_second']:.2f}",
                speedup
            )
        
        console.print(table)
    
    def plot_results(self, results: dict, save_path: str = None):
        """Create performance plots"""
        batch_sizes = sorted(results.keys())
        avg_times = [results[bs]['avg_time'] for bs in batch_sizes]
        texts_per_second = [results[bs]['texts_per_second'] for bs in batch_sizes]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Average time vs batch size
        ax1.plot(batch_sizes, avg_times, 'b-o', linewidth=2, markersize=8)
        ax1.set_xlabel('Batch Size')
        ax1.set_ylabel('Average Time (seconds)')
        ax1.set_title('Translation Time vs Batch Size')
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log', base=2)
        
        # Plot 2: Throughput vs batch size
        ax2.plot(batch_sizes, texts_per_second, 'r-o', linewidth=2, markersize=8)
        ax2.set_xlabel('Batch Size')
        ax2.set_ylabel('Texts per Second')
        ax2.set_title('Translation Throughput vs Batch Size')
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log', base=2)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            console.print(f"[bold green]Plot saved to: {save_path}[/bold green]")
        
        plt.show()
    
    def find_optimal_batch_size(self, results: dict) -> int:
        """Find the optimal batch size based on throughput"""
        best_batch_size = max(results.keys(), key=lambda bs: results[bs]['texts_per_second'])
        best_throughput = results[best_batch_size]['texts_per_second']
        
        console.print(f"\n[bold green]Optimal batch size: {best_batch_size}[/bold green]")
        console.print(f"[bold green]Best throughput: {best_throughput:.2f} texts/second[/bold green]")
        
        return best_batch_size

def main():
    # Configuration
    subtitle_path = r"c:\Users\Jonandrop\IdeaProjects\SubtitleTranslate\Episode 1 Staffel 1 von Call the Midwife - Ruf des Lebens S to -.srt"
    src_lang = 'de'  # German
    tgt_lang = 'es'  # Spanish
    
    # Batch sizes to test
    batch_sizes = [1, 2, 4, 8, 16, 32, 64]
    num_runs = 3  # Number of runs per batch size for averaging
    
    console.print("[bold blue]Subtitle Translation Batch Speed Test[/bold blue]")
    console.print(f"[bold yellow]Source: {src_lang} -> Target: {tgt_lang}[/bold yellow]")
    console.print(f"[bold yellow]Subtitle file: {os.path.basename(subtitle_path)}[/bold yellow]")
    
    # Check if subtitle file exists
    if not os.path.exists(subtitle_path):
        console.print(f"[bold red]Subtitle file not found: {subtitle_path}[/bold red]")
        sys.exit(1)
    
    # Initialize tester
    tester = BatchSpeedTester(src_lang, tgt_lang)
    
    # Load model
    if not tester.load_model():
        sys.exit(1)
    
    # Run speed tests
    console.print(f"\n[bold blue]Running speed tests with batch sizes: {batch_sizes}[/bold blue]")
    results = tester.run_speed_test(subtitle_path, batch_sizes, num_runs)
    
    if not results:
        console.print("[bold red]No results obtained. Exiting.[/bold red]")
        sys.exit(1)
    
    # Display results
    console.print("\n[bold blue]Results Summary:[/bold blue]")
    tester.display_results(results)
    
    # Find optimal batch size
    optimal_batch_size = tester.find_optimal_batch_size(results)
    
    # Create plots
    plot_path = os.path.join(os.path.dirname(subtitle_path), "batch_speed_results.png")
    tester.plot_results(results, plot_path)
    
    # Save detailed results to file
    results_path = os.path.join(os.path.dirname(subtitle_path), "batch_speed_results.txt")
    with open(results_path, 'w', encoding='utf-8') as f:
        f.write("Subtitle Translation Batch Speed Test Results\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Source Language: {src_lang}\n")
        f.write(f"Target Language: {tgt_lang}\n")
        f.write(f"Subtitle File: {os.path.basename(subtitle_path)}\n")
        f.write(f"Device: {tester.device}\n")
        f.write(f"Number of runs per batch size: {num_runs}\n\n")
        
        f.write("Batch Size\tAvg Time (s)\tStd Dev (s)\tTexts/Second\tSpeedup\n")
        baseline_time = results[1]['avg_time'] if 1 in results else None
        
        for batch_size in sorted(results.keys()):
            data = results[batch_size]
            speedup = baseline_time / data['avg_time'] if baseline_time else 1.0
            f.write(f"{batch_size}\t{data['avg_time']:.2f}\t{data['std_time']:.2f}\t{data['texts_per_second']:.2f}\t{speedup:.2f}x\n")
        
        f.write(f"\nOptimal Batch Size: {optimal_batch_size}\n")
        f.write(f"Best Throughput: {results[optimal_batch_size]['texts_per_second']:.2f} texts/second\n")
    
    console.print(f"\n[bold green]Detailed results saved to: {results_path}[/bold green]")
    console.print("[bold blue]Speed test completed![/bold blue]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Test interrupted by user.[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
        sys.exit(1)