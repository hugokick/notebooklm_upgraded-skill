# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.2] - 2026-03-12

### Added
- **Robust Research Queries** - Increased timeouts and added error handling for deep-dive queries in complex notebooks.

### Fixed
- **Headless Mode Documentation** - Explicitly noted background operation as the default efficiency mode.

## [1.5.1] - 2026-03-12

### Added
- **Streamlined Notebook Creation** - New `create_notebook.py` for direct, high-speed creation and naming.
- **Self-Healing UI** - Internal logic to automatically detect and dismiss onboarding overlays blocking automation.

## [1.5.0] - 2026-03-12

### Added
- **V1.5.0 Milestone** - Major efficiency overhaul and batch processing stability.

## [1.4.0] - 2026-03-12

### Added
- **Batch File Upload** - Supporting `upload_source.py --file path1 --file path2` to add multiple sources in one session.
- **Dynamic Waits** - Replaced many `time.sleep()` calls with Playwright event-based waits for faster and more robust execution.
- **Chinese Name Support** - Fixed character encoding issues when saving/loading notebook libraries and authentication info on Windows.
- **Reliability Enhancements** - Added strict URL verification, forced "Sources" tab navigation, and per-file upload confirmation.

## [1.3.0] - 2025-11-21

### Added
- **Modular Architecture** - Refactored codebase for better maintainability
  - New `config.py` - Centralized configuration (paths, selectors, timeouts)
  - New `browser_utils.py` - BrowserFactory and StealthUtils classes
  - Cleaner separation of concerns across all scripts

### Changed
- **Timeout increased to 120 seconds** - Long queries no longer timeout prematurely
  - `ask_question.py`: 30s → 120s
  - `browser_session.py`: 30s → 120s
  - Resolves Issue #4

### Fixed
- **Thinking Message Detection** - Fixed incomplete answers showing placeholder text
  - Now waits for `div.thinking-message` element to disappear before reading answer
  - Answers like "Reviewing the content..." or "Looking for answers..." no longer returned prematurely
  - Works reliably across all languages and NotebookLM UI changes

- **Correct CSS Selectors** - Updated to match current NotebookLM UI
  - Changed from `.response-content, .message-content` to `.to-user-container .message-text-content`
  - Consistent selectors across all scripts

- **Stability Detection** - Improved answer completeness check
  - Now requires 3 consecutive stable polls instead of 1 second wait
  - Prevents truncated responses during streaming

## [1.2.0] - 2025-10-28

### Added
- Initial public release
- NotebookLM integration via browser automation
- Session-based conversations with Gemini 2.5
- Notebook library management
- Knowledge base preparation tools
- Google authentication with persistent sessions
