"""
Script to help convert hardcoded URLs in test files to use url_builder pattern.
This script identifies and provides replacement suggestions for hardcoded API URLs.

Usage:
    python convert_hardcoded_urls.py [test_directory]

If no directory is provided, scans all test files in the current directory.
"""

import glob
import os
import re

# This script can run standalone without importing the app
# It focuses on static analysis of test files

# Mapping of hardcoded URLs to their route names
URL_MAPPINGS = {
    # Auth endpoints
    '"/api/auth/me"': 'url_builder.url_for("auth_get_current_user")',
    "'/api/auth/me'": 'url_builder.url_for("auth_get_current_user")',
    '"/api/auth/login"': '# Note: FastAPI-Users handles this, use client.post("/api/auth/login")',
    "'/api/auth/login'": '# Note: FastAPI-Users handles this, use client.post("/api/auth/login")',
    '"/api/auth/register"': '# Note: FastAPI-Users handles this, use client.post("/api/auth/register")',
    "'/api/auth/register'": '# Note: FastAPI-Users handles this, use client.post("/api/auth/register")',
    '"/api/auth/logout"': '# Note: FastAPI-Users handles this, use client.post("/api/auth/logout")',
    "'/api/auth/logout'": '# Note: FastAPI-Users handles this, use client.post("/api/auth/logout")',
    # Video endpoints
    '"/api/videos"': 'url_builder.url_for("get_videos")',
    "'/api/videos'": 'url_builder.url_for("get_videos")',
    '"/api/videos/upload"': 'url_builder.url_for("upload_video_generic")',
    "'/api/videos/upload'": 'url_builder.url_for("upload_video_generic")',
    # Vocabulary endpoints
    '"/api/vocabulary/library/stats"': 'url_builder.url_for("get_library_stats")',
    "'/api/vocabulary/library/stats'": 'url_builder.url_for("get_library_stats")',
    '"/api/vocabulary/stats"': 'url_builder.url_for("get_vocabulary_stats")',
    "'/api/vocabulary/stats'": 'url_builder.url_for("get_vocabulary_stats")',
    '"/api/vocabulary/blocking-words"': 'url_builder.url_for("get_blocking_words")',
    "'/api/vocabulary/blocking-words'": 'url_builder.url_for("get_blocking_words")',
    '"/api/vocabulary/mark-known"': 'url_builder.url_for("mark_word_known")',
    "'/api/vocabulary/mark-known'": 'url_builder.url_for("mark_word_known")',
    '"/api/vocabulary/preload"': 'url_builder.url_for("preload_vocabulary")',
    "'/api/vocabulary/preload'": 'url_builder.url_for("preload_vocabulary")',
    # Processing endpoints
    '"/api/processing/transcribe"': 'url_builder.url_for("transcribe_video")',
    "'/api/processing/transcribe'": 'url_builder.url_for("transcribe_video")',
    '"/api/processing/filter-subtitles"': 'url_builder.url_for("filter_subtitles")',
    "'/api/processing/filter-subtitles'": 'url_builder.url_for("filter_subtitles")',
    '"/api/processing/translate-subtitles"': 'url_builder.url_for("translate_subtitles")',
    "'/api/processing/translate-subtitles'": 'url_builder.url_for("translate_subtitles")',
    '"/api/processing/chunk"': 'url_builder.url_for("process_chunk")',
    "'/api/processing/chunk'": 'url_builder.url_for("process_chunk")',
    # Profile endpoints
    '"/api/profile"': 'url_builder.url_for("profile_get")',
    "'/api/profile'": 'url_builder.url_for("profile_get")',
    '"/api/profile/languages"': 'url_builder.url_for("profile_get_supported_languages")',
    "'/api/profile/languages'": 'url_builder.url_for("profile_get_supported_languages")',
    '"/api/profile/settings"': 'url_builder.url_for("profile_get_settings")',
    "'/api/profile/settings'": 'url_builder.url_for("profile_get_settings")',
    # Progress endpoints
    '"/api/progress/user"': 'url_builder.url_for("progress_get_user")',
    "'/api/progress/user'": 'url_builder.url_for("progress_get_user")',
    '"/api/progress/update"': 'url_builder.url_for("progress_update_user")',
    "'/api/progress/update'": 'url_builder.url_for("progress_update_user")',
    '"/api/progress/daily"': 'url_builder.url_for("progress_get_daily")',
    "'/api/progress/daily'": 'url_builder.url_for("progress_get_daily")',
    # Debug endpoints
    '"/api/debug/health"': 'url_builder.url_for("debug_health")',
    "'/api/debug/health'": 'url_builder.url_for("debug_health")',
    # Game endpoints
    '"/api/game/start"': 'url_builder.url_for("game_start_session")',
    "'/api/game/start'": 'url_builder.url_for("game_start_session")',
    '"/api/game/sessions"': 'url_builder.url_for("game_get_user_sessions")',
    "'/api/game/sessions'": 'url_builder.url_for("game_get_user_sessions")',
    '"/api/game/answer"': 'url_builder.url_for("game_submit_answer")',
    "'/api/game/answer'": 'url_builder.url_for("game_submit_answer")',
    # Logs endpoints
    '"/api/logs/frontend"': 'url_builder.url_for("logs_receive_frontend")',
    "'/api/logs/frontend'": 'url_builder.url_for("logs_receive_frontend")',
}

# Dynamic URL patterns that need special handling
DYNAMIC_PATTERNS = [
    # Pattern: f"/api/videos/{series}/{episode}" -> url_builder.url_for("stream_video", series=series, episode=episode)
    (r'f"/api/videos/\{([^}]+)\}/\{([^}]+)\}"', r'url_builder.url_for("stream_video", \1=\1, \2=\2)'),
    (r"f'/api/videos/\{([^}]+)\}/\{([^}]+)\}'", r'url_builder.url_for("stream_video", \1=\1, \2=\2)'),
    # Pattern: f"/api/videos/{video_id}/status" -> url_builder.url_for("get_video_status", video_id=video_id)
    (r'f"/api/videos/\{([^}]+)\}/status"', r'url_builder.url_for("get_video_status", \1=\1)'),
    (r"f'/api/videos/\{([^}]+)\}/status'", r'url_builder.url_for("get_video_status", \1=\1)'),
    # Pattern: f"/api/videos/{video_id}/vocabulary" -> url_builder.url_for("get_video_vocabulary", video_id=video_id)
    (r'f"/api/videos/\{([^}]+)\}/vocabulary"', r'url_builder.url_for("get_video_vocabulary", \1=\1)'),
    (r"f'/api/videos/\{([^}]+)\}/vocabulary'", r'url_builder.url_for("get_video_vocabulary", \1=\1)'),
    # Pattern: f"/api/vocabulary/library/{level}" -> url_builder.url_for("get_vocabulary_level", level=level)
    (r'f"/api/vocabulary/library/\{([^}]+)\}"', r'url_builder.url_for("get_vocabulary_level", \1=\1)'),
    (r"f'/api/vocabulary/library/\{([^}]+)\}'", r'url_builder.url_for("get_vocabulary_level", \1=\1)'),
    # Pattern: f"/api/processing/progress/{task_id}" -> url_builder.url_for("get_task_progress", task_id=task_id)
    (r'f"/api/processing/progress/\{([^}]+)\}"', r'url_builder.url_for("get_task_progress", \1=\1)'),
    (r"f'/api/processing/progress/\{([^}]+)\}'", r'url_builder.url_for("get_task_progress", \1=\1)'),
    # Pattern: f"/api/game/session/{session_id}" -> url_builder.url_for("game_get_session", session_id=session_id)
    (r'f"/api/game/session/\{([^}]+)\}"', r'url_builder.url_for("game_get_session", \1=\1)'),
    (r"f'/api/game/session/\{([^}]+)\}'", r'url_builder.url_for("game_get_session", \1=\1)'),
]


def scan_test_files(directory: str = ".", recursive: bool = True) -> dict[str, list[tuple[int, str, str]]]:
    """
    Scan test files for hardcoded URLs and return findings.

    Returns:
        Dict mapping file paths to list of (line_number, original_line, suggested_replacement)
    """
    findings = {}

    pattern = "**/*.py" if recursive else "*.py"
    test_files = glob.glob(os.path.join(directory, pattern), recursive=recursive)

    # Filter to only actual test files and avoid virtual environments/packages
    test_files = [
        f
        for f in test_files
        if ("test_" in os.path.basename(f) or f.endswith("_test.py") or "test" in f.lower())
        and "venv" not in f.lower()
        and "site-packages" not in f
        and "__pycache__" not in f
    ]

    for file_path in test_files:
        file_findings = []
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Skip comments and docstrings
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Look for hardcoded API URLs
                for url_pattern, replacement in URL_MAPPINGS.items():
                    if url_pattern in line:
                        file_findings.append((line_num, line.strip(), replacement))

                # Look for other potential hardcoded URLs
                api_url_patterns = [
                    r'["\']\/api\/[^"\']*["\']',  # "/api/..." or '/api/...'
                    r'client\.(get|post|put|delete|patch)\(["\'][^"\']*["\']',  # client.get("/...")
                ]

                for pattern in api_url_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0] if len(match) == 1 else str(match)

                        # Skip if we already have a mapping for this
                        if any(mapped_url in line for mapped_url in URL_MAPPINGS):
                            continue

                        # Suggest route name based on URL pattern
                        suggested_route = suggest_route_name(match if isinstance(match, str) else line)
                        if suggested_route:
                            suggestion = f'url_builder.url_for("{suggested_route}")'
                            file_findings.append((line_num, line.strip(), suggestion))

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

        if file_findings:
            findings[file_path] = file_findings

    return findings


def suggest_route_name(url_or_line: str) -> str:
    """
    Suggest a route name based on URL pattern.
    """
    # Extract URL from line if needed
    url_match = re.search(r'["\']([^"\']*)["\']', url_or_line)
    url = url_match.group(1) if url_match else url_or_line

    # Common patterns
    route_suggestions = {
        "/api/auth/me": "auth_get_current_user",
        "/api/user/profile": "profile_get",
        "/api/videos/stream/": "stream_video",  # with parameter
        "/api/vocabulary/stats": "vocab_get_stats",
        "/api/progress/user": "progress_get_user",
        "/api/game/session": "game_start_session",
        "/api/debug/health": "debug_health",
        "/api/logs/files": "logs_list_files",
    }

    for pattern, route_name in route_suggestions.items():
        if pattern in url:
            return route_name

    # Generic suggestion based on URL structure
    parts = [p for p in url.split("/") if p and p != "api"]
    if len(parts) >= 2:
        return f"{parts[0]}_{parts[1]}"
    elif len(parts) == 1:
        return f"{parts[0]}_endpoint"

    return "unknown_route"


def generate_conversion_report(directory: str = "."):
    """
    Generate and print a conversion report for hardcoded URLs.
    """
    print("🔍 HARDCODED URL SCAN RESULTS")
    print("=" * 40)

    findings = scan_test_files(directory)

    if not findings:
        print("✅ No hardcoded URLs found! Your tests are already robust.")
        return

    total_issues = sum(len(issues) for issues in findings.values())
    print(f"Found {total_issues} potential hardcoded URLs in {len(findings)} files\n")

    for file_path, issues in findings.items():
        print(f"📄 {file_path}")
        print("-" * len(file_path))

        for line_num, original_line, suggestion in issues:
            print(f"  Line {line_num}: {original_line}")
            print(f"  Suggestion: {suggestion}")
            print()

    print("💡 SUGGESTED FIXTURE ADDITION")
    print("=" * 30)
    print("""
Add this fixture to your test files:

@pytest.fixture
def url_builder(client):
    '''URL builder fixture for robust URL generation'''
    from tests.utils.url_builder import get_url_builder
    return get_url_builder(client.app)

Then use url_builder.url_for("route_name") instead of hardcoded URLs.
""")


if __name__ == "__main__":
    generate_conversion_report()
