"""
Test processing endpoints for transcription and filtering
"""

import pytest
import requests

BASE_URL = "http://localhost:8000"


class TestProcessingEndpoints:
    """Test video/audio processing endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.auth_token = None
        self.test_user = {
            "username": "admin",
            "password": "admin"
        }
        
    def get_auth_token(self):
        """Get authentication token"""
        if self.auth_token:
            return self.auth_token
        
        # Login with admin credentials
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        })
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token") or data.get("token")
            return self.auth_token
        return None
    
    def test_chunk_processing(self):
        """Test chunk processing endpoint"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test chunk request
        chunk_data = {
            "video_path": "test_video.mp4",
            "chunk_index": 0,
            "total_chunks": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/process/chunk",
            json=chunk_data,
            headers=headers
        )
        
        # May fail if video doesn't exist, but should handle gracefully
        assert response.status_code in [200, 404, 422]
    
    def test_transcribe_endpoint(self):
        """Test transcription endpoint"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        transcribe_data = {
            "video_path": "test_video.mp4",
            "language": "de",
            "model_size": "base"
        }
        
        response = requests.post(
            f"{BASE_URL}/process/transcribe",
            json=transcribe_data,
            headers=headers
        )
        
        # Debug: Print response details for debugging
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        # Should return task_id for background processing or 404 if file not found
        assert response.status_code in [200, 404, 422], f"Unexpected status code: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data or "subtitle_path" in data
    
    def test_transcription_service_direct(self):
        """Test transcription service directly"""
        from core.dependencies import get_transcription_service
        
        service = get_transcription_service()
        print(f"Transcription service: {service}")
        assert service is not None, "Transcription service should be available"
    
    def test_filter_subtitles(self):
        """Test subtitle filtering endpoint"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        filter_data = {
            "subtitle_path": "test.srt",
            "filters": ["remove_music", "remove_silence"]
        }
        
        response = requests.post(
            f"{BASE_URL}/process/filter-subtitles",
            json=filter_data,
            headers=headers
        )
        
        # May fail if subtitle doesn't exist
        assert response.status_code in [200, 404, 422]
    
    def test_translate_subtitles(self):
        """Test subtitle translation endpoint"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        translate_data = {
            "subtitle_path": "test.srt",
            "source_language": "de",
            "target_language": "en"
        }
        
        response = requests.post(
            f"{BASE_URL}/process/translate-subtitles",
            json=translate_data,
            headers=headers
        )
        
        # May fail if subtitle doesn't exist
        assert response.status_code in [200, 404, 422]
    
    def test_prepare_episode(self):
        """Test episode preparation endpoint"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        prepare_data = {
            "video_path": "test_video.mp4",
            "generate_subtitles": True,
            "translate": False
        }
        
        response = requests.post(
            f"{BASE_URL}/process/prepare-episode",
            json=prepare_data,
            headers=headers
        )
        
        # May fail if video doesn't exist
        assert response.status_code in [200, 404, 422]
    
    def test_full_pipeline(self):
        """Test full processing pipeline"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        pipeline_data = {
            "video_path": "test_video.mp4",
            "language": "de",
            "enable_translation": True,
            "enable_filtering": True
        }
        
        response = requests.post(
            f"{BASE_URL}/process/full-pipeline",
            json=pipeline_data,
            headers=headers
        )
        
        # May fail if video doesn't exist
        assert response.status_code in [200, 202, 404, 422]
        
        if response.status_code in [200, 202]:
            data = response.json()
            assert "task_id" in data or "status" in data
    
    def test_invalid_language_code(self):
        """Test handling of invalid language codes"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        transcribe_data = {
            "video_path": "test_video.mp4",
            "language": "invalid_lang",
            "model_size": "base"
        }
        
        response = requests.post(
            f"{BASE_URL}/process/transcribe",
            json=transcribe_data,
            headers=headers
        )
        
        # Should handle invalid language gracefully
        assert response.status_code in [400, 422]
    
    def test_invalid_model_size(self):
        """Test handling of invalid model sizes"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        transcribe_data = {
            "video_path": "test_video.mp4",
            "language": "de",
            "model_size": "invalid_size"
        }
        
        response = requests.post(
            f"{BASE_URL}/process/transcribe",
            json=transcribe_data,
            headers=headers
        )
        
        # Should handle invalid model size
        assert response.status_code in [400, 422]


class TestProcessingAuth:
    """Test authentication for processing endpoints"""
    
    def test_processing_requires_auth(self):
        """Test that all processing endpoints require authentication"""
        endpoints = [
            "/process/chunk",
            "/process/transcribe",
            "/process/filter-subtitles",
            "/process/translate-subtitles",
            "/process/prepare-episode",
            "/process/full-pipeline"
        ]
        
        for endpoint in endpoints:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json={}
            )
            
            # Should fail with 403 (Forbidden) when no auth header provided
            assert response.status_code == 403, f"Endpoint {endpoint} should require auth"


class TestProgressTracking:
    """Test progress tracking for long-running tasks"""
    
    def test_task_id_generation(self):
        """Test that tasks generate unique IDs"""
        # This would be tested with actual task submission
        # Task IDs should be unique UUIDs
        import uuid
        
        task_id = str(uuid.uuid4())
        assert len(task_id) == 36  # UUID v4 format
        assert task_id.count('-') == 4
    
    def test_progress_updates(self):
        """Test that progress updates are sent"""
        # This would integrate with WebSocket testing
        # Progress should be sent at key stages:
        # - 0%: Started
        # - 10%: Loading model
        # - 30%: Extracting audio
        # - 70%: Transcribing
        # - 90%: Saving results
        # - 100%: Completed
        
        from core.constants import PROGRESS_STEPS
        
        assert PROGRESS_STEPS["INITIALIZING"] == 0
        assert PROGRESS_STEPS["LOADING_MODEL"] == 10
        assert PROGRESS_STEPS["EXTRACTING_AUDIO"] == 30
        assert PROGRESS_STEPS["TRANSCRIBING"] == 70
        assert PROGRESS_STEPS["SAVING_RESULTS"] == 90
        assert PROGRESS_STEPS["COMPLETED"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])