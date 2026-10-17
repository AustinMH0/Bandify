"""Bound browser work so one track fits within the public API request deadline."""
from time import monotonic
from playwright.sync_api import sync_playwright


def page_html(url, deadline):
    def remaining_ms():
        remaining = int((deadline - monotonic()) * 1000)
        if remaining <= 0:
            raise TimeoutError("Store lookup deadline exceeded")
        return remaining

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, timeout=remaining_ms(),
            args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process"],
        )
        try:
            page = browser.new_page()
            response = page.goto(url, timeout=remaining_ms(), wait_until="domcontentloaded")
            if response and response.status >= 400:
                raise RuntimeError(f"Store returned HTTP {response.status}")
            page.wait_for_timeout(min(500, remaining_ms()))
            return page.content()
        finally:
            browser.close()
