from playwright.sync_api import sync_playwright
from .interaction import set_page_zoom
import os
import signal

def setup_browser(session_dir="./browser_data", headless=False):
    """Set up and configure the browser instance with persistence"""
    # Create session directory if it doesn't exist
    os.makedirs(session_dir, exist_ok=True)
    storage_file = os.path.join(session_dir, "storage.json")

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=headless, 
        args=['--enable-automation', '--show-debug-info']
    )
   
    # Create context with storage state if it exists
    context_params = {}
    if os.path.exists(storage_file):
        context_params['storage_state'] = storage_file
    
    context = browser.new_context(**context_params)
    page = context.new_page()

    set_page_zoom(page, 1)
    return playwright, browser, page
    
    # Save storage state on page navigation and close
    def save_storage():
        context.storage_state(path=storage_file)
    
    page.on('close', save_storage)
    page.on('framenavigated', save_storage)
    
    return playwright, browser, page