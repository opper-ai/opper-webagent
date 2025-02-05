import asyncio
import json
import os
import time
import uuid
from threading import Event
from typing import Callable, Dict, List, Optional

from opperai import trace
from playwright.async_api import async_playwright

from .ai.decide import decide_next_action
from .ai.observe import get_page_observation
from .ai.parse import look_at_page_content
from .ai.reflect import reflect_on_progress
from .ai.response import bake_response
from .ai.vision import find_coordinates
from .browser.click import click_at_coordinates, draw_click_dot
from .browser.navigate import navigate_to_url
from .browser.screenshot import take_screenshot
from .browser.scroll import scroll_page
from .browser.setup import setup_browser
from .browser.type import type_text
from .models import ActionResult
from .status import StatusManager

__all__ = ["WebAgent"]


class WebAgent:
    def __init__(
        self,
        status_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self.status_callback = status_callback

        self._stop_event = Event()
        self._stop_event.clear()
        self._screenshot_files: List[str] = []
        self._status_manager = StatusManager(status_callback)

    def get_status(self) -> Dict:
        """Get the current status of the web agent."""
        if self._status_manager:
            return self._status_manager.get_current()
        return {"action": None, "details": None, "screenshot_path": None}

    def stop(self):
        """Stop the currently running navigation."""
        self._stop_event.set()

    @trace(name="attempt")
    async def attempt(self, page, browser, goal, subgoal, trajectory, response_schema):
        """Execute one round of the agent's decision-making and action loop."""
        # Make the last opened page active
        pages = browser.contexts[0].pages
        if pages:
            page = pages[-1]

        # Take a screenshot of the current page
        screenshot_path, screenshot_result = await take_screenshot(page)
        if screenshot_path:
            self._screenshot_files.append(screenshot_path)
        if not screenshot_result.success:
            trajectory.append(
                {"action": "screenshot", "result": f"Failed: {screenshot_result.error}"}
            )

        # Produce an observation of the current page
        result = get_page_observation(subgoal, trajectory, screenshot_path)
        trajectory.append(
            {
                "action": "observation",
                "result": result.observation if result else "Failed to get observation",
            }
        )

        # Given the page, decide what to do
        decision = reflect_on_progress(goal, page.url, trajectory)
        self._status_manager.update("reflection", decision.reflection, screenshot_path)

        if decision.decision == "finished":
            self._status_manager.update("finishing up", decision.param, screenshot_path)
            completed_result = decision.param

            if response_schema:
                try:
                    final_response = bake_response(completed_result, response_schema)
                    completed_result = final_response
                except Exception as e:
                    completed_result = {
                        "error": "Failed to validate response against schema",
                        "original_response": completed_result,
                        "validation_error": str(e),
                    }
            return "finished", completed_result

        elif decision.decision == "break":
            self._status_manager.update("breaking", decision.param, screenshot_path)
            completed_result = decision.param

            if response_schema:
                try:
                    final_response = bake_response(completed_result, response_schema)
                    completed_result = final_response
                except Exception as e:
                    completed_result = {
                        "error": "Failed to validate response against schema",
                        "original_response": completed_result,
                        "validation_error": str(e),
                    }
            return "break", completed_result

        elif decision.decision == "continue":
            # Construct an action of what to do next
            action = decide_next_action(decision.param, page.url, trajectory, result)

            # Take action on actions
            if action.action == "navigate":
                result = await navigate_to_url(page, action.param)
                await asyncio.sleep(1)
                trajectory.append(
                    {
                        "action_goal": action.action_goal,
                        "action": "navigate",
                        "param": action.param,
                        "result": result.output if result.success else result.error,
                    }
                )
                self._status_manager.update(
                    "navigating", f"Going to {action.param}", screenshot_path
                )

            elif action.action == "look":
                self._status_manager.update(
                    "looking", f"{action.action_goal}", screenshot_path
                )
                try:
                    result = await look_at_page_content(page, action.action_goal)
                except Exception as e:
                    result = f"Looking failed: {str(e)}"
                trajectory.append(
                    {
                        "action_goal": action.action_goal,
                        "action": "look",
                        "param": action.param,
                        "result": result,
                    }
                )

            elif action.action == "click":
                self._status_manager.update(
                    "clicking", f"Finding and clicking {action.param}", screenshot_path
                )
                try:
                    x, y = find_coordinates(screenshot_path, "click " + action.param)
                    html = page.locator("html")
                    bbox = await html.bounding_box()
                    scroll_y = abs(bbox["y"])
                    y = y + scroll_y
                    await draw_click_dot(page, x, y)
                    result = await click_at_coordinates(page, x, y)
                    await asyncio.sleep(1)
                except Exception as e:
                    result = ActionResult(success=False, error=str(e))
                trajectory.append(
                    {
                        "action_goal": action.action_goal,
                        "action": "click",
                        "param": action.param,
                        "result": result.output if result.success else result.error,
                    }
                )

            elif action.action == "type":
                self._status_manager.update(
                    "typing", f"Entering text: {action.param}", screenshot_path
                )
                result = await type_text(page, action.param)
                await asyncio.sleep(1)
                trajectory.append(
                    {
                        "action_goal": action.action_goal,
                        "action": "type",
                        "param": action.param,
                        "result": result.output if result.success else result.error,
                    }
                )

            elif action.action == "scroll_down":
                self._status_manager.update(
                    "scrolling", "Scrolling down", screenshot_path
                )
                try:
                    x, y = find_coordinates(screenshot_path, "click" + action.param)
                    result = await scroll_page(page, x, y, "down")
                except Exception as e:
                    result = ActionResult(success=False, error=str(e))
                trajectory.append(
                    {
                        "action_goal": action.action_goal,
                        "action": "scroll_down",
                        "param": action.param,
                        "result": result.output if result.success else result.error,
                    }
                )

            elif action.action == "scroll_up":
                self._status_manager.update(
                    "scrolling", "Scrolling up", screenshot_path
                )
                try:
                    x, y = find_coordinates(screenshot_path, "click" + action.param)
                    result = await scroll_page(page, x, y, "up")
                except Exception as e:
                    result = ActionResult(success=False, error=str(e))
                trajectory.append(
                    {
                        "action_goal": action.action_goal,
                        "action": "scroll_up",
                        "param": action.param,
                        "result": result.output if result.success else result.error,
                    }
                )

            elif action.action == "wait":
                self._status_manager.update(
                    "waiting", "Waiting for 5 seconds", screenshot_path
                )
                await asyncio.sleep(5)
                result = "Waited 5 seconds"
                trajectory.append(
                    {
                        "action_goal": action.action_goal,
                        "action": "wait",
                        "param": action.param,
                        "result": result,
                    }
                )

            return "continue", None

    def _prepare_goal(
        self,
        goal: str,
        secrets: Optional[str] = None,
        response_schema: Optional[Dict] = None,
    ) -> str:
        """Prepare the goal string with optional secrets and response schema."""
        if secrets:
            goal += "\n\nLogin details (optional):\n" + secrets
        if response_schema:
            goal += (
                "\n\nPlease structure the final response according to this schema:\n"
                + json.dumps(response_schema, indent=2)
            )
        return goal

    async def _cleanup_screenshots(self):
        """Clean up browser and screenshot resources."""
        for screenshot_file in self._screenshot_files:
            try:
                if os.path.exists(screenshot_file):
                    os.remove(screenshot_file)
            except Exception:
                pass
        self._screenshot_files.clear()

    @trace(name="run")
    async def run(
        self,
        goal: str,
        secrets: Optional[str] = None,
        headless: bool = True,
        response_schema: Optional[Dict] = None,
        status_callback: Optional[Callable[[str, str], None]] = None,
        session_id: Optional[str] = None,
    ) -> Dict:
        """Execute an AI-guided web navigation session."""

        if not session_id:
            session_id = str(uuid.uuid4())

        # Start playwright

        start_time = time.time()
        self._stop_event.clear()

        # Initialize status tracking
        self._status_manager = StatusManager(status_callback)
        self._status_manager.update("starting", f"{goal}")

        # Prepare the complete goal
        goal = self._prepare_goal(goal, secrets, response_schema)

        # Initialize trajectory and completed result
        trajectory = []
        completed_result = None

        # Setup browser session
        self._status_manager.update("setup", "Initializing browser")
        async with async_playwright() as playwright:
            playwright, browser, page, teardown = await setup_browser(
                playwright=playwright,
                headless=headless,
            )
            trajectory.append(
                {"action": "setup", "result": "Opened up an empty browser window"}
            )

            # Execute navigation loop
            try:
                while not self._stop_event.is_set():
                    status, result = await self.attempt(
                        page, browser, goal, None, trajectory, response_schema
                    )
                    if status in ["finished", "break"]:
                        completed_result = result
                        break

                # Handle stopped state
                if self._stop_event.is_set():
                    completed_result = "Navigation stopped by user"
                    trajectory.append({"action": "stopped", "result": completed_result})

                return {
                    "result": completed_result,
                    "trajectory": trajectory,
                    "duration_seconds": time.time() - start_time,
                }

            except Exception as e:
                self._status_manager.update("error", str(e))
                raise

            finally:
                self._status_manager.update(
                    "cleanup", "Done with task, closing browser"
                )
                await teardown()
                await self._cleanup_screenshots()
