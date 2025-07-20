import torch
import gc
import whisper
from transformers import MarianMTModel, MarianTokenizer
from rich.console import Console

console = Console()

class ModelManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.whisper_model = None
            cls._instance.translation_model = None
            cls._instance.translation_tokenizer = None
            cls._instance.spacy_model = None
            cls._instance.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            console.print(f"[bold]Using device: {cls._instance.device}[/bold]")
        return cls._instance

    def get_device(self):
        return self.device

    def get_whisper_model(self):
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

    def get_translation_model(self, src_lang="de", tgt_lang="es"):
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

    def get_spacy_model(self):
        if self.spacy_model is None:
            console.print("[bold blue]Loading SpaCy model...[/bold blue]")
            try:
                import spacy
                self.spacy_model = spacy.load('de_core_news_lg')
                console.print("[bold green]SpaCy model loaded successfully.[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error loading SpaCy model: {e}[/bold red]")
        return self.spacy_model

    def cleanup_cuda_memory(self):
        if self.device == 'cuda':
            allocated_before, cached_before = self.get_cuda_memory_info()
            torch.cuda.empty_cache()
            gc.collect()
            allocated_after, cached_after = self.get_cuda_memory_info()
            console.print(f"[bold yellow]CUDA memory cleaned. Before: {allocated_before:.2f}GB allocated, {cached_before:.2f}GB cached. After: {allocated_after:.2f}GB allocated, {cached_after:.2f}GB cached.[/bold yellow]")

    def get_cuda_memory_info(self):
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
        console.print("[bold blue]Cleaning up all models...[/bold blue]")
        self.whisper_model = None
        self.translation_model = None
        self.translation_tokenizer = None
        self.spacy_model = None
        gc.collect()
        if self.device == 'cuda':
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        console.print("[bold green]All models cleaned up successfully.[/bold green]")
