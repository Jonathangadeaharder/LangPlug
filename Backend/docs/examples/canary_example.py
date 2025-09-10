"""
Example usage of NVIDIA Canary-1b-v2 transcription and translation service
"""
import os
from services import (
    TranscriptionServiceFactory, 
    CANARY_AVAILABLE,
    CANARY_SUPPORTED_LANGUAGES
)


def example_canary_basic():
    """Basic example of using Canary for transcription."""
    print("\n=== Canary Basic Transcription Example ===\n")
    
    # Check if Canary is available
    if not CANARY_AVAILABLE:
        print("Canary service is not available. Please install NeMo toolkit:")
        print("pip install -U nemo_toolkit['asr']")
        return
    
    # List available services
    print(f"Available transcription services: {TranscriptionServiceFactory.get_available_services()}")
    
    # Create Canary service
    canary_service = TranscriptionServiceFactory.create_service(
        service_type='canary',
        device=0,  # Use GPU 0, or -1 for CPU
        enable_timestamps=True
    )
    
    print(f"\nSupported languages: {', '.join(CANARY_SUPPORTED_LANGUAGES)}")
    
    # Example: Transcribe English audio
    audio_path = "example_en.wav"
    if os.path.exists(audio_path):
        result = canary_service.transcribe_audio(audio_path, language='en')
        
        print("\nTranscription Result:")
        print(f"  Language: {result.language}")
        print(f"  Duration: {result.duration:.2f} seconds")
        print(f"  Segments: {len(result.segments)}")
        
        # Show first few segments
        for i, segment in enumerate(result.segments[:3]):
            print(f"\n  Segment {i+1}:")
            print(f"    [{segment.start:.2f}s - {segment.end:.2f}s]")
            print(f"    {segment.text}")


def example_canary_translation():
    """Example of using Canary for speech translation."""
    print("\n=== Canary Speech Translation Example ===\n")
    
    if not CANARY_AVAILABLE:
        print("Canary service is not available. Please install NeMo toolkit.")
        return
    
    # Create Canary service
    canary_service = TranscriptionServiceFactory.create_service('canary')
    
    # Example 1: English to Spanish translation
    print("Example 1: English → Spanish")
    audio_path = "example_en.wav"
    if os.path.exists(audio_path):
        result = canary_service.transcribe_audio(
            audio_path, 
            language='en',
            target_lang='es',  # Translate to Spanish
            timestamps=True
        )
        
        print(f"  Source language: {result.language}")
        print(f"  Target language: {result.metadata.get('target_language', 'N/A')}")
        
        for i, segment in enumerate(result.segments[:2]):
            print(f"\n  Segment {i+1}:")
            print(f"    [{segment.start:.2f}s - {segment.end:.2f}s]")
            print(f"    {segment.text}")
    
    # Example 2: German to English translation
    print("\n\nExample 2: German → English")
    audio_path = "example_de.wav"
    if os.path.exists(audio_path):
        result = canary_service.transcribe_audio(
            audio_path,
            language='de',
            target_lang='en',  # Translate to English
            timestamps=True
        )
        
        print(f"  Source language: {result.language}")
        print(f"  Target language: {result.metadata.get('target_language', 'N/A')}")
        
        for i, segment in enumerate(result.segments[:2]):
            print(f"\n  Segment {i+1}:")
            print(f"    [{segment.start:.2f}s - {segment.end:.2f}s]")
            print(f"    {segment.text}")


def example_canary_multilingual():
    """Example of processing multiple languages with Canary."""
    print("\n=== Canary Multilingual Processing Example ===\n")
    
    if not CANARY_AVAILABLE:
        print("Canary service is not available.")
        return
    
    from services import CanaryTranscriptionService
    
    # Create service directly for access to special methods
    canary_service = CanaryTranscriptionService(
        model_name="nvidia/canary-1b-v2",
        device=0
    )
    
    # Check supported translation pairs
    translation_pairs = canary_service.get_supported_translation_pairs()
    
    print("Supported Translation Directions:")
    print(f"  From English to: {', '.join(translation_pairs['en'][:10])}...")
    print(f"  To English from: {', '.join(list(translation_pairs.keys())[:10])}...")
    
    # Process multiple files in different languages
    test_files = [
        ("example_en.wav", "en", "es"),  # English to Spanish
        ("example_de.wav", "de", "en"),  # German to English
        ("example_fr.wav", "fr", "en"),  # French to English
        ("example_es.wav", "es", "en"),  # Spanish to English
    ]
    
    print("\n\nBatch Processing:")
    for audio_file, source_lang, target_lang in test_files:
        if not os.path.exists(audio_file):
            continue
        
        # Validate translation pair
        if canary_service.validate_translation_pair(source_lang, target_lang):
            print(f"\n  Processing {audio_file}: {source_lang} → {target_lang}")
            
            result = canary_service.transcribe_and_translate(
                audio_file,
                source_lang=source_lang,
                target_lang=target_lang,
                timestamps=False  # Disable for faster processing
            )
            
            # Show first segment only
            if result.segments:
                print(f"    Result: {result.segments[0].text[:100]}...")
        else:
            print(f"\n  Skipping {audio_file}: {source_lang} → {target_lang} not supported")


def example_canary_long_form():
    """Example of using Canary for long-form audio transcription."""
    print("\n=== Canary Long-Form Audio Example ===\n")
    
    if not CANARY_AVAILABLE:
        print("Canary service is not available.")
        return
    
    # Create service with custom chunk settings for long audio
    canary_service = TranscriptionServiceFactory.create_service(
        service_type='canary',
        device=0,
        chunk_length_s=40.0  # 40-second chunks with overlap
    )
    
    # Process long audio file
    long_audio = "podcast_episode.wav"
    if os.path.exists(long_audio):
        print(f"Processing long-form audio: {long_audio}")
        print("Using dynamic chunking for efficient processing...")
        
        result = canary_service.transcribe_audio(
            long_audio,
            language='en',
            timestamps=True
        )
        
        print("\nResults:")
        print(f"  Total duration: {result.duration:.2f} seconds")
        print(f"  Total segments: {len(result.segments)}")
        
        # Calculate statistics
        if result.segments:
            avg_segment_length = sum(seg.end - seg.start for seg in result.segments) / len(result.segments)
            print(f"  Average segment length: {avg_segment_length:.2f} seconds")
            
            # Show sample from middle of transcription
            mid_idx = len(result.segments) // 2
            mid_segment = result.segments[mid_idx]
            print(f"\n  Sample from middle (segment {mid_idx}):")
            print(f"    [{mid_segment.start:.2f}s - {mid_segment.end:.2f}s]")
            print(f"    {mid_segment.text}")


def example_canary_video():
    """Example of using Canary for video transcription and translation."""
    print("\n=== Canary Video Processing Example ===\n")
    
    if not CANARY_AVAILABLE:
        print("Canary service is not available.")
        return
    
    canary_service = TranscriptionServiceFactory.create_service('canary')
    
    video_path = "example_video.mp4"
    if os.path.exists(video_path):
        print(f"Processing video: {video_path}")
        
        # Transcribe and translate video (German to English)
        result = canary_service.transcribe_video(
            video_path,
            language='de',
            target_lang='en',
            timestamps=True
        )
        
        print("\nVideo Transcription Results:")
        print(f"  Source: {result.metadata.get('source', 'N/A')}")
        print(f"  Duration: {result.duration:.2f} seconds")
        print(f"  Segments: {len(result.segments)}")
        
        # Save as SRT subtitle file
        srt_output = ""
        for i, segment in enumerate(result.segments):
            srt_output += f"{i+1}\n"
            srt_output += f"{format_time(segment.start)} --> {format_time(segment.end)}\n"
            srt_output += f"{segment.text}\n\n"
        
        output_file = "video_subtitles_en.srt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(srt_output)
        
        print(f"  Subtitles saved to: {output_file}")


def example_canary_comparison():
    """Compare Canary with Whisper for the same audio."""
    print("\n=== Canary vs Whisper Comparison ===\n")
    
    audio_path = "example_comparison.wav"
    if not os.path.exists(audio_path):
        print(f"Test file {audio_path} not found")
        return
    
    results = {}
    
    # Test with Whisper
    print("Testing with Whisper...")
    try:
        whisper_service = TranscriptionServiceFactory.create_service(
            'whisper',
            model_size='base',
            device='cpu'
        )
        
        import time
        start_time = time.time()
        whisper_result = whisper_service.transcribe_audio(audio_path, language='en')
        whisper_time = time.time() - start_time
        
        results['whisper'] = {
            'time': whisper_time,
            'segments': len(whisper_result.segments),
            'text': whisper_result.segments[0].text if whisper_result.segments else ""
        }
        print(f"  Completed in {whisper_time:.2f} seconds")
    except Exception as e:
        print(f"  Whisper failed: {e}")
    
    # Test with Canary
    if CANARY_AVAILABLE:
        print("\nTesting with Canary...")
        try:
            canary_service = TranscriptionServiceFactory.create_service('canary', device=-1)
            
            import time
            start_time = time.time()
            canary_result = canary_service.transcribe_audio(audio_path, language='en')
            canary_time = time.time() - start_time
            
            results['canary'] = {
                'time': canary_time,
                'segments': len(canary_result.segments),
                'text': canary_result.segments[0].text if canary_result.segments else ""
            }
            print(f"  Completed in {canary_time:.2f} seconds")
        except Exception as e:
            print(f"  Canary failed: {e}")
    
    # Compare results
    if len(results) == 2:
        print("\n\nComparison Results:")
        print(f"  Speed: Canary is {results['whisper']['time']/results['canary']['time']:.2f}x "
              f"{'faster' if results['canary']['time'] < results['whisper']['time'] else 'slower'}")
        print(f"  Segments: Whisper: {results['whisper']['segments']}, "
              f"Canary: {results['canary']['segments']}")
        
        print("\n  Sample Output:")
        print(f"    Whisper: {results['whisper']['text'][:100]}...")
        print(f"    Canary:  {results['canary']['text'][:100]}...")


def format_time(timestamp):
    """Format timestamp for SRT format."""
    hours = int(timestamp // 3600)
    minutes = int((timestamp % 3600) // 60)
    seconds = int(timestamp % 60)
    milliseconds = int((timestamp % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


if __name__ == "__main__":
    print("=" * 60)
    print("NVIDIA Canary-1b-v2 Service Examples")
    print("=" * 60)
    
    # Check if NeMo is installed
    if not CANARY_AVAILABLE:
        print("\n⚠️  Canary service requires NeMo toolkit.")
        print("Install it with: pip install -U nemo_toolkit['asr']")
        print("\nNote: NeMo requires PyTorch and CUDA for optimal performance.")
        print("Visit: https://github.com/NVIDIA/NeMo for installation guide.")
    else:
        print("\n✅ Canary service is available!")
        print(f"Supported languages: {len(CANARY_SUPPORTED_LANGUAGES)} languages")
    
    # Run examples
    try:
        example_canary_basic()
    except Exception as e:
        print(f"Basic example error: {e}")
    
    try:
        example_canary_translation()
    except Exception as e:
        print(f"Translation example error: {e}")
    
    try:
        example_canary_multilingual()
    except Exception as e:
        print(f"Multilingual example error: {e}")
    
    try:
        example_canary_long_form()
    except Exception as e:
        print(f"Long-form example error: {e}")
    
    try:
        example_canary_video()
    except Exception as e:
        print(f"Video example error: {e}")
    
    try:
        example_canary_comparison()
    except Exception as e:
        print(f"Comparison example error: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)