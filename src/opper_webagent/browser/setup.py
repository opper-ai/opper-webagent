from playwright.async_api import Playwright

from .screenshot import set_page_zoom


async def setup_browser(
    playwright: Playwright,
    headless=False,
    remote_debugging_port=None,
):
    """Set up and configure the browser instance with persistence"""
    # Configure browser launch args
    browser_args = {}
    if remote_debugging_port:
        browser_args["args"] = [f"--remote-debugging-port={remote_debugging_port}"]
    browser_args["headless"] = headless

    browser = await playwright.chromium.launch(**browser_args)
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    # Set initial zoom level 
    await set_page_zoom(page, 1)

    # Save storage on exit
    # NOTE: unclear how this works with _cleanup_resources
    async def teardown():
        try:
            await browser.close()
            await playwright.stop()
        except Exception as e:
            print(f"Error during teardown: {e}")

    return playwright, browser, page, teardown
