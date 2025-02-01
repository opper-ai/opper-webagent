from flask import Flask, render_template, request, jsonify, send_file, Response
import sys
import os
from pathlib import Path
import json
import tempfile
import queue
from threading import Event
import base64

# Add the src directory to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / 'src'))

from web_agent import navigate_with_ai, get_status, stop

app = Flask(__name__)

# Default response schema
DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "failure", "partial"],
            "description": "The outcome of the requested task"
        },
        "message": {
            "type": "string",
            "description": "A detailed description of what was accomplished or why it failed"
        }
    },
    "required": ["status", "message"]
}

# Queue for status updates
status_updates = queue.Queue()
status_event = Event()

def status_callback(action: str, details: str, screenshot_path: str = None):
    """Callback function to receive status updates from the agent"""
    # Get latest screenshot path if not provided
    if screenshot_path is None:
        status = get_status()
        screenshot_path = status.get('screenshot_path')
    
    # Convert screenshot to base64 if available
    screenshot_data = None
    if screenshot_path and os.path.isfile(screenshot_path):
        with open(screenshot_path, 'rb') as f:
            screenshot_data = base64.b64encode(f.read()).decode('utf-8')
    
    status_updates.put({
        "action": action,
        "details": details,
        "screenshot_data": screenshot_data
    })
    status_event.set()

@app.route('/status-stream')
def status_stream():
    """SSE endpoint for streaming status updates"""
    def generate():
        while True:
            try:
                status = status_updates.get(timeout=1)
                yield f"data: {json.dumps(status)}\n\n"
            except queue.Empty:
                # Send a keep-alive comment every second
                yield ": keep-alive\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/', methods=['GET'])
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Headless Web Automator</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #111827;
                color: #e5e7eb;
                line-height: 1.6;
                height: 100vh;
                display: flex;
                overflow: hidden;
            }
            .sidebar {
                width: 27%;
                background-color: #1f2937;
                box-shadow: 2px 0 6px rgba(0,0,0,0.2);
                height: 100vh;
                box-sizing: border-box;
                position: fixed;
                left: 0;
                top: 0;
                border-right: 1px solid #374151;
                display: flex;
                flex-direction: column;
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }
            .sidebar.active {
                transform: translateX(0);
            }
            .main-content {
                width: 100%;
                margin-left: 0;
                padding: 32px;
                box-sizing: border-box;
                height: 100vh;
                display: flex;
                flex-direction: column;
                gap: 24px;
                overflow-y: auto;
                transition: margin-left 0.3s ease, width 0.3s ease;
            }
            .main-content.sidebar-active {
                width: 73%;
                margin-left: 27%;
            }
            .centered-content {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 20px;
                box-sizing: border-box;
                background-color: #111827;
                z-index: 1000;
            }
            .centered-content.hidden {
                display: none;
            }
            .logo-container {
                margin-bottom: 24px;
                text-align: center;
                animation: fadeInDown 0.6s ease-out;
            }
            .logo-title {
                font-size: 3rem;
                font-weight: 800;
                color: #e5e7eb;
                margin: 0;
                margin-bottom: 12px;
                background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -0.5px;
            }
            .logo-subtitle {
                font-size: 1.2rem;
                color: #9ca3af;
                margin: 0;
                font-weight: 500;
            }
            .example-tasks {
                display: flex;
                gap: 8px;
                margin-bottom: 32px;
                flex-wrap: wrap;
                justify-content: center;
                animation: fadeInDown 0.4s ease-out;
            }
            .example-task {
                background: #374151;
                border: 1px solid #4B5563;
                border-radius: 8px;
                padding: 10px 16px;
                color: #e5e7eb;
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .example-task:hover {
                background: #4B5563;
                transform: translateY(-2px);
                box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
            }
            .example-task i {
                font-size: 1rem;
                color: #10B981;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group:last-child {
                margin-bottom: 0;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #e5e7eb;
                font-size: 0.95rem;
                letter-spacing: 0.01em;
            }
            textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #374151;
                border-radius: 12px;
                font-size: 1rem;
                font-family: 'Inter', sans-serif;
                transition: all 0.2s ease;
                box-sizing: border-box;
                background-color: #111827;
                color: #e5e7eb;
                resize: none;
                line-height: 1.5;
                min-height: 80px;
            }
            textarea::placeholder {
                color: #6B7280;
            }
            .advanced-options {
                background: #111827;
                border-radius: 12px;
                padding: 16px;
                margin-top: 24px;
                margin-bottom: 24px;
                border: 1px solid #374151;
            }
            .advanced-options summary {
                color: #9CA3AF;
                cursor: pointer;
                font-weight: 500;
                user-select: none;
                padding: 8px;
                margin: -8px;
                border-radius: 8px;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .advanced-options summary::before {
                content: '';
                width: 20px;
                height: 20px;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%239CA3AF'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 5l7 7-7 7'%3E%3C/path%3E%3C/svg%3E");
                background-size: contain;
                transform: rotate(90deg);
                transition: transform 0.2s ease;
            }
            .advanced-options[open] summary::before {
                transform: rotate(270deg);
            }
            .advanced-options summary:hover {
                background: rgba(75, 85, 99, 0.3);
            }
            .advanced-options-content {
                margin-top: 16px;
                display: grid;
                gap: 20px;
                padding: 4px;
            }
            .advanced-options-content .form-group:last-child {
                margin-bottom: 0;
            }
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: rgba(75, 85, 99, 0.2);
                border-radius: 8px;
                margin-top: 8px;
                border: 1px solid rgba(75, 85, 99, 0.5);
            }
            .checkbox-group input[type="checkbox"] {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #4B5563;
                background: #111827;
                cursor: pointer;
                position: relative;
                appearance: none;
                -webkit-appearance: none;
                transition: all 0.2s ease;
            }
            .checkbox-group input[type="checkbox"]:checked {
                background: #10B981;
                border-color: #10B981;
            }
            .checkbox-group input[type="checkbox"]:checked::after {
                content: '';
                position: absolute;
                left: 6px;
                top: 2px;
                width: 4px;
                height: 10px;
                border: solid white;
                border-width: 0 2px 2px 0;
                transform: rotate(45deg);
            }
            .checkbox-group label {
                margin: 0;
                font-size: 0.9rem;
                color: #9CA3AF;
            }
            button[type="submit"] {
                background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
                color: white;
                padding: 14px 28px;
                border: none;
                border-radius: 12px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                width: 100%;
                text-shadow: 0 1px 2px rgba(0,0,0,0.1);
                margin-top: 8px;
            }
            button[type="submit"]:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
            }
            .main-container {
                position: relative;
                width: 100%;
                height: 100vh;
                display: none;
            }
            .main-container.active {
                display: block;
            }
            .browser-container {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 0;
            }
            .browser-window {
                background: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                width: fit-content;
                max-width: 90%;
                margin: 0 auto;
            }
            .screenshot-container {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
                overflow: hidden;
                position: relative;
                flex: 1;
            }
            .screenshot-container.in-results {
                max-height: none;
                margin-bottom: 24px;
            }
            .screenshot-container img {
                width: 100%;
                height: 100%;
                object-fit: contain;
                display: block;
            }
            .screenshot-container.in-results img {
                height: auto;
            }
            .screenshot-container.loading::after {
                content: 'Loading...';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #e5e7eb;
                background-color: rgba(31, 41, 55, 0.8);
                padding: 8px 16px;
                border-radius: 4px;
            }
            h1 {
                color: #e5e7eb;
                margin: 0;
                padding: 16px;
                font-weight: 600;
                font-size: 1.25rem;
                border-bottom: 1px solid #374151;
            }
            .subtitle {
                color: #9CA3AF;
                font-size: 0.875rem;
                line-height: 1.5;
                padding: 16px;
                background-color: #111827;
            }
            form {
                padding: 16px;
            }
            .output-card {
                background-color: #1f2937;
                padding: 24px;
                border-radius: 12px;
                border: 1px solid #374151;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                animation: slideIn 0.3s ease;
            }
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            .loading {
                display: none;
                text-align: center;
                margin: 24px 0;
                color: #e5e7eb;
                font-weight: 500;
                padding: 16px;
                background-color: #111827;
                border-radius: 8px;
                border: 1px solid #374151;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
                }
            }
            pre {
                background-color: #111827;
                color: #e5e7eb;
                padding: 16px;
                border-radius: 8px;
                border: 1px solid #374151;
                overflow-x: auto;
                font-size: 0.875rem;
            }
            h3, h4 {
                color: #e5e7eb;
                margin: 16px 0 12px 0;
                font-weight: 600;
            }
            p {
                margin: 12px 0;
                color: #e5e7eb;
            }
            strong {
                color: #10B981;
                font-weight: 600;
            }
            #stopButton {
                background-color: #ef4444;
                margin-top: 12px;
                display: none;
            }
            #stopButton:hover {
                background-color: #dc2626;
            }
            #runButton {
                transition: all 0.3s ease;
            }
            #runButton.running {
                background-color: #ef4444;
            }
            #runButton.running:hover {
                background-color: #dc2626;
            }
            .status-log {
                flex: 1;
                overflow-y: auto;
                font-family: 'Inter', sans-serif;
                font-size: 0.875rem;
                line-height: 1.5;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
                background: #111827;
                min-height: 0;
            }
            #result {
                flex: 1;
                overflow-y: auto;
                min-height: 0;
            }
            .status-entry {
                padding: 12px 16px;
                background: #1f2937;
                border-radius: 8px;
                animation: slideIn 0.3s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                word-break: break-word;
                border: 1px solid transparent;
                transition: all 0.3s ease;
            }
            
            .status-entry.latest {
                border-color: #10B981;
                background: rgba(16, 185, 129, 0.1);
                animation: slideIn 0.3s ease, pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(16, 185, 129, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
                }
            }
            .status-tag {
                font-size: 0.75rem;
                font-weight: 600;
                opacity: 0.7;
                margin-bottom: 4px;
                display: block;
            }
            .status-details {
                color: inherit;
                font-size: 0.9rem;
            }
            .hidden {
                display: none;
            }
            #formContent {
                display: flex;
                flex-direction: column;
                height: 100%;
                min-height: 0;
            }
            .form-container {
                padding: 16px;
                border-bottom: 1px solid #374151;
                background: #1f2937;
                transition: all 0.3s ease;
            }
            .status-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                min-height: 0;
                overflow: auto;
            }
            .status-header {
                padding: 16px;
                border-bottom: 1px solid #374151;
                background: #111827;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .status-title {
                color: #e5e7eb;
                font-size: 0.875rem;
                font-weight: 600;
            }
            .cancel-button {
                background: #ef4444;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
            }
            .cancel-button:hover {
                background: #dc2626;
                transform: translateY(-1px);
            }
            .cancel-button i {
                font-size: 0.875rem;
            }
            .goal-header {
                color: #e5e7eb;
                font-weight: 600;
                font-size: 1rem;
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .form-container.hidden {
                display: none;
            }
            .browser-header {
                background: #111827;
                padding: 8px 12px;
                border-bottom: 1px solid #374151;
                display: flex;
                gap: 8px;
                align-items: center;
            }
            .browser-controls {
                display: flex;
                gap: 8px;
            }
            .browser-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
            }
            .browser-dot.red { background-color: #ef4444; }
            .browser-dot.yellow { background-color: #f59e0b; }
            .browser-dot.green { background-color: #10b981; }
            .browser-content {
                background: #111827;
                position: relative;
                min-height: 200px;
            }
            .screenshot-container {
                margin: 0;
                background-color: transparent;
                border: none;
                border-radius: 0;
                position: relative;
                min-height: 200px;
            }
            .screenshot-container.loading::after {
                content: 'Loading...';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #e5e7eb;
                background-color: rgba(31, 41, 55, 0.8);
                padding: 8px 16px;
                border-radius: 4px;
                z-index: 2;
            }
            .screenshot-container img {
                display: block;
                width: 100%;
                height: auto;
                margin: 0;
            }
            .output-card {
                margin: 24px;
            }
            .result-container {
                background: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
                overflow: hidden;
            }
            .result-header {
                background: #111827;
                padding: 16px 24px;
                border-bottom: 1px solid #374151;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .result-header-left {
                display: flex;
                align-items: center;
                gap: 16px;
            }
            .result-header h3 {
                margin: 0;
                color: #e5e7eb;
                font-size: 1rem;
                font-weight: 600;
            }
            .completion-time {
                color: #9ca3af;
                font-size: 0.875rem;
            }
            .result-content {
                padding: 24px;
            }
            .result-content pre {
                margin: 0;
                white-space: pre-wrap;
                word-break: break-word;
            }
            .result-content.json {
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.875rem;
                line-height: 1.5;
            }
            .result-content.text {
                font-family: 'Inter', sans-serif;
                font-size: 1rem;
                line-height: 1.6;
                color: #e5e7eb;
            }
            .key {
                color: #93c5fd;
            }
            .string {
                color: #86efac;
            }
            .number {
                color: #fca5a5;
            }
            .boolean {
                color: #f9a8d4;
            }
            .null {
                color: #9ca3af;
            }
            .final-screenshot {
                margin-top: 24px;
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid #374151;
            }
            .final-screenshot img {
                width: 100%;
                height: auto;
                display: block;
            }
            .new-task-button {
                background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                font-size: 0.875rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                text-shadow: 0 1px 2px rgba(0,0,0,0.1);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }
            .new-task-button:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
            }
            .new-task-button i {
                font-size: 1rem;
            }
            .centered-form {
                width: 100%;
                max-width: 700px;
                background: #1f2937;
                padding: 24px;
                border-radius: 16px;
                border: 1px solid #374151;
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                animation: fadeInUp 0.6s ease-out;
                position: relative;
                z-index: 1;
                max-height: 80vh;
                overflow-y: auto;
            }
        </style>
    </head>
    <body>
        <div class="centered-content" id="centeredContent">
            <div class="logo-container">
                <h1 class="logo-title">Towards agents that work while we sleep</h1>
                <p class="logo-subtitle">Web Automation with AI powered by headless, open source agent framework by Opper </p>
            </div>
            <div class="example-tasks">
                <button class="example-task" data-task="Go to our company blog at https://opper.ai/blog and verify that our latest post about Deepseek is published">
                    <i class="ri-article-line"></i>
                    Verify A Social Post
                </button>
                <button class="example-task" data-task="Go to Hackernews and extract the latest news about artificial intelligence from the past 24 hours">
                    <i class="ri-newspaper-line"></i>
                    Extract Latest News
                </button>
                <button class="example-task" data-task="Log into Meetup.com, find any AI meetups in Stockholm and register.">
                    <i class="ri-window-line"></i>
                    Perform SaaS Task
                </button>
            </div>
            <div class="centered-form">
                <form id="agentForm">
                    <div class="form-group">
                        <label for="goal">What would you like the agent to do?</label>
                        <textarea id="goal" name="goal" rows="3" required 
                            placeholder="Describe your task in natural language, e.g., 'Go to LinkedIn and find posts about AI'"></textarea>
                    </div>
                    <details class="advanced-options">
                        <summary>Advanced options</summary>
                        <div class="advanced-options-content">
                            <div class="form-group">
                                <label for="secrets">Authentication Details</label>
                                <textarea id="secrets" name="secrets" rows="2" 
                                    placeholder="Optional: Enter login credentials if needed for the task"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="responseSchema">Custom Response Schema</label>
                                <textarea id="responseSchema" name="responseSchema" rows="4" 
                                    placeholder="Optional: Specify a JSON schema for structured output"></textarea>
                            </div>
                        </div>
                    </details>
                    <button type="submit" id="runButton">Run Task</button>
                </form>
            </div>
        </div>

        <div class="main-container" id="mainContainer">
            <div class="sidebar" id="sidebar">
                <div id="formContent">
                    <div class="status-header">
                        <div class="status-title">Task Progress</div>
                        <button class="cancel-button" id="statusButton">
                            <i class="ri-close-circle-line"></i>
                            Cancel
                        </button>
                    </div>
                    <div class="status-container">
                        <div id="status" class="status-log"></div>
                    </div>
                </div>
            </div>
            <div class="main-content" id="mainContent">
                <div class="browser-container" id="browserContainer">
                    <div class="browser-window">
                        <div class="browser-header">
                            <div class="browser-controls">
                                <div class="browser-dot red"></div>
                                <div class="browser-dot yellow"></div>
                                <div class="browser-dot green"></div>
                            </div>
                        </div>
                        <div class="browser-content">
                            <div class="screenshot-container">
                                <img id="latestScreenshot" src="" alt="Latest screenshot" style="display: none;">
                            </div>
                        </div>
                    </div>
                </div>
                <div id="result" class="result-container hidden">
                    <div class="result-header">
                        <div class="result-header-left">
                            <h3>Completion Report</h3>
                            <span class="completion-time" id="completionTime"></span>
                        </div>
                    </div>
                    <div class="result-content" id="resultContent"></div>
                </div>
            </div>
        </div>

        <script>
            let screenshotInterval;
            let isRunning = false;
            let eventSource;
            let startTime;
            let latestScreenshotPath = null;
            
            // Initialize response schema field with default schema
            const DEFAULT_SCHEMA = {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["success", "failure", "partial"],
                        "description": "The outcome of the requested task"
                    },
                    "message": {
                        "type": "string",
                        "description": "A detailed description of the task result or why it failed"
                    }
                },
                "required": ["status", "message"]
            };

            const responseSchemaField = document.getElementById('responseSchema');
            responseSchemaField.value = JSON.stringify(DEFAULT_SCHEMA, null, 2);
            
            // Add event listener to format JSON when the field is modified
            responseSchemaField.addEventListener('input', function() {
                try {
                    if (this.value.trim()) {
                        const formatted = JSON.stringify(JSON.parse(this.value), null, 2);
                        this.value = formatted;
                    }
                } catch (e) {
                    // If JSON is invalid, leave as-is
                }
            });
            
            // Add event listener to clear field on focus if it contains default schema
            responseSchemaField.addEventListener('focus', function() {
                if (this.value === JSON.stringify(DEFAULT_SCHEMA, null, 2)) {
                    this.value = '';
                }
            });
            
            // Add event listener to restore default schema if field is emptied
            responseSchemaField.addEventListener('blur', function() {
                if (!this.value.trim()) {
                    this.value = JSON.stringify(DEFAULT_SCHEMA, null, 2);
                }
            });
            
            function updateScreenshot() {
                const img = document.getElementById('latestScreenshot');
                const container = img.parentElement;
                
                if (!latestScreenshotPath) {
                    img.style.display = 'none';
                    container.classList.add('loading');
                    return;
                }
                
                // Display base64 image data directly
                img.onload = () => {
                    img.style.display = 'block';
                    container.classList.remove('loading');
                };
                img.src = `data:image/png;base64,${latestScreenshotPath}`;
            }
            
            function setupStatusStream() {
                if (eventSource) {
                    eventSource.close();
                }
                
                eventSource = new EventSource('/status-stream');
                const statusDiv = document.getElementById('status');
                
                eventSource.onmessage = function(event) {
                    const status = JSON.parse(event.data);
                    
                    // Remove 'latest' class from previous latest entry
                    const previousLatest = statusDiv.querySelector('.status-entry.latest');
                    if (previousLatest) {
                        previousLatest.classList.remove('latest');
                    }
                    
                    const statusUpdate = document.createElement('div');
                    statusUpdate.className = 'status-entry latest';
                    statusUpdate.innerHTML = `
                        <span class="status-tag">${status.action}</span>
                        <span class="status-details">${status.details || ''}</span>
                    `;
                    statusDiv.appendChild(statusUpdate);
                    
                    // Update screenshot if we have new image data
                    if (status.screenshot_data) {
                        latestScreenshotPath = status.screenshot_data;
                        updateScreenshot();
                    }
                    
                    // Auto-scroll to the latest update
                    statusUpdate.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    
                    // Check for idle status to stop the agent
                    if (status.action === 'idle') {
                        const runButton = document.getElementById('runButton');
                        const statusButton = document.getElementById('statusButton');
                        runButton.textContent = 'Run Task';
                        runButton.classList.remove('running');
                        runButton.disabled = false;
                        isRunning = false;
                        eventSource.close();
                        
                        // Change cancel button to new task button
                        statusButton.className = 'cancel-button new-task-button';
                        statusButton.innerHTML = '<i class="ri-add-line"></i>New Task';
                        statusButton.onclick = startNewTask;
                    }
                };
                
                eventSource.onerror = function(error) {
                    console.error('EventSource failed:', error);
                    eventSource.close();
                };
            }

            function stopTask() {
                if (isRunning) {
                    fetch('/stop', { method: 'POST' });
                    isRunning = false;
                    if (eventSource) {
                        eventSource.close();
                    }
                    startNewTask();
                }
            }

            document.getElementById('agentForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                startTime = new Date();
                const form = e.target;
                const statusLog = document.getElementById('status');
                const browserContainer = document.getElementById('browserContainer');
                const centeredContent = document.getElementById('centeredContent');
                const mainContainer = document.getElementById('mainContainer');
                const sidebar = document.getElementById('sidebar');
                const mainContent = document.getElementById('mainContent');
                const resultDiv = document.getElementById('result');
                const statusButton = document.getElementById('statusButton');
                
                // Reset status button to Cancel
                statusButton.className = 'cancel-button';
                statusButton.innerHTML = '<i class="ri-close-circle-line"></i>Cancel';
                statusButton.onclick = stopTask;
                
                // Reset screenshot path
                latestScreenshotPath = null;
                
                if (isRunning) {
                    // If running, stop the agent
                    await fetch('/stop', { method: 'POST' });
                    isRunning = false;
                    if (eventSource) {
                        eventSource.close();
                    }
                    startNewTask();
                    return;
                }

                // Hide any previous results
                resultDiv.classList.add('hidden');

                // Transition from centered to main view
                centeredContent.classList.add('hidden');
                mainContainer.classList.add('active');
                sidebar.classList.add('active');
                mainContent.classList.add('sidebar-active');

                // Show status log
                statusLog.classList.remove('hidden');
                statusLog.innerHTML = ''; // Clear previous status
                
                isRunning = true;
                
                // Start status stream
                setupStatusStream();
                
                try {
                    const response = await fetch('/run', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            goal: form.goal.value,
                            secrets: form.secrets.value,
                            responseSchema: form.responseSchema.value
                        }),
                    });
                    
                    const data = await response.json();
                    
                    // Display the result
                    await displayResult(data);
                    
                } catch (error) {
                    console.error('Error:', error);
                    statusLog.innerHTML += `
                        <div class="status-entry error">
                            <span class="status-tag">Error</span>
                            <span class="status-details">${error.message}</span>
                        </div>
                    `;
                } finally {
                    isRunning = false;
                    if (eventSource) {
                        eventSource.close();
                    }
                }
            });

            function formatJSON(obj) {
                const jsonString = JSON.stringify(obj, null, 2);
                return jsonString.replace(
                    /(".*?":|true|false|null|[0-9]+)/g, 
                    match => {
                        if (match.endsWith(':')) return `<span class="key">${match}</span>`;
                        if (match === 'true' || match === 'false') return `<span class="boolean">${match}</span>`;
                        if (match === 'null') return `<span class="null">${match}</span>`;
                        if (!isNaN(match)) return `<span class="number">${match}</span>`;
                        return `<span class="string">${match}</span>`;
                    }
                );
            }

            function formatDuration(ms) {
                if (ms < 1000) return `${ms}ms`;
                const seconds = Math.floor(ms / 1000);
                if (seconds < 60) return `${seconds}s`;
                const minutes = Math.floor(seconds / 60);
                const remainingSeconds = seconds % 60;
                return `${minutes}m ${remainingSeconds}s`;
            }

            async function displayResult(data) {
                const resultDiv = document.getElementById('result');
                const resultContent = document.getElementById('resultContent');
                const completionTime = document.getElementById('completionTime');
                const browserContainer = document.getElementById('browserContainer');
                const duration = new Date() - startTime;
                
                // Hide browser container
                browserContainer.style.display = 'none';
                
                completionTime.textContent = `Completed in ${formatDuration(duration)}`;
                
                // Extract the result from the data
                const result = data.result || data;
                
                let isJSON = false;
                try {
                    if (typeof result === 'string') {
                        JSON.parse(result);
                        isJSON = true;
                    } else {
                        isJSON = true;
                    }
                } catch (e) {
                    isJSON = false;
                }

                let content = '';
                if (isJSON) {
                    resultContent.className = 'result-content json';
                    content = `<pre>${formatJSON(typeof result === 'string' ? JSON.parse(result) : result)}</pre>`;
                } else {
                    resultContent.className = 'result-content text';
                    content = `<pre>${result}</pre>`;
                }
                
                // Add final screenshot if available
                if (latestScreenshotPath) {
                    content += `
                        <div class="final-screenshot">
                            <img src="data:image/png;base64,${latestScreenshotPath}" alt="Final state">
                        </div>
                    `;
                }
                
                resultContent.innerHTML = content;
                resultDiv.classList.remove('hidden');
            }

            function startNewTask() {
                // Reset the form to its initial state
                const form = document.getElementById('agentForm');
                if (form) {
                    form.reset();
                    // Clear any custom values that might not be cleared by reset
                    Array.from(form.elements).forEach(element => {
                        if (element.type === 'textarea') {
                            element.value = element.defaultValue;
                        } else if (element.type === 'checkbox') {
                            element.checked = element.defaultChecked;
                        }
                    });
                }
                
                // Hide the main container and show the centered content
                document.getElementById('mainContainer').classList.remove('active');
                document.getElementById('sidebar').classList.remove('active');
                document.getElementById('mainContent').classList.remove('sidebar-active');
                document.getElementById('centeredContent').classList.remove('hidden');
                
                // Clear any previous results and status
                document.getElementById('result').classList.add('hidden');
                document.getElementById('status').innerHTML = '';
                
                // Reset screenshot
                latestScreenshotPath = null;
                const screenshotImg = document.getElementById('latestScreenshot');
                if (screenshotImg) {
                    screenshotImg.style.display = 'none';
                    screenshotImg.src = '';
                }
                
                // Show browser container again (for next run)
                document.getElementById('browserContainer').style.display = 'flex';
                
                // Reset any event source
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                
                // Reset running state
                isRunning = false;
                
                // Reset the start time
                startTime = null;
                
                // Create a fresh form in the centered view
                const centeredForm = document.querySelector('.centered-form');
                if (centeredForm) {
                    // Clear any existing content
                    centeredForm.innerHTML = `
                        <form id="agentForm">
                            <div class="form-group">
                                <label for="goal">What would you like the agent to do?</label>
                                <textarea id="goal" name="goal" rows="3" required 
                                    placeholder="Describe your task in natural language, e.g., 'Go to LinkedIn and find posts about AI'"></textarea>
                            </div>
                            <details class="advanced-options">
                                <summary>Advanced options</summary>
                                <div class="advanced-options-content">
                                    <div class="form-group">
                                        <label for="secrets">Authentication Details</label>
                                        <textarea id="secrets" name="secrets" rows="2" 
                                            placeholder="Optional: Enter login credentials if needed for the task"></textarea>
                                    </div>
                                    <div class="form-group">
                                        <label for="responseSchema">Custom Response Schema</label>
                                        <textarea id="responseSchema" name="responseSchema" rows="4" 
                                            placeholder="Optional: Specify a JSON schema for structured output"></textarea>
                                    </div>
                                </div>
                            </details>
                            <button type="submit" id="runButton">Run Task</button>
                        </form>
                    `;
                    
                    // Reattach the submit event listener to the new form
                    document.getElementById('agentForm').addEventListener('submit', handleFormSubmit);
                }
                
                // Scroll to top of page
                window.scrollTo(0, 0);
            }

            // Extract the form submit handler to a named function so we can reattach it
            function handleFormSubmit(e) {
                e.preventDefault();
                const form = e.target;
                startTime = new Date();
                const statusLog = document.getElementById('status');
                const browserContainer = document.getElementById('browserContainer');
                const centeredContent = document.getElementById('centeredContent');
                const mainContainer = document.getElementById('mainContainer');
                const sidebar = document.getElementById('sidebar');
                const mainContent = document.getElementById('mainContent');
                const resultDiv = document.getElementById('result');
                
                // Rest of the existing submit handler code...
                // Copy the rest of the submit handler here
            }

            // Add example task functionality
            document.querySelectorAll('.example-task').forEach(button => {
                button.addEventListener('click', () => {
                    const taskText = button.getAttribute('data-task');
                    document.getElementById('goal').value = taskText;
                });
            });
        </script>
    </body>
    </html>
    '''

@app.route('/status')
def get_current_status():
    return jsonify(get_status())

@app.route('/stop', methods=['POST'])
def stop_agent():
    stop()
    return jsonify({'status': 'stopped'})

@app.route('/run', methods=['POST'])
def run_agent():
    data = request.json
    schema = json.loads(data['responseSchema']) if data['responseSchema'] else DEFAULT_SCHEMA
    result = navigate_with_ai(
        goal=data['goal'],
        secrets=data['secrets'] if data['secrets'] else None,
        debug=False,
        response_schema=schema,
        status_callback=status_callback
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)