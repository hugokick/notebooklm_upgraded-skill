#!/usr/bin/env python3
"""
NotebookLM Notebook Creation Script
Automates clicking the "Create notebook" button and capturing the new URL.
"""

import argparse
import sys
import time
import re
from pathlib import Path

from patchright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from browser_utils import BrowserFactory, StealthUtils


def create_notebook(name: str = None, headless: bool = True) -> str:
    """Create a new notebook and return its URL."""
    auth = AuthManager()
    if not auth.is_authenticated():
        print("Error: Not authenticated. Run: python auth_manager.py setup")
        return None

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
        page = context.new_page()

        print("Navigating to dashboard...")
        page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=60000)
        
        # Wait for the URL to settle or look for the library header
        try:
            page.wait_for_url(re.compile(r"notebooklm\.google\.com"), timeout=10000)
        except:
            pass

        # Step 1: Click "Create notebook"
        print("Looking for 'Create notebook' button...")
        # Possible selectors based on common patterns
        create_btn_selectors = [
            "button:has-text('Create notebook')",
            ".create-notebook-button",
            "button[aria-label*='Create']",
            "div[role='button']:has-text('Create notebook')"
        ]
        
        create_btn = None
        for selector in create_btn_selectors:
            try:
                create_btn = page.wait_for_selector(selector, timeout=10000)
                if create_btn:
                    print(f"Found button: {selector}")
                    break
            except:
                continue
        
        if not create_btn:
            # Fallback: look for any button with a plus icon or similar text
            print("Trying fallback selectors...")
            create_btn = page.locator("button").filter(has_text=re.compile(r"Create|New", re.I)).first
            if create_btn.count() == 0:
                print("Error: Could not find 'Create notebook' button")
                page.screenshot(path="debug_dashboard_error.png")
                return None

        print("Clicking 'Create notebook'...")
        create_btn.click()

        # Step 2: Wait for navigation to the new notebook
        print("Waiting for new notebook to load (stable ID)...")
        # Notebook URLs usually look like https://notebooklm.google.com/notebook/[ID]
        try:
            # Wait for URL to NOT contain 'creating' and match the pattern
            def is_stable_url(url):
                return "/notebook/" in url and "/creating" not in url
            
            page.wait_for_function("() => window.location.href.includes('/notebook/') && !window.location.href.includes('/creating')", timeout=30000)
            new_url = page.url
            print(f"New notebook created: {new_url}")
        except:
            print(f"Error: Timed out or URL remained unstable. Current URL: {page.url}")
            page.screenshot(path="debug_create_timeout.png")
            return None

        # Step 3: Rename (Optional)
        if name:
            print(f"Attempting to rename notebook to '{name}'...")
            try:
                # Look for the title element. It's often an input or a div that becomes an input
                title_selectors = [
                    "input[aria-label*='title']",
                    ".notebook-title",
                    "h1[contenteditable='true']",
                    "div[role='heading'][aria-label*='title']"
                ]
                
                title_el = None
                for selector in title_selectors:
                    if page.locator(selector).count() > 0:
                        title_el = page.locator(selector).first
                        break
                
                if title_el:
                    title_el.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.keyboard.type(name)
                    page.keyboard.press("Enter")
                    print(f"Renamed to: {name}")
                    time.sleep(2) # Wait for save
                else:
                    print("Warning: Could not find title element to rename")
            except Exception as e:
                print(f"Warning: Rename failed: {e}")

        page.screenshot(path="new_notebook_ready.png")
        return new_url

    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        if context: context.close()
        if playwright: playwright.stop()


def main():
    parser = argparse.ArgumentParser(description='Create a new NotebookLM notebook')
    parser.add_argument('--name', help='Name for the new notebook')
    parser.add_argument('--show-browser', action='store_true', help='Show browser')

    args = parser.parse_args()

    url = create_notebook(name=args.name, headless=not args.show_browser)
    if url:
        print(f"SUCCESS: {url}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
