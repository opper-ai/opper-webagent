"""
Example usage:

# Start a navigation job
curl -X POST http://localhost:10000/navigate \
  -H "Content-Type: application/json" \
  -d '{"goal": "Log in to example.com", "secrets": "username: user, password: pass"}'

# Check status of a specific job
curl http://localhost:10000/status/<job_id>

# List all jobs
curl http://localhost:10000/jobs
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from src.web_agent.main import navigate_with_ai
from multiprocessing import Process, Queue, current_process
from flask_cors import CORS
import time
import uuid
from threading import Lock
import queue
import os
import multiprocessing

# Ensure we're using fork method on Unix systems
if os.name != 'nt':
    multiprocessing.set_start_method('fork')

# Configure template directory
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)

# Store active jobs with their status
jobs = {}
jobs_lock = Lock()
result_queues = {}
processes = {}  # Store process objects

def run_navigation(job_id, goal, secrets, result_queue):
    try:
        with jobs_lock:
            jobs[job_id]['status'] = 'running'
        
        result = navigate_with_ai(goal, secrets)
        print(f"Navigation result for job {job_id}:", result)
        
        with jobs_lock:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['result'] = result
            
        result_queue.put(result)
    except Exception as e:
        with jobs_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['result'] = {'error': str(e)}
        result_queue.put({'error': str(e)})

# Example usage with curl:
# curl -X POST http://localhost:10000/navigate \
#   -H "Content-Type: application/json" \
#   -d '{"goal": "Log in to example.com", "secrets": "username: user, password: pass"}'

@app.route('/navigate', methods=['POST'])
def navigate():
    try:
        data = request.get_json()
        goal = data.get('goal')
        secrets = data.get('secrets')

        if not goal:
            return jsonify({'error': 'Goal is required'}), 400

        job_id = str(uuid.uuid4())
        result_queue = Queue()
        result_queues[job_id] = result_queue
        
        with jobs_lock:
            jobs[job_id] = {
                'status': 'working',
                'goal': goal,
                'start_time': time.time(),
                'result': None,
                'error': None
            }
        
        process = Process(target=run_navigation, args=(job_id, goal, secrets, result_queue))
        process.daemon = True  # Ensure process exits when parent exits
        process.start()
        processes[job_id] = process
        
        return jsonify({
            'job_id': job_id,
            'status': 'working',
            'message': 'Navigation job started'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    try:
        with jobs_lock:
            if job_id not in jobs:
                return jsonify({'error': 'Job not found'}), 404
            
            job = jobs[job_id].copy()
            
        # Check if process has finished
        if job_id in processes:
            process = processes[job_id]
            if not process.is_alive():
                # Process finished, get result if we haven't already
                if job_id in result_queues and not job['result']:
                    try:
                        result = result_queues[job_id].get_nowait()
                        print(f"Retrieved result for job {job_id}:", result)
                        with jobs_lock:
                            jobs[job_id]['result'] = result
                            jobs[job_id]['status'] = 'completed'
                        job['result'] = result
                        job['status'] = 'completed'
                    except queue.Empty:
                        pass
                # Clean up process
                process.join()
                del processes[job_id]
            
        response = {
            'job_id': job_id,
            'status': job['status'],
            'goal': job['goal'],
            'duration': time.time() - job['start_time'],
            'result': job['result']
        }
        
        if job['status'] == 'failed':
            response['error'] = job['error']
            
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs', methods=['GET'])
def list_jobs():
    try:
        with jobs_lock:
            # Update status of completed processes
            for job_id in list(processes.keys()):
                process = processes[job_id]
                if not process.is_alive():
                    if job_id in result_queues and not jobs[job_id]['result']:
                        try:
                            result = result_queues[job_id].get_nowait()
                            jobs[job_id]['result'] = result
                            jobs[job_id]['status'] = 'completed'
                        except queue.Empty:
                            pass
                    process.join()
                    del processes[job_id]

            job_list = [
                {
                    'job_id': job_id,
                    'status': info['status'],
                    'goal': info['goal'],
                    'duration': time.time() - info['start_time'],
                    'result': info.get('result'),
                    'error': info.get('error'),
                    'trajectory': info.get('result', {}).get('trajectory') if isinstance(info.get('result'), dict) else None
                }
                for job_id, info in jobs.items()
            ]
        return jsonify({'jobs': job_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=10000)
