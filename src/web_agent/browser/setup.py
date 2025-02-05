import os

from playwright.async_api import Playwright

from .screenshot import set_page_zoom


async def setup_browser(
    playwright: Playwright,
    session_dir="./browser_data",
    headless=False,
    remote_debugging_port=None,
):
    """Set up and configure the browser instance with persistence"""
    # Create session directory if it doesn't exist
    os.makedirs(session_dir, exist_ok=True)
    storage_file = os.path.join(session_dir, "storage.json")

    # Configure browser launch args
    browser_args = {}
    if remote_debugging_port:
        browser_args["args"] = [f"--remote-debugging-port={remote_debugging_port}"]
    browser_args["headless"] = headless

    browser = await playwright.chromium.launch(**browser_args)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        storage_state=storage_file if os.path.exists(storage_file) else None,
    )
    page = await context.new_page()

    # Set initial zoom level
    await set_page_zoom(page, 1)

    # Save storage on exit
    # NOTE: unclear how this works with _cleanup_resources
    async def teardown():
        try:
            await context.storage_state(path=storage_file)
            await browser.close()
            await playwright.stop()
        except Exception as e:
            print(f"Error during teardown: {e}")

    return playwright, browser, page, teardown
