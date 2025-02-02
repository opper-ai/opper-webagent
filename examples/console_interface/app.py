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
from rich.prompt import Prompt, Confirm

# Add the src directory to the Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / 'src'))

from web_agent import run, get_status, stop

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

def create_status_entry(action, details):
    """Create a status entry for display"""
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

def get_task_configuration():
    """Interactive dialog to get task configuration from user"""
    console.print(Panel.fit(
        "[bold blue]Task Configuration[/bold blue]\n"
        "Please provide the following information:",
        border_style="blue"
    ))
    
    # Get the main task description
    task = Prompt.ask("\n[cyan]Enter the task description[/cyan]")
    
    # Ask about browser visibility
    headless = not Confirm.ask(
        "\n[cyan]Would you like to see the browser window while the task runs?[/cyan]",
        default=False
    )
    
    # Ask about schema
    use_schema = Confirm.ask(
        "\n[cyan]Would you like to provide a response schema for validation?[/cyan]",
        default=False
    )
    
    schema = None
    if use_schema:
        schema_input = Prompt.ask(
            "\n[cyan]Enter the JSON schema string[/cyan] (press Enter to skip)",
            default="{}"
        )
        try:
            schema = json.loads(schema_input)
        except json.JSONDecodeError:
            console.print("[yellow]Invalid JSON schema. Proceeding without schema.[/yellow]")
            schema = None
    
    return {
        "task": task,
        "headless": headless,
        "schema": schema
    }

def main():
    parser = argparse.ArgumentParser(description="Web Agent Console Interface - Browser automation with AI assistance")
    parser.add_argument("--task", help="Task description for the AI to execute")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window (default: headless)")
    parser.add_argument("--schema", help="JSON schema string for response validation")
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold green]Web Agent Console Interface[/bold green]\n"
        "Interactive browser automation with AI assistance",
        border_style="green"
    ))

    # If no task is provided via command line, use interactive configuration
    if not args.task:
        config = get_task_configuration()
        task = config["task"]
        headless = config["headless"]
        response_schema = config["schema"]
    else:
        task = args.task
        headless = not args.no_headless
        response_schema = json.loads(args.schema) if args.schema else None

    result = None
    error = None

    try:
        def status_callback(action, details):
            status_entry = create_status_entry(action, details)
            if status_entry:
                console.print(status_entry)

        # Show configuration summary
        console.print(Panel(
            "[bold cyan]Task Configuration Summary:[/bold cyan]\n" +
            f"Task: {task}\n" +
            f"Browser Mode: {'visible' if not headless else 'headless'}\n" +
            f"Schema Validation: {'enabled' if response_schema else 'disabled'}",
            border_style="cyan"
        ))

        if Confirm.ask("\n[cyan]Proceed with the task?[/cyan]", default=True):
            result = run(
                task,
                headless=headless,
                response_schema=response_schema,
                status_callback=status_callback
            )
        else:
            console.print("[yellow]Task cancelled by user[/yellow]")
            return

        # Display execution summary
        console.print("\n[bold green]Execution Summary[/bold green]")
        
        if isinstance(result, dict):
            # Display final result
            console.print(Panel(
                "[bold green]Final Result:[/bold green]\n" + 
                json.dumps(result.get('result', {}), indent=2),
                title="Result",
                border_style="green"
            ))
            
            # Display duration
            console.print(f"[cyan]Duration:[/cyan] {result.get('duration_seconds', 0):.2f} seconds")
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