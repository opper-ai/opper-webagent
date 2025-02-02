from ..models import ActionResult

def click_at_coordinates(page, x, y):
    """Click at specific coordinates on the page."""
    try:
        page.mouse.click(x, y)
        return ActionResult(success=True, output=f"Clicked at ({x}, y)")
    except Exception as e:
        return ActionResult(success=False, error=str(e))

def draw_click_dot(page, x, y):
    """Draw a temporary visual indicator where a click occurred."""
    page.evaluate("""([x, y]) => {
        const dot = document.createElement('div');
        dot.style.position = 'absolute';
        dot.style.left = x + 'px';
        dot.style.top = y + 'px';
        dot.style.width = '25px';
        dot.style.height = '25px';
        dot.style.backgroundColor = 'blue';
        dot.style.borderRadius = '50%';
        dot.style.opacity = '0.5';
        dot.style.pointerEvents = 'none';
        dot.style.transform = 'translate(-50%, -50%)';
        dot.style.zIndex = '9999';
        document.body.appendChild(dot);
        setTimeout(() => dot.remove(), 2500);
    }""", [x, y]) 