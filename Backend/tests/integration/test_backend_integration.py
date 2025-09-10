"""
Comprehensive Backend Integration Test
Tests all API routes as they would be called from the frontend in a full QA workflow
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional
import sys
import random

class BackendIntegrationTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def add_result(self, test_name: str, success: bool, details: str = ""):
        """Track test results"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        status = "PASSED" if success else "FAILED"
        self.log(f"{test_name}: {status} {details}")
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add auth header if we have a token
        if self.auth_token and 'headers' not in kwargs:
            kwargs['headers'] = {}
        if self.auth_token:
            kwargs.setdefault('headers', {})['Authorization'] = f"Bearer {self.auth_token}"
            
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Log request details
            self.log(f"{method} {endpoint} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                self.log(f"Error response: {response.text}", "ERROR")
                return {"error": response.text, "status_code": response.status_code}
                
            return response.json() if response.text else {}
            
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            return None
            
    # ========== HEALTH CHECK TESTS ==========
    
    def test_health_check(self):
        """Test health endpoint"""
        self.log("=" * 60)
        self.log("Testing Health Check")
        
        result = self.make_request("GET", "/health")
        success = result and "status" in result and result["status"] == "healthy"
        
        self.add_result(
            "Health Check",
            success,
            f"Server version: {result.get('version', 'unknown')}" if result else "Server not responding"
        )
        return success
        
    # ========== AUTHENTICATION TESTS ==========
    
    def test_user_registration(self):
        """Test user registration flow"""
        self.log("=" * 60)
        self.log("Testing User Registration")
        
        # Generate unique username
        username = f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        password = "TestPassword123!"
        
        registration_data = {
            "username": username,
            "password": password
        }
        
        result = self.make_request("POST", "/auth/register", json=registration_data)
        success = result and "id" in result
        
        if success:
            self.user_data = {
                "username": username,
                "password": password,
                "id": result["id"]
            }
            
        self.add_result(
            "User Registration",
            success,
            f"Registered user: {username}" if success else "Registration failed"
        )
        return success
        
    def test_user_login(self):
        """Test user login flow"""
        self.log("=" * 60)
        self.log("Testing User Login")
        
        if not self.user_data:
            self.log("No user data available, registering new user first")
            if not self.test_user_registration():
                self.add_result("User Login", False, "Failed to register user for login test")
                return False
                
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        
        result = self.make_request("POST", "/auth/login", json=login_data)
        success = result and "token" in result
        
        if success:
            self.auth_token = result["token"]
            
        self.add_result(
            "User Login",
            success,
            f"Logged in as: {self.user_data['username']}" if success else "Login failed"
        )
        return success
        
    def test_get_current_user(self):
        """Test getting current user info"""
        self.log("=" * 60)
        self.log("Testing Get Current User")
        
        if not self.auth_token:
            self.add_result("Get Current User", False, "No auth token available")
            return False
            
        result = self.make_request("GET", "/auth/me")
        success = result and "username" in result
        
        self.add_result(
            "Get Current User",
            success,
            f"Current user: {result.get('username', 'unknown')}" if success else "Failed to get user info"
        )
        return success
        
    def test_user_logout(self):
        """Test user logout"""
        self.log("=" * 60)
        self.log("Testing User Logout")
        
        if not self.auth_token:
            self.add_result("User Logout", False, "No auth token available")
            return False
            
        result = self.make_request("POST", "/auth/logout")
        success = result and result.get("success", False)
        
        if success:
            old_token = self.auth_token
            self.auth_token = None
            
            # Verify token is invalid after logout
            self.auth_token = old_token
            verify_result = self.make_request("GET", "/auth/me")
            self.auth_token = None
            
            success = verify_result and "error" in verify_result
            
        self.add_result(
            "User Logout",
            success,
            "Session invalidated successfully" if success else "Logout failed"
        )
        return success
        
    # ========== VOCABULARY TESTS ==========
    
    def test_vocabulary_stats(self):
        """Test vocabulary statistics endpoint"""
        self.log("=" * 60)
        self.log("Testing Vocabulary Stats")
        
        # Need to be logged in
        if not self.auth_token:
            self.test_user_login()
            
        result = self.make_request("GET", "/vocabulary/library/stats")
        success = result and "levels" in result
        
        if success:
            total_words = result.get("total_words", 0)
            details = f"Total words: {total_words}"
        else:
            details = "Failed to get vocabulary stats"
            
        self.add_result("Vocabulary Stats", success, details)
        return success
        
    def test_vocabulary_level(self):
        """Test getting vocabulary for a specific level"""
        self.log("=" * 60)
        self.log("Testing Vocabulary Level Retrieval")
        
        if not self.auth_token:
            self.test_user_login()
            
        levels_tested = []
        all_success = True
        
        for level in ["A1", "A2", "B1", "B2"]:
            result = self.make_request("GET", f"/vocabulary/library/{level}")
            success = result and "error" not in result
            
            if success and "words" in result:
                word_count = len(result.get("words", []))
                levels_tested.append(f"{level}: {word_count} words")
            else:
                levels_tested.append(f"{level}: Failed")
                all_success = False
                
        self.add_result(
            "Vocabulary Levels",
            all_success,
            ", ".join(levels_tested)
        )
        return all_success
        
    def test_mark_word_known(self):
        """Test marking words as known"""
        self.log("=" * 60)
        self.log("Testing Mark Word Known")
        
        if not self.auth_token:
            self.test_user_login()
            
        # First get some words
        result = self.make_request("GET", "/vocabulary/library/A1")
        
        if not result or "words" not in result or len(result["words"]) == 0:
            self.add_result("Mark Word Known", False, "No words available to mark")
            return False
            
        # Mark first word as known
        word = result["words"][0]["word"]
        mark_data = {"word": word, "known": True}
        
        result = self.make_request("POST", "/vocabulary/mark-known", json=mark_data)
        success = result and result.get("success", False)
        
        self.add_result(
            "Mark Word Known",
            success,
            f"Marked '{word}' as known" if success else "Failed to mark word"
        )
        return success
        
    def test_bulk_mark_words(self):
        """Test bulk marking words"""
        self.log("=" * 60)
        self.log("Testing Bulk Mark Words")
        
        if not self.auth_token:
            self.test_user_login()
            
        bulk_data = {
            "level": "A1",
            "known": True
        }
        
        result = self.make_request("POST", "/vocabulary/library/bulk-mark", json=bulk_data)
        success = result and result.get("success", False)
        
        self.add_result(
            "Bulk Mark Words",
            success,
            f"Marked {result.get('marked_count', 0)} words" if success else "Failed to bulk mark"
        )
        return success
        
    # ========== VIDEO/EPISODE TESTS ==========
    
    def test_list_videos(self):
        """Test listing available videos"""
        self.log("=" * 60)
        self.log("Testing List Videos")
        
        if not self.auth_token:
            self.test_user_login()
            
        result = self.make_request("GET", "/videos")
        success = result and isinstance(result, list) and len(result) > 0
        
        video_count = len(result) if success else 0
        
        self.add_result(
            "List Videos",
            success,
            f"Found {video_count} videos" if success else "Failed to list videos"
        )
        return success
        
    def test_get_video_details(self):
        """Test getting video details"""
        self.log("=" * 60)
        self.log("Testing Get Video Details")
        
        if not self.auth_token:
            self.test_user_login()
            
        # First get list of videos
        result = self.make_request("GET", "/videos")
        
        if not result or not isinstance(result, list) or len(result) == 0:
            self.add_result("Get Video Details", False, "No videos available")
            return False
            
        # Get details for first video - videos returns list directly with video objects
        video = result[0]
        success = video and "title" in video and "path" in video
        
        self.add_result(
            "Get Video Details",
            success,
            f"Got details for: {video.get('title', 'unknown')}" if success else "Failed to get details"
        )
        return success
        
    # ========== PROCESSING TESTS ==========
    
    def test_upload_subtitle(self):
        """Test subtitle upload"""
        self.log("=" * 60)
        self.log("Testing Subtitle Upload")
        
        if not self.auth_token:
            self.test_user_login()
            
        # Create a sample SRT content
        srt_content = """1
00:00:01,000 --> 00:00:03,000
Hallo, wie geht es dir?

2
00:00:03,500 --> 00:00:05,500
Mir geht es gut, danke!
"""
        
        files = {
            'subtitle_file': ('test_subtitle.srt', srt_content, 'text/plain')
        }
        
        # Get a valid video path from the videos list first
        videos_result = self.make_request("GET", "/videos")
        if videos_result and isinstance(videos_result, list) and len(videos_result) > 0:
            video_path = videos_result[0]["path"]
        else:
            video_path = 'episode1.mp4'  # fallback
        
        params = {
            'video_path': video_path
        }
        
        result = self.make_request("POST", "/videos/subtitle/upload", files=files, params=params)
        success = result and result.get("success", False)
        
        self.add_result(
            "Subtitle Upload",
            success,
            "Subtitle uploaded successfully" if success else "Failed to upload subtitle"
        )
        return success
        
    def test_blocking_words(self):
        """Test getting blocking words for a video segment"""
        self.log("=" * 60)
        self.log("Testing Blocking Words")
        
        if not self.auth_token:
            self.test_user_login()
            
        params = {
            "video_path": "test_video.mp4",
            "segment_start": 0,
            "segment_duration": 300
        }
        
        result = self.make_request("GET", "/vocabulary/blocking-words", params=params)
        success = result and "blocking_words" in result
        
        word_count = len(result.get("blocking_words", [])) if success else 0
        
        self.add_result(
            "Blocking Words",
            success,
            f"Found {word_count} blocking words" if success else "Failed to get blocking words"
        )
        return success
        
    # ========== MAIN TEST RUNNER ==========
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.log("=" * 60)
        self.log("STARTING BACKEND INTEGRATION TESTS")
        self.log("=" * 60)
        self.log(f"Testing against: {self.base_url}")
        self.log("=" * 60)
        
        start_time = time.time()
        
        # Test categories
        test_suites = [
            ("HEALTH CHECK", [
                self.test_health_check
            ]),
            ("AUTHENTICATION", [
                self.test_user_registration,
                self.test_user_login,
                self.test_get_current_user,
                self.test_user_logout
            ]),
            ("VOCABULARY", [
                self.test_user_login,  # Need to login again after logout
                self.test_vocabulary_stats,
                self.test_vocabulary_level,
                self.test_mark_word_known,
                self.test_bulk_mark_words
            ]),
            ("VIDEOS", [
                self.test_list_videos,
                self.test_get_video_details
            ]),
            ("PROCESSING", [
                self.test_upload_subtitle,
                self.test_blocking_words
            ])
        ]
        
        # Run each test suite
        for suite_name, tests in test_suites:
            self.log("")
            self.log("=" * 60)
            self.log(f"TESTING {suite_name}")
            self.log("=" * 60)
            
            for test in tests:
                try:
                    test()
                    time.sleep(0.5)  # Small delay between tests
                except Exception as e:
                    self.log(f"Test crashed: {e}", "ERROR")
                    self.add_result(test.__name__, False, f"Exception: {str(e)}")
                    
        # Generate summary
        elapsed_time = time.time() - start_time
        self.generate_summary(elapsed_time)
        
    def generate_summary(self, elapsed_time: float):
        """Generate test summary report"""
        self.log("")
        self.log("=" * 60)
        self.log("TEST SUMMARY REPORT")
        self.log("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {failed_tests}")
        self.log(f"Pass Rate: {pass_rate:.1f}%")
        self.log(f"Execution Time: {elapsed_time:.2f} seconds")
        
        if failed_tests > 0:
            self.log("")
            self.log("FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    self.log(f"  FAILED: {result['test']}: {result['details']}")
                    
        if passed_tests > 0:
            self.log("")
            self.log("PASSED TESTS:")
            for result in self.test_results:
                if result["success"]:
                    self.log(f"  PASSED: {result['test']}: {result['details']}")
                    
        # Save results to file
        self.save_results()
        
        # Overall status
        self.log("")
        self.log("=" * 60)
        if pass_rate == 100:
            self.log("ALL TESTS PASSED!")
        elif pass_rate >= 80:
            self.log("MOSTLY PASSING - Some issues to fix")
        elif pass_rate >= 50:
            self.log("PARTIAL SUCCESS - Several issues need attention")
        else:
            self.log("CRITICAL FAILURES - Major issues detected")
        self.log("=" * 60)
        
        return pass_rate == 100
        
    def save_results(self):
        """Save test results to JSON file"""
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_tests": len(self.test_results),
            "passed": sum(1 for r in self.test_results if r["success"]),
            "failed": sum(1 for r in self.test_results if not r["success"]),
            "results": self.test_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"Results saved to: {results_file}")


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code != 200:
            print("ERROR: Backend server is not responding properly")
            print("Please ensure the backend is running on port 8000")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("ERROR: Backend server is not running!")
        print("Please start the backend server first:")
        print("  cd Backend")
        print("  python main.py")
        sys.exit(1)
        
    # Run tests
    tester = BackendIntegrationTest()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)