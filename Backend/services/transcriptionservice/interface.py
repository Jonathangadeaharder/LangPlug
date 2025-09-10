"""
Transcription Service Interface
Defines the contract that all transcription services must implement
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing"""
    start_time: float
    end_time: float
    text: str
    confidence: Optional[float] = None
    speaker: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptionResult:
    """Result of a transcription operation"""
    full_text: str
    segments: List[TranscriptionSegment]
    language: Optional[str] = None
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ITranscriptionService(ABC):
    """
    Interface for transcription services
    All transcription implementations must implement these methods
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the transcription service and load models"""
        pass
    
    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file
        
        Args:
            audio_path: Path to the audio file
            language: Optional language hint (e.g., 'en', 'de')
            
        Returns:
            TranscriptionResult with transcription details
        """
        pass
    
    @abstractmethod
    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe with detailed timestamps for each segment
        
        Args:
            audio_path: Path to the audio file
            language: Optional language hint
            
        Returns:
            TranscriptionResult with timed segments
        """
        pass
    
    @abstractmethod
    def transcribe_batch(
        self,
        audio_paths: List[str],
        language: Optional[str] = None
    ) -> List[TranscriptionResult]:
        """
        Transcribe multiple audio files in batch
        
        Args:
            audio_paths: List of paths to audio files
            language: Optional language hint
            
        Returns:
            List of TranscriptionResult objects
        """
        pass
    
    @abstractmethod
    def supports_video(self) -> bool:
        """
        Check if the service supports direct video transcription
        
        Returns:
            True if video files are supported, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_audio_from_video(
        self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            output_path: Optional path for extracted audio
            
        Returns:
            Path to extracted audio file
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes
        
        Returns:
            List of language codes (e.g., ['en', 'de', 'es'])
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources and unload models"""
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Get the name of this transcription service"""
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if the service is initialized and ready"""
        pass
    
    @property
    @abstractmethod
    def model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        pass