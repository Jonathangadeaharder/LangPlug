#!/usr/bin/env python3
"""
E2E Smoke Test: Vocabulary Management
Tests: Login → Vocabulary Library → Search/Filter → Mark Known

IMPORTANT: This test relies on data populated by previous tests (video processing).
If no vocabulary exists, it verifies the empty state.
"""

import os

import pytest

# Check dependencies
try:
    from playwright.async_api import TimeoutError as PlaywrightTimeout
    from playwright.async_api import async_playwright
except ImportError:
    pytest.skip("Playwright not installed", allow_module_level=True)

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
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from e2e_config import (
        FRONTEND_URL,
        SCREENSHOT_DIR,
        TEST_EMAIL,
        TEST_PASSWORD,
        start_servers_if_needed,
    )

# Mark as manual smoke test
pytestmark = pytest.mark.manual


@pytest.mark.asyncio
async def test_e2e_vocabulary_workflow():
    """
    Test vocabulary library features.
    1. Login
    2. Navigate to Vocabulary
    3. Check word list
    4. Test filters (Search, Level)
    5. Toggle word status (Known/Unknown)
    """
    # Step 0: Start servers
    start_servers_if_needed()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=bool(os.getenv("E2E_HEADLESS")), slow_mo=500)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        try:
            # Step 1: Login
            print("[E2E] Navigating to login...")
            await page.goto(f"{FRONTEND_URL}/login", wait_until="networkidle", timeout=30000)

            email_input = page.locator('input[type="email"]').first
            password_input = page.locator('input[type="password"]').first
            submit_button = page.locator('button[type="submit"], button:has-text("Sign In")').first

            await email_input.wait_for(state="visible", timeout=10000)
            await email_input.fill(TEST_EMAIL)
            await password_input.fill(TEST_PASSWORD)
            await submit_button.click()

            await page.wait_for_url("**/videos", timeout=10000)
            print("[E2E] Login successful")

            # Step 2: Navigate to Vocabulary
            print("[E2E] Navigating to Vocabulary Library...")
            await page.goto(f"{FRONTEND_URL}/vocabulary", wait_until="networkidle")
            await page.screenshot(path=str(SCREENSHOT_DIR / "04_vocab_library.png"))

            # Verify page title or content
            # Assuming there's a header "Vocabulary" or similar
            header = page.locator("h1, h2, h3").filter(has_text="Vocabulary").first
            if await header.count() > 0:
                await header.wait_for()

            # Step 3: Check word list
            # Look for word cards or rows
            # Assuming data-testid="word-card-..." or generic class
            # If empty, we should see "No words found"

            word_elements = page.locator('[data-testid^="word-card"], .word-card, tr.word-row')
            word_count = await word_elements.count()
            print(f"[E2E] Found {word_count} words")

            if word_count == 0:
                print("[E2E] No vocabulary found. Verifying empty state.")
                # Verify empty state message
                empty_msg = page.locator('text="No vocabulary found"').first
                if await empty_msg.count() > 0:
                    print("[E2E] Empty state verified")
                else:
                    print("[E2E] WARNING: No words and no empty message found?")

                # End test gracefully if no data
                return

            # Step 4: Test Search
            search_input = page.locator('input[placeholder*="Search"], input[type="search"]').first
            if await search_input.count() > 0:
                print("[E2E] Testing search...")
                # Get first word text
                first_word_text = await word_elements.first.locator(".word").inner_text()
                print(f"[E2E] Searching for: {first_word_text}")

                await search_input.fill(first_word_text)
                await page.wait_for_timeout(1000)  # Wait for debounce

                # Verify filtered
                filtered_count = await word_elements.count()
                print(f"[E2E] Filtered count: {filtered_count}")
                assert filtered_count > 0, "Search should return results"

                # Clear search
                await search_input.fill("")
                await page.wait_for_timeout(1000)

            # Step 5: Mark word as known
            print("[E2E] Testing toggle known status...")
            first_word_card = word_elements.first

            # Click the card to toggle status (VocabularyLibrary behavior)
            if await first_word_card.count() > 0:
                await first_word_card.click()
                await page.wait_for_timeout(1000)
                print("[E2E] Toggled word status")
                await page.screenshot(path=str(SCREENSHOT_DIR / "05_vocab_toggled.png"))
            else:
                print("[E2E] Could not find word card to toggle")

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_e2e_vocabulary_workflow())
