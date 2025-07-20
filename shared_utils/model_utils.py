import torch
import gc
import whisper
import threading
import time
from contextlib import contextmanager
from typing import Optional, Tuple, Any
from transformers import MarianMTModel, MarianTokenizer
from rich.console import Console

console = Console()

class ModelManager:
    _instance = None
    _lock = threading.RLock()  # Reentrant lock for thread safety

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(ModelManager, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the ModelManager instance with thread-safe attributes."""
        # Model storage
        self.whisper_model = None
        self.translation_model = None
        self.translation_tokenizer = None
        self.spacy_model = None
        
        # Device configuration
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Thread safety locks for individual models
        self._whisper_lock = threading.RLock()
        self._translation_lock = threading.RLock()
        self._spacy_lock = threading.RLock()
        self._cuda_lock = threading.RLock()
        
        # Model usage tracking for concurrency management
        self._model_usage = {
            'whisper': 0,
            'translation': 0,
            'spacy': 0
        }
        self._usage_lock = threading.RLock()
        
        console.print(f"[bold]Using device: {self.device}[/bold]")
        console.print(f"[bold green]ModelManager initialized with thread safety[/bold green]")

    def get_device(self):
        return self.device
    
    @contextmanager
    def _track_model_usage(self, model_name: str):
        """Context manager to track model usage for concurrency control."""
        with self._usage_lock:
            self._model_usage[model_name] += 1
            current_usage = self._model_usage[model_name]
        
        try:
            if current_usage > 1:
                console.print(f"[bold yellow]Warning: {model_name} model is being used by {current_usage} concurrent processes[/bold yellow]")
            yield
        finally:
            with self._usage_lock:
                self._model_usage[model_name] -= 1

    def get_whisper_model(self):
        with self._whisper_lock:
            if self.whisper_model is None:
                console.print("[bold blue]Loading Whisper model...[/bold blue]")
                try:
                    self.whisper_model = whisper.load_model("turbo", device=self.device)
                    console.print("[bold green]Whisper model loaded successfully.[/bold green]")
                    self.log_cuda_memory("after loading Whisper")
                except Exception as e:
                    console.print(f"[bold red]Error loading Whisper model: {e}[/bold red]")
                    if self.device == 'cuda':
                        console.print("[bold yellow]Attempting to load Whisper model on CPU...[/bold yellow]")
                        self.device = 'cpu'
                        self.whisper_model = whisper.load_model("turbo", device=self.device)
                        console.print("[bold green]Whisper model loaded successfully on CPU.[/bold green]")
            return self.whisper_model
    
    @contextmanager
    def get_whisper_model_safe(self):
        """Get Whisper model with usage tracking for safe concurrent access."""
        with self._track_model_usage('whisper'):
            model = self.get_whisper_model()
            yield model

    def get_translation_model(self, src_lang="de", tgt_lang="es"):
        with self._translation_lock:
            if self.translation_model is None or self.translation_tokenizer is None:
                console.print(f"[bold blue]Loading translation model for {src_lang}->{tgt_lang}...[/bold blue]")
                try:
                    model_name = f'Helsinki-NLP/opus-mt-tc-big-{src_lang}-{tgt_lang}'
                    self.translation_tokenizer = MarianTokenizer.from_pretrained(model_name)
                    self.translation_model = MarianMTModel.from_pretrained(model_name).to(self.device)
                    console.print("[bold green]Translation model loaded successfully.[/bold green]")
                    self.log_cuda_memory("after loading translation model")
                except Exception as e:
                    console.print(f"[bold red]Error loading translation model: {e}[/bold red]")
                    return None, None
            return self.translation_model, self.translation_tokenizer
    
    @contextmanager
    def get_translation_model_safe(self, src_lang="de", tgt_lang="es"):
        """Get translation model with usage tracking for safe concurrent access."""
        with self._track_model_usage('translation'):
            model, tokenizer = self.get_translation_model(src_lang, tgt_lang)
            yield model, tokenizer

    def get_spacy_model(self):
        with self._spacy_lock:
            if self.spacy_model is None:
                console.print("[bold blue]Loading SpaCy model...[/bold blue]")
                try:
                    import spacy
                    self.spacy_model = spacy.load('de_core_news_lg')
                    console.print("[bold green]SpaCy model loaded successfully.[/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Error loading SpaCy model: {e}[/bold red]")
            return self.spacy_model
    
    @contextmanager
    def get_spacy_model_safe(self):
        """Get SpaCy model with usage tracking for safe concurrent access."""
        with self._track_model_usage('spacy'):
            model = self.get_spacy_model()
            yield model

    def cleanup_cuda_memory(self):
        with self._cuda_lock:
            if self.device == 'cuda':
                allocated_before, cached_before = self.get_cuda_memory_info()
                torch.cuda.empty_cache()
                gc.collect()
                allocated_after, cached_after = self.get_cuda_memory_info()
                console.print(f"[bold yellow]CUDA memory cleaned. Before: {allocated_before:.2f}GB allocated, {cached_before:.2f}GB cached. After: {allocated_after:.2f}GB allocated, {cached_after:.2f}GB cached.[/bold yellow]")

    def get_cuda_memory_info(self):
        with self._cuda_lock:
            if self.device == 'cuda':
                allocated = torch.cuda.memory_allocated() / 1024**3
                cached = torch.cuda.memory_reserved() / 1024**3
                return allocated, cached
            return 0, 0

    def log_cuda_memory(self, context=""):
        if self.device == 'cuda':
            allocated, cached = self.get_cuda_memory_info()
            console.print(f"[bold blue]CUDA memory {context}: {allocated:.2f}GB allocated, {cached:.2f}GB cached[/bold blue]")

    def cleanup_all_models(self):
        # Use all locks to ensure thread safety during cleanup
        with self._whisper_lock, self._translation_lock, self._spacy_lock, self._cuda_lock:
            console.print("[bold blue]Cleaning up all models...[/bold blue]")
            
            # Wait for any ongoing model usage to complete
            max_wait_time = 30  # seconds
            wait_start = time.time()
            
            while any(usage > 0 for usage in self._model_usage.values()):
                if time.time() - wait_start > max_wait_time:
                    console.print("[bold yellow]Warning: Forcing cleanup despite ongoing model usage[/bold yellow]")
                    break
                console.print("[bold yellow]Waiting for ongoing model usage to complete...[/bold yellow]")
                time.sleep(1)
            
            self.whisper_model = None
            self.translation_model = None
            self.translation_tokenizer = None
            self.spacy_model = None
            gc.collect()
            
            if self.device == 'cuda':
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            console.print("[bold green]All models cleaned up successfully.[/bold green]")
    
    def get_model_usage_stats(self) -> dict:
        """Get current model usage statistics for monitoring."""
        with self._usage_lock:
            return {
                'current_usage': self._model_usage.copy(),
                'device': self.device,
                'models_loaded': {
                    'whisper': self.whisper_model is not None,
                    'translation': self.translation_model is not None,
                    'spacy': self.spacy_model is not None
                }
            }
    
    def wait_for_model_availability(self, model_name: str, max_concurrent: int = 1, timeout: int = 30) -> bool:
        """Wait for a model to be available for use (concurrency control)."""
        start_time = time.time()
        
        while True:
            with self._usage_lock:
                if self._model_usage.get(model_name, 0) < max_concurrent:
                    return True
            
            if time.time() - start_time > timeout:
                console.print(f"[bold red]Timeout waiting for {model_name} model availability[/bold red]")
                return False
            
            time.sleep(0.1)
    
    @contextmanager
    def exclusive_model_access(self, model_name: str, timeout: int = 30):
        """Get exclusive access to a model (only one process can use it)."""
        if not self.wait_for_model_availability(model_name, max_concurrent=1, timeout=timeout):
            raise RuntimeError(f"Could not acquire exclusive access to {model_name} model")
        
        with self._track_model_usage(model_name):
            yield
