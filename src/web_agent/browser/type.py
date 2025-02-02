from ..models import ActionResult

def type_text(page, text):
    """Type text and press Enter and Tab."""
    try:
        page.keyboard.type(text)
        page.keyboard.press('Enter')
        page.keyboard.press('Tab')
        return ActionResult(success=True, output=f"Typed: {text}")
    except Exception as e:
        return ActionResult(success=False, error=str(e)) 