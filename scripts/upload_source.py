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


def upload_source(notebook_url: str, file_paths: list = None, youtube_url: str = None, headless: bool = False) -> bool:
    """Add new sources (files or youtube link) to a notebook."""
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    except:
        pass

    if not file_paths and not youtube_url:
        print("Error: Must provide either --file or --youtube")
        return False
    if file_paths and youtube_url:
        print("Error: Provide ONLY --file OR --youtube, not both")
        return False

    auth = AuthManager()
    if not auth.is_authenticated():
        print("Not authenticated. Run: python auth_manager.py setup")
        return False

    resolved_files = []
    if file_paths:
        for fp in file_paths:
            p = Path(fp).expanduser().resolve()
            if not p.exists():
                print(f"Error: File does not exist: {p}")
                return False
            resolved_files.append(str(p))

    print(f"Opening notebook: {notebook_url}")
    print(f"Preparing to upload: {resolved_files if resolved_files else youtube_url}")

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
        page = context.new_page()

        # Extract expected ID from URL for verification
        notebook_id_match = re.search(r'/notebook/([a-zA-Z0-9-]+)', notebook_url)
        expected_id = notebook_id_match.group(1) if notebook_id_match else None

        # --- Step 1: Navigate ---
        print("  Step 1: Navigating to notebook...")
        page.goto(notebook_url, wait_until="domcontentloaded", timeout=60000)
        
        # Verify we are on the correct page
        if expected_id and expected_id not in page.url:
             print(f"  Critical Error: Navigation failed or redirected. Expected ID {expected_id} not in current URL.")
             # Try one more time with a longer wait if we are on dashboard
             if "notebooklm.google.com" in page.url and "/notebook/" not in page.url:
                 print("  Currently on dashboard. Re-attempting navigation...")
                 page.goto(notebook_url, wait_until="networkidle", timeout=30000)
                 if expected_id not in page.url:
                      print("  Failing: Still not in target notebook.")
                      return False

        # Wait for the main UI to settle
        try:
            # Look for notebook-specific elements
            page.wait_for_selector("button:has-text('Sources'), .source-list, [role='main']", timeout=20000)
        except:
            print("  Warning: Notebook UI elements not detected. Proceeding with caution.")

        # --- Step 2: Click Sources tab ---
        print("  Step 2: Ensuring Sources tab is active...")
        try:
            # Try a broader selector for the tab
            sources_tab = page.locator("button, a, div").filter(has_text=re.compile(r"^Sources$", re.I)).first
            if sources_tab.count() > 0:
                print("  Clicking Sources tab...")
                sources_tab.click()
                # Wait for the sources list or "Add sources" button to become visible
                page.wait_for_selector("button:has-text('Add sources'), .source-list", timeout=10000)
                print("  Sources panel loaded.")
            else:
                print("  Warning: Sources tab not found. Trying to proceed anyway.")
        except Exception as e:
            print(f"  Warning: Sources tab navigation failed: {e}")

        # Function to handle a single upload action
        def perform_upload(target_path=None, target_youtube=None):
            # --- Step 3: Click "+ Add sources" ---
            print("  Step 3: Clicking Add sources...")
            
            # Use very specific selectors that exclude the main header/sidebar
            # We want the button INSIDE the sources panel
            add_btn_selectors = [
                 "button:has-text('Add sources'):visible",
                 ".source-list-header button",
                 "button:has-text('Upload a source')",
            ]
            
            add_btn = None
            for selector in add_btn_selectors:
                try:
                    candidates = page.locator(selector)
                    count = candidates.count()
                    for i in range(count):
                        el = candidates.nth(i)
                        text = (el.inner_text() or "").lower()
                        # Critical: EXCLUDE "Create notebook"
                        if "create" not in text and el.is_visible():
                            add_btn = el
                            break
                    if add_btn: break
                except:
                    pass

            if not add_btn:
                # Last resort: look for a button with "Add" text that is NOT the create button
                try:
                    all_btns = page.query_selector_all("button:visible")
                    for b in all_btns:
                        text = (b.inner_text() or "").lower()
                        if "add" in text and "create" not in text:
                            # Verify it has an add icon or is in the right area
                            add_btn = b
                            break
                except:
                    pass

            if not add_btn:
                page.screenshot(path="upload_error_no_btn.png")
                print("  Error: Could not find Add sources button (avoided Create notebook)")
                return False

            add_btn.click()
            
            # Wait for dialog
            try:
                # Dialog usually has specific headers like "Add sources"
                page.wait_for_selector("[role='dialog'], mat-dialog-container", timeout=10000)
                time.sleep(1) # Let animations finish
            except:
                print("  Warning: Dialog did not appear quickly")

            # --- Step 4: Handle dialog ---
            if target_youtube:
                print(f"  Step 4: Pasting YouTube URL...")
                search_input = page.locator("[role='dialog'] input, mat-dialog-container input").first
                search_input.wait_for(state="visible", timeout=5000)
                search_input.fill(target_youtube)
                page.keyboard.press("Enter")
                
                try:
                    page.wait_for_selector("button:has-text('Insert'), button:has-text('Add')", timeout=10000)
                    page.locator("button:has-text('Insert'), button:has-text('Add')").first.click()
                    print("  Clicked confirmation button")
                except:
                    pass
            elif target_path:
                filename = Path(target_path).name
                print(f"  Step 4: Uploading file: {filename}")
                
                # Check for direct file input
                try:
                    file_input = page.locator("input[type='file']")
                    if file_input.count() > 0:
                        file_input.first.set_input_files(target_path)
                        print("  File selected via direct input")
                        # Wait for dialog to close
                        page.wait_for_selector("[role='dialog']", state="hidden", timeout=15000)
                        return True
                except:
                    pass
                # Use specific button if available
                upload_btn = page.locator("button:has-text('Upload files'), button:has-text('and more')").first
                try:
                    print("  Attempting to trigger file chooser via 'Upload files' button...")
                    with page.expect_file_chooser(timeout=15000) as fc_info:
                        upload_btn.click(force=True)
                    fc_info.value.set_files(target_path)
                    print("  File selected via chooser")
                except:
                    try:
                        print("  Attempting fallback via 'drop your files' text...")
                        with page.expect_file_chooser(timeout=10000) as fc_info:
                            page.locator("text='drop your files'").first.click(force=True)
                        fc_info.value.set_files(target_path)
                        print("  File selected via fallback chooser")
                    except:
                        print("  Error: Could not trigger file chooser. Trying direct input set as final fallback...")
                        try:
                            page.locator("input[type='file']").first.set_input_files(target_path)
                            print("  File set via direct input fallback")
                        except Exception as e2:
                            print(f"  Final fallback failed: {e2}")
                            return False

            # Verification: Wait for dialog to close and file to appear or progress bar to show
            try:
                # Wait longer for the processing of large files (like 15MB PDFs)
                print("  Waiting for upload dialog to close...")
                page.wait_for_selector("[role='dialog']", state="hidden", timeout=30000)
            except:
                print("  Warning: Dialog still open, but check for processing...")
            
            return True

        if youtube_url:
            if not perform_upload(target_youtube=youtube_url):
                return False
        else:
            for fp in resolved_files:
                filename = Path(fp).name
                if not perform_upload(target_path=fp):
                    print(f"  Failed to initiate upload: {fp}")
                    continue
                
                # Verify processing for this specific file
                print(f"  Verifying upload of {filename} (waiting for indexing to complete)...")
                try:
                    # 1. Wait for the filename to appear
                    page.wait_for_selector(f"text='{filename}'", timeout=90000)
                    print(f"  {filename} is visible in the list")
                    
                    # 2. Wait for the 'Syncing' spinner to disappear
                    # In NotebookLM, syncing indicates server-side processing.
                    # We wait until the selector that matches the syncing icon is gone for this specific row.
                    # Or just wait globally for no syncing indicators in the main panel.
                    sync_selector = "[aria-label='Source is syncing']"
                    print("  Waiting for 'Syncing' spinners to clear (this is critical for recognition)...")
                    try:
                        # Wait for at least one to be hidden or non-existent
                        page.wait_for_selector(sync_selector, state="hidden", timeout=180000)
                        print("  Syncing indicators cleared!")
                    except:
                        print("  Warning: Syncing is taking longer than 180s. Continuing anyway...")
                    
                    # 3. Final verification: Check for the checkbox (indicates 'Ready')
                    ready_indicator = page.locator("div[role='checkbox']").last
                    if ready_indicator.is_visible():
                         print(f"  {filename} appears Ready (Checkbox visible)")
                    
                    time.sleep(5) # Final safety buffer
                    
                except Exception as e:
                    print(f"  Verification warning for {filename}: {e}")
                
                time.sleep(2) # Gap between files

        page.screenshot(path="upload_final_check.png")
        print("  Final screenshot saved")
        print("  Upload sequence completed!")
        return True

    except Exception as e:
        print(f"  Error: {e}")
        return False
    finally:
        if context: context.close()
        if playwright: playwright.stop()


def main():
    parser = argparse.ArgumentParser(description='Add source(s) to NotebookLM')
    parser.add_argument('--notebook-url', help='NotebookLM notebook URL')
    parser.add_argument('--notebook-id', help='Notebook ID from library')
    parser.add_argument('--file', action='append', help='Path to local file (can be repeated for batch)')
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
        file_paths=args.file,
        youtube_url=args.youtube,
        headless=not args.show_browser
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
