"""
Example usage:

# Start a navigation job
curl -X POST http://localhost:5000/navigate \
  -H "Content-Type: application/json" \
  -d '{"goal": "Log in to example.com", "secrets": "username: user, password: pass"}'

# Check status of a specific job
curl http://localhost:5000/status/<job_id>

# List all jobs
curl http://localhost:5000/jobs
"""

from flask import Flask, request, jsonify
from src.web_agent.main import navigate_with_ai
from multiprocessing import Process, Queue, current_process
import time
import uuid
from threading import Lock
import queue
import os
import multiprocessing

# Ensure we're using fork method on Unix systems
if os.name != 'nt':
    multiprocessing.set_start_method('fork')

app = Flask(__name__)

# Store active jobs with their status
jobs = {}
jobs_lock = Lock()

def run_navigation(job_id, goal, secrets, result_queue):
    try:
        with jobs_lock:
            jobs[job_id]['status'] = 'running'
        
        result = navigate_with_ai(goal, secrets)
        
        with jobs_lock:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['result'] = result
            
        result_queue.put(result)
    except Exception as e:
        with jobs_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
        result_queue.put({'error': str(e)})

# Example usage with curl:
# curl -X POST http://localhost:5000/navigate \
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
        
        with jobs_lock:
            jobs[job_id] = {
                'status': 'pending',
                'goal': goal,
                'start_time': time.time(),
                'result': None,
                'error': None
            }
        
        process = Process(target=run_navigation, args=(job_id, goal, secrets, result_queue))
        process.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
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
            
        response = {
            'job_id': job_id,
            'status': job['status'],
            'goal': job['goal'],
            'duration': time.time() - job['start_time']
        }
        
        if job['status'] == 'completed':
            response['result'] = job['result']
        elif job['status'] == 'failed':
            response['error'] = job['error']
            
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs', methods=['GET'])
def list_jobs():
    try:
        with jobs_lock:
            job_list = [
                {
                    'job_id': job_id,
                    'status': info['status'],
                    'goal': info['goal'],
                    'duration': time.time() - info['start_time']
                }
                for job_id, info in jobs.items()
            ]
        return jsonify({'jobs': job_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
