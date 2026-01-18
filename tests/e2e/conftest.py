# Playwright E2E Test Configuration
# Run with: pytest tests/e2e/ --headed (for visible browser)
# Or: pytest tests/e2e/ (headless mode)

import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Configure browser launch arguments"""
    return {
        "headless": True,
        "slow_mo": 100,  # Slow down actions by 100ms for debugging
    }

@pytest.fixture(scope="session")
def browser_context_args():
    """Configure browser context arguments"""
    return {
        "viewport": {"width": 1280, "height": 720},
        "locale": "en-US",
        "timezone_id": "Asia/Riyadh",
        "ignore_https_errors": True,
    }
