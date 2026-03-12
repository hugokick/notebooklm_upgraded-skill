#!/usr/bin/env python3
import sys
from pathlib import Path
from patchright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from auth_manager import AuthManager
from browser_utils import BrowserFactory

def check_state():
    auth = AuthManager()
    if not auth.is_authenticated():
        print("Not authenticated")
        return

    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=True)
        page = context.new_page()
        
        print("Checking Dashboard...")
        page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        page.screenshot(path="debug_dashboard_current.png")
        print("Dashboard screenshot saved.")
        
        print("Checking Notebook 测试笔记本...")
        page.goto("https://notebooklm.google.com/notebook/3339d6d6-cf3a-45f0-a51c-2013105afd2d", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        page.screenshot(path="debug_notebook_current.png")
        print("Notebook screenshot saved.")
        
        context.close()

if __name__ == "__main__":
    check_state()
