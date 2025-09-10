"""
Example usage of NVIDIA Parakeet-TDT-0.6b-v3 transcription service
High-throughput multilingual speech-to-text with automatic language detection
"""
import os
import time
from services import (
    TranscriptionServiceFactory, 
    PARAKEET_AVAILABLE,
    PARAKEET_SUPPORTED_LANGUAGES
)


def example_parakeet_basic():
    """Basic example of using Parakeet for transcription."""
    print("\n=== Parakeet Basic Transcription Example ===\n")
    
    # Check if Parakeet is available
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available. Please install NeMo toolkit:")
        print("pip install -U nemo_toolkit['asr']")
        return
    
    # List available services
    print(f"Available transcription services: {TranscriptionServiceFactory.get_available_services()}")
    
    # Create Parakeet service
    parakeet_service = TranscriptionServiceFactory.create_service(
        service_type='parakeet',
        device=0,  # Use GPU 0, or -1 for CPU
        enable_timestamps=True,
        timestamp_levels=['word', 'segment']
    )
    
    print(f"\nSupported languages: {', '.join(PARAKEET_SUPPORTED_LANGUAGES)}")
    print("Note: Parakeet automatically detects the language!")
    
    # Example: Transcribe with auto language detection
    audio_path = "example_multilang.wav"
    if os.path.exists(audio_path):
        result = parakeet_service.transcribe_audio(audio_path)  # No language specified
        
        print("\nTranscription Result:")
        print(f"  Detected language: {result.detected_language or 'unknown'}")
        print(f"  Duration: {result.duration:.2f} seconds")
        print(f"  Segments: {len(result.segments)}")
        
        # Show first few segments
        for i, segment in enumerate(result.segments[:3]):
            print(f"\n  Segment {i+1}:")
            print(f"    [{segment.start:.2f}s - {segment.end:.2f}s]")
            print(f"    {segment.text}")


def example_parakeet_timestamps():
    """Example showing Parakeet's multi-level timestamp capabilities."""
    print("\n=== Parakeet Multi-Level Timestamps Example ===\n")
    
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available.")
        return
    
    from services import ParakeetTranscriptionService
    
    # Create service with all timestamp levels
    parakeet_service = ParakeetTranscriptionService(
        device=0,
        enable_timestamps=True,
        timestamp_levels=['char', 'word', 'segment']
    )
    
    audio_path = "example_timestamps.wav"
    if os.path.exists(audio_path):
        result = parakeet_service.transcribe_audio(
            audio_path,
            timestamps=True
        )
        
        print("Timestamp Levels Available:")
        
        # Segment-level timestamps
        if result.segments:
            print(f"\n  Segment-level: {len(result.segments)} segments")
            print(f"    Sample: [{result.segments[0].start:.2f}s - {result.segments[0].end:.2f}s]")
            print(f"    Text: {result.segments[0].text[:50]}...")
        
        # Character-level timestamps (if available)
        if result.char_timestamps:
            print(f"\n  Character-level: {len(result.char_timestamps)} characters")
            print("    Sample characters with timing:")
            for char_info in result.char_timestamps[:10]:
                print(f"      '{char_info.get('char', '')}' at {char_info.get('time', 0):.3f}s")


def example_parakeet_long_form():
    """Example of using Parakeet for long-form audio transcription."""
    print("\n=== Parakeet Long-Form Audio Example ===\n")
    
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available.")
        return
    
    # Create service with local attention for long audio
    parakeet_service = TranscriptionServiceFactory.create_service(
        service_type='parakeet',
        device=0,
        use_local_attention=True,  # Enable for long audio
        attention_context_size=(256, 256)
    )
    
    # Process long audio files
    long_audio_files = [
        ("podcast_1hour.wav", 3600),  # 1 hour
        ("lecture_30min.wav", 1800),   # 30 minutes
        ("meeting_2hours.wav", 7200)   # 2 hours
    ]
    
    for audio_file, expected_duration in long_audio_files:
        if os.path.exists(audio_file):
            print(f"\nProcessing: {audio_file}")
            print(f"  Expected duration: {expected_duration/60:.1f} minutes")
            
            start_time = time.time()
            result = parakeet_service.transcribe_audio(audio_file)
            processing_time = time.time() - start_time
            
            print(f"  Processing time: {processing_time:.2f} seconds")
            print(f"  Real-time factor: {expected_duration/processing_time:.2f}x")
            print(f"  Segments: {len(result.segments)}")
            
            # Sample from middle
            if result.segments:
                mid_idx = len(result.segments) // 2
                mid_segment = result.segments[mid_idx]
                print(f"\n  Sample (segment {mid_idx}):")
                print(f"    [{mid_segment.start:.2f}s - {mid_segment.end:.2f}s]")
                print(f"    {mid_segment.text[:100]}...")


def example_parakeet_multilingual_batch():
    """Example of processing multiple files in different languages."""
    print("\n=== Parakeet Multilingual Batch Processing ===\n")
    
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available.")
        return
    
    parakeet_service = TranscriptionServiceFactory.create_service('parakeet', device=0)
    
    # Test files in different languages (Parakeet will auto-detect)
    test_files = [
        "example_en.wav",  # English
        "example_de.wav",  # German
        "example_fr.wav",  # French
        "example_es.wav",  # Spanish
        "example_ru.wav",  # Russian
        "example_uk.wav",  # Ukrainian
    ]
    
    print("Processing files with automatic language detection:\n")
    
    for audio_file in test_files:
        if os.path.exists(audio_file):
            print(f"Processing: {audio_file}")
            
            result = parakeet_service.transcribe_audio(audio_file)
            
            print(f"  Detected language: {result.detected_language or 'unknown'}")
            print(f"  Duration: {result.duration:.2f}s")
            
            if result.segments:
                print(f"  First segment: {result.segments[0].text[:80]}...")
            print()


def example_parakeet_streaming_config():
    """Example showing streaming configuration for Parakeet."""
    print("\n=== Parakeet Streaming Configuration Example ===\n")
    
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available.")
        return
    
    from services import ParakeetTranscriptionService
    
    parakeet_service = ParakeetTranscriptionService()
    
    # Get streaming configuration
    streaming_config = parakeet_service.configure_for_streaming(
        chunk_secs=2.0,
        left_context_secs=10.0,
        right_context_secs=2.0
    )
    
    print("Streaming Configuration for Parakeet:")
    print(f"  Model: {streaming_config['model_name']}")
    print(f"  Chunk duration: {streaming_config['chunk_secs']} seconds")
    print(f"  Left context: {streaming_config['left_context_secs']} seconds")
    print(f"  Right context: {streaming_config['right_context_secs']} seconds")
    print(f"  Batch size: {streaming_config['batch_size']}")
    
    print("\nTo use streaming, run:")
    print("python NeMo/examples/asr/asr_chunked_inference/rnnt/speech_to_text_streaming_infer_rnnt.py \\")
    print(f"    pretrained_name=\"{streaming_config['model_name']}\" \\")
    print(f"    chunk_secs={streaming_config['chunk_secs']} \\")
    print(f"    left_context_secs={streaming_config['left_context_secs']} \\")
    print(f"    right_context_secs={streaming_config['right_context_secs']} \\")
    print(f"    batch_size={streaming_config['batch_size']}")


def example_parakeet_vs_canary():
    """Compare Parakeet with Canary for performance and features."""
    print("\n=== Parakeet vs Canary Comparison ===\n")
    
    from services import CANARY_AVAILABLE
    
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available.")
        return
    
    # Model comparison
    print("Model Comparison:")
    print("\nParakeet-TDT-0.6b-v3:")
    print("  - Parameters: 600M (smaller, faster)")
    print("  - Languages: 25 (ASR only)")
    print("  - Features: Auto language detection")
    print("  - Best for: High-throughput transcription")
    print("  - Max duration: 3 hours (local attention)")
    
    if CANARY_AVAILABLE:
        print("\nCanary-1b-v2:")
        print("  - Parameters: 1B (larger, more accurate)")
        print("  - Languages: 25 (ASR + translation)")
        print("  - Features: Speech translation")
        print("  - Best for: Transcription + translation")
        print("  - Translation: En↔24 languages")
    
    # Performance test if both available
    if CANARY_AVAILABLE:
        audio_path = "example_comparison.wav"
        if os.path.exists(audio_path):
            print("\n\nPerformance Test:")
            
            # Test Parakeet
            parakeet_service = TranscriptionServiceFactory.create_service('parakeet', device=0)
            start_time = time.time()
            parakeet_result = parakeet_service.transcribe_audio(audio_path)
            parakeet_time = time.time() - start_time
            
            # Test Canary
            canary_service = TranscriptionServiceFactory.create_service('canary', device=0)
            start_time = time.time()
            canary_result = canary_service.transcribe_audio(audio_path, language='en')
            canary_time = time.time() - start_time
            
            print("\nResults:")
            print(f"  Parakeet time: {parakeet_time:.2f}s")
            print(f"  Canary time: {canary_time:.2f}s")
            print(f"  Speed ratio: Parakeet is {canary_time/parakeet_time:.2f}x "
                  f"{'faster' if parakeet_time < canary_time else 'slower'}")
            
            print(f"\n  Parakeet segments: {len(parakeet_result.segments)}")
            print(f"  Canary segments: {len(canary_result.segments)}")


def example_parakeet_noise_robustness():
    """Example showing Parakeet's noise robustness."""
    print("\n=== Parakeet Noise Robustness Example ===\n")
    
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available.")
        return
    
    parakeet_service = TranscriptionServiceFactory.create_service('parakeet', device=0)
    
    # Test files with different noise levels
    noise_test_files = [
        ("clean_audio.wav", "Clean"),
        ("snr_10db.wav", "SNR 10dB"),
        ("snr_5db.wav", "SNR 5dB"),
        ("snr_0db.wav", "SNR 0dB"),
        ("snr_minus5db.wav", "SNR -5dB"),
    ]
    
    print("Testing noise robustness (lower WER is better):\n")
    
    reference_text = "This is a test of speech recognition in noisy conditions."
    
    for audio_file, noise_level in noise_test_files:
        if os.path.exists(audio_file):
            result = parakeet_service.transcribe_audio(audio_file)
            
            if result.segments:
                transcribed_text = ' '.join(seg.text for seg in result.segments)
                
                # Simple WER calculation (for demo)
                from difflib import SequenceMatcher
                similarity = SequenceMatcher(None, reference_text.lower(), 
                                           transcribed_text.lower()).ratio()
                wer_estimate = (1 - similarity) * 100
                
                print(f"{noise_level:12s}: WER ≈ {wer_estimate:.1f}%")
                print(f"              Text: {transcribed_text[:60]}...")


def example_parakeet_model_info():
    """Display detailed information about the Parakeet model."""
    print("\n=== Parakeet Model Information ===\n")
    
    if not PARAKEET_AVAILABLE:
        print("Parakeet service is not available.")
        return
    
    from services import ParakeetTranscriptionService
    
    parakeet_service = ParakeetTranscriptionService()
    info = parakeet_service.get_model_info()
    
    print(f"Model: {info['name']}")
    print(f"Parameters: {info['parameters']}")
    print(f"Languages: {info['languages']} supported")
    print("\nSupported Languages:")
    for i in range(0, len(info['supported_languages']), 10):
        langs = info['supported_languages'][i:i+10]
        print(f"  {', '.join(langs)}")
    
    print("\nFeatures:")
    for feature in info['features']:
        print(f"  • {feature}")
    
    print("\nMax Duration:")
    print(f"  Full attention: {info['max_duration']['full_attention']}")
    print(f"  Local attention: {info['max_duration']['local_attention']}")


if __name__ == "__main__":
    print("=" * 60)
    print("NVIDIA Parakeet-TDT-0.6b-v3 Service Examples")
    print("=" * 60)
    
    # Check if NeMo is installed
    if not PARAKEET_AVAILABLE:
        print("\n⚠️  Parakeet service requires NeMo toolkit.")
        print("Install it with: pip install -U nemo_toolkit['asr']")
        print("\nNote: NeMo requires PyTorch and CUDA for optimal performance.")
        print("Visit: https://github.com/NVIDIA/NeMo for installation guide.")
    else:
        print("\n✅ Parakeet service is available!")
        print(f"Supported languages: {len(PARAKEET_SUPPORTED_LANGUAGES)} languages")
        print("Key advantage: Automatic language detection!")
    
    # Run examples
    try:
        example_parakeet_basic()
    except Exception as e:
        print(f"Basic example error: {e}")
    
    try:
        example_parakeet_timestamps()
    except Exception as e:
        print(f"Timestamps example error: {e}")
    
    try:
        example_parakeet_long_form()
    except Exception as e:
        print(f"Long-form example error: {e}")
    
    try:
        example_parakeet_multilingual_batch()
    except Exception as e:
        print(f"Multilingual batch example error: {e}")
    
    try:
        example_parakeet_streaming_config()
    except Exception as e:
        print(f"Streaming config example error: {e}")
    
    try:
        example_parakeet_vs_canary()
    except Exception as e:
        print(f"Comparison example error: {e}")
    
    try:
        example_parakeet_noise_robustness()
    except Exception as e:
        print(f"Noise robustness example error: {e}")
    
    try:
        example_parakeet_model_info()
    except Exception as e:
        print(f"Model info example error: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)