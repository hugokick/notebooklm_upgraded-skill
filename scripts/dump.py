"""Diagnostic: Click Add sources and capture the dialog that appears."""
import sys, codecs, time, re
from pathlib import Path
from patchright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from browser_utils import BrowserFactory

def diag():
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    playwright = sync_playwright().start()
    context = BrowserFactory.launch_persistent_context(playwright, headless=False)
    page = context.new_page()
    
    url = "https://notebooklm.google.com/notebook/bcf73eee-8d13-4c2f-a894-12b8e21989c4"
    print("Navigating...")
    try:
        page.goto(url, wait_until="commit", timeout=30000)
    except:
        pass
    time.sleep(10)
    
    # Click Sources tab
    tab = page.get_by_text("Sources", exact=True)
    if tab.count() > 0:
        tab.first.click()
        print("Clicked Sources tab")
        time.sleep(3)
    
    # Click Add sources
    btn = page.get_by_text("Add sources", exact=False)
    if btn.count() > 0:
        btn.first.click()
        print("Clicked Add sources")
        time.sleep(3)
    
    # Take screenshot of the dialog
    page.screenshot(path="diag_add_dialog.png")
    print("Screenshot saved")
    
    # Dump ALL elements inside overlay panels
    elements = page.evaluate('''() => {
        let results = [];
        // Check overlay panes
        let panes = document.querySelectorAll('.cdk-overlay-pane, .mat-dialog-container, [role="dialog"], [role="listbox"], [role="menu"]');
        for (let pane of panes) {
            let all = pane.querySelectorAll('*');
            for (let el of all) {
                let rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    let text = (el.innerText || el.textContent || '').trim().split('\\n')[0].substring(0, 80);
                    if (text) {
                        results.push({
                            tag: el.tagName,
                            text: text,
                            cls: (typeof el.className === 'string' ? el.className : '').substring(0, 100),
                            role: el.getAttribute('role') || '',
                            id: el.id || ''
                        });
                    }
                }
            }
        }
        
        // Also check top-level dialog/modal components
        let modals = document.querySelectorAll('mat-dialog-container, mat-bottom-sheet-container, .cdk-overlay-connected-position-bounding-box');
        for (let m of modals) {
            results.push({tag: m.tagName, text: m.innerText?.substring(0, 200) || '', cls: m.className?.substring(0, 100) || '', role: '', id: ''});
        }
        
        return results;
    }''')
    
    print(f"\\n=== Dialog/Overlay elements: {len(elements)} ===")
    seen = set()
    for el in elements:
        key = f"{el['tag']}|{el['text'][:30]}"
        if key not in seen:
            seen.add(key)
            print(f"  <{el['tag']} role='{el['role']}' cls='{el['cls'][:50]}'> {el['text']}")
    
    # Also dump all buttons on the page for good measure
    buttons = page.evaluate('''() => {
        let results = [];
        let all = document.querySelectorAll('button, [role="button"], [role="menuitem"], [role="option"]');
        for (let el of all) {
            let rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                let text = (el.innerText || el.textContent || '').trim().split('\\n')[0].substring(0, 80);
                results.push({
                    tag: el.tagName, text: text,
                    cls: (typeof el.className === 'string' ? el.className : '').substring(0, 80)
                });
            }
        }
        return results;
    }''')
    
    print(f"\\n=== All visible buttons: {len(buttons)} ===")
    seen2 = set()
    for b in buttons:
        key = b['text'][:30]
        if key not in seen2:
            seen2.add(key)
            print(f"  <{b['tag']} cls='{b['cls'][:40]}'> {b['text']}")
    
    context.close()
    playwright.stop()

if __name__ == "__main__":
    diag()
