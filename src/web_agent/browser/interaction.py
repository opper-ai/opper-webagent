from web_agent.models import Action, Decision, ActionResult
import tempfile
import logging

def click_at_coordinates(page, x, y):
    try:
        page.mouse.click(x, y)
        return ActionResult(success=True, output=f"Clicked at ({x}, y)")
    except Exception as e:
        return ActionResult(success=False, error=str(e))

def take_screenshot(page):
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        page.screenshot(path=temp_filename, type='png')
        return temp_filename, ActionResult(success=True, output=f"Screenshot saved to {temp_filename}")
    except Exception as e:
        return None, ActionResult(success=False, error=str(e))

def set_page_zoom(page, zoom_factor):
    try:
        page.evaluate(f"""
            document.body.style.transform = 'scale({zoom_factor})';
            document.body.style.transformOrigin = '0 0';
        """)
        
        original_viewport = page.viewport_size
        if original_viewport:
            new_width = int(original_viewport['width'] * (1/zoom_factor))
            new_height = int(original_viewport['height'] * (1/zoom_factor))
            page.set_viewport_size({"width": new_width, "height": new_height})
            
    except Exception as e:
        logging.error(f"Failed to set zoom level: {str(e)}")
        raise

def draw_click_dot(page, x, y):
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