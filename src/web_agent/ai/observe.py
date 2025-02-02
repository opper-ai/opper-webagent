from opperai import Opper
from opperai.types import CallConfiguration, ImageInput
from ..models import ScreenOutput
import logging

opper = Opper()

def get_page_observation(goal, trajectory, screenshot_path, debug: bool = False):
    """Get an observation of the current page state from a screenshot."""
    if trajectory: 
        last_action = trajectory[-1]
    else: 
        last_action = "No action"

    instruction = f"""Given a page screenshot of the current page as part of the process of reaching the goal `{goal}`.
    Provide an analysis of what you are currently observing on the page, if the last action worked `{last_action}`, what seems to be left to do in the current view, and what distinct elements can you interact with (click, type, scroll etc) and for each how would you describe them (label etc) and what are their pixel coordinate? 
    Be very descriptive of how interaction elements are visually represented."""

    try:
        result, _ = opper.call(
            name="look_at_page",
            instructions=instruction,
            input=ImageInput.from_path(screenshot_path),
            output_type=ScreenOutput,
            model="anthropic/claude-3.5-sonnet-20241022",
            configuration=CallConfiguration(evaluation={"enabled": False}),
        )
        return result
    except Exception as e:
        logging.error(f"Failed to analyze page: {str(e)}")
        return "Failed to analyze screenshot" 