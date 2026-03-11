"""
Configuration for NotebookLM Skill
Centralizes constants, selectors, and paths
"""

from pathlib import Path

# Paths
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"
AUTH_INFO_FILE = DATA_DIR / "auth_info.json"
LIBRARY_FILE = DATA_DIR / "library.json"

# NotebookLM Selectors
QUERY_INPUT_SELECTORS = [
    "textarea.query-box-input",  # Primary
    'textarea[aria-label="Feld für Anfragen"]',  # Fallback German
    'textarea[aria-label="Input for queries"]',  # Fallback English
]

RESPONSE_SELECTORS = [
    ".to-user-container .message-text-content",  # Primary
    "[data-message-author='bot']",
    "[data-message-author='assistant']",
]

# Upload Selectors
ADD_SOURCE_BUTTON = [
    "button:has-text('Upload a source')",
    "button:has-text('Add source')",
    "button.add-data-source-btn",
    "button[aria-label*='source']",
    ".add-source-button"
]

UPLOAD_OPTIONS = {
    "file": [
        "input[type='file']" 
    ],
    "youtube": [
        "div[role='menuitem']:has-text('YouTube')",
        "div.source-option-youtube"
    ]
}

YOUTUBE_INPUT = [
    "input[aria-label*='YouTube']",
    "input[placeholder*='YouTube']",
    ".youtube-url-input"
]

YOUTUBE_INSERT_BUTTON = [
    "button:has-text('Insert')",
    "button:has-text('Add')"
]

# Browser Configuration
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',  # Patches navigator.webdriver
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--no-first-run',
    '--no-default-browser-check'
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Timeouts
LOGIN_TIMEOUT_MINUTES = 10
QUERY_TIMEOUT_SECONDS = 120
PAGE_LOAD_TIMEOUT = 30000
