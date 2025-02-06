from ..models import ActionResult


async def navigate_to_url(page, url):
    """Navigate to a specific URL."""
    try:
        await page.goto(url, timeout=30000)
        return ActionResult(success=True, output=f"Navigated to {url}")
    except Exception as e:
        return ActionResult(success=False, error=str(e))
