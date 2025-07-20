from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, Optional, runtime_checkable
from rich.console import Console

console = Console()


@runtime_checkable
class ITranscriptionContext(Protocol):
    """Interface for contexts used by transcription steps."""
    video_file: str
    model_manager: Any
    language: str
    no_preview: bool
    
    # Results that transcription steps produce
    preview_srt: Optional[str]
    full_srt: Optional[str]


@runtime_checkable
class IFilteringContext(Protocol):
    """Interface for contexts used by filtering steps."""
    model_manager: Any  # For SpaCy model
    known_words: Optional[set]
    
    # Input subtitles to filter
    full_srt: Optional[str]
    preview_srt: Optional[str]
    
    # Results that filtering steps produce
    filtered_srt: Optional[str]


@runtime_checkable
class ITranslationContext(Protocol):
    """Interface for contexts used by translation steps."""
    model_manager: Any  # For translation model
    src_lang: str
    tgt_lang: str
    
    # Input subtitles to translate
    full_srt: Optional[str]
    filtered_srt: Optional[str]
    
    # Results that translation steps produce
    translated_srt: Optional[str]


@runtime_checkable
class IPreviewProcessingContext(Protocol):
    """Interface for contexts used by preview processing steps."""
    video_file: str
    model_manager: Any
    language: str
    src_lang: str
    tgt_lang: str
    preview_srt: Optional[str]
    
    # Configuration data needed for preview processing
    known_words: Optional[set]
    word_list_files: Optional[Dict[str, str]]
    processing_config: Optional[Dict[str, Any]]


@runtime_checkable
class IConfigurationContext(Protocol):
    """Interface for contexts that provide configuration data."""
    known_words: Optional[set]
    word_list_files: Optional[Dict[str, str]]
    processing_config: Optional[Dict[str, Any]]


@runtime_checkable
class IMetadataContext(Protocol):
    """Interface for contexts that provide metadata storage."""
    metadata: Dict[str, Any]


# Abstract base classes for processing steps with specific context requirements
class TranscriptionStep(ABC):
    """Abstract base class for transcription processing steps."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: ITranscriptionContext) -> bool:
        """Execute the transcription step.
        
        Args:
            context: Context providing transcription-specific data
            
        Returns:
            bool: True if the step completed successfully, False otherwise
        """
        pass
    
    def log_start(self):
        """Log the start of the processing step."""
        console.print(f"\n[bold blue]Starting {self.name}...[/bold blue]")
    
    def log_success(self, message: str = ""):
        """Log successful completion of the processing step."""
        success_msg = f"[bold green]{self.name} completed successfully.[/bold green]"
        if message:
            success_msg += f" {message}"
        console.print(success_msg)
    
    def log_error(self, error: str):
        """Log an error during the processing step."""
        console.print(f"[bold red]{self.name} failed: {error}[/bold red]")
    
    def log_skip(self, reason: str):
        """Log that the processing step was skipped."""
        console.print(f"[bold yellow]{self.name} skipped: {reason}[/bold yellow]")


class FilteringStep(ABC):
    """Abstract base class for filtering processing steps."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: IFilteringContext) -> bool:
        """Execute the filtering step.
        
        Args:
            context: Context providing filtering-specific data
            
        Returns:
            bool: True if the step completed successfully, False otherwise
        """
        pass
    
    def log_start(self):
        """Log the start of the processing step."""
        console.print(f"\n[bold blue]Starting {self.name}...[/bold blue]")
    
    def log_success(self, message: str = ""):
        """Log successful completion of the processing step."""
        success_msg = f"[bold green]{self.name} completed successfully.[/bold green]"
        if message:
            success_msg += f" {message}"
        console.print(success_msg)
    
    def log_error(self, error: str):
        """Log an error during the processing step."""
        console.print(f"[bold red]{self.name} failed: {error}[/bold red]")
    
    def log_skip(self, reason: str):
        """Log that the processing step was skipped."""
        console.print(f"[bold yellow]{self.name} skipped: {reason}[/bold yellow]")


class TranslationStep(ABC):
    """Abstract base class for translation processing steps."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: ITranslationContext) -> bool:
        """Execute the translation step.
        
        Args:
            context: Context providing translation-specific data
            
        Returns:
            bool: True if the step completed successfully, False otherwise
        """
        pass
    
    def log_start(self):
        """Log the start of the processing step."""
        console.print(f"\n[bold blue]Starting {self.name}...[/bold blue]")
    
    def log_success(self, message: str = ""):
        """Log successful completion of the processing step."""
        success_msg = f"[bold green]{self.name} completed successfully.[/bold green]"
        if message:
            success_msg += f" {message}"
        console.print(success_msg)
    
    def log_error(self, error: str):
        """Log an error during the processing step."""
        console.print(f"[bold red]{self.name} failed: {error}[/bold red]")
    
    def log_skip(self, reason: str):
        """Log that the processing step was skipped."""
        console.print(f"[bold yellow]{self.name} skipped: {reason}[/bold yellow]")


class PreviewProcessingStep(ABC):
    """Abstract base class for preview processing steps."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: IPreviewProcessingContext) -> bool:
        """Execute the preview processing step.
        
        Args:
            context: Context providing preview processing-specific data
            
        Returns:
            bool: True if the step completed successfully, False otherwise
        """
        pass
    
    def log_start(self):
        """Log the start of the processing step."""
        console.print(f"\n[bold blue]Starting {self.name}...[/bold blue]")
    
    def log_success(self, message: str = ""):
        """Log successful completion of the processing step."""
        success_msg = f"[bold green]{self.name} completed successfully.[/bold green]"
        if message:
            success_msg += f" {message}"
        console.print(success_msg)
    
    def log_error(self, error: str):
        """Log an error during the processing step."""
        console.print(f"[bold red]{self.name} failed: {error}[/bold red]")
    
    def log_skip(self, reason: str):
        """Log that the processing step was skipped."""
        console.print(f"[bold yellow]{self.name} skipped: {reason}[/bold yellow]")