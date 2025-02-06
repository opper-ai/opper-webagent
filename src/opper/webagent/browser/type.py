from ..models import ActionResult


async def type_text(page, text):
    """Type text and press Enter and Tab."""
    try:
        await page.keyboard.type(text)
        await page.keyboard.press("Enter")
        await page.keyboard.press("Tab")
        return ActionResult(success=True, output=f"Typed: {text}")
    except Exception as e:
        return ActionResult(success=False, error=str(e))
