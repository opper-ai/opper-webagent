from opperai import Opper
from opperai.types import CallConfiguration

opper = Opper()

def look_at_page_content(page, action_goal):
    """Extract and analyze relevant information from the page content."""
    try:
        text_content = page.evaluate("() => document.body.innerText")
        result, _ = opper.call(
            name="parse_page_content",
            instructions="Given a pages text content and a goal, extract the relevant information",
            model="gcp/gemini-1.5-flash-002-eu",
            input={"goal": action_goal, "page_content": text_content},
            output_type=str,
            configuration=CallConfiguration(evaluation={"enabled": False}),
        )
    except Exception as e:
        result = f"Looking at page content failed: {str(e)}"
    
    return result 