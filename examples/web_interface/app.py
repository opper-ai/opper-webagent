from flask import Flask, render_template, request, jsonify, send_file
import sys
import os
from pathlib import Path
import json
import tempfile

# Add the src directory to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / 'src'))

from web_agent import navigate_with_ai, get_status, stop

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Headless Web Automator</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
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
                padding: 32px;
                box-shadow: 2px 0 6px rgba(0,0,0,0.2);
                overflow-y: auto;
                height: 100vh;
                box-sizing: border-box;
                position: fixed;
                left: 0;
                top: 0;
                border-right: 1px solid #374151;
            }
            .main-content {
                width: 73%;
                margin-left: 27%;
                padding: 32px;
                box-sizing: border-box;
                height: 100vh;
                display: flex;
                flex-direction: column;
                gap: 24px;
                overflow-y: auto;
            }
            .screenshot-container {
                background-color: #1f2937;
                border-radius: 12px;
                border: 1px solid #374151;
                overflow: hidden;
                position: relative;
                flex-shrink: 0;
                max-height: 40vh;
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
                margin-bottom: 16px;
                font-weight: 600;
                font-size: 1.75rem;
            }
            .subtitle {
                color: #9CA3AF;
                margin-bottom: 32px;
                font-size: 0.875rem;
                line-height: 1.5;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 16px;
                background-color: #111827;
            }
            form {
                margin-bottom: 32px;
            }
            .form-group {
                margin-bottom: 24px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 400;
                color: #9CA3AF;
                font-size: 0.875rem;
            }
            textarea, input {
                width: 100%;
                padding: 12px;
                margin-bottom: 8px;
                border: 1px solid #374151;
                border-radius: 8px;
                font-size: 1rem;
                font-family: 'Inter', sans-serif;
                transition: all 0.2s ease;
                box-sizing: border-box;
                background-color: #111827;
                color: #e5e7eb;
            }
            textarea:focus, input:focus {
                outline: none;
                border-color: #10B981;
                box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
            }
            .checkbox-group {
                display: flex;
                align-items: center;
                margin-bottom: 12px;
            }
            .checkbox-group input[type="checkbox"] {
                width: auto;
                margin-right: 8px;
                margin-bottom: 0;
                margin-top: 0;
            }
            .checkbox-group label {
                display: inline;
                margin: 0;
                line-height: 1;
            }
            button {
                background-color: #10B981;
                color: #111827;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                width: 100%;
            }
            button:hover {
                background-color: #059669;
                transform: translateY(-1px);
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
            .status-update {
                margin-bottom: 16px;
                padding: 16px;
                background-color: #111827;
                color: #e5e7eb;
                border-radius: 8px;
                border: 1px solid #374151;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                animation: slideIn 0.3s ease;
                position: relative;
                display: flex;
                align-items: center;
            }
            .status-update::before {
                content: '';
                width: 8px;
                height: 8px;
                background-color: #10B981;
                border-radius: 50%;
                margin-right: 12px;
                animation: pulse 2s infinite;
                min-width: 8px;
                min-height: 8px;
                max-width: 8px; 
                max-height: 8px;
            }
            .status-label {
                background-color: #374151;
                padding: 4px 8px;
                border-radius: 4px;
                margin-right: 8px;
                font-size: 0.75rem;
                font-weight: 500;
                min-width: 75px;
                display: inline-block;
                text-align: center;
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
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 16px;
                flex: 1;
                overflow-y: auto;
                font-family: monospace;
                font-size: 0.875rem;
                line-height: 1.5;
                min-height: 0;
            }
            #result {
                flex: 1;
                overflow-y: auto;
                min-height: 0;
            }
            .status-entry {
                padding: 8px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
            }
            .status-entry:last-child {
                margin-bottom: 0;
            }
            .status-entry::before {
                content: '';
                width: 8px;
                height: 8px;
                background-color: #10B981;
                border-radius: 50%;
                margin-right: 12px;
                animation: pulse 2s infinite;
            }
            .status-tag {
                background-color: #374151;
                color: #e5e7eb;
                padding: 2px 8px;
                border-radius: 4px;
                margin-right: 12px;
                font-size: 0.75rem;
                white-space: nowrap;
            }
            .status-details {
                color: #e5e7eb;
                flex: 1;
            }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h1>Autonomous Web Agent</h1>
            <p class="subtitle">This is an experimental compound web agent built on top of the Opper platform. Feel free to give it a try, but be warned that it may not always work as expected.</p>
            <form id="agentForm">
                <div class="form-group">
                    <label for="goal">Goal:</label>
                    <textarea id="goal" name="goal" rows="4" required 
                        placeholder="What do you want to get done?"></textarea>
                </div>
                <div class="form-group">
                    <label for="secrets">Secrets (optional):</label>
                    <textarea id="secrets" name="secrets" rows="2" 
                        placeholder="Enter any login details if needed..."></textarea>
                </div>
                <div class="form-group">
                    <label for="responseSchema">Response Schema (optional):</label>
                    <textarea id="responseSchema" name="responseSchema" rows="4" 
                        placeholder="Enter a JSON schema to structure the response..."></textarea>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="showBrowser" name="showBrowser">
                    <label for="showBrowser">Show browser window</label>
                </div>
                <button type="submit" id="runButton">Run</button>
            </form>
            <div class="loading" id="loading">
                Running web agent... This may take a few minutes.
            </div>
        </div>
        <div class="main-content">
            <div class="screenshot-container">
                <img id="latestScreenshot" src="" alt="Latest screenshot" style="display: none;">
            </div>
            <div id="status" class="status-log"></div>
        </div>
        <script>
            let statusInterval;
            let screenshotInterval;
            let lastStatus = '';
            let lastDetails = '';
            let isRunning = false;
            
            function updateScreenshot() {
                const img = document.getElementById('latestScreenshot');
                const container = img.parentElement;
                
                // Add timestamp to prevent caching
                const timestamp = new Date().getTime();
                fetch(`/latest_screenshot?t=${timestamp}`)
                    .then(response => {
                        if (response.ok) {
                            return response.blob();
                        }
                        throw new Error('Screenshot not available');
                    })
                    .then(blob => {
                        const url = URL.createObjectURL(blob);
                        img.src = url;
                        img.style.display = 'block';
                        container.classList.remove('loading');
                    })
                    .catch(() => {
                        img.style.display = 'none';
                        container.classList.add('loading');
                    });
            }
            
            async function pollStatus() {
                try {
                    const response = await fetch('/status');
                    const status = await response.json();
                    const statusDiv = document.getElementById('status');
                    
                    if (status.action !== lastStatus || status.details !== lastDetails) {
                        const statusUpdate = document.createElement('div');
                        statusUpdate.className = 'status-entry';
                        statusUpdate.innerHTML = `
                            <span class="status-tag">${status.action}</span>
                            <span class="status-details">${status.details || ''}</span>
                        `;
                        statusDiv.appendChild(statusUpdate);
                        lastStatus = status.action;
                        lastDetails = status.details;
                        
                        // Auto-scroll to the latest update
                        statusUpdate.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                    
                    if (status.action === 'idle') {
                        clearInterval(statusInterval);
                        const runButton = document.getElementById('runButton');
                        runButton.textContent = 'Run';
                        runButton.classList.remove('running');
                        runButton.disabled = false;
                        isRunning = false;
                    }
                } catch (error) {
                    console.error('Error polling status:', error);
                }
            }

            document.getElementById('agentForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const form = e.target;
                const loading = document.getElementById('loading');
                const mainContent = document.querySelector('.main-content');
                const runButton = document.getElementById('runButton');
                
                if (isRunning) {
                    // If running, stop the agent
                    await fetch('/stop', { method: 'POST' });
                    isRunning = false;
                    runButton.textContent = 'Run';
                    runButton.classList.remove('running');
                    loading.style.display = 'none';
                    clearInterval(screenshotInterval);
                    return;
                }

                // Start new run
                loading.style.display = 'block';
                runButton.textContent = 'Stop';
                runButton.classList.add('running');
                
                // Reset main content to show live status
                mainContent.innerHTML = `
                    <div class="screenshot-container">
                        <img id="latestScreenshot" src="" alt="Latest screenshot" style="display: none;">
                    </div>
                    <div id="status" class="status-log"></div>
                `;
                
                lastStatus = '';
                lastDetails = '';
                isRunning = true;
                
                // Start polling status and screenshot
                statusInterval = setInterval(pollStatus, 3000);
                screenshotInterval = setInterval(updateScreenshot, 2000);
                
                try {
                    const response = await fetch('/run', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            goal: form.goal.value,
                            secrets: form.secrets.value,
                            headless: !form.showBrowser.checked,
                            responseSchema: form.responseSchema.value
                        }),
                    });
                    
                    const data = await response.json();
                    
                    // Get the final screenshot one last time
                    await updateScreenshot();
                    
                    // Replace content with results
                    mainContent.innerHTML = '';
                    
                    // Create single result card
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'output-card';

                    // Try to parse the result as JSON
                    let finalResult = data.result;
                    try {
                        if (typeof finalResult === 'string') {
                            const parsedResult = JSON.parse(finalResult);
                            finalResult = JSON.stringify(parsedResult, null, 2);
                        } else {
                            finalResult = JSON.stringify(finalResult, null, 2);
                        }
                    } catch (e) {
                        // If parsing fails, use the original string
                        finalResult = data.result;
                    }

                    resultDiv.innerHTML = `
                        <h3>Final Results</h3>
                        <div class="screenshot-container in-results">
                            <h4>Final State</h4>
                            <img src="/latest_screenshot?t=${new Date().getTime()}" alt="Final screenshot">
                        </div>
                        <p><strong>Final Result:</strong></p>
                        <pre>${finalResult}</pre>
                        <p><strong>Duration:</strong> ${data.duration_seconds.toFixed(2)} seconds</p>
                        <h4>Trajectory</h4>
                        <pre>${JSON.stringify(data.trajectory, null, 2)}</pre>
                    `;
                    mainContent.appendChild(resultDiv);
                } catch (error) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'output-card';
                    errorDiv.innerHTML = `<p style="color: #ef4444;">Error: ${error.message}</p>`;
                    mainContent.appendChild(errorDiv);
                } finally {
                    loading.style.display = 'none';
                    isRunning = false;
                    runButton.textContent = 'Run';
                    runButton.classList.remove('running');
                    clearInterval(statusInterval);
                    clearInterval(screenshotInterval);
                }
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
    result = navigate_with_ai(
        goal=data['goal'],
        secrets=data['secrets'] if data['secrets'] else None,
        headless=data['headless'],
        debug=False,
        response_schema=json.loads(data['responseSchema']) if data['responseSchema'] else None
    )
    return jsonify(result)

@app.route('/latest_screenshot')
def get_latest_screenshot():
    # Get all files in the temp directory
    temp_dir = tempfile.gettempdir()
    screenshot_files = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
    
    if not screenshot_files:
        return jsonify({'error': 'No screenshot available'}), 404
    
    # Sort by creation time and get the latest
    latest_screenshot = max(
        [os.path.join(temp_dir, f) for f in screenshot_files],
        key=os.path.getmtime
    )
    
    return send_file(latest_screenshot, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, port=5000)