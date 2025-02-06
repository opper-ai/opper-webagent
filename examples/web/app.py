import asyncio
import base64
import json
import os
import sys
import uuid
from pathlib import Path
from queue import Queue

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add the src directory to the Python path for the examples
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

from opper_webagent import WebAgent

app = FastAPI()
templates = Jinja2Templates(directory="examples/web_interface/templates")

# Global state for status updates
status_queues = {}


def create_status_callback(session_id: str):
    """Create a status callback for a specific session"""

    def status_callback(action: str, details: str, screenshot_path: str = None):
        """Callback function to receive status updates from the agent"""
        print(
            f"Session {session_id}: {action} {details} {screenshot_path if screenshot_path else 'no screenshot'}"
        )

        # Convert screenshot to base64 if available
        screenshot_data = None
        if screenshot_path and os.path.isfile(screenshot_path):
            with open(screenshot_path, "rb") as f:
                screenshot_data = base64.b64encode(f.read()).decode("utf-8")

        if session_id in status_queues:
            status_queues[session_id].put(
                {
                    "action": action,
                    "details": details,
                    "screenshot_data": screenshot_data,
                }
            )

    return status_callback


class TaskRequest(BaseModel):
    goal: str
    secrets: str = None
    response_schema: dict = None


async def run_agent_task(
    session_id: str, goal: str, secrets: str = None, response_schema: dict = None
):
    """Run the agent task"""
    agent = WebAgent()
    try:
        result = await agent.run(
            goal=goal,
            secrets=secrets,
            response_schema=response_schema,
            status_callback=create_status_callback(session_id),
        )
        if session_id in status_queues:
            status_queues[session_id].put(
                {"action": "completed", "details": "Task completed", "result": result}
            )
    except Exception as e:
        if session_id in status_queues:
            status_queues[session_id].put(
                {"action": "error", "details": f"Task failed: {str(e)}"}
            )
        raise
    finally:
        # Clean up queue after task completes
        status_queues.pop(session_id, None)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/run")
async def start_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    """Start a new agent task"""
    session_id = str(uuid.uuid4())

    # Create new queue for this session
    status_queues[session_id] = Queue()

    # Add task to background tasks
    background_tasks.add_task(
        run_agent_task,
        session_id=session_id,
        goal=task_request.goal,
        secrets=task_request.secrets,
        response_schema=task_request.response_schema,
    )

    return JSONResponse({"session_id": session_id})


async def status_event_generator(session_id: str):
    """Generate SSE events for task status updates"""
    if session_id not in status_queues:
        return

    queue = status_queues[session_id]
    while True:
        try:
            # Non-blocking check for new status
            if not queue.empty():
                status = queue.get()
                yield f"data: {json.dumps(status)}\n\n"
                # If task completed or errored, stop streaming
                if status["action"] in ["completed", "error"]:
                    break
            else:
                # Send keep-alive and sleep briefly
                yield ": keep-alive\n\n"
                await asyncio.sleep(1.0)
        except Exception as e:
            print(f"Error in status generator: {e}")
            break


@app.get("/status/{session_id}")
async def status_stream(session_id: str):
    """Stream status updates for a session"""
    return StreamingResponse(
        status_event_generator(session_id), media_type="text/event-stream"
    )


@app.post("/stop/{session_id}")
async def stop_task(session_id: str):
    """Stop updates for a session"""
    status_queues.pop(session_id, None)
    return JSONResponse({"status": "stopped"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
