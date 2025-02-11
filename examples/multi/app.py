import asyncio
import json
import aiohttp
from typing import Dict, List
import time
from aiohttp import ClientTimeout
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text
from datetime import datetime
from rich import box
import argparse

# We start by defining our tasks: 
TASKS = [
    {
        "id": "accessibility_check_1",
        "goal": "Check that a login page is present on the URL https://platform.opper.ai."
    },
    {
        "id": "unite_ai_conferences",
        "goal": "Identify the next 3 conferences listed on https://www.unite.ai/conferences/ and extract their names and dates."
    },
    {
        "id": "verify_ad",
        "goal": "Verify that our ad for Opper.ai is present when searching for AI proxy on Bing"
    },
    {
        "id": "huggingface_models",
        "goal": "Visit huggingface.co and extract the names and download counts of the 5 most popular AI models."
    },
    {
        "id": "government_funding",
        "goal": "Identify funding opportunities for artificial intelligence on https://www.vinnova.se/en/apply-for-funding/find-the-right-funding/ ."
    }, 
    {
        "id": "paperswithcode_sota",
        "goal": "Summarize the trending research listed on paperswithcode.com."
    },
    {
        "id": "github_trending_ai",
        "goal": "Visit GitHub's trending page and find the top 3 AI/ML repositories of today. Extract their names, descriptions, and star counts."
    },
     {
        "id": "chatgpt_trending",
        "goal": "Identify if the trend for searches on 'chatgpt' over the last 12 months is increasing or decreasing."
    },
    {
        "id": "post_tweet",
        "goal": "Post a riddle on x.com and ask people to solve it."
    },
    {
        "id": "like_linkedin_post",
        "goal": "Like the top 3 most recent posts on LinkedIn in the 'Artificial Intelligence' category."
    },
    {
        "id": "linkedin_ai_jobs",
        "goal": "Go to LinkedIn's job search, look for 'AI Engineer' positions in San Francisco, and extract the top 5 job titles and companies."
    },
    {
        "id": "medium_ai_articles",
        "goal": "Visit Medium.com and extract the titles and authors of the 5 most recent featured articles about artificial intelligence."
    },
    {
        "id": "youtube_ai_lectures",
        "goal": "Go to YouTube and find the top 3 most viewed AI lecture videos from major universities this year. Extract titles and view counts."
    },
    {
        "id": "kaggle_competitions",
        "goal": "Visit Kaggle.com and extract the details of all active AI/ML competitions, including prize amounts and deadlines."
    },
    {
        "id": "reddit_ai_posts",
        "goal": "Go to reddit.com/r/artificial and extract the top 5 most upvoted posts of the week, including titles and upvote counts."
    },
    {
        "id": "ai_conference_dates",
        "goal": "Visit the AAAI conference website and extract the important dates and deadlines for the next conference."
    },
    {
        "id": "paperswithcode_sota",
        "goal": "Go to paperswithcode.com and extract the current state-of-the-art results for image classification on ImageNet."
    }
]

# We define a structured completion schema for the tasks so that we can interpret the result in code
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "failure"],
            "description": "Whether the task was completed successfully"
        },
        "data": {
            "type": "object",
            "description": "The extracted data or verification results"
        },
    },
    "required": ["status", "data"]
}

# We define where we can find the actual Agent API
DEFAULT_API_BASE_URL = "http://localhost:8000"

# Maximum number of retries for each task
MAX_RETRIES = 1

# Timeout for each task in seconds
TIMEOUT_SECONDS = 300 

# Global status dictionary to track all tasks
task_status = {}

def format_result_text(result_data) -> str:
    """Format the result text in a clean way"""
    if not result_data:
        return ""
        
    try:
        if isinstance(result_data, dict):
            # If it's a dictionary with a 'result' key, get that
            if 'result' in result_data and 'data' in result_data['result']:
                data = result_data['result']['data']
                return str(data)
            # If no result.data, try just data
            elif 'data' in result_data:
                data = result_data['data']
               
                return str(data)
        # If not a dict, convert to string
        return str(result_data)
    except Exception:
        # If any error in formatting, return as is
        return str(result_data)

def create_status_table() -> Table:
    """Create a status table with space-themed colors"""
    table = Table(
        title="[bold magenta]🚀 Web Automation Tasks Status 🌌[/]",
        border_style="blue",
        header_style="bold magenta",
        pad_edge=False,
        box=box.ROUNDED
    )
    
    # Add columns with space-themed colors
    table.add_column("Task", style="cyan", width=35)
    table.add_column("Status", style="magenta", justify="center", width=10)
    table.add_column("Latest Action", style="green", width=30)
    table.add_column("Result/Error", style="white", overflow="fold", width=50)
    table.add_column("Time", style="blue", justify="right", width=10)
    
    # Sort tasks by their ID for consistent display
    task_ids = sorted(task_status.keys())
    
    for task_id in task_ids:
        status = task_status[task_id]
        
        # Space-themed status styles with emojis
        status_style = {
            "pending": "yellow bold",
            "running": "blue bold",
            "success": "green bold",
            "failure": "red bold"
        }.get(status["status"], "white")
        
        # Add status emojis
        status_text = {
            "pending": "⏳ PENDING",
            "running": "🚀 RUNNING",
            "success": "✨ SUCCESS",
            "failure": "💥 FAILED"
        }.get(status["status"], status["status"].upper())
        
        # Format the result text
        result_text = format_result_text(status.get("data")) or status.get("error") or ""
        if len(str(result_text)) > 50:
            result_text = str(result_text)[:47] + "..."
        
        # Add a subtle gradient to the task description
        description = status.get("description", task_id)
        
        table.add_row(
            f"[cyan]{description}[/]",
            Text(status_text, style=status_style),
            Text(status.get("latest_action", ""), style="green"),
            Text(str(result_text), style="white"),
            Text(status.get("time", ""), style="blue")
        )
    
    return table

def clean_action_text(action: str, details: str) -> str:
    """Clean and format the action text with space-themed emojis"""
    # Remove common prefixes and clean up the text
    action = action.lower().strip()
    details = details.strip()
    
    # Map common actions to space-themed versions
    action_map = {
        "observe": "👀 Observing",
        "reflect": "🤔 Analyzing",
        "decide": "🎯 Planning",
        "act": "⚡ Executing",
        "completed": "✨ Completed",
        "error": "💥 Error"
    }
    
    # Get the cleaned action text
    action_text = action_map.get(action, action.title())
    
    # Clean up details
    if details.lower().startswith(action.lower()):
        details = details[len(action):].strip()
    if details.startswith(":"):
        details = details[1:].strip()
    
    # Combine action and details
    if details:
        return f"{action_text}: {details}"
    return action_text

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run web automation tasks')
    parser.add_argument('--base-url', type=str, default=DEFAULT_API_BASE_URL,
                      help=f'Base URL for the API (default: {DEFAULT_API_BASE_URL})')
    return parser.parse_args()

async def submit_task(session: aiohttp.ClientSession, task: Dict, api_base_url: str) -> Dict:
    """Submit a task for processing"""
    task_id = task["id"]
    task_status[task_id] = {
        "status": "pending",
        "latest_action": "Submitting task",
        "time": datetime.now().strftime("%H:%M:%S"),
        "description": task["goal"][:30] + "..." if len(task["goal"]) > 30 else task["goal"]
    }
    
    payload = {
        "goal": task["goal"],
        "responseSchema": TASK_SCHEMA
    }
    
    timeout = ClientTimeout(total=TIMEOUT_SECONDS)
    async with session.post(f"{api_base_url}/run", json=payload, timeout=timeout) as response:
        result = await response.json()
        task_status[task_id]["status"] = "running"
        task_status[task_id]["latest_action"] = "Task submitted"
        task_status[task_id]["time"] = datetime.now().strftime("%H:%M:%S")
        return {
            "task_id": task_id,
            "session_id": result["session_id"]
        }

async def monitor_task(session: aiohttp.ClientSession, session_id: str, task_id: str, live: Live, api_base_url: str) -> Dict:
    """Monitor the progress of a task through SSE stream with retry logic"""
    result = {
        "task_id": task_id,
        "status": "pending",
        "data": None,
        "error": None
    }
    
    for retry in range(MAX_RETRIES):
        try:
            timeout = ClientTimeout(total=TIMEOUT_SECONDS)
            async with session.get(
                f"{api_base_url}/status-stream/{session_id}",
                headers={"Accept": "text/event-stream"},
                timeout=timeout
            ) as response:
                buffer = ""
                async for chunk in response.content.iter_chunked(1024):
                    try:
                        buffer += chunk.decode('utf-8')
                        lines = buffer.split('\n')
                        
                        # Process complete lines
                        for line in lines[:-1]:
                            line = line.strip()
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])
                                    
                                    # Update status with cleaned action text
                                    if data.get("action") and data.get("details"):
                                        task_status[task_id]["latest_action"] = clean_action_text(
                                            data["action"],
                                            data["details"]
                                        )
                                        task_status[task_id]["time"] = datetime.now().strftime("%H:%M:%S")
                                        live.update(create_status_table())
                                    
                                    # Check for completion or error
                                    if data.get("action") == "completed":
                                        result["status"] = "success"
                                        if "result" in data:
                                            data = data["result"]
                                            result["status"] = "success"
                                            result["data"] = data
                                            task_status[task_id].update({
                                                "status": "success",
                                                "data": data,
                                                "latest_action": "Task completed",
                                                "time": datetime.now().strftime("%H:%M:%S")
                                            })
                                        live.update(create_status_table())
                                        return result
                                    elif data.get("action") == "error":
                                        result["status"] = "failure"
                                        error = data.get("details")
                                        result["error"] = error
                                        task_status[task_id].update({
                                            "status": "failure",
                                            "error": error,
                                            "latest_action": f"Error: {error}",
                                            "time": datetime.now().strftime("%H:%M:%S")
                                        })
                                        live.update(create_status_table())
                                        return result
                                except json.JSONDecodeError:
                                    continue
                        
                        # Keep the incomplete line in the buffer
                        buffer = lines[-1]
                    except Exception as chunk_error:
                        task_status[task_id]["latest_action"] = f"Warning: {str(chunk_error)}"
                        task_status[task_id]["time"] = datetime.now().strftime("%H:%M:%S")
                        live.update(create_status_table())
                        continue
                        
            # If we get here without a return, something went wrong
            if retry < MAX_RETRIES - 1:
                task_status[task_id]["latest_action"] = f"Retrying (attempt {retry + 2}/{MAX_RETRIES})"
                task_status[task_id]["time"] = datetime.now().strftime("%H:%M:%S")
                live.update(create_status_table())
                await asyncio.sleep(1)  # Wait before retry
            else:
                result["status"] = "failure"
                result["error"] = "Maximum retries reached"
                task_status[task_id].update({
                    "status": "failure",
                    "error": "Maximum retries reached",
                    "latest_action": "Failed: Maximum retries reached",
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                live.update(create_status_table())
                
        except asyncio.TimeoutError:
            if retry < MAX_RETRIES - 1:
                task_status[task_id]["latest_action"] = f"Timeout, retrying (attempt {retry + 2}/{MAX_RETRIES})"
                task_status[task_id]["time"] = datetime.now().strftime("%H:%M:%S")
                live.update(create_status_table())
                await asyncio.sleep(1)  # Wait before retry
            else:
                result["status"] = "failure"
                result["error"] = "Operation timed out after multiple retries"
                task_status[task_id].update({
                    "status": "failure",
                    "error": "Timeout after multiple retries",
                    "latest_action": "Failed: Timeout after multiple retries",
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                live.update(create_status_table())
        except Exception as e:
            if retry < MAX_RETRIES - 1:
                task_status[task_id]["latest_action"] = f"Error, retrying (attempt {retry + 2}/{MAX_RETRIES})"
                task_status[task_id]["time"] = datetime.now().strftime("%H:%M:%S")
                live.update(create_status_table())
                await asyncio.sleep(1)  # Wait before retry
            else:
                result["status"] = "failure"
                result["error"] = str(e)
                task_status[task_id].update({
                    "status": "failure",
                    "error": str(e),
                    "latest_action": f"Failed: {str(e)}",
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                live.update(create_status_table())
    
    return result

async def process_task(session: aiohttp.ClientSession, task: Dict, live: Live, api_base_url: str) -> Dict:
    """Process a single task - submit and monitor progress"""
    try:
        # Submit the task
        task_info = await submit_task(session, task, api_base_url)
        # Monitor the task
        result = await monitor_task(session, task_info["session_id"], task_info["task_id"], live, api_base_url)
        return result
    except Exception as e:
        task_status[task["id"]].update({
            "status": "failure",
            "error": str(e),
            "time": datetime.now().strftime("%H:%M:%S")
        })
        live.update(create_status_table())
        return {
            "task_id": task["id"],
            "status": "failure",
            "error": str(e)
        }

async def main():
    """Main function to process all tasks"""
    args = parse_args()
    api_base_url = args.base_url

    tasks = TASKS
    # Initialize status for all tasks
    for task in tasks:
        task_status[task["id"]] = {
            "status": "pending",
            "latest_action": "Waiting to start",
            "time": datetime.now().strftime("%H:%M:%S"),
            "description": task["goal"][:30] + "..." if len(task["goal"]) > 30 else task["goal"]
        }
    
    # Configure client session with default timeout
    timeout = ClientTimeout(total=TIMEOUT_SECONDS)
    connector = aiohttp.TCPConnector(limit=5)  # Limit concurrent connections
    
    console = Console()
    
    with Live(create_status_table(), refresh_per_second=4) as live:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Process tasks in smaller batches to avoid overwhelming the server
            batch_size = 5  # Reduced batch size due to more complex tasks
            all_results = []
            
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                
                # Create tasks for the current batch
                batch_tasks = []
                for task in batch:
                    try:
                        task_future = process_task(session, task, live, api_base_url)
                        batch_tasks.append(task_future)
                    except Exception as e:
                        console.print(f"[red]Failed to create task for {task['id']}: {str(e)}[/]")
                        task_status[task["id"]].update({
                            "status": "failure",
                            "error": f"Failed to start task: {str(e)}",
                            "time": datetime.now().strftime("%H:%M:%S")
                        })
                        live.update(create_status_table())
                
                # Wait for current batch to complete, handling failures individually
                if batch_tasks:
                    try:
                        # Use gather with return_exceptions=True to continue even if some tasks fail
                        results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                        
                        # Process results, handling any exceptions
                        for result in results:
                            if isinstance(result, Exception):
                                console.print(f"[red]Task failed with error: {str(result)}[/]")
                            else:
                                all_results.append(result)
                    except Exception as e:
                        console.print(f"[red]Batch processing error: {str(e)}[/]")
                
                # Small delay between batches if there are more tasks
                if i + batch_size < len(tasks):
                    next_batch = tasks[i + batch_size:min(i + batch_size * 2, len(tasks))]
                    for task in next_batch:
                        if task["id"] in task_status:
                            task_status[task["id"]]["latest_action"] = "Waiting for next batch"
                            task_status[task["id"]]["time"] = datetime.now().strftime("%H:%M:%S")
                    live.update(create_status_table())
                    await asyncio.sleep(2)
    
    # Save results to file
    try:
        with open("automation_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
        console.print("\n[green]Results have been saved to automation_results.json[/]")
    except Exception as e:
        console.print(f"\n[red]Failed to save results: {str(e)}[/]")

if __name__ == "__main__":
    # Ensure the FastAPI server is running first
    console = Console()
    args = parse_args()
    console.print(f"[yellow]Make sure the FastAPI server is running at {args.base_url}")
    console.print("[green]Starting automation in 3 seconds...")
    console.print("")
    time.sleep(3)
    
    asyncio.run(main())
