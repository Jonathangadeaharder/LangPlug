#!/usr/bin/env python3
"""
Script to run all currently passing tests.
This provides a baseline for verifying that core functionality works.
"""
import os
import subprocess
import sys


def run_tests():
    """Run all currently passing tests with 60s timeout."""
    # Get the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # Change to backend directory
    os.chdir(backend_dir)

    # Test command with timeout
    cmd = [
        "api_venv/Scripts/python.exe", "-m", "pytest",
        # Unit tests that pass
        "tests/unit/test_subtitle_chunk_generation.py",
        "tests/unit/test_vocabulary_service.py",
        "tests/services/test_auth_service.py::TestAuthService::test_init",
        "tests/services/test_auth_service.py::TestAuthService::test_hash_password",
        "tests/services/test_auth_service.py::TestAuthService::test_register_user_success",
        "tests/services/test_auth_service.py::TestAuthService::test_register_user_invalid_username",
        "tests/services/test_auth_service.py::TestAuthService::test_register_user_invalid_password",
        "tests/services/test_auth_service.py::TestAuthService::test_register_user_already_exists",
        "tests/services/test_auth_service.py::TestAuthService::test_login_invalid_credentials",
        "tests/services/test_auth_service.py::TestAuthService::test_validate_session_expired",
        "tests/services/test_auth_service.py::TestAuthService::test_logout",
        "tests/services/test_auth_service.py::TestAuthService::test_update_language_preferences",
        # API tests that pass
        "tests/api/test_auth_simple.py",
        "tests/api/test_endpoints.py",
        "tests/api/test_debug_endpoint.py",
        "tests/api/test_minimal_post.py",
        "tests/api/test_video_contract.py::TestVideoContract::test_stream_video_endpoint_contract",
        "tests/api/test_video_contract.py::TestVideoContract::test_stream_video_not_found_contract",
        "tests/api/test_video_contract.py::TestVideoContract::test_video_endpoints_content_type_contract",
        "tests/api/test_video_contract.py::TestVideoContract::test_video_path_validation_contract",
        "tests/api/test_video_contract.py::TestVideoContract::test_video_authentication_contract",
        "tests/api/test_videos_errors.py::test_subtitles_404",
        "tests/api/test_videos_errors.py::test_stream_video_unknown_series",
        "tests/api/test_videos_errors.py::test_upload_subtitle_missing_video",
        "tests/api/test_auth_endpoints.py::test_register_endpoint",
        # Add timeout and verbose flags
        "-v", "--timeout=60"
    ]

    print("Running passing tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        # Run the tests
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=300)

        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Check result
        if result.returncode == 0:
            print("\n[PASS] All passing tests completed successfully!")
            return True
        else:
            print(f"\n[FAIL] Tests failed with return code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("[FAIL] Tests timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"[ERROR] Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
