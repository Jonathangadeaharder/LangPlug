"""
Test suite for ITranscriptionService interface
Tests focus on interface contract compliance for all implementations
"""

from abc import ABC

import pytest

from services.transcriptionservice.interface import ITranscriptionService, TranscriptionResult, TranscriptionSegment


class MockTranscriptionService(ITranscriptionService):
    """Mock implementation of ITranscriptionService for testing interface contract"""

    def __init__(self):
        self._initialized = False
        self._service_name = "MockTranscriptionService"

    def initialize(self) -> None:
        """Mock implementation of initialize"""
        self._initialized = True

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """Mock implementation of transcribe"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        return TranscriptionResult(
            full_text="This is a test transcription",
            segments=[
                TranscriptionSegment(start_time=0.0, end_time=5.0, text="This is a test transcription", confidence=0.95)
            ],
            language=language or "en",
            duration=5.0,
        )

    def transcribe_with_timestamps(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        """Mock implementation of transcribe_with_timestamps"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        return TranscriptionResult(
            full_text="Word by word transcription",
            segments=[
                TranscriptionSegment(start_time=0.0, end_time=1.0, text="Word", confidence=0.98),
                TranscriptionSegment(start_time=1.0, end_time=2.0, text="by", confidence=0.95),
                TranscriptionSegment(start_time=2.0, end_time=3.0, text="word", confidence=0.97),
                TranscriptionSegment(start_time=3.0, end_time=5.0, text="transcription", confidence=0.93),
            ],
            language=language or "en",
            duration=5.0,
        )

    def transcribe_batch(self, audio_paths: list[str], language: str | None = None) -> list[TranscriptionResult]:
        """Mock implementation of transcribe_batch"""
        if not self._initialized:
            raise RuntimeError("Service not initialized")

        results = []
        for i, _path in enumerate(audio_paths):
            results.append(
                TranscriptionResult(
                    full_text=f"Transcription for file {i + 1}",
                    segments=[
                        TranscriptionSegment(
                            start_time=0.0, end_time=3.0, text=f"Transcription for file {i + 1}", confidence=0.9
                        )
                    ],
                    language=language or "en",
                    duration=3.0,
                )
            )
        return results

    def supports_video(self) -> bool:
        """Mock implementation of supports_video"""
        return True

    def extract_audio_from_video(self, video_path: str, output_path: str | None = None) -> str:
        """Mock implementation of extract_audio_from_video"""
        if not self.supports_video():
            raise NotImplementedError("Video extraction not supported")

        output_path = output_path or video_path.replace(".mp4", ".wav")
        return output_path

    def get_supported_languages(self) -> list[str]:
        """Mock implementation of get_supported_languages"""
        return ["en", "de", "fr", "es", "it"]

    def cleanup(self) -> None:
        """Mock implementation of cleanup"""
        self._initialized = False

    @property
    def service_name(self) -> str:
        """Mock implementation of service_name property"""
        return self._service_name

    @property
    def is_initialized(self) -> bool:
        """Mock implementation of is_initialized property"""
        return self._initialized

    @property
    def model_info(self) -> dict[str, any]:
        """Mock implementation of model_info property"""
        return {"model_name": "MockModel", "version": "1.0.0", "language_support": self.get_supported_languages()}


@pytest.fixture
def transcription_service():
    """Create mock transcription service for testing"""
    return MockTranscriptionService()


class TestTranscriptionServiceInterface:
    """Test ITranscriptionService interface contract compliance"""

    def test_interface_is_abstract(self):
        """Test that ITranscriptionService is properly abstract"""
        assert issubclass(ITranscriptionService, ABC)

        # Should not be able to instantiate interface directly
        with pytest.raises(TypeError):
            ITranscriptionService()

    def test_service_implements_interface(self, transcription_service):
        """Test that mock service properly implements the interface"""
        assert isinstance(transcription_service, ITranscriptionService)

    def test_initialization_lifecycle(self, transcription_service):
        """Test service initialization lifecycle"""
        # Service should not be initialized initially
        assert not transcription_service.is_initialized

        # Initialize service
        transcription_service.initialize()
        assert transcription_service.is_initialized

        # Cleanup service
        transcription_service.cleanup()
        assert not transcription_service.is_initialized

    def test_service_properties(self, transcription_service):
        """Test required service properties"""
        # Service name should be accessible
        assert isinstance(transcription_service.service_name, str)
        assert len(transcription_service.service_name) > 0

        # Model info should return dictionary
        model_info = transcription_service.model_info
        assert isinstance(model_info, dict)

        # Is initialized should be boolean
        assert isinstance(transcription_service.is_initialized, bool)

    def test_transcribe_requires_initialization(self, transcription_service):
        """Test that transcription methods require initialization"""
        # Should fail when not initialized
        with pytest.raises(RuntimeError):
            transcription_service.transcribe("/path/to/audio.wav")

        # Should work after initialization
        transcription_service.initialize()
        result = transcription_service.transcribe("/path/to/audio.wav")
        assert isinstance(result, TranscriptionResult)

    def test_transcribe_basic_functionality(self, transcription_service):
        """Test basic transcription functionality"""
        transcription_service.initialize()

        # Test basic transcription
        result = transcription_service.transcribe("/test/audio.wav")

        # Verify result structure
        assert isinstance(result, TranscriptionResult)
        assert isinstance(result.full_text, str)
        assert isinstance(result.segments, list)
        assert len(result.segments) > 0
        assert isinstance(result.segments[0], TranscriptionSegment)

    def test_transcribe_with_language_hint(self, transcription_service):
        """Test transcription with language hint"""
        transcription_service.initialize()

        # Test with language hint
        result = transcription_service.transcribe("/test/audio.wav", language="de")

        assert result.language == "de"

    def test_transcribe_with_timestamps(self, transcription_service):
        """Test timestamped transcription"""
        transcription_service.initialize()

        result = transcription_service.transcribe_with_timestamps("/test/audio.wav")

        # Should return more detailed segments
        assert isinstance(result, TranscriptionResult)
        assert len(result.segments) > 0

        # Verify segment timing
        for segment in result.segments:
            assert isinstance(segment.start_time, float)
            assert isinstance(segment.end_time, float)
            assert segment.start_time < segment.end_time

    def test_transcribe_batch_processing(self, transcription_service):
        """Test batch transcription processing"""
        transcription_service.initialize()

        audio_files = ["/test/audio1.wav", "/test/audio2.wav", "/test/audio3.wav"]
        results = transcription_service.transcribe_batch(audio_files)

        # Should return results for all files
        assert len(results) == len(audio_files)
        assert all(isinstance(result, TranscriptionResult) for result in results)

    def test_transcribe_batch_empty_list(self, transcription_service):
        """Test batch transcription with empty list"""
        transcription_service.initialize()

        results = transcription_service.transcribe_batch([])
        assert isinstance(results, list)
        assert len(results) == 0

    def test_video_support_capability(self, transcription_service):
        """Test video support capabilities"""
        # Video support should be boolean
        supports_video = transcription_service.supports_video()
        assert isinstance(supports_video, bool)

    def test_video_audio_extraction(self, transcription_service):
        """Test video to audio extraction"""
        if not transcription_service.supports_video():
            pytest.skip("Service doesn't support video")

        # Test audio extraction
        video_path = "/test/video.mp4"
        audio_path = transcription_service.extract_audio_from_video(video_path)

        assert isinstance(audio_path, str)
        assert len(audio_path) > 0

        # Test with custom output path
        custom_output = "/test/custom_audio.wav"
        audio_path_custom = transcription_service.extract_audio_from_video(video_path, custom_output)
        assert audio_path_custom == custom_output

    def test_supported_languages(self, transcription_service):
        """Test supported languages functionality"""
        languages = transcription_service.get_supported_languages()

        # Should return list of language codes
        assert isinstance(languages, list)
        assert all(isinstance(lang, str) for lang in languages)
        assert all(len(lang) >= 2 for lang in languages)  # ISO language codes

    def test_error_handling_patterns(self, transcription_service):
        """Test consistent error handling patterns"""
        # Test uninitialized service
        with pytest.raises(RuntimeError):
            transcription_service.transcribe("/test/audio.wav")

        with pytest.raises(RuntimeError):
            transcription_service.transcribe_with_timestamps("/test/audio.wav")

        with pytest.raises(RuntimeError):
            transcription_service.transcribe_batch(["/test/audio.wav"])


class TestTranscriptionResultDataStructures:
    """Test TranscriptionResult and TranscriptionSegment data structures"""

    def test_transcription_segment_creation(self):
        """Test TranscriptionSegment creation and properties"""
        segment = TranscriptionSegment(
            start_time=0.0, end_time=5.0, text="Test segment", confidence=0.95, speaker="Speaker1"
        )

        assert segment.start_time == 0.0
        assert segment.end_time == 5.0
        assert segment.text == "Test segment"
        assert segment.confidence == 0.95
        assert segment.speaker == "Speaker1"

    def test_transcription_segment_optional_fields(self):
        """Test TranscriptionSegment with optional fields"""
        # Minimal segment
        segment = TranscriptionSegment(start_time=1.0, end_time=2.0, text="Minimal segment")

        assert segment.confidence is None
        assert segment.speaker is None
        assert isinstance(segment.metadata, dict)

    def test_transcription_segment_with_metadata(self):
        """Test TranscriptionSegment with metadata"""
        metadata = {"source": "microphone", "noise_level": 0.1}
        segment = TranscriptionSegment(start_time=0.0, end_time=1.0, text="Segment with metadata", metadata=metadata)

        assert segment.metadata == metadata

    def test_transcription_result_creation(self):
        """Test TranscriptionResult creation and properties"""
        segments = [TranscriptionSegment(0.0, 2.0, "First segment"), TranscriptionSegment(2.0, 4.0, "Second segment")]

        result = TranscriptionResult(
            full_text="First segment Second segment", segments=segments, language="en", duration=4.0
        )

        assert result.full_text == "First segment Second segment"
        assert len(result.segments) == 2
        assert result.language == "en"
        assert result.duration == 4.0

    def test_transcription_result_optional_fields(self):
        """Test TranscriptionResult with optional fields"""
        # Minimal result
        result = TranscriptionResult(full_text="Test transcription", segments=[])

        assert result.language is None
        assert result.duration is None
        assert result.metadata is None

    def test_transcription_result_with_metadata(self):
        """Test TranscriptionResult with metadata"""
        metadata = {"model": "whisper", "processing_time": 1.5}
        result = TranscriptionResult(full_text="Test", segments=[], metadata=metadata)

        assert result.metadata == metadata


class TestInterfaceContractEnforcement:
    """Test that the interface contract is properly enforced"""

    def test_all_methods_must_be_implemented(self):
        """Test that all abstract methods must be implemented"""

        # Incomplete implementation should fail
        class IncompleteService(ITranscriptionService):
            def initialize(self):
                pass

            # Missing other required methods

        with pytest.raises(TypeError):
            IncompleteService()

    def test_property_contracts(self, transcription_service):
        """Test that all properties follow the interface contract"""
        # Service name must be string
        assert isinstance(transcription_service.service_name, str)

        # Is initialized must be boolean
        assert isinstance(transcription_service.is_initialized, bool)

        # Model info must be dictionary
        assert isinstance(transcription_service.model_info, dict)

    def test_method_signatures(self, transcription_service):
        """Test that method signatures match the interface"""
        # Methods should be callable
        assert callable(transcription_service.initialize)
        assert callable(transcription_service.transcribe)
        assert callable(transcription_service.transcribe_with_timestamps)
        assert callable(transcription_service.transcribe_batch)
        assert callable(transcription_service.supports_video)
        assert callable(transcription_service.extract_audio_from_video)
        assert callable(transcription_service.get_supported_languages)
        assert callable(transcription_service.cleanup)

    def test_return_type_contracts(self, transcription_service):
        """Test that return types match the interface contract"""
        transcription_service.initialize()

        # transcribe should return TranscriptionResult
        result = transcription_service.transcribe("/test/audio.wav")
        assert isinstance(result, TranscriptionResult)

        # transcribe_batch should return list of TranscriptionResult
        batch_results = transcription_service.transcribe_batch(["/test/audio.wav"])
        assert isinstance(batch_results, list)
        assert all(isinstance(r, TranscriptionResult) for r in batch_results)

        # supports_video should return bool
        assert isinstance(transcription_service.supports_video(), bool)

        # get_supported_languages should return list of strings
        languages = transcription_service.get_supported_languages()
        assert isinstance(languages, list)
        assert all(isinstance(lang, str) for lang in languages)

        # extract_audio_from_video should return string
        if transcription_service.supports_video():
            audio_path = transcription_service.extract_audio_from_video("/test/video.mp4")
            assert isinstance(audio_path, str)
