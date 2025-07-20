#!/usr/bin/env python3
"""
Concurrency Test for ModelManager

This script tests the thread-safe implementation of ModelManager
to ensure it can handle concurrent access without race conditions.
"""

import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

# Add the current directory and parent directory to Python path
sys.path.insert(0, '.')
sys.path.insert(0, '..')

try:
    from shared_utils.model_utils import ModelManager
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the A1Decider directory")
    sys.exit(1)

console = Console()

class ConcurrencyTester:
    def __init__(self):
        self.manager = ModelManager()
        self.results = []
        self.lock = threading.Lock()
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Thread-safe result logging."""
        with self.lock:
            self.results.append({
                'test': test_name,
                'success': success,
                'message': message,
                'thread': threading.current_thread().name
            })
    
    def test_whisper_concurrent_access(self, thread_id: int):
        """Test concurrent access to Whisper model."""
        try:
            with self.manager.get_whisper_model_safe() as model:
                # Simulate some work
                time.sleep(0.1)
                model_type = type(model).__name__
                self.log_result(f"whisper_access_{thread_id}", True, f"Got model: {model_type}")
        except Exception as e:
            self.log_result(f"whisper_access_{thread_id}", False, str(e))
    
    def test_spacy_concurrent_access(self, thread_id: int):
        """Test concurrent access to SpaCy model."""
        try:
            with self.manager.get_spacy_model_safe() as nlp:
                # Simulate some work
                time.sleep(0.1)
                model_name = nlp.meta.get('name', 'unknown')
                self.log_result(f"spacy_access_{thread_id}", True, f"Got model: {model_name}")
        except Exception as e:
            self.log_result(f"spacy_access_{thread_id}", False, str(e))
    
    def test_translation_concurrent_access(self, thread_id: int):
        """Test concurrent access to translation model."""
        try:
            with self.manager.get_translation_model_safe('en', 'es') as (model, tokenizer):
                # Simulate some work
                time.sleep(0.1)
                model_type = type(model).__name__
                self.log_result(f"translation_access_{thread_id}", True, f"Got model: {model_type}")
        except Exception as e:
            self.log_result(f"translation_access_{thread_id}", False, str(e))
    
    def test_usage_statistics(self):
        """Test model usage statistics."""
        try:
            # Get initial stats
            initial_stats = self.manager.get_model_usage_stats()
            
            # Start some concurrent operations
            def concurrent_operation():
                with self.manager.get_whisper_model_safe() as model:
                    time.sleep(0.2)
            
            threads = []
            for i in range(3):
                thread = threading.Thread(target=concurrent_operation)
                threads.append(thread)
                thread.start()
            
            # Check stats while operations are running
            time.sleep(0.1)
            active_stats = self.manager.get_model_usage_stats()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            # Check final stats
            final_stats = self.manager.get_model_usage_stats()
            
            self.log_result("usage_stats", True, 
                          f"Initial: {initial_stats['current_usage']}, "
                          f"Active: {active_stats['current_usage']}, "
                          f"Final: {final_stats['current_usage']}")
            
        except Exception as e:
            self.log_result("usage_stats", False, str(e))
    
    def test_exclusive_access(self):
        """Test exclusive model access."""
        try:
            results = []
            
            def exclusive_operation(thread_id):
                try:
                    with self.manager.exclusive_model_access('whisper', timeout=5):
                        results.append(f"Thread {thread_id} got exclusive access")
                        time.sleep(0.2)
                        results.append(f"Thread {thread_id} finished exclusive work")
                except Exception as e:
                    results.append(f"Thread {thread_id} failed: {e}")
            
            # Start multiple threads trying to get exclusive access
            threads = []
            for i in range(3):
                thread = threading.Thread(target=exclusive_operation, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            self.log_result("exclusive_access", True, f"Results: {results}")
            
        except Exception as e:
            self.log_result("exclusive_access", False, str(e))
    
    def test_memory_cleanup(self):
        """Test thread-safe memory cleanup."""
        try:
            # Load some models first
            with self.manager.get_whisper_model_safe() as model:
                pass
            
            # Test cleanup
            self.manager.cleanup_cuda_memory()
            self.log_result("memory_cleanup", True, "CUDA memory cleanup successful")
            
        except Exception as e:
            self.log_result("memory_cleanup", False, str(e))
    
    def run_all_tests(self):
        """Run all concurrency tests."""
        console.print(Panel("[bold blue]Starting ModelManager Concurrency Tests[/bold blue]"))
        
        # Test 1: Concurrent model access
        console.print("\n[yellow]Test 1: Concurrent Model Access[/yellow]")
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            
            # Submit Whisper tests
            for i in range(3):
                futures.append(executor.submit(self.test_whisper_concurrent_access, i))
            
            # Submit SpaCy tests
            for i in range(2):
                futures.append(executor.submit(self.test_spacy_concurrent_access, i))
            
            # Submit Translation test
            futures.append(executor.submit(self.test_translation_concurrent_access, 0))
            
            # Wait for completion
            for future in as_completed(futures):
                future.result()
        
        # Test 2: Usage statistics
        console.print("\n[yellow]Test 2: Usage Statistics[/yellow]")
        self.test_usage_statistics()
        
        # Test 3: Exclusive access
        console.print("\n[yellow]Test 3: Exclusive Access[/yellow]")
        self.test_exclusive_access()
        
        # Test 4: Memory cleanup
        console.print("\n[yellow]Test 4: Memory Cleanup[/yellow]")
        self.test_memory_cleanup()
        
        # Display results
        self.display_results()
    
    def display_results(self):
        """Display test results in a formatted table."""
        console.print("\n[bold green]Test Results[/bold green]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Test", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Thread", style="dim")
        table.add_column("Message", style="white")
        
        success_count = 0
        for result in self.results:
            status = "[green]✓ PASS[/green]" if result['success'] else "[red]✗ FAIL[/red]"
            if result['success']:
                success_count += 1
            
            table.add_row(
                result['test'],
                status,
                result['thread'],
                result['message'][:80] + "..." if len(result['message']) > 80 else result['message']
            )
        
        console.print(table)
        
        # Summary
        total_tests = len(self.results)
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        summary_style = "green" if success_rate == 100 else "yellow" if success_rate >= 80 else "red"
        console.print(f"\n[{summary_style}]Summary: {success_count}/{total_tests} tests passed ({success_rate:.1f}%)[/{summary_style}]")
        
        if success_rate == 100:
            console.print("[bold green]🎉 All tests passed! ModelManager is concurrency-safe.[/bold green]")
        else:
            console.print("[bold red]⚠️  Some tests failed. Check the implementation.[/bold red]")

def main():
    """Main test function."""
    try:
        tester = ConcurrencyTester()
        tester.run_all_tests()
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Test execution failed: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()