import asyncio
import base64
import json
import os
import sys
import uuid
from pathlib import Path
from queue import Queue
from typing import Dict, Optional

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add the src directory to the Python path for the examples
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

from opper_webagent import WebAgent

app = FastAPI()

templates = Jinja2Templates(directory="examples/rest/templates")

# Store active sessions and their status
status_queues: Dict[str, Queue] = {}

# Default response schema
DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "failure", "partial"],
            "description": "The outcome of the requested task",
        },
        "message": {
            "type": "string",
            "description": "A detailed description of what was accomplished or why it failed",
        },
    },
    "required": ["status", "message"],
}


# Request/Response models
class RunRequest(BaseModel):
    goal: str
    secrets: Optional[str] = None
    responseSchema: Optional[dict] = None


def status_callback(
    action: str, details: str, screenshot_path: str = None, session_id: str = None
):
    """Callback function to receive status updates from the agent"""
    print(f"{session_id}: {action}, {details}, {screenshot_path}")

    # Convert screenshot to base64 if available
    screenshot_data = None
    if screenshot_path and os.path.isfile(screenshot_path):
        with open(screenshot_path, "rb") as f:
            screenshot_data = base64.b64encode(f.read()).decode("utf-8")

    status_update = {
        "action": action,
        "details": details,
        "screenshot_data": screenshot_data,
    }

    if session_id:
        status_queues[session_id].put(status_update)


async def status_stream_generator(session_id: str):
    """Generate status stream events"""
    if session_id not in status_queues:
        return

    queue = status_queues[session_id]
    while True:
        try:
            if not queue.empty():
                status = queue.get()
                yield f"data: {json.dumps(status)}\n\n".encode("utf-8")
                if status.get("action") in ["completed", "error"]:
                    break
            else:
                # Send keep-alive every second if no updates
                await asyncio.sleep(1)
                yield ": keep-alive\n\n"
                # yield b'data: {"action": null, "details": null}\n\n'

        except Exception as e:
            print(f"error in status stream: {str(e)}")
            break


@app.get("/status-stream/{session_id}")
async def status_stream(session_id: str):
    """SSE endpoint for streaming status updates"""
    return StreamingResponse(
        status_stream_generator(session_id), media_type="text/event-stream"
    )


@app.patch("/stop/{session_id}")
async def stop_agent(session_id: str):
    """Stop an agent session"""
    if session_id and session_id in status_queues:
        status_queues.pop(session_id, None)
    return JSONResponse({"status": "stopped"})


# Create a session-specific callback
def _get_session_callback(session_id: str):
    def callback(action, details, screenshot_path=None):
        status_callback(action, details, screenshot_path, session_id)

    return callback


async def _run_agent(session_id: str, request: RunRequest):
    """Start a new agent run"""
    schema = request.responseSchema if request.responseSchema else DEFAULT_SCHEMA

    callback = _get_session_callback(session_id)
    callback("initializing", "starting task")

    try:
        result = await WebAgent().run(
            goal=request.goal,
            secrets=request.secrets,
            response_schema=schema,
            status_callback=callback,
            session_id=session_id,
        )
        if session_id in status_queues:
            status_queues[session_id].put(
                {"action": "completed", "details": "Task completed", "result": result}
            )
        return result
    except Exception as e:
        if session_id in status_queues:
            status_queues[session_id].put(
                {"action": "error", "details": f"Task failed: {str(e)}"}
            )
        raise
    finally:
        status_queues.pop(session_id, None)


@app.post("/run")
async def run_agent(request: RunRequest, background_tasks: BackgroundTasks):
    """Start a new agent run"""
    # Generate a new session ID
    session_id = str(uuid.uuid4())

    status_queues[session_id] = Queue()

    background_tasks.add_task(_run_agent, session_id, request)

    return JSONResponse({"session_id": session_id, "result": "task started"})


@app.get("/api/agent")
async def get_agent_info():
    """Get information about the web agent's capabilities"""
    return JSONResponse(
        {
            "name": "Web Agent",
            "version": "1.0",
            "supported_actions": [
                "navigate",
                "click",
                "type",
                "scroll_down",
                "scroll_up",
                "look",
                "wait",
            ],
            "status": {"active_sessions": len(status_queues), "available": True},
        }
    )


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", workers=4)
