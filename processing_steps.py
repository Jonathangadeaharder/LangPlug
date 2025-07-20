from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from processing_interfaces import (
    ITranscriptionContext,
    IFilteringContext,
    ITranslationContext,
    IPreviewProcessingContext,
    IConfigurationContext,
    IMetadataContext
)

console = Console()

@dataclass
class ProcessingContext(ITranscriptionContext, IFilteringContext, ITranslationContext, 
                       IPreviewProcessingContext, IConfigurationContext, IMetadataContext):
    """Context object that holds all data and state for the processing pipeline.
    
    This class implements all granular context interfaces to provide a unified
    context object while maintaining interface segregation for processing steps.
    """
    video_file: str
    model_manager: Any
    language: str = "de"
    src_lang: str = "de"
    tgt_lang: str = "es"
    no_preview: bool = False
    
    # Configuration data (loaded from centralized config)
    known_words: Optional[set] = None
    word_list_files: Optional[Dict[str, str]] = None
    processing_config: Optional[Dict[str, Any]] = None
    
    # Processing results
    preview_srt: Optional[str] = None
    full_srt: Optional[str] = None
    filtered_srt: Optional[str] = None
    translated_srt: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.word_list_files is None:
            self.word_list_files = {}
        if self.processing_config is None:
            self.processing_config = {}

class ProcessingStep(ABC):
    """Abstract base class for processing steps in the subtitle processing pipeline."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: ProcessingContext) -> bool:
        """Execute the processing step.
        
        Args:
            context: The processing context containing all necessary data
            
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

class ProcessingPipeline:
    """Pipeline that executes a sequence of processing steps."""
    
    def __init__(self, steps: list[ProcessingStep]):
        self.steps = steps
    
    def execute(self, context: ProcessingContext) -> bool:
        """Execute all steps in the pipeline.
        
        Args:
            context: The processing context
            
        Returns:
            bool: True if all steps completed successfully, False otherwise
        """
        console.print(f"\n[bold cyan]Starting processing pipeline with {len(self.steps)} steps[/bold cyan]")
        
        for i, step in enumerate(self.steps, 1):
            console.print(f"\n[bold magenta]Step {i}/{len(self.steps)}: {step.name}[/bold magenta]")
            
            try:
                success = step.execute(context)
                if not success:
                    console.print(f"[bold red]Pipeline stopped at step {i}: {step.name}[/bold red]")
                    return False
            except Exception as e:
                step.log_error(str(e))
                console.print(f"[bold red]Pipeline failed at step {i}: {step.name}[/bold red]")
                return False
        
        console.print(f"\n[bold green]Processing pipeline completed successfully![/bold green]")
        return True