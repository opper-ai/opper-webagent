from opperai import Opper
from opperai.types import CallConfiguration, ImageInput
from web_agent.models import Action, Decision, ActionResult, ScreenOutput, RelevantInteraction
import logging

opper = Opper()

def get_page_observation(goal, trajectory, screenshot_path, debug: bool = False):

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
            model="anthropic/claude-3.5-sonnet",
            configuration=CallConfiguration(evaluation={"enabled": False}),
        )
        return result
    except Exception as e:
        logging.error(f"Failed to analyze page: {str(e)}")
        return "Failed to analyze screenshot"

def decide_subgoal(goal, current_url, trajectory, current_view):
    instruction = """Given the overall goal and current state, decide on the next immediate subgoal that needs to be accomplished.
    This should be a single, clear objective that moves us one step closer to the overall goal.
    
    Consider:
    * What is visible on the current page
    * What has been done so far in the trajectory
    * What logical next step would make progress
    * Keep subgoals small and achievable in one or two actions
    """
    
    subgoal, _ = opper.call(
        name="decide_subgoal",
        instructions=instruction,
        input={
            "goal": goal,
            "trajectory": trajectory[-10:],
            "current_url": current_url, 
            "current_page": current_view
        },
        model="anthropic/claude-3.5-sonnet",
        output_type=Decision,
        configuration=CallConfiguration(evaluation={"enabled": False}),
    )
    return subgoal

def decide_next_action(subgoal, current_url, trajectory, current_view):
    
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
    * When you have the answer or have met the goal use the finish action. Add all details to the param action.

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

def look_at_page_content(page, action_goal):
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