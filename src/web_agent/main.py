from rich.console import Console
from rich.panel import Panel
from rich import print
import time
import argparse
import json
from threading import Lock, Event
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, create_model, ValidationError
import os

from .browser.setup import setup_browser
from .browser.interaction import click_at_coordinates, take_screenshot, draw_click_dot
from .ai.coordinator import (
    reflect_on_progress,
    decide_next_action,
    look_at_page_content,
    get_page_observation,
    bake_response,
)
from .ai.vision import find_coordinates
from opperai import trace

# Pretty output - only used in debug mode
console = Console()

@dataclass
class StatusEntry:
    timestamp: datetime
    action: str
    details: str = None
    screenshot_path: Optional[str] = None

# Global status tracking
_status_lock = Lock()
_status_log: List[StatusEntry] = []
_stop_event = Event()
_stop_event.clear()  # Make sure stop event starts cleared
_screenshot_files: List[str] = []  # Track screenshot files

def get_status() -> Dict:
    """Get the current status of the web agent."""
    with _status_lock:
        if _status_log:
            latest = _status_log[-1]
            return {
                "action": latest.action,
                "details": latest.details,
                "screenshot_path": latest.screenshot_path
            }
        return {"action": None, "details": None, "screenshot_path": None}

def _update_status(action: str, details: str = None, callback: Optional[Callable[[str, str], None]] = None, screenshot_path: Optional[str] = None):
    """Update the current status of the web agent."""
    with _status_lock:
        _status_log.append(StatusEntry(
            timestamp=datetime.now(),
            action=action,
            details=details,
            screenshot_path=screenshot_path
        ))
    if callback:
        callback(action, details)

def stop():
    """Stop the currently running navigation."""
    _stop_event.set()

@trace(name="attempt")
def _execute_agent_round(page, browser, goal, subgoal, trajectory, debug, response_schema, status_callback=None):
    """Execute one round of the agent's decision-making and action loop."""
    if debug and trajectory:
        console.print(Panel(str(trajectory[-1]), title="Last Trajectory Item", border_style="magenta"))

    # Make the last opened page active
    pages = browser.contexts[0].pages
    if pages:
        page = pages[-1]

    # Take a screenshot of the current page
    screenshot_path, screenshot_result = take_screenshot(page)
    if screenshot_path:
        _screenshot_files.append(screenshot_path)
    if not screenshot_result.success and debug:
        console.print(Panel(f"Failed to take screenshot: {screenshot_result.error}", title="Error", border_style="red"))
        trajectory.append({"action": "screenshot", "result": f"Failed: {screenshot_result.error}"})
    
    # Produce an observation of the current page
    result = get_page_observation(subgoal, trajectory, screenshot_path)
    
    # Given the page, decide what to do
    decision = reflect_on_progress(goal, page.url, trajectory, result)
    _update_status("reflection", decision.reflection, status_callback, screenshot_path)

    if decision.decision == "finished":
        _update_status("finishing up", decision.param, status_callback, screenshot_path)
        if debug:
            console.print("[green]Goal completed![/green]")
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
        _update_status("breaking", decision.param, status_callback, screenshot_path)
        return "break", decision.param

    elif decision.decision == "continue":

        if debug:
            console.print(Panel(decision.observation, title="Observation", border_style="blue"))
            console.print(Panel(decision.reflection, title="Reflection", border_style="yellow"))
        
        # Construct an action of what to do next
        action = decide_next_action(decision.param, page.url, trajectory, result)
        if debug:
            console.print(Panel(action.action_goal + ": " + action.param, title="Action", border_style="green"))
        
        # Take action on actions
        if action.action == "navigate":
            _update_status("navigating", f"Going to {action.param}", status_callback, screenshot_path)
            try:
                page.goto(action.param, timeout=30000)
                result = f"Navigated to {action.param}"
            except Exception as e:
                result = f"Navigation failed: {str(e)}"
            time.sleep(1)
            trajectory.append({"action_goal": action.action_goal, "action": "navigate", "param": action.param, "result": result})
        
        elif action.action == "look":
            _update_status("looking", f"{action.action_goal}", status_callback, screenshot_path)
            try:
                result = look_at_page_content(page, action.action_goal)
            except Exception as e:
                result = f"Looking failed: {str(e)}"
            trajectory.append({"action_goal": action.action_goal, "action": "look", "param": action.param, "result": result})

        elif action.action == "click":
            _update_status("clicking", f"Finding and clicking {action.param}", status_callback, screenshot_path)
            try:
                x, y = find_coordinates(screenshot_path, "click " + action.param)
                html = page.locator('html')
                bbox = html.bounding_box()
                scroll_y = abs(bbox['y'])
                y = y + scroll_y
                draw_click_dot(page, x, y)
                click = click_at_coordinates(page, x, y)
                result = f"Clicked at ({x}, {y})"
                time.sleep(1)
            except Exception as e:
                result = f"Clicking failed: {str(e)}"
            trajectory.append({"action_goal": action.action_goal, "action": "click", "param": action.param, "result": result})
        
        elif action.action == "type":
            _update_status("typing", f"Entering text: {action.param}", status_callback, screenshot_path)
            try:
                page.keyboard.type(action.param)
                page.keyboard.press('Enter')
                page.keyboard.press('Tab')
                result = f"Typed: {action.param}"
                time.sleep(1)
            except Exception as e:
                result = f"Typing failed: {str(e)}"
            trajectory.append({"action_goal": action.action_goal, "action": "type", "param": action.param, "result": result})
        
        elif action.action == "scroll_down":
            _update_status("scrolling", "Scrolling down", status_callback, screenshot_path)
            try:
                x, y = find_coordinates(screenshot_path, "click" + action.param)
                page.mouse.move(x, y)
                page.mouse.wheel(0, 250)
                result = f"Scrolled down at ({x}, {y})"
            except Exception as e:
                result = f"Scrolling down failed: {str(e)}"
            trajectory.append({"action": "scroll_down", "param": action.param, "result": result, "action_goal": action.action_goal})

        elif action.action == "scroll_up":
            _update_status("scrolling", "Scrolling up", status_callback, screenshot_path)
            try:
                x, y = find_coordinates(screenshot_path, "click" + action.param)
                page.mouse.move(x, y)
                page.mouse.wheel(0, -250)
                result = f"Scrolled up at ({x}, {y})"
            except Exception as e:
                result = f"Scrolling up failed: {str(e)}"
            trajectory.append({"action_goal": action.action_goal, "action": "scroll_up", "param": action.param, "result": result})

        elif action.action == "wait":
            _update_status("waiting", "Waiting for 10 seconds", status_callback, screenshot_path)
            time.sleep(10)
            result = "Waited 10 seconds"
            trajectory.append({"action_goal": action.action_goal, "action": "wait", "param": action.param, "result": result})

        return "continue", None

# Trace this session
@trace(name="run")
def navigate_with_ai(goal, secrets=None, headless=True, debug=False, response_schema: Optional[Dict] = None, status_callback: Optional[Callable[[str, str], None]] = None):
    start_time = time.time()
    # Reset stop event at start of navigation
    _stop_event.clear()

    if debug:
        console.print(Panel(f"Starting AI-guided navigation with goal: {goal}", title="Navigation Start", border_style="green"))
    
    _update_status("starting", f"{goal}", status_callback)
   
    if secrets:
        goal = goal + "\n\nLogin details (optional):\n" + secrets

    if response_schema:
        goal = goal + "\n\nPlease structure the final response according to this schema:\n" + json.dumps(response_schema, indent=2)

    subgoal = None
    trajectory = []
    completed_result = None
    
    # Create a playwright session
    _update_status("setup", "Initializing browser", status_callback)
    playwright, browser, page = setup_browser(headless=headless)
    
    try:
        while not _stop_event.is_set():
            status, result = _execute_agent_round(page, browser, goal, subgoal, trajectory, debug, response_schema, status_callback)
            if status in ["finished", "break"]:
                completed_result = result
                break

        if _stop_event.is_set():
            completed_result = "Navigation stopped by user"
            trajectory.append({"action": "stopped", "result": completed_result})
        
        duration = time.time() - start_time
        return {"result": completed_result, "trajectory": trajectory, "duration_seconds": duration}
    except Exception as e:
        _update_status("error", str(e), status_callback)
        raise e
    finally:
        _update_status("cleanup", "Done with task, closing browser", status_callback)
        # Clean up screenshot files
        for screenshot_file in _screenshot_files:
            try:
                if os.path.exists(screenshot_file):
                    os.remove(screenshot_file)
            except Exception as e:
                if debug:
                    console.print(f"Failed to remove screenshot {screenshot_file}: {str(e)}")
        _screenshot_files.clear()
        browser.close()
        playwright.stop()

def main():
    parser = argparse.ArgumentParser(description="AI-guided web navigation")
    parser.add_argument("goal", type=str, help="The goal for the AI to achieve")
    parser.add_argument("--secrets", type=str, help="Optional login details", default=None)
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode", default=False)
    parser.add_argument("--debug", action="store_true", help="Enable debug output", default=False)
    parser.add_argument("--response-schema", type=str, help="JSON schema for structuring the final response", default=None)
    args = parser.parse_args()

    def debug_status_callback(action: str, details: str):
        if args.debug:
            console.print(f"Status Update - {action}: {details}")

    response_schema = json.loads(args.response_schema) if args.response_schema else None
    result = navigate_with_ai(
        args.goal, 
        args.secrets, 
        args.headless, 
        args.debug, 
        response_schema,
        status_callback=debug_status_callback if args.debug else None
    )
    if args.debug:
        console.print(f"Final result: {result['result']}")
        console.print(f"Duration: {result['duration_seconds']:.2f} seconds")
        console.print(f"Trajectory: {result['trajectory']}")

def my_status_callback(action: str, details: str):
    print(f"Status: {action} - {details}")

if __name__ == "__main__":
    main()