#!/usr/bin/env python3
"""
E2E Smoke Test: Registration Error Handling
Tests: Registration with invalid password -> Verify specific error message
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
        FRONTEND_URL,
        SCREENSHOT_DIR,
        start_servers_if_needed,
    )
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from e2e_config import (
        FRONTEND_URL,
        SCREENSHOT_DIR,
        start_servers_if_needed,
    )

# Mark as manual smoke test
pytestmark = pytest.mark.manual


@pytest.mark.asyncio
async def test_e2e_registration_error_workflow():
    """
    Test registration error handling.
    1. Navigate to Register
    2. Enter invalid password (short)
    3. Submit
    4. Verify specific error message (not generic)
    """
    # Step 0: Start servers
    start_servers_if_needed()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=bool(os.getenv("E2E_HEADLESS")), slow_mo=500)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        try:
            # Step 1: Navigate to Register
            print("[E2E] Navigating to Register...")
            await page.goto(f"{FRONTEND_URL}/register", wait_until="networkidle", timeout=30000)

            email_input = page.locator('input[type="email"]').first
            username_input = page.locator('input[name="username"]').first
            password_input = page.locator('input[name="password"]').first
            confirm_input = page.locator('input[name="confirm_password"]').first
            submit_button = page.locator('button[type="submit"]').first

            await email_input.wait_for(state="visible", timeout=10000)

            # Step 2: Fill invalid data
            print("[E2E] Filling invalid data (short password)...")
            await email_input.fill(f"test_invalid_{os.urandom(4).hex()}@example.com")
            await username_input.fill("validuser")
            await password_input.fill("short")  # Too short
            await confirm_input.fill("short")

            # Step 3: Submit
            await submit_button.click()

            # Wait for error message
            # The fix uses formatApiError which should show backend message
            # Backend (Pydantic) usually returns "Value error, Password must be at least 12 characters long"
            # Or "Password must be at least 12 characters long"

            # Wait for ANY error message
            error_msg_locator = page.locator('div[class*="ErrorMessage"], p[class*="ErrorMessage"], .sc-gsnTZi')
            # Note: sc-gsnTZi is hash, unreliable.
            # RegisterForm uses <ErrorMessage>{error}</ErrorMessage>
            # ErrorMessage is styled.div from GlobalStyles.

            # Better: look for text
            print("[E2E] Waiting for error message...")
            # We expect "at least 12 characters"
            try:
                await page.wait_for_selector("text=at least 12 characters", timeout=5000)
                print("[E2E] Success: Found specific error message")
            except PlaywrightTimeout:
                # Dump page content to see what we got
                content = await page.content()
                if "Failed to create account" in content:
                    print("[E2E] FAILURE: Found generic error message (Fix did not work?)")
                    raise AssertionError("Found generic error instead of specific validation error")
                else:
                    print("[E2E] FAILURE: No error message found?")
                    await page.screenshot(path=str(SCREENSHOT_DIR / "error_validation_fail.png"))
                    raise AssertionError("Validation error not found")

            await page.screenshot(path=str(SCREENSHOT_DIR / "06_registration_error.png"))

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_e2e_registration_error_workflow())
