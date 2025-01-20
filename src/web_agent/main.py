from rich.console import Console
from rich.panel import Panel
from rich import print
import time
import argparse
from threading import Lock, Event

from .browser.setup import setup_browser
from .browser.interaction import click_at_coordinates, take_screenshot, draw_click_dot
from .ai.coordinator import (
    decide_subgoal,
    decide_next_action,
    look_at_page_content,
    get_page_observation,
)
from .ai.vision import find_coordinates
from opperai import trace

# Pretty output
console = Console()

# Global status tracking
_status_lock = Lock()
_current_status = {"action": None, "details": None}
_stop_event = Event()
_stop_event.clear()  # Make sure stop event starts cleared

def get_status():
    """Get the current status of the web agent."""
    with _status_lock:
        return dict(_current_status)

def _update_status(action, details=None):
    """Update the current status of the web agent."""
    with _status_lock:
        _current_status["action"] = action
        _current_status["details"] = details

def stop():
    """Stop the currently running navigation."""
    _stop_event.set()

# Trace this session
@trace
def navigate_with_ai(goal, secrets=None, headless=True, debug=False):
    start_time = time.time()
    # Reset stop event at start of navigation
    _stop_event.clear()
    
    console.print(Panel(f"Starting AI-guided navigation with goal: {goal}", title="Navigation Start", border_style="green"))
    _update_status("starting", f"Goal: {goal}")
   
    if secrets:
        goal = goal + "\n\nLogin details (optional):\n" + secrets

    subgoal = None
    trajectory = []
    completed_result = None
    
    # Create a playwright session
    _update_status("setup", "Initializing browser")
    playwright, browser, page = setup_browser(headless=headless)
    
    try:
        while not _stop_event.is_set():
            if debug and trajectory:
                console.print(Panel(str(trajectory[-1]), title="Last Trajectory Item", border_style="magenta"))

            # Make the last opened page active
            pages = browser.contexts[0].pages
            if pages:
                page = pages[-1]

            # Take a screenshot of the current page
            screenshot_path, screenshot_result = take_screenshot(page)
            if not screenshot_result.success:
                console.print(Panel(f"Failed to take screenshot: {screenshot_result.error}", title="Error", border_style="red"))
            
            # Produce an observation of the current page
            result = get_page_observation(subgoal, trajectory, screenshot_path)
            
            # Given the page, decide what to do
            decision = decide_subgoal(goal, page.url, trajectory, result)
            console.print(Panel(decision.observation, title="Observation", border_style="blue"))
            console.print(Panel(decision.reflection, title="Reflection", border_style="yellow"))
            
            # Construct an action of what to do next
            action = decide_next_action(decision.subgoal, page.url, trajectory, result)
            console.print(Panel(action.action_goal + ": " + action.param, title="Action", border_style="green"))
            
            # Take action on actions
            if action.action == "navigate":
                _update_status("navigating", f"Going to {action.param}")
                try:
                    page.goto(action.param, timeout=30000)
                    result = f"Navigated to {action.param}"
                except Exception as e:
                    result = f"Navigation failed: {str(e)}"
                time.sleep(1)
                trajectory.append({"action_goal": action.action_goal, "action": "navigate", "param": action.param, "result": result})
            
            elif action.action == "look":
                _update_status("looking", f"Examining {action.action_goal}")
                try:
                    result = look_at_page_content(page, action.action_goal)
                except Exception as e:
                    result = f"Looking failed: {str(e)}"
                trajectory.append({"action_goal": action.action_goal, "action": "look", "param": action.param, "result": result})

            elif action.action == "click":
                _update_status("clicking", f"Finding and clicking {action.param}")
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
                _update_status("typing", f"Entering text: {action.param}")
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
                _update_status("scrolling", "Scrolling down")
                try:
                    x, y = find_coordinates(screenshot_path, "click" + action.param)
                    page.mouse.move(x, y)
                    page.mouse.wheel(0, 250)
                    result = f"Scrolled down at ({x}, {y})"
                except Exception as e:
                    result = f"Scrolling down failed: {str(e)}"
                trajectory.append({"action": "scroll_down", "param": action.param, "result": result, "action_goal": action.action_goal})

            elif action.action == "scroll_up":
                _update_status("scrolling", "Scrolling up")
                try:
                    x, y = find_coordinates(screenshot_path, "click" + action.param)
                    page.mouse.move(x, y)
                    page.mouse.wheel(0, -250)
                    result = f"Scrolled up at ({x}, {y})"
                except Exception as e:
                    result = f"Scrolling up failed: {str(e)}"
                trajectory.append({"action_goal": action.action_goal, "action": "scroll_up", "param": action.param, "result": result})

            elif action.action == "wait":
                _update_status("waiting", "Waiting for 10 seconds")
                time.sleep(10)
                result = "Waited 10 seconds"
                trajectory.append({"action_goal": action.action_goal, "action": "wait", "param": action.param, "result": result})

            elif action.action == "finished":
                _update_status("finishing up", action.param)
                console.print("[green]Goal completed![/green]")
                completed_result = action.param
                trajectory.append({"action_goal": action.action_goal, "action": "finished", "param": action.param, "result": "Reached goal"})
                break

        if _stop_event.is_set():
            completed_result = "Navigation stopped by user"
            trajectory.append({"action": "stopped", "result": completed_result})
        
        # When done, leave the page open for a bit
        time.sleep(10)
        duration = time.time() - start_time
        return {"result": completed_result, "trajectory": trajectory, "duration_seconds": duration}
    finally:
        _update_status("cleanup", "Closing browser")
        browser.close()
        playwright.stop()
        _update_status("idle", None)

def main():
    parser = argparse.ArgumentParser(description="AI-guided web navigation")
    parser.add_argument("goal", type=str, help="The goal for the AI to achieve")
    parser.add_argument("--secrets", type=str, help="Optional login details", default=None)
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode", default=False)
    parser.add_argument("--debug", action="store_true", help="Enable debug output", default=False)
    args = parser.parse_args()

    result = navigate_with_ai(args.goal, args.secrets, args.headless, args.debug)
    print(f"Final result: {result['result']}")
    print(f"Duration: {result['duration_seconds']:.2f} seconds")
    print(f"Trajectory: {result['trajectory']}")

if __name__ == "__main__":
    main()