from playwright.sync_api import sync_playwright
import os
import atexit

def setup_browser(session_dir="./browser_data", headless=False):
    """Set up and configure the browser instance with persistence"""
    # Create session directory if it doesn't exist
    os.makedirs(session_dir, exist_ok=True)
    storage_file = os.path.join(session_dir, "storage.json")

    # Start playwright
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        storage_state=storage_file if os.path.exists(storage_file) else None
    )
    page = context.new_page()

    # Import here to avoid circular dependency
    from .interaction import set_page_zoom
    set_page_zoom(page, 1)

    # Save storage on exit
    def save_storage():
        try:
            context.storage_state(path=storage_file)
            browser.close()
            playwright.stop()
        except:
            pass  # Ignore errors during cleanup

    # Register cleanup using atexit instead of signals
    atexit.register(save_storage)

    return playwright, browser, page