#!/usr/bin/env python3
"""
Sync Library for NotebookLM
Discovers all notebooks from the dashboard and updates the local library.
"""

import sys
import time
import json
import argparse
import re
from pathlib import Path
from patchright.sync_api import sync_playwright

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir.absolute()))

from browser_utils import BrowserFactory
from notebook_manager import NotebookLibrary

def sync_library(show_browser=False):
    """
    Synchronize local library with the NotebookLM dashboard
    """
    print("🔄 Starting NotebookLM library synchronization...")
    
    library = NotebookLibrary()
    playwright = None
    context = None
    
    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=not show_browser)
        page = context.new_page()
        
        print(f"🌐 Navigating to NotebookLM dashboard... Currently at: {page.url}")
        page.goto("https://notebooklm.google.com/", wait_until="load", timeout=60000)
        print(f"📍 Landed at: {page.url}")
        page.screenshot(path=str(library.data_dir / "sync_1_landed.png"))
        
        # Wait for any meaningful content
        time.sleep(5)
        print(f"🕒 After 5s wait: {page.url}")
        page.screenshot(path=str(library.data_dir / "sync_2_waited.png"))

        # Click "My notebooks" to ensure we see the user's personal notebooks
        try:
            my_tab = page.get_by_text("My notebooks")
            if my_tab.count() > 0:
                print("🖱️ Clicking 'My notebooks' tab...")
                my_tab.first.click()
                time.sleep(5)
                print(f"📍 After clicking tab: {page.url}")
                page.screenshot(path=str(library.data_dir / "sync_3_after_tab.png"))
        except Exception as e:
            print(f"⚠️ Tab error: {e}")

        print("🔍 Extracting notebooks using Project Button Title pattern...")
        notebook_data = []
        # Use Locators to find all titles
        # Pattern: <span class="project-button-title" id="project-{ID}-title"> {NAME} </span>
        titles = page.locator(".project-button-title").all()
        print(f"🔗 Found {len(titles)} notebook title elements.")
        
        for title in titles:
            try:
                elem_id = title.get_attribute("id") or ""
                # Extract ID from project-{ID}-title
                match = re.search(r'project-([a-zA-Z0-9-]+)-title', elem_id)
                if match:
                    notebook_id = match.group(1)
                    if any(r['id'] == notebook_id for r in notebook_data):
                        continue
                        
                    name = title.inner_text().strip()
                    
                    if notebook_id and name:
                        notebook_data.append({
                            'id': notebook_id,
                            'name': name,
                            'url': f"https://notebooklm.google.com/notebook/{notebook_id}"
                        })
                        print(f"📍 Found: {name} ({notebook_id})")
            except Exception as e:
                print(f"⚠️ Error processing title element: {e}")

        # Fallback: if no titles found, try slightly different pattern
        if not notebook_data:
            print("🕵️ No titles found via .project-button-title. Trying generic search...")
            # Search for any ID pattern in all IDs on the page
            all_ids = page.evaluate("() => Array.from(document.querySelectorAll('[id]')).map(el => el.id)")
            for eid in all_ids:
                match = re.search(r'project-([a-zA-Z0-9-]+)-title', eid)
                if match:
                    notebook_id = match.group(1)
                    if any(r['id'] == notebook_id for r in notebook_data):
                        continue
                    try:
                        name = page.locator(f"#{eid}").inner_text().strip()
                        if name:
                            notebook_data.append({
                                'id': notebook_id,
                                'name': name,
                                'url': f"https://notebooklm.google.com/notebook/{notebook_id}"
                            })
                            print(f"📍 Found (fallback): {name} ({notebook_id})")
                    except:
                        pass

        print(f"✅ Found {len(notebook_data)} notebooks.")

        # Update library
        count = 0
        for entry in notebook_data:
            library.sync_entry(
                url=entry['url'],
                name=entry['name'],
                notebook_id=entry['id']
            )
            count += 1
            
        print(f"🚀 Successfully synchronized {count} notebooks.")
        return True

    except Exception as e:
        print(f"❌ Error during synchronization: {e}")
        return False
    finally:
        if context: context.close()
        if playwright: playwright.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync NotebookLM library with cloud')
    parser.add_argument('--show-browser', action='store_true', help='Show browser during sync')
    args = parser.parse_args()
    
    success = sync_library(show_browser=args.show_browser)
    sys.exit(0 if success else 1)
