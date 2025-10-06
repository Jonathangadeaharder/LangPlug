#!/usr/bin/env python3
"""
E2E Smoke Test: Simple Subtitle Verification

Tests: Login → Superstore → Episode 1 → Skip Game → Video with Subtitles

IMPORTANT: This test requires:
1. Backend server running on E2E_BACKEND_URL (default: localhost:8000)
2. Frontend server running on E2E_FRONTEND_URL (default: localhost:3000)
3. E2E_TEST_PASSWORD environment variable set
4. Playwright browser installed: python -m playwright install chromium

Run with: pytest tests/manual/smoke/test_e2e_simple.py -m manual
"""

import os

import pytest

# Check dependencies
try:
    from playwright.async_api import TimeoutError as PlaywrightTimeout
    from playwright.async_api import async_playwright
except ImportError as e:
    raise ImportError(
        "Playwright not installed. Install with: pip install playwright && python -m playwright install chromium"
    ) from e

try:
    from .e2e_config import (
        BACKEND_URL,
        FRONTEND_URL,
        SCREENSHOT_DIR,
        TEST_EMAIL,
        TEST_PASSWORD,
        start_servers_if_needed,
    )
except ImportError:
    # Allow running as standalone script
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from e2e_config import BACKEND_URL, FRONTEND_URL, SCREENSHOT_DIR, TEST_EMAIL, TEST_PASSWORD, start_servers_if_needed


# Mark as manual smoke test
pytestmark = pytest.mark.manual


def register_test_user_if_needed():
    """Register test user via API if not already registered."""
    import requests

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json={"username": "e2etest", "email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10,
        )
        if response.status_code == 201:
            print(f"[E2E] Created test user: {TEST_EMAIL}")
        elif response.status_code == 400 and (
            "already exists" in response.text.lower() or "REGISTER_USER_ALREADY_EXISTS" in response.text
        ):
            print(f"[E2E] Test user already exists: {TEST_EMAIL}")
        else:
            raise AssertionError(f"User registration failed: {response.status_code} - {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Cannot connect to backend for user registration: {e}") from e


@pytest.mark.asyncio
async def test_e2e_subtitle_display_workflow():
    """
    E2E test verifying complete subtitle workflow.

    Prerequisites:
    - Servers must be running (use scripts/start-all.bat)
    - E2E_TEST_PASSWORD must be set

    Test flow:
    1. Start servers if not running
    2. Navigate to frontend
    3. Login with test credentials
    4. Select Superstore series
    5. Play Episode 1
    6. Skip vocabulary games
    7. Verify video player loads with subtitles
    """
    # Start servers if needed (acceptable for manual tests)
    start_servers_if_needed()

    # Register test user
    register_test_user_if_needed()

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=bool(os.getenv("E2E_HEADLESS")), slow_mo=500)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        # Capture console logs and errors
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console_logs.append(f"[PAGE ERROR] {exc}"))

        # Capture network failures
        page.on(
            "requestfailed", lambda req: console_logs.append(f"[NETWORK FAIL] {req.method} {req.url} - {req.failure}")
        )

        try:
            # Step 1: Navigate to frontend
            await page.goto(FRONTEND_URL, timeout=15000)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(SCREENSHOT_DIR / "00_homepage.png"))

            # Step 2: Login
            email_input = page.locator('input[type="email"]').first
            password_input = page.locator('input[type="password"]').first
            submit_button = page.locator('button:has-text("Sign In")').first

            await email_input.fill(TEST_EMAIL)
            await password_input.fill(TEST_PASSWORD)
            await page.screenshot(path=str(SCREENSHOT_DIR / "01_login_filled.png"))
            await submit_button.click()

            # Wait for navigation away from login page
            try:
                # Wait for URL to change from /login
                await page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception as nav_error:
                # Login failed, capture state and logs
                await page.screenshot(path=str(SCREENSHOT_DIR / "02_login_timeout.png"))
                page_html = await page.content()
                (SCREENSHOT_DIR / "02_login_timeout.html").write_text(page_html, encoding="utf-8")

                print("\n[E2E] Login failed - still on login page after 10s")
                print(f"[E2E] Current URL: {page.url}")
                print("[E2E] Browser console logs:")
                for log in console_logs:
                    print(f"  {log}")

                raise AssertionError(f"Login failed - URL did not change from /login: {nav_error}") from nav_error

            # Save debug screenshot
            await page.screenshot(path=str(SCREENSHOT_DIR / "02_after_login.png"))

            # Debug: Save page HTML
            page_html = await page.content()
            (SCREENSHOT_DIR / "02_after_login.html").write_text(page_html, encoding="utf-8")

            # Check if we're actually logged in or still on login page
            current_url = page.url
            print(f"[DEBUG] Current URL after login: {current_url}")

            # Step 3: Navigate to Superstore
            superstore_card = page.locator('[data-testid="series-card-superstore"]')
            await superstore_card.wait_for(state="visible", timeout=15000)
            await superstore_card.click()
            await page.wait_for_load_state("networkidle")

            # Step 4: Click Play on Episode 1
            play_button = page.locator('[data-testid="episode-play-button"]').first
            if await play_button.count() == 0:
                # Fallback if data-testid not available
                play_button = page.locator('button:has-text("Play")').first

            await play_button.wait_for(state="visible", timeout=10000)
            await play_button.click()

            # Step 5: Wait for processing and skip games
            max_wait_seconds = 300
            check_interval_seconds = 5

            for elapsed in range(0, max_wait_seconds, check_interval_seconds):
                # Check if video player appeared
                video_element = page.locator("video").first
                if await video_element.count() > 0:
                    break

                # Check for action buttons (game screens)
                action_button = page.locator(
                    '[data-testid="skip-button"], '
                    '[data-testid="continue-button"], '
                    'button:has-text("Skip"), '
                    'button:has-text("Continue"), '
                    'button:has-text("Start"), '
                    'button:has-text("Next")'
                ).first

                if await action_button.count() > 0:
                    try:
                        await action_button.click(timeout=2000)
                        await page.wait_for_load_state("networkidle", timeout=3000)
                    except PlaywrightTimeout:
                        # Button clicked but page still loading
                        pass

                await page.wait_for_timeout(check_interval_seconds * 1000)
            else:
                # Max wait exceeded
                await page.screenshot(path=str(SCREENSHOT_DIR / "error_no_video.png"))
                raise AssertionError(
                    f"Video player did not appear within {max_wait_seconds} seconds. "
                    f"Check screenshot: {SCREENSHOT_DIR / 'error_no_video.png'}"
                )

            # Step 6: Verify video player
            video_element = page.locator("video").first
            await video_element.wait_for(state="visible", timeout=5000)
            assert await video_element.is_visible(), "Video element must be visible"

            # Start playback
            await video_element.click()
            await page.wait_for_timeout(2000)

            # Attempt to play via JavaScript (some browsers require this)
            is_playing = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (!video) return false;
                    video.play().catch(() => {});
                    return !video.paused;
                }
            """)

            # Wait for subtitles to render
            await page.wait_for_timeout(3000)

            # Verify subtitle tracks exist
            subtitle_track_count = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (!video) return 0;
                    return video.textTracks.length;
                }
            """)

            assert subtitle_track_count > 0, f"Expected subtitle tracks, found {subtitle_track_count}"

            # Take final screenshot for manual verification
            await page.screenshot(path=str(SCREENSHOT_DIR / "02_video_with_subtitles.png"))

            # Verify video is loaded
            video_duration = await page.evaluate("document.querySelector('video')?.duration || 0")
            assert video_duration > 0, "Video must have valid duration"

        except Exception as e:
            # Print all captured logs on failure
            print("\n[E2E] Browser console logs:")
            for log in console_logs:
                print(f"  {log}")
            raise
        finally:
            # Always print logs for debugging
            print("\n[E2E] Browser console logs:")
            for log in console_logs:
                print(f"  {log}")
            await browser.close()


if __name__ == "__main__":
    # Allow running as standalone script
    import asyncio

    asyncio.run(test_e2e_subtitle_display_workflow())
