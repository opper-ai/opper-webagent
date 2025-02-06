# Web Agent Console Interface

A command-line interface for interacting with the Web Agent, featuring a beautiful terminal UI powered by Rich.

## Features

- Interactive menu-driven interface
- Real-time status updates
- Beautiful terminal output with colors and formatting
- Easy-to-use prompts for input
- Support for headless/non-headless browser automation

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python app.py
```

The interface provides four main options:

1. **Run browser automation**: Start a new automation task by providing a URL and instructions
2. **Check status**: View the current status of any running automation
3. **Stop current automation**: Stop any running automation task
4. **Exit**: Close the application

## Example

To automate a web task:
1. Select option 1
2. Enter the starting URL (e.g., "https://example.com")
3. Describe what you want the AI to do (e.g., "Find and click the first link, then extract all headings")
4. Choose whether to run in headless mode
5. Watch the automation progress in real-time 