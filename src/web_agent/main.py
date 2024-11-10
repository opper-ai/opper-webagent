from rich.console import Console
from rich.panel import Panel
from rich import print
import time
import argparse
import signal
import sys

from browser.setup import setup_browser
from browser.interaction import click_at_coordinates, take_screenshot, draw_click_dot
from ai.coordinator import decide_subgoal, decide_next_action, look_at_page_content, get_page_observation
from ai.vision import find_coordinates
from opperai import trace

# Pretty output
console = Console()
DEBUG = True

# Trace this session
@trace
def navigate_with_ai(goal, secrets=None):
    console.print(Panel(f"Starting AI-guided navigation with goal: {goal}", title="Navigation Start", border_style="green"))
   
    if secrets:
        goal = goal + "\n\nLogin details (optional):\n" + secrets

    subgoal = None
    trajectory = []
    
    # Create a playwright session
    playwright, browser, page = setup_browser()
    
    def handle_exit(signum, frame):
        console.print("[red]Exiting gracefully...[/red]")
        browser.close()
        playwright.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        while True:

            if DEBUG and trajectory:
                console.print(Panel(str(trajectory[-1]), title="Last Trajectory Item", border_style="magenta"))
        
            # Make the last opened page active
            pages = browser.contexts[0].pages
            if pages:
                page = pages[-1]

            # Naively wait for page to load
            time.sleep(1)

            # Take a screenshot of the current page
            screenshot_path, screenshot_result = take_screenshot(page)
            if not screenshot_result.success:
                console.print(Panel(f"Failed to take screenshot: {screenshot_result.error}", title="Error", border_style="red"))
                break
            
            # Produce an observation of the current page
            result = get_page_observation(subgoal, trajectory, screenshot_path)
            
            # Given the page, decide what to do
            decision = decide_subgoal(goal, page.url, trajectory, result)
            console.print(Panel(decision.observation, title="Observation", border_style="blue"))
            console.print(Panel(decision.reflection, title="Reflection", border_style="yellow"))
            
            # Construct an action of what to do next
            action = decide_next_action(decision.subgoal, page.url, trajectory, result)
            console.print(Panel(action.action + ": " + action.param, title="Action", border_style="green"))
            
            # Take action on actions

            if action.action == "navigate":
                try:
                    page.goto(action.param, timeout=30000)
                    result = f"Navigated to {action.param}"
                except Exception as e:
                    result = f"Navigation failed: {str(e)}"
                
                trajectory.append({"action_goal": action.action_goal, "action": "navigate", "param": action.param, "result": result})
            
            elif action.action == "look":
                try:
                    result = look_at_page_content(page, action.action_goal)
                except Exception as e:
                    result = f"Looking failed: {str(e)}"
                trajectory.append({"action_goal": action.action_goal, "action": "look", "param": action.param, "result": result})

            elif action.action == "click":
                try:
                    x, y = find_coordinates(screenshot_path, action.action_goal + ": click " + action.param)
                    
                    # We also need to add any distance to the scroll to the screenshot coordinates
                    html = page.locator('html')
                    bbox = html.bounding_box()
                    scroll_y = abs(bbox['y'])
                    y = y + scroll_y

                    draw_click_dot(page, x, y)
                    click = click_at_coordinates(page, x, y)
                    result = f"Clicked at ({x}, {y})"
                except Exception as e:
                    result = f"Clicking failed: {str(e)}"
                trajectory.append({"action_goal": action.action_goal, "action": "click", "param": action.param, "result": result})
            
            elif action.action == "type":
                try:
                    page.keyboard.type(action.param)
                    page.keyboard.press('Enter')
                    page.keyboard.press('Tab')
                    result = f"Typed: {action.param}"
                except Exception as e:
                    result = f"Typing failed: {str(e)}"
                trajectory.append({"action_goal": action.action_goal, "action": "type", "param": action.param, "result": result})
            
            elif action.action == "scroll_down":
                try:
                    x, y = find_coordinates(screenshot_path, "click" + action.param)
                    page.mouse.move(x, y)
                    page.mouse.wheel(0, 250)
                    result = f"Scrolled down at ({x}, {y})"
                except Exception as e:
                    result = f"Scrolling down failed: {str(e)}"
                trajectory.append({"action": "scroll_down", "param": action.param, "result": result, "action_goal": action.action_goal})

            elif action.action == "scroll_up":
                try:
                    x, y = find_coordinates(screenshot_path, "click" + action.param)
                    page.mouse.move(x, y)
                    page.mouse.wheel(0, -250)
                    result = f"Scrolled up at ({x}, {y})"
                except Exception as e:
                    result = f"Scrolling up failed: {str(e)}"
                trajectory.append({"action_goal": action.action_goal, "action": "scroll_up", "param": action.param, "result": result})

            elif action.action == "wait":
                time.sleep(10)
                result = "Waited 10 seconds"
                trajectory.append({"action_goal": action.action_goal, "action": "wait", "param": action.param, "result": result})

            elif action.action == "finished":
                console.print("[green]Goal completed![/green]")
                trajectory.append({"action_goal": action.action_goal, "action": "finished", "param": action.param, "result": "Reached goal"})
                break
        
        # When done, leave the page open for a bit
        time.sleep(10)
    finally:
        browser.close()
        playwright.stop()

def main():
    parser = argparse.ArgumentParser(description="AI-guided web navigation")
    parser.add_argument("goal", type=str, help="The goal for the AI to achieve")
    parser.add_argument("--secrets", type=str, help="Optional login details", default=None)
    args = parser.parse_args()

    navigate_with_ai(args.goal, args.secrets)

if __name__ == "__main__":
    main()