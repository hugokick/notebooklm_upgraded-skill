#!/usr/bin/env python3
"""
NotebookLM Source Uploader Interface
Allows automatically adding PDF/TXT files or YouTube links to an existing notebook.

Based on NotebookLM UI analysis (March 2026):
- Sources tab → "+ Add sources" button
- Dialog opens with:
  - "Search the web for new sources" input (paste YouTube URLs here)
  - "or drop your files" zone (file upload via hidden input)
"""

import argparse
import sys
import time
import re
import codecs
from pathlib import Path

from patchright.sync_api import sync_playwright

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from notebook_manager import NotebookLibrary
from browser_utils import BrowserFactory


def upload_source(notebook_url: str, file_path: str = None, youtube_url: str = None, headless: bool = False) -> bool:
    """Add a new source (file or youtube link) to a notebook."""
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    except:
        pass

    if not file_path and not youtube_url:
        print("Error: Must provide either --file or --youtube")
        return False
    if file_path and youtube_url:
        print("Error: Provide ONLY --file OR --youtube, not both")
        return False

    auth = AuthManager()
    if not auth.is_authenticated():
        print("Not authenticated. Run: python auth_manager.py setup")
        return False

    if file_path:
        p = Path(file_path).expanduser().resolve()
        if not p.exists():
            print(f"Error: File does not exist: {p}")
            return False
        file_path = str(p)

    print(f"Opening notebook: {notebook_url}")
    print(f"Preparing to upload: {file_path if file_path else youtube_url}")

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
        page = context.new_page()

        # --- Step 1: Navigate ---
        print("  Step 1: Navigating to notebook...")
        try:
            page.goto(notebook_url, wait_until="commit", timeout=30000)
        except:
            pass
        time.sleep(10)

        if "notebooklm.google.com" not in page.url:
            print(f"  Error: Not on NotebookLM. URL: {page.url}")
            return False

        # --- Step 2: Click Sources tab ---
        print("  Step 2: Clicking Sources tab...")
        try:
            tab = page.get_by_text("Sources", exact=True)
            if tab.count() > 0:
                tab.first.click()
                time.sleep(3)
                print("  Clicked Sources tab")
        except:
            print("  Warning: Could not click Sources tab")

        # --- Step 3: Click "+ Add sources" ---
        print("  Step 3: Clicking Add sources...")
        add_btn = None
        for approach in [
            lambda: page.get_by_text("Add sources", exact=False),
            lambda: page.get_by_text("Upload a source", exact=False),
            lambda: page.locator("button:has-text('Add sources')"),
        ]:
            try:
                el = approach()
                if el.count() > 0 and el.first.is_visible():
                    add_btn = el.first
                    break
            except:
                pass

        if not add_btn:
            page.screenshot(path="upload_debug.png")
            print("  Error: Could not find Add sources button")
            return False

        add_btn.click()
        print("  Clicked Add sources")
        time.sleep(3)

        # --- Step 4: Handle dialog ---
        # The dialog has:
        # - A search bar "Search the web for new sources" (for URLs/YouTube)
        # - A file drop zone "or drop your files" 

        if youtube_url:
            print(f"  Step 4: Pasting YouTube URL into search bar...")
            
            # Find the search input inside the dialog
            search_input = None
            for approach in [
                lambda: page.locator("[role='dialog'] input[type='text']"),
                lambda: page.locator("[role='dialog'] input"),
                lambda: page.locator("mat-dialog-container input"),
                lambda: page.get_by_placeholder("Search the web"),
            ]:
                try:
                    el = approach()
                    if el.count() > 0 and el.first.is_visible():
                        search_input = el.first
                        break
                except:
                    pass

            if search_input:
                search_input.click()
                search_input.fill(youtube_url)
                print("  Pasted YouTube URL")
                time.sleep(1)
                
                # Click the submit/arrow button
                submit = None
                try:
                    # The arrow button inside the dialog
                    arrow = page.locator("[role='dialog'] button[aria-label*='Search']")
                    if arrow.count() > 0:
                        submit = arrow.first
                    else:
                        # Try finding the arrow/submit button near the input
                        arrow = page.locator("[role='dialog'] button.submit-button, [role='dialog'] button mat-icon:has-text('arrow')")
                        if arrow.count() > 0:
                            submit = arrow.first
                except:
                    pass

                if submit:
                    submit.click()
                    print("  Clicked search submit")
                else:
                    print("  Pressing Enter to submit")
                    page.keyboard.press("Enter")
            else:
                print("  Warning: Could not find search input, trying keyboard")
                page.keyboard.press("Tab")
                time.sleep(0.5)
                page.keyboard.type(youtube_url, delay=20)
                time.sleep(0.5)
                page.keyboard.press("Enter")

            time.sleep(5)

            # After pasting a YouTube URL, NotebookLM may show a confirmation
            # Look for an "Insert" or "Add" button
            try:
                for txt in ['Insert', 'Add', 'import']:
                    btn = page.locator(f"[role='dialog'] button:has-text('{txt}')")
                    if btn.count() > 0:
                        for i in range(btn.count()):
                            if btn.nth(i).is_visible() and btn.nth(i).is_enabled():
                                btn.nth(i).click()
                                print(f"  Clicked {txt} button")
                                break
                        break
            except:
                pass

        elif file_path:
            print(f"  Step 4: Uploading file: {Path(file_path).name}")

            # Look for hidden file input 
            file_input = page.locator("input[type='file']")
            if file_input.count() > 0:
                file_input.first.set_input_files(file_path)
                print("  File selected via input element")
            else:
                # Click on the drop zone to trigger file picker
                drop_zone = None
                try:
                    drop_zone = page.locator("[role='dialog'] .drop-zone, [role='dialog'] button.drop-zone")
                    if drop_zone.count() == 0:
                        drop_zone = page.get_by_text("drop your files", exact=False)
                except:
                    pass

                if drop_zone and drop_zone.count() > 0:
                    # Use file chooser handler
                    with page.expect_file_chooser() as fc_info:
                        drop_zone.first.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(file_path)
                    print("  File selected via file chooser")
                else:
                    print("  Error: Could not find file upload mechanism")
                    page.screenshot(path="upload_debug.png")
                    return False

        # --- Step 5: Wait for processing ---
        print("  Step 5: Waiting for source to be processed...")
        time.sleep(15)

        page.screenshot(path="upload_result.png")
        print("  Result screenshot saved")
        print("  Upload completed!")
        return True

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if context:
            try:
                context.close()
            except:
                pass
        if playwright:
            try:
                playwright.stop()
            except:
                pass


def main():
    parser = argparse.ArgumentParser(description='Add a source to NotebookLM')
    parser.add_argument('--notebook-url', help='NotebookLM notebook URL')
    parser.add_argument('--notebook-id', help='Notebook ID from library')
    parser.add_argument('--file', help='Path to local file (PDF, TXT, MD, audio, etc.)')
    parser.add_argument('--youtube', help='YouTube link to add as source')
    parser.add_argument('--show-browser', action='store_true', help='Show browser')

    args = parser.parse_args()

    notebook_url = args.notebook_url
    if not notebook_url and args.notebook_id:
        library = NotebookLibrary()
        notebook = library.get_notebook(args.notebook_id)
        if notebook:
            notebook_url = notebook['url']
        else:
            print(f"Notebook '{args.notebook_id}' not found")
            return 1

    if not notebook_url:
        library = NotebookLibrary()
        active = library.get_active_notebook()
        if active:
            notebook_url = active['url']
            print(f"Using active notebook: {active['name']}")
        else:
            print("Please provide --notebook-url or --notebook-id")
            return 1

    success = upload_source(
        notebook_url=notebook_url,
        file_path=args.file,
        youtube_url=args.youtube,
        headless=not args.show_browser
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
