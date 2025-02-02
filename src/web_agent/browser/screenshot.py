import tempfile
from ..models import ActionResult

def take_screenshot(page):
    """Take a screenshot of the current page state."""
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        page.screenshot(path=temp_filename, type='png')
        return temp_filename, ActionResult(success=True, output=f"Screenshot saved to {temp_filename}")
    except Exception as e:
        return None, ActionResult(success=False, error=str(e))

def set_page_zoom(page, zoom_factor):
    """Adjust the zoom level of the page."""
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