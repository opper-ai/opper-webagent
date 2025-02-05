import asyncio
import base64
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from web_agent import WebAgent

# Add the src directory to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "src"))

app = FastAPI()

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

# Store active sessions and their status
active_sessions: Dict[str, dict] = {}


# Request/Response models
class RunRequest(BaseModel):
    goal: str
    secrets: Optional[str] = None
    responseSchema: Optional[dict] = None


def get_status(session_id: str = None) -> dict:
    """Get status for a specific session"""
    if session_id is None:
        return {}
    return active_sessions.get(session_id, {})


def stop(session_id: str = None) -> None:
    """Stop a specific session"""
    if session_id and session_id in active_sessions:
        active_sessions.pop(session_id, None)


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
        active_sessions[session_id] = status_update


async def status_stream_generator(session_id: str):
    """Generate status stream events"""
    while True:
        try:
            status = get_status(session_id)
            if not status:
                # Send keep-alive every second if no updates
                await asyncio.sleep(1)
                yield b'data: {"action": null, "details": null}\n\n'
                continue

            yield f"data: {json.dumps(status)}\n\n".encode("utf-8")

            # Clear status after sending
            if session_id in active_sessions:
                active_sessions[session_id] = {}

            # If task is complete, end stream
            if status.get("action") == "cleanup":
                return

        except Exception as e:
            print(f"error in status stream: {str(e)}")
            break


@app.get("/status-stream/{session_id}")
async def status_stream(session_id: str):
    """SSE endpoint for streaming status updates"""
    return StreamingResponse(
        status_stream_generator(session_id), media_type="text/event-stream"
    )


@app.get("/status/{session_id}")
async def get_current_status(session_id: str):
    """Get current status"""
    status = get_status(session_id)
    return JSONResponse(status)


@app.patch("/stop/{session_id}")
async def stop_agent(session_id: str):
    """Stop an agent session"""
    stop(session_id)
    return JSONResponse({"status": "stopped"})


# Create a session-specific callback
def session_callback(session_id: str):
    def callback(action, details, screenshot_path=None):
        status_callback(action, details, screenshot_path, session_id)

    return callback


async def _run_agent(session_id: str, request: RunRequest):
    """Start a new agent run"""
    schema = request.responseSchema if request.responseSchema else DEFAULT_SCHEMA

    callback = session_callback(session_id)
    callback("initializing", "starting task")

    await WebAgent().run(
        goal=request.goal,
        secrets=request.secrets,
        response_schema=schema,
        status_callback=callback,
        session_id=session_id,
    )


@app.post("/run")
async def run_agent(request: RunRequest):
    """Start a new agent run"""
    # Generate a new session ID
    session_id = str(uuid.uuid4())

    asyncio.create_task(_run_agent(session_id, request))

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
            "status": {"active_sessions": len(active_sessions), "available": True},
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", workers=4)
