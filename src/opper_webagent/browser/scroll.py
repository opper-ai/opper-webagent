from ..models import ActionResult


async def scroll_page(page, x, y, direction="down"):
    """Scroll the page up or down at specific coordinates."""
    try:
        await page.mouse.move(x, y)
        delta = 250 if direction == "down" else -250
        await page.mouse.wheel(0, delta)
        return ActionResult(success=True, output=f"Scrolled {direction} at ({x}, {y})")
    except Exception as e:
        return ActionResult(success=False, error=str(e))
