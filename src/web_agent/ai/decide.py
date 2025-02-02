from opperai import Opper
from opperai.types import CallConfiguration
from ..models import Action

opper = Opper()

def decide_next_action(subgoal, current_url, trajectory, current_view):
    """Decide the next action to take based on the current state and subgoal."""
    instruction = """You are an agent in control of a browser and you are tasked to decide the next action towards a subgoal.
    
    Your task is to decide the next step to take on the page. 
    
    Your main source of input to the next action is a visual interpretation in `current_page` - use this as the main source of information when deciding the next action to take.
    
    Important:  
    * Think hard about the page you are looking at. It has the truth of the current state and always trust this before other things.
    * You might be using a stored session, so you might have cookies from previous sessions loaded.
    * Only provide one next action, never propose multiple actions at once or jump to far ahead. Take your time to do things right.
    * Use the navigate action to set a url.
    * Always use click action to perform navigations and put focus on input fields etc. Choose a param that clearly explains what to click on such as the current field value.
    * Before using an action `type` always make sure you have clicked on the field where you want to type. Don't assume you have clicked unless it is in your trajectory of past actions. Important!
    * The type action always follows with an automatic tab and enter press.
    * Use scroll_down or scroll_up actions to navigate vertically on the page. Scroll down is useful for seeing more results, scroll up for seeing filters etc.
    * You can extract text content of the page with the look action.
    * When you have the answer or have met the goal use the finish action. Add all details that you have of the result of the task to the action params

    Continue until you have clearly met the goal. Always accept cookie popups or any other popups before proceeding.

    Very important!! 
    * Make sure to click before you type!! 
    * ONLY ISSUE ONE ACTION, for example ONE very specific click not some compound action.
    """
    action, _ = opper.call(
        name="decide_action",
        instructions=instruction,
        input={
            "goal": subgoal,
            "trajectory": trajectory[-3:],
            "current_url": current_url,
            "current_page": current_view,
        },
        model="anthropic/claude-3.5-sonnet",
        output_type=Action,
        configuration=CallConfiguration(evaluation={"enabled": False}),
    )
    return action 