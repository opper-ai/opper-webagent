import time
import argparse
import json
from threading import Event
from typing import List, Dict, Optional, Callable
from datetime import datetime
import os

from .browser.setup import setup_browser
from .browser.click import click_at_coordinates, draw_click_dot
from .browser.screenshot import take_screenshot
from .browser.navigate import navigate_to_url
from .browser.type import type_text
from .browser.scroll import scroll_page

from .ai.reflect import reflect_on_progress
from .ai.decide import decide_next_action
from .ai.parse import look_at_page_content
from .ai.observe import get_page_observation
from .ai.response import bake_response
from .ai.vision import find_coordinates

from .status import StatusManager

from opperai import trace

__all__ = ['run', 'get_status', 'stop']

# Global state
_stop_event = Event()
_stop_event.clear()  # Make sure stop event starts cleared
_screenshot_files: List[str] = []  # Track screenshot files
_status_manager: Optional[StatusManager] = None

def get_status() -> Dict:
    """Get the current status of the web agent."""
    global _status_manager
    if _status_manager:
        return _status_manager.get_current()
    return {"action": None, "details": None, "screenshot_path": None}

def stop():
    """Stop the currently running navigation."""
    _stop_event.set()

@trace(name="attempt")
def attempt(page, browser, goal, subgoal, trajectory, response_schema):
    """Execute one round of the agent's decision-making and action loop."""
    # Make the last opened page active
    pages = browser.contexts[0].pages
    if pages:
        page = pages[-1]

    # Take a screenshot of the current page
    screenshot_path, screenshot_result = take_screenshot(page)
    if screenshot_path:
        _screenshot_files.append(screenshot_path)
    if not screenshot_result.success:
        trajectory.append({"action": "screenshot", "result": f"Failed: {screenshot_result.error}"})
    
    # Produce an observation of the current page
    result = get_page_observation(subgoal, trajectory, screenshot_path)
    trajectory.append({
        "action": "observation", 
        "result": result.observation if result else "Failed to get observation"
        })        
    
    # Given the page, decide what to do
    decision = reflect_on_progress(goal, page.url, trajectory)
    _status_manager.update("reflection", decision.reflection, screenshot_path)

    if decision.decision == "finished":
        _status_manager.update("finishing up", decision.param, screenshot_path)
        completed_result = decision.param
        
        if response_schema:
            try:
                final_response = bake_response(completed_result, response_schema)
                completed_result = final_response
            except Exception as e:
                completed_result = {
                    "error": "Failed to validate response against schema",
                    "original_response": completed_result,
                    "validation_error": str(e)
                }
        return "finished", completed_result

    elif decision.decision == "break":
        _status_manager.update("breaking", decision.param, screenshot_path)
        completed_result = decision.param
        
        if response_schema:
            try:
                final_response = bake_response(completed_result, response_schema)
                completed_result = final_response
            except Exception as e:
                completed_result = {
                    "error": "Failed to validate response against schema", 
                    "original_response": completed_result,
                    "validation_error": str(e)
                }
        return "break", completed_result

    elif decision.decision == "continue":
        # Construct an action of what to do next
        action = decide_next_action(decision.param, page.url, trajectory, result)
        
        # Take action on actions
        if action.action == "navigate":
            result = navigate_to_url(page, action.param)
            time.sleep(1)
            trajectory.append({
                "action_goal": action.action_goal, 
                "action": "navigate", 
                "param": action.param, 
                "result": result.output if result.success else result.error
                })    
            _status_manager.update("navigating", f"Going to {action.param}", screenshot_path)

        elif action.action == "look":
            _status_manager.update("looking", f"{action.action_goal}", screenshot_path)
            try:
                result = look_at_page_content(page, action.action_goal)
            except Exception as e:
                result = f"Looking failed: {str(e)}"
            trajectory.append({
                "action_goal": action.action_goal, 
                "action": "look", 
                "param": action.param, 
                "result": result
                })

        elif action.action == "click":
            _status_manager.update("clicking", f"Finding and clicking {action.param}", screenshot_path)
            try:
                x, y = find_coordinates(screenshot_path, "click " + action.param)
                html = page.locator('html')
                bbox = html.bounding_box()
                scroll_y = abs(bbox['y'])
                y = y + scroll_y
                draw_click_dot(page, x, y)
                result = click_at_coordinates(page, x, y)
                time.sleep(1)
            except Exception as e:
                result = ActionResult(success=False, error=str(e))
            trajectory.append({
                "action_goal": action.action_goal, 
                "action": "click", 
                "param": action.param, 
                "result": result.output if result.success else result.error
                })
        
        elif action.action == "type":
            _status_manager.update("typing", f"Entering text: {action.param}", screenshot_path)
            result = type_text(page, action.param)
            time.sleep(1)
            trajectory.append({
                "action_goal": action.action_goal,
                "action": "type",
                "param": action.param,
                "result": result.output if result.success else result.error
            })
        
        elif action.action == "scroll_down":
            _status_manager.update("scrolling", "Scrolling down", screenshot_path)
            try:
                x, y = find_coordinates(screenshot_path, "click" + action.param)
                result = scroll_page(page, x, y, "down")
            except Exception as e:
                result = ActionResult(success=False, error=str(e))
            trajectory.append({
                    "action_goal": action.action_goal,
                    "action": "scroll_down", 
                    "param": action.param, 
                    "result": result.output if result.success else result.error, 
                })

        elif action.action == "scroll_up":
            _status_manager.update("scrolling", "Scrolling up", screenshot_path)
            try:
                x, y = find_coordinates(screenshot_path, "click" + action.param)
                result = scroll_page(page, x, y, "up")
            except Exception as e:
                result = ActionResult(success=False, error=str(e))
            trajectory.append({
                "action_goal": action.action_goal,
                "action": "scroll_up", 
                "param": action.param, 
                "result": result.output if result.success else result.error, 
            })

        elif action.action == "wait":
            _status_manager.update("waiting", "Waiting for 5 seconds", screenshot_path)
            time.sleep(5)
            result = "Waited 5 seconds"
            trajectory.append({
                "action_goal": action.action_goal, 
                "action": "wait", 
                "param": action.param, 
                "result": result
                })

        return "continue", None

def _prepare_goal(goal: str, secrets: Optional[str] = None, response_schema: Optional[Dict] = None) -> str:
    """Prepare the goal string with optional secrets and response schema."""
    if secrets:
        goal += "\n\nLogin details (optional):\n" + secrets
    if response_schema:
        goal += "\n\nPlease structure the final response according to this schema:\n" + json.dumps(response_schema, indent=2)
    return goal

def _cleanup_resources(browser, playwright, screenshot_files):
    """Clean up browser and screenshot resources."""
    for screenshot_file in screenshot_files:
        try:
            if os.path.exists(screenshot_file):
                os.remove(screenshot_file)
        except Exception:
            pass
    screenshot_files.clear()
    browser.close()
    playwright.stop()

@trace(name="run")
def run(
    goal: str, 
    secrets: Optional[str] = None, 
    headless: bool = True, 
    response_schema: Optional[Dict] = None, 
    status_callback: Optional[Callable[[str, str], None]] = None
) -> Dict:
    """Execute an AI-guided web navigation session."""
    
    global _status_manager, _screenshot_files
    start_time = time.time()
    _stop_event.clear()
    
    # Initialize status tracking
    _status_manager = StatusManager(status_callback)
    _status_manager.update("starting", f"{goal}")
    
    # Prepare the complete goal
    goal = _prepare_goal(goal, secrets, response_schema)
    
    # Initialize trajectory and completed result
    trajectory = []
    completed_result = None

    # Setup browser session
    _status_manager.update("setup", "Initializing browser")
    playwright, browser, page = setup_browser(headless=headless)
    trajectory.append(
        {"action": "setup", 
         "result": "Opened up an empty browser window"
         })
    
    # Execute navigation loop
    try:
        while not _stop_event.is_set():
            status, result = attempt(page, browser, goal, None, trajectory, response_schema)
            if status in ["finished", "break"]:
                completed_result = result
                break
        
        # Handle stopped state
        if _stop_event.is_set():
            completed_result = "Navigation stopped by user"
            trajectory.append({"action": "stopped", "result": completed_result})
        
        return {
            "result": completed_result,
            "trajectory": trajectory,
            "duration_seconds": time.time() - start_time
        }
        
    except Exception as e:
        _status_manager.update("error", str(e))
        raise
        
    finally:
        _status_manager.update("cleanup", "Done with task, closing browser")
        _cleanup_resources(browser, playwright, _screenshot_files)

def main():
    parser = argparse.ArgumentParser(description="AI-guided web navigation")
    parser.add_argument("goal", type=str, help="The goal for the AI to achieve")
    parser.add_argument("--secrets", type=str, help="Optional login details", default=None)
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode", default=False)
    parser.add_argument("--response-schema", type=str, help="JSON schema for structuring the final response", default=None)
    args = parser.parse_args()

    response_schema = json.loads(args.response_schema) if args.response_schema else None
    result = run(
        args.goal, 
        args.secrets, 
        args.headless, 
        response_schema
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()