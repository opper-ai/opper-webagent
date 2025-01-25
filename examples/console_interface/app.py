import sys
import os
import json
import argparse
import time
import threading
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.live import Live
from rich.layout import Layout

# Add the src directory to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / 'src'))

from web_agent import navigate_with_ai, get_status, stop

console = Console()

def display_trajectory(trajectory):
    if not trajectory:
        return
    
    table = Table(title="Action Trajectory", show_header=True, header_style="bold green")
    table.add_column("Step", style="dim")
    table.add_column("Action", style="cyan")
    table.add_column("Details", style="yellow")
    
    for idx, action in enumerate(trajectory, 1):
        details = json.dumps(action.get('details', {}), indent=2) if isinstance(action, dict) else str(action)
        action_type = action.get('action', 'Unknown') if isinstance(action, dict) else 'Action'
        table.add_row(str(idx), action_type, details)
    
    console.print(table)

def create_status_entry(status):
    """Create a status entry for display"""
    action = status.get('action', 'None')
    details = status.get('details', '')
    
    if not action and not details:
        return None
    
    status_table = Table(show_header=False, box=None)
    status_table.add_row("[bold cyan]Status:[/bold cyan]", f"[cyan]{action.upper()}[/cyan]")
    if details:
        status_table.add_row("[bold yellow]Details:[/bold yellow]", f"[yellow]{details}[/yellow]")
    
    return Panel(
        status_table,
        border_style="green",
        padding=(0, 1)
    )

def main():
    parser = argparse.ArgumentParser(description="Web Agent Console Interface - Browser automation with AI assistance")
    parser.add_argument("task", help="Task description for the AI to execute")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window (default: headless)")
    parser.add_argument("--schema", help="JSON schema string for response validation")
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold green]Web Agent Console Interface[/bold green]\n"
        "Interactive browser automation with AI assistance",
        border_style="green"
    ))

    response_schema = json.loads(args.schema) if args.schema else None
    result = None
    error = None
    
    # Create a thread to run the navigation
    def run_navigation():
        nonlocal result, error
        try:
            result = navigate_with_ai(args.task, headless=not args.no_headless, response_schema=response_schema)
        except Exception as e:
            error = e
    
    navigation_thread = threading.Thread(target=run_navigation)
    navigation_thread.start()
    
    try:
        # Poll and display status while automation is running
        last_status = None
        while navigation_thread.is_alive():
            status = get_status()
            if status != last_status:  # Only print if status changed
                status_entry = create_status_entry(status)
                if status_entry:
                    console.print(status_entry)
                last_status = status.copy()  # Make a copy to properly detect changes
                
            time.sleep(0.1)  # Small sleep to prevent CPU overuse
        
        # Wait for thread to complete
        navigation_thread.join()
        
        # Check if there was an error
        if error:
            raise error
            
        # Display execution summary
        console.print("\n[bold green]Execution Summary[/bold green]")
        
        if isinstance(result, dict):
            # Display trajectory if available
            if 'trajectory' in result:
                display_trajectory(result['trajectory'])
            
            # Display final result
            console.print(Panel(
                "[bold green]Final Result:[/bold green]\n" + 
                json.dumps(result.get('result', {}), indent=2),
                title="Result",
                border_style="green"
            ))
            
            # Display metadata
            metadata_table = Table(show_header=False, box=None)
            metadata_table.add_row("Duration:", f"{result.get('duration_seconds', 0):.2f} seconds")
            if 'status' in result:
                metadata_table.add_row("Status:", result['status'])
            console.print(metadata_table)
        else:
            console.print(Panel(f"[green]Result:[/green]\n{result}", border_style="green"))
            
    except Exception as e:
        console.print(Panel(
            f"[red bold]Error occurred during execution:[/red bold]\n{str(e)}",
            border_style="red"
        ))
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user[/yellow]")
        stop()  # Stop the agent gracefully
        sys.exit(1)