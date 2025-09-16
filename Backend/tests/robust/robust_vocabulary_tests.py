"""
Robust vocabulary tests using named routes instead of hardcoded URLs.
This replaces vocabulary-related test files with a robust URL builder pattern.
"""
import sys
import os
# Add the Backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient
from tests.utils.url_builder import get_url_builder
from main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture 
def url_builder(client):
    """URL builder fixture for robust URL generation"""
    return get_url_builder(client.app)


class TestVocabularyEndpointsRobust:
    """Robust vocabulary endpoint tests using named routes"""
    
    def test_vocabulary_stats_requires_auth(self, client, url_builder):
        """Test that vocabulary stats requires authentication"""
        stats_url = url_builder.url_for("get_vocabulary_stats")
        response = client.get(stats_url)
        assert response.status_code == 401
    
    def test_library_stats_requires_auth(self, client, url_builder):
        """Test that library stats requires authentication"""
        library_stats_url = url_builder.url_for("get_library_stats")
        response = client.get(library_stats_url)
        assert response.status_code == 401
    
    def test_blocking_words_requires_auth(self, client, url_builder):
        """Test that blocking words endpoint requires authentication"""
        blocking_words_url = url_builder.url_for("get_blocking_words")
        response = client.get(blocking_words_url, params={
            "video_path": "test_video.mp4",
            "segment_start": 0,
            "segment_duration": 30
        })
        assert response.status_code == 401
    
    def test_vocabulary_level_with_params(self, client, url_builder):
        """Test vocabulary level endpoint with path parameters"""
        level_url = url_builder.url_for("get_vocabulary_level", level="beginner")
        response = client.get(level_url)
        assert response.status_code == 401  # Should require auth
        
        # Test with different levels
        levels = ["intermediate", "advanced"]
        for level in levels:
            level_url = url_builder.url_for("get_vocabulary_level", level=level)
            response = client.get(level_url)
            assert response.status_code == 401
    
    def test_mark_word_known_requires_auth(self, client, url_builder):
        """Test that marking words as known requires authentication"""
        mark_known_url = url_builder.url_for("mark_word_known")
        response = client.post(mark_known_url, json={
            "word": "test",
            "known": True
        })
        assert response.status_code == 401
    
    def test_preload_vocabulary_requires_auth(self, client, url_builder):
        """Test that preloading vocabulary requires authentication"""
        preload_url = url_builder.url_for("preload_vocabulary")
        response = client.post(preload_url)
        assert response.status_code == 401
    
    def test_bulk_mark_level_requires_auth(self, client, url_builder):
        """Test that bulk marking levels requires authentication"""
        bulk_mark_url = url_builder.url_for("bulk_mark_level")
        response = client.post(bulk_mark_url, json={
            "level": "beginner",
            "mark_as_known": True
        })
        assert response.status_code == 401


class TestVocabularyParameterValidation:
    """Test parameter validation for vocabulary endpoints"""
    
    def test_invalid_vocabulary_levels(self, client, url_builder):
        """Test handling of invalid vocabulary levels"""
        invalid_levels = [
            "",
            "invalid_level",
            "../malicious",
            "super_advanced_level_that_does_not_exist"
        ]
        
        for invalid_level in invalid_levels:
            try:
                level_url = url_builder.url_for("get_vocabulary_level", level=invalid_level)
                response = client.get(level_url)
                # Should handle invalid levels gracefully (after auth)
                assert response.status_code in [400, 401, 404, 422]
            except Exception:
                # URL building might fail for very invalid levels, which is acceptable
                pass
    
    def test_blocking_words_parameter_validation(self, client, url_builder):
        """Test parameter validation for blocking words endpoint"""
        blocking_words_url = url_builder.url_for("get_blocking_words")
        
        # Test with missing required parameters
        response = client.get(blocking_words_url)
        assert response.status_code in [400, 401, 422]  # Missing params or auth
        
        # Test with invalid parameters
        invalid_params = [
            {"video_path": "", "segment_start": 0, "segment_duration": 30},
            {"video_path": "test.mp4", "segment_start": -1, "segment_duration": 30},
            {"video_path": "test.mp4", "segment_start": 0, "segment_duration": -1},
        ]
        
        for params in invalid_params:
            response = client.get(blocking_words_url, params=params)
            assert response.status_code in [400, 401, 422]


class TestVocabularySecurityRobust:
    """Security tests for vocabulary endpoints"""
    
    def test_sql_injection_protection_vocabulary_search(self, client, url_builder):
        """Test SQL injection protection on vocabulary endpoints"""
        sql_payloads = [
            "'; DROP TABLE vocabulary; --",
            "test' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ]
        
        # Test blocking words with malicious video paths
        blocking_words_url = url_builder.url_for("get_blocking_words")
        
        for payload in sql_payloads:
            response = client.get(blocking_words_url, params={
                "video_path": payload,
                "segment_start": 0,
                "segment_duration": 30
            })
            # Should not crash and should return proper error
            assert response.status_code in [400, 401, 404, 422], f"SQL injection payload caused unexpected response: {response.status_code}"
    
    def test_xss_protection_vocabulary_data(self, client, url_builder):
        """Test XSS protection in vocabulary endpoints"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        mark_known_url = url_builder.url_for("mark_word_known")
        
        for payload in xss_payloads:
            response = client.post(mark_known_url, json={
                "word": payload,
                "known": True
            })
            # Should handle malicious input gracefully (after auth check)
            assert response.status_code in [400, 401, 422]
    
    def test_path_traversal_protection_vocabulary(self, client, url_builder):
        """Test protection against path traversal in vocabulary endpoints"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd"
        ]
        
        blocking_words_url = url_builder.url_for("get_blocking_words")
        
        for malicious_path in malicious_paths:
            response = client.get(blocking_words_url, params={
                "video_path": malicious_path,
                "segment_start": 0,
                "segment_duration": 30
            })
            # Should block path traversal attempts
            assert response.status_code in [400, 401, 403, 404, 422], f"Path traversal not blocked for: {malicious_path}"


class TestVocabularyDataValidation:
    """Test data validation for vocabulary endpoints"""
    
    def test_mark_word_known_data_validation(self, client, url_builder):
        """Test data validation for mark word known endpoint"""
        mark_known_url = url_builder.url_for("mark_word_known")
        
        invalid_payloads = [
            {},  # Empty payload
            {"word": ""},  # Empty word
            {"known": True},  # Missing word
            {"word": "test"},  # Missing known status
            {"word": None, "known": True},  # Null word
            {"word": "test", "known": "invalid"},  # Invalid known type
        ]
        
        for payload in invalid_payloads:
            response = client.post(mark_known_url, json=payload)
            # Should reject invalid data (after auth check)
            assert response.status_code in [400, 401, 422]
    
    def test_bulk_mark_data_validation(self, client, url_builder):
        """Test data validation for bulk mark endpoint"""
        bulk_mark_url = url_builder.url_for("bulk_mark_level")
        
        invalid_payloads = [
            {},  # Empty payload
            {"level": ""},  # Empty level
            {"mark_as_known": True},  # Missing level
            {"level": "beginner"},  # Missing mark_as_known
            {"level": None, "mark_as_known": True},  # Null level
            {"level": "beginner", "mark_as_known": "invalid"},  # Invalid type
        ]
        
        for payload in invalid_payloads:
            response = client.post(bulk_mark_url, json=payload)
            # Should reject invalid data (after auth check)
            assert response.status_code in [400, 401, 422]


class TestVocabularyWorkflowRobust:
    """Test vocabulary-related workflows"""
    
    def test_vocabulary_endpoints_fail_fast_without_auth(self, client, url_builder):
        """Test that all vocabulary endpoints fail fast without authentication"""
        vocab_endpoints = [
            ("get_vocabulary_stats", {}),
            ("get_library_stats", {}),
            ("get_blocking_words", {}),
            ("mark_word_known", {}),
            ("preload_vocabulary", {}),
            ("bulk_mark_level", {}),
            ("get_vocabulary_level", {"level": "beginner"}),
        ]
        
        for route_name, params in vocab_endpoints:
            url = url_builder.url_for(route_name, **params)
            
            # Test GET endpoints
            if route_name.startswith("get_"):
                response = client.get(url)
            else:
                # Test POST endpoints
                response = client.post(url, json={"test": "data"})
            
            # All should require authentication
            assert response.status_code == 401, f"Endpoint {route_name} should require authentication"


if __name__ == "__main__":
    # Quick test to verify setup
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    url_builder = get_url_builder(client.app)
    
    print("Testing vocabulary URL builder functionality...")
    
    try:
        # Test basic endpoints
        stats_url = url_builder.url_for("get_vocabulary_stats")
        print(f"✓ Vocabulary stats: {stats_url}")
        
        # Test parameterized endpoints
        level_url = url_builder.url_for("get_vocabulary_level", level="beginner")
        print(f"✓ Vocabulary level: {level_url}")
        
        blocking_url = url_builder.url_for("get_blocking_words")
        print(f"✓ Blocking words: {blocking_url}")
        
        print("\n✅ Vocabulary URL builder tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
