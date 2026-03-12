import sys
from pathlib import Path
from patchright.sync_api import sync_playwright
import time
import re

# Add parent directory to path
sys.path.insert(0, str(Path("scripts").resolve()))

from auth_manager import AuthManager
from browser_utils import BrowserFactory

def rename_notebook(url, new_name):
    auth = AuthManager()
    playwright = sync_playwright().start()
    context = BrowserFactory.launch_persistent_context(playwright, headless=True)
    page = context.new_page()
    
    print(f"Navigating to {url}...")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    
    print("Attempting rename...")
    try:
        # Based on UI inspection, the title might be a div that becomes an input
        title_el = page.locator("div[role='heading'], h1, .notebook-title").filter(has_text=re.compile(r"Untitled", re.I)).first
        if title_el.count() > 0:
            title_el.click()
            time.sleep(1)
            # After click, it might become an input
            input_el = page.locator("input[aria-label*='title'], input.title-input, [contenteditable='true']").first
            if input_el.count() > 0:
                input_el.fill(new_name)
                input_el.press("Enter")
                print(f"Renamed to {new_name}")
            else:
                # Try direct keyboard actions if no input found
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(new_name)
                page.keyboard.press("Enter")
                print("Likely renamed via keyboard")
        else:
            print("Could not find 'Untitled' title")
            
        page.screenshot(path="rename_check.png")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        context.close()
        playwright.stop()

if __name__ == "__main__":
    rename_notebook("https://notebooklm.google.com/notebook/a989f6af-c712-45e8-a4a9-4ec052e6b3ac", "测试笔记本")
