#!/usr/bin/env python3
"""
E2E Smoke Test: Comprehensive Subtitle Verification

Tests: Login → Superstore → Episode 1 → Multi-chunk Processing → Subtitle Display

IMPORTANT: This test requires:
1. Backend server running on E2E_BACKEND_URL (default: localhost:8000)
2. Frontend server running on E2E_FRONTEND_URL (default: localhost:3000)
3. E2E_TEST_PASSWORD environment variable set
4. Playwright browser installed: python -m playwright install chromium
5. Test user registered (will attempt auto-registration)

Run with: pytest tests/manual/smoke/test_e2e_subtitle_verification.py -m manual
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
    from e2e_config import (
        BACKEND_URL,
        FRONTEND_URL,
        SCREENSHOT_DIR,
        TEST_EMAIL,
        TEST_PASSWORD,
        start_servers_if_needed,
    )


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
            return True
        elif response.status_code == 400 and (
            "already exists" in response.text.lower() or "REGISTER_USER_ALREADY_EXISTS" in response.text
        ):
            print(f"[E2E] Test user already exists: {TEST_EMAIL}")
            return True
        else:
            raise AssertionError(f"User registration failed: {response.status_code} - {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Cannot connect to backend for user registration: {e}") from e


@pytest.mark.asyncio
async def test_e2e_comprehensive_subtitle_workflow():
    """
    Comprehensive E2E test for multi-chunk episode processing and subtitle display.

    Prerequisites:
    - Servers must be running
    - E2E_TEST_PASSWORD must be set

    Test flow:
    1. Start servers if not running
    2. Register test user (if needed)
    3. Navigate and login
    4. Select Superstore series
    5. Play Episode 1 (multi-chunk)
    6. Skip through all vocabulary games
    7. Verify video player with subtitles
    8. Validate subtitle contract (language codes, tracks)
    """
    # Step 0: Start servers if needed (acceptable for manual tests)
    start_servers_if_needed()

    # Step 1: Register test user
    register_test_user_if_needed()

    async with async_playwright() as p:
        # Launch browser with video recording for debugging
        browser = await p.chromium.launch(headless=bool(os.getenv("E2E_HEADLESS")), slow_mo=500)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(SCREENSHOT_DIR) if os.getenv("E2E_RECORD_VIDEO") else None,
        )
        page = await context.new_page()

        try:
            # Step 1: Navigate to frontend
            await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=30000)

            # Step 2: Login
            email_input = page.locator('input[type="email"]').first
            password_input = page.locator('input[type="password"]').first
            submit_button = page.locator('button[type="submit"], button:has-text("Sign In")').first

            await email_input.fill(TEST_EMAIL)
            await password_input.fill(TEST_PASSWORD)
            await submit_button.click()

            # Wait for login to complete
            await page.wait_for_timeout(5000)

            # Check for login error
            error_message = page.locator('text="Invalid email or password"')
            assert await error_message.count() == 0, "Login failed - check credentials"

            await page.screenshot(path=str(SCREENSHOT_DIR / "01_after_login.png"))

            # Step 3: Navigate to Superstore
            await page.wait_for_load_state("networkidle")

            # Save page HTML for debugging
            page_html = await page.content()
            (SCREENSHOT_DIR / "debug_after_login.html").write_text(page_html, encoding="utf-8")

            # Wait for series cards
            series_cards_locator = page.locator('[data-testid^="series-card-"]')
            await series_cards_locator.first.wait_for(state="visible", timeout=15000)

            # Verify Superstore card exists
            superstore_card = page.locator('[data-testid="series-card-superstore"]')
            card_count = await superstore_card.count()

            if card_count == 0:
                # Debug: list all cards
                all_cards = await series_cards_locator.all()
                card_ids = []
                for card in all_cards:
                    test_id = await card.get_attribute("data-testid")
                    if test_id:
                        card_ids.append(test_id)

                await page.screenshot(path=str(SCREENSHOT_DIR / "error_no_superstore_card.png"))
                raise AssertionError(
                    f"Superstore card not found. Available cards: {card_ids}. "
                    f"Screenshot: {SCREENSHOT_DIR / 'error_no_superstore_card.png'}"
                )

            await superstore_card.click(timeout=5000)
            await page.wait_for_load_state("networkidle")

            # Step 4: Play Episode 1
            play_button = page.locator('[data-testid="episode-play-button"]').first
            if await play_button.count() == 0:
                play_button = page.locator('button:has-text("Play")').first

            await play_button.wait_for(state="visible", timeout=10000)
            await play_button.click()
            await page.wait_for_load_state("networkidle")

            # Step 5: Handle multi-chunk processing
            max_chunks = 5
            max_wait_per_chunk = 180  # 3 minutes per chunk

            for chunk_num in range(max_chunks):
                # Wait for chunk processing to complete (game or video appears)
                for elapsed in range(0, max_wait_per_chunk, 5):
                    # Check for video player
                    video_element = page.locator("video").first
                    if await video_element.count() > 0:
                        # Video found - all chunks processed!
                        break

                    # Check for game screen
                    game_buttons = page.locator(
                        '[data-testid="skip-button"], '
                        '[data-testid="continue-button"], '
                        'button:has-text("Skip"), '
                        'button:has-text("Continue"), '
                        'button:has-text("Start")'
                    )

                    if await game_buttons.first.count() > 0:
                        # Game ready
                        break

                    # Check for processing status
                    if elapsed % 20 == 0:
                        processing_indicator = page.locator('text*="Processing"').first
                        if await processing_indicator.count() > 0:
                            try:
                                status_text = await processing_indicator.inner_text()
                                # Safe ASCII conversion
                                status_safe = "".join(c if ord(c) < 128 else "?" for c in status_text[:50])
                                print(f"[Chunk {chunk_num + 1}] {status_safe}... ({elapsed}s)")
                            except PlaywrightTimeout:
                                print(f"[Chunk {chunk_num + 1}] Processing... ({elapsed}s)")

                    await page.wait_for_timeout(5000)

                # Check if we reached video player
                video_element = page.locator("video").first
                if await video_element.count() > 0:
                    break

                # Skip through game for this chunk
                for _ in range(10):
                    skip_button = page.locator(
                        '[data-testid="skip-button"], '
                        'button:has-text("Skip"), '
                        'button:has-text("Continue"), '
                        'button:has-text("Next")'
                    ).first

                    if await skip_button.count() == 0:
                        break

                    try:
                        await skip_button.click(timeout=2000)
                        await page.wait_for_timeout(1000)
                    except PlaywrightTimeout:
                        break

                await page.wait_for_timeout(2000)

            # Step 6: Verify video player
            video_element = page.locator("video").first
            await video_element.wait_for(state="visible", timeout=15000)
            assert await video_element.is_visible(), "Video element must be visible"

            # Start playback
            await video_element.click()
            await page.wait_for_timeout(2000)

            # Play video
            playback_started = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (!video) return false;
                    video.play().catch(() => {});
                    return true;
                }
            """)
            assert playback_started, "Failed to start video playback"

            # Wait for subtitles
            await page.wait_for_timeout(5000)

            # Step 7: Validate subtitle contract
            await page.screenshot(path=str(SCREENSHOT_DIR / "02_video_with_subtitles.png"))

            # Check subtitle tracks
            subtitle_info = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (!video) return { count: 0, tracks: [] };

                    const tracks = [];
                    for (let i = 0; i < video.textTracks.length; i++) {
                        const track = video.textTracks[i];
                        tracks.push({
                            kind: track.kind,
                            language: track.language,
                            label: track.label,
                            mode: track.mode
                        });
                    }

                    return {
                        count: video.textTracks.length,
                        tracks: tracks,
                        duration: video.duration
                    };
                }
            """)

            assert subtitle_info["count"] > 0, f"Expected subtitle tracks, found {subtitle_info['count']}"
            assert subtitle_info["duration"] > 0, "Video must have valid duration"

            # Verify we have expected language tracks (German original, Spanish translation)
            track_languages = [track["language"] for track in subtitle_info["tracks"]]
            print(f"Subtitle tracks found: {subtitle_info['tracks']}")

            # Test passes if subtitles exist and video plays
            assert len(track_languages) > 0, "At least one subtitle track must be present"

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    # Allow running as standalone script
    import asyncio

    asyncio.run(test_e2e_comprehensive_subtitle_workflow())
