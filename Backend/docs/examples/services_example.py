"""
Example usage of the transcription and translation services with Factory Pattern
"""
import os
from services import (
    TranscriptionServiceFactory,
    TranslationServiceFactory,
    TranscriptionSegment
)


def example_transcription():
    """Example of using transcription services."""
    print("\n=== Transcription Service Example ===\n")
    
    # List available services
    print(f"Available transcription services: {TranscriptionServiceFactory.get_available_services()}")
    
    # Create a Whisper transcription service
    service = TranscriptionServiceFactory.create_service(
        service_type='whisper',
        model_size='base',  # Can be: tiny, base, small, medium, large, turbo
        device='cpu'  # or 'cuda' for GPU
    )
    
    # Example 1: Transcribe an audio file
    audio_path = "example_audio.wav"
    if os.path.exists(audio_path):
        result = service.transcribe_audio(audio_path, language='en')
        
        print("Transcription completed:")
        print(f"  Duration: {result.duration:.2f} seconds")
        print(f"  Language: {result.language}")
        print(f"  Number of segments: {len(result.segments)}")
        
        # Display first 3 segments
        for i, segment in enumerate(result.segments[:3]):
            print(f"\n  Segment {i+1}:")
            print(f"    Time: {segment.start:.2f}s - {segment.end:.2f}s")
            print(f"    Text: {segment.text}")
    
    # Example 2: Transcribe a video file
    video_path = "example_video.mp4"
    if os.path.exists(video_path):
        result = service.transcribe_video(video_path, language='de')
        
        print("\nVideo transcription completed:")
        print(f"  Segments: {len(result.segments)}")
        print(f"  Metadata: {result.metadata}")
        
        # Save as SRT
        srt_output = ""
        for i, segment in enumerate(result.segments):
            srt_output += f"{i+1}\n"
            srt_output += f"{format_time(segment.start)} --> {format_time(segment.end)}\n"
            srt_output += f"{segment.text}\n\n"
        
        with open("output.srt", "w", encoding="utf-8") as f:
            f.write(srt_output)
        print("  Saved to: output.srt")


def example_translation():
    """Example of using translation services."""
    print("\n=== Translation Service Example ===\n")
    
    # List available services
    print(f"Available translation services: {TranslationServiceFactory.get_available_services()}")
    
    # Example 1: Using Marian translation service
    marian_service = TranslationServiceFactory.create_service(
        service_type='marian',
        use_gpu=False  # Set to True if you have CUDA
    )
    
    # Translate single text
    text = "Guten Tag, wie geht es Ihnen?"
    translated = marian_service.translate_text(text, source_lang='de', target_lang='en')
    print("\nMarian Translation:")
    print(f"  Original: {text}")
    print(f"  Translated: {translated}")
    
    # Example 2: Using HuggingFace pipeline service (for batch processing)
    hf_service = TranslationServiceFactory.create_service(
        service_type='huggingface',
        device=-1  # -1 for CPU, 0 for GPU
    )
    
    # Translate multiple segments (e.g., from subtitles)
    segments = [
        {'start': 0.0, 'end': 2.5, 'text': 'Hallo Welt'},
        {'start': 2.5, 'end': 5.0, 'text': 'Wie geht es dir heute?'},
        {'start': 5.0, 'end': 8.0, 'text': 'Das Wetter ist schön.'}
    ]
    
    result = hf_service.translate_segments(
        segments, 
        source_lang='de', 
        target_lang='en'
    )
    
    print("\nBatch Translation (HuggingFace):")
    print(f"  Source language: {result.source_language}")
    print(f"  Target language: {result.target_language}")
    
    for i, segment in enumerate(result.segments):
        print(f"\n  Segment {i+1}:")
        print(f"    Time: {segment.start:.2f}s - {segment.end:.2f}s")
        print(f"    Original: {segment.original_text}")
        print(f"    Translation: {segment.translated_text}")
    
    # Example 3: Translate subtitle file
    subtitle_path = "example.srt"
    if os.path.exists(subtitle_path):
        output_path = marian_service.translate_subtitle_file(
            subtitle_path,
            source_lang='de',
            target_lang='es'
        )
        print(f"\nSubtitle file translated: {output_path}")


def example_custom_service():
    """Example of registering a custom service."""
    print("\n=== Custom Service Registration Example ===\n")
    
    from services import TranscriptionService, TranscriptionResult
    
    # Define a custom transcription service
    class DummyTranscriptionService(TranscriptionService):
        """A dummy transcription service for demonstration."""
        
        def transcribe_audio(self, audio_path: str, language: str = "en", **kwargs) -> TranscriptionResult:
            # This would contain your custom transcription logic
            segments = [
                TranscriptionSegment(0.0, 2.0, "This is a dummy transcription"),
                TranscriptionSegment(2.0, 4.0, "It doesn't actually transcribe anything")
            ]
            return TranscriptionResult(
                segments=segments,
                language=language,
                duration=4.0,
                metadata={'service': 'dummy'}
            )
        
        def transcribe_video(self, video_path: str, language: str = "en", **kwargs) -> TranscriptionResult:
            # Extract audio and transcribe
            return self.transcribe_audio("dummy_audio.wav", language, **kwargs)
    
    # Register the custom service
    TranscriptionServiceFactory.register_service('dummy', DummyTranscriptionService)
    
    # Now it's available in the factory
    print(f"Services after registration: {TranscriptionServiceFactory.get_available_services()}")
    
    # Use the custom service
    custom_service = TranscriptionServiceFactory.create_service('dummy')
    result = custom_service.transcribe_audio("any_file.wav")
    
    print("\nCustom service result:")
    for segment in result.segments:
        print(f"  {segment.start:.1f}s - {segment.end:.1f}s: {segment.text}")


def example_switching_services():
    """Example of dynamically switching between services."""
    print("\n=== Dynamic Service Switching Example ===\n")
    
    # Configuration-based service selection
    config = {
        'transcription': {
            'service': 'whisper',  # Could be loaded from config file
            'params': {
                'model_size': 'base',
                'device': 'cpu'
            }
        },
        'translation': {
            'service': 'marian',  # Could switch to 'huggingface' easily
            'params': {
                'use_gpu': False
            }
        }
    }
    
    # Create services based on configuration
    transcription_service = TranscriptionServiceFactory.create_service(
        config['transcription']['service'],
        **config['transcription']['params']
    )
    
    translation_service = TranslationServiceFactory.create_service(
        config['translation']['service'],
        **config['translation']['params']
    )
    
    print(f"Transcription service: {config['transcription']['service']}")
    print(f"Translation service: {config['translation']['service']}")
    
    # Use the services...
    text = "Hello world"
    translated = translation_service.translate_text(text, 'en', 'de')
    print(f"\nTranslated '{text}' to: {translated}")


def format_time(timestamp):
    """Format timestamp for SRT format."""
    hours = int(timestamp // 3600)
    minutes = int((timestamp % 3600) // 60)
    seconds = int(timestamp % 60)
    milliseconds = int((timestamp % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


if __name__ == "__main__":
    # Run examples
    try:
        example_transcription()
    except Exception as e:
        print(f"Transcription example error: {e}")
    
    try:
        example_translation()
    except Exception as e:
        print(f"Translation example error: {e}")
    
    try:
        example_custom_service()
    except Exception as e:
        print(f"Custom service example error: {e}")
    
    try:
        example_switching_services()
    except Exception as e:
        print(f"Service switching example error: {e}")