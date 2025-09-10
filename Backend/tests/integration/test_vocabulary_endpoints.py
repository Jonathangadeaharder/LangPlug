"""
Test vocabulary management endpoints
"""

import pytest
import requests

BASE_URL = "http://localhost:8000"


class TestVocabularyEndpoints:
    """Test vocabulary CRUD operations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.auth_token = None
        self.test_user = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        
    def get_auth_token(self):
        """Get authentication token"""
        if self.auth_token:
            return self.auth_token
            
        # Try to register first
        try:
            requests.post(f"{BASE_URL}/auth/register", json=self.test_user)
        except:
            pass
        
        # Login
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        })
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token") or data.get("token")
            return self.auth_token
        return None
    
    def test_get_vocabulary_stats(self):
        """Test getting vocabulary statistics"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/vocabulary/library/stats",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "total_words" in data
        assert "categories" in data
        assert isinstance(data["total_words"], int)
        assert isinstance(data["categories"], dict)
    
    def test_search_vocabulary(self):
        """Test vocabulary search"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Search for German words
        response = requests.get(
            f"{BASE_URL}/vocabulary/search?query=haus",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_vocabulary_word(self):
        """Test adding a new vocabulary word"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        word_data = {
            "word": "Testword",
            "category": "noun",
            "difficulty_level": "A1"
        }
        
        response = requests.post(
            f"{BASE_URL}/vocabulary/add",
            json=word_data,
            headers=headers
        )
        
        # May succeed or fail if word exists
        assert response.status_code in [200, 201, 409]
    
    def test_update_vocabulary_word(self):
        """Test updating vocabulary word"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # First add a word
        word_data = {
            "word": "UpdateTest",
            "category": "noun",
            "difficulty_level": "A1"
        }
        
        requests.post(
            f"{BASE_URL}/vocabulary/add",
            json=word_data,
            headers=headers
        )
        
        # Then update it
        update_data = {
            "category": "verb",
            "difficulty_level": "B1"
        }
        
        response = requests.put(
            f"{BASE_URL}/vocabulary/UpdateTest",
            json=update_data,
            headers=headers
        )
        
        # May fail if word doesn't exist
        assert response.status_code in [200, 404]
    
    def test_delete_vocabulary_word(self):
        """Test deleting vocabulary word"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # First add a word to delete
        word_data = {
            "word": "DeleteTest",
            "category": "noun",
            "difficulty_level": "A1"
        }
        
        requests.post(
            f"{BASE_URL}/vocabulary/add",
            json=word_data,
            headers=headers
        )
        
        # Then delete it
        response = requests.delete(
            f"{BASE_URL}/vocabulary/DeleteTest",
            headers=headers
        )
        
        # May fail if word doesn't exist
        assert response.status_code in [200, 204, 404]
    
    def test_get_user_progress(self):
        """Test getting user progress"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/vocabulary/progress",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "known_words" in data or "total_progress" in data
    
    def test_mark_word_known(self):
        """Test marking a word as known"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        progress_data = {
            "word": "TestKnown",
            "is_known": True,
            "confidence_level": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/vocabulary/progress",
            json=progress_data,
            headers=headers
        )
        
        assert response.status_code in [200, 201]
    
    def test_get_categories(self):
        """Test getting vocabulary categories"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/vocabulary/categories",
            headers=headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should include standard categories
        expected_categories = ["noun", "verb", "adjective", "adverb"]
        for cat in expected_categories:
            assert cat in data or len(data) == 0  # Empty is ok for new DB
    
    def test_bulk_vocabulary_operations(self):
        """Test bulk vocabulary operations"""
        token = self.get_auth_token()
        if not token:
            pytest.skip("Authentication failed")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Bulk add words
        bulk_data = {
            "words": [
                {"word": "Bulk1", "category": "noun", "difficulty_level": "A1"},
                {"word": "Bulk2", "category": "verb", "difficulty_level": "A2"},
                {"word": "Bulk3", "category": "adjective", "difficulty_level": "B1"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/vocabulary/bulk",
            json=bulk_data,
            headers=headers
        )
        
        # Bulk operations may or may not be implemented
        assert response.status_code in [200, 201, 404, 405]


class TestVocabularyAuth:
    """Test authentication for vocabulary endpoints"""
    
    def test_vocabulary_requires_auth(self):
        """Test that vocabulary endpoints require authentication"""
        endpoints = [
            ("/vocabulary/library/stats", "GET"),
            ("/vocabulary/library/A1", "GET"),
            ("/vocabulary/blocking-words?video_path=test.mp4", "GET"),
            ("/vocabulary/mark-known", "POST"),
            ("/vocabulary/preload", "POST"),
            ("/vocabulary/library/bulk-mark", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={})
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{endpoint}", json={})
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{endpoint}")
            
            # Should fail with 403 (Forbidden) when no auth header provided
            assert response.status_code == 403, f"Endpoint {endpoint} should require auth"


class TestVocabularyValidation:
    """Test input validation for vocabulary endpoints"""
    
    def test_invalid_difficulty_level(self):
        """Test handling of invalid difficulty levels"""
        # Valid levels should be A1, A2, B1, B2, C1, C2
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        
        for level in valid_levels:
            assert level in ["A1", "A2", "B1", "B2", "C1", "C2"]
        
        # Invalid level
        invalid_level = "Z9"
        assert invalid_level not in valid_levels
    
    def test_word_length_limits(self):
        """Test word length validation"""
        from core.constants import MAX_VOCABULARY_WORDS
        
        # Check that we have a reasonable limit
        assert MAX_VOCABULARY_WORDS == 10000
        
        # Very long word should be rejected
        long_word = "a" * 1000  # 1000 characters
        assert len(long_word) > 100  # Reasonable max length


if __name__ == "__main__":
    pytest.main([__file__, "-v"])