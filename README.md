# AI Web Navigation Agent

This project implements an AI-powered web navigation agent that can autonomously browse websites to accomplish specified goals.

## Overview

The main script (`src/web_agent/main.py`) contains the core navigation logic that enables an AI agent to:

- Navigate to web pages
- Analyze page content using computer vision
- Make decisions about next actions
- Interact with pages through clicking, typing, and scrolling
- Track progress toward goals

## Key Components

### Main Navigation Loop

The `navigate_with_ai()` function implements the main navigation loop:

1. Takes a goal and optional login credentials as input
2. Sets up a browser session using Playwright
3. Continuously:
   - Observes the current page state
   - Decides on subgoals
   - Determines next action
   - Executes actions (navigate, click, type, scroll, etc.)
   - Tracks trajectory of actions and results
4. Terminates when goal is achieved

### Supported Actions

The agent can perform these actions:
- `navigate`: Go to a specific URL
- `look`: Analyze page content
- `click`: Click at specific coordinates
- `type`: Enter text and press Enter/Tab
- `scroll_down`/`scroll_up`: Scroll the page
- `wait`: Pause execution
- `finished`: Complete the goal

### Usage

To use the navigation agent:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the main script with your desired goal:
   ```bash
   python src/web_agent/main.py "Your goal here"
   ```

### Example

To navigate to a website and log in:

1. Set your goal:
   ```bash
   python src/web_agent/main.py "Log in to example.com"
   ```

2. Optionally, provide login details:
   ```bash
   python src/web_agent/main.py "Log in to example.com" --secrets "username: your_username, password: your_password"
   ```

### Configuration

You can configure the agent's behavior by modifying the following parameters in `src/web_agent/main.py`:

- `DEBUG`: Set to `True` to enable debug mode and print additional information.
- `timeout`: Adjust the timeout for page navigation actions.

### Logging

Logs are generated to help you understand the agent's decisions and actions. You can find logs in the `logs/` directory.

### Extending the Agent

The agent's capabilities can be extended by adding new actions or improving existing ones. To add a new action:

1. Define the action in `src/web_agent/models/schemas.py`.
2. Implement the action logic in `src/web_agent/ai/coordinator.py`.
3. Update the main navigation loop in `src/web_agent/main.py` to handle the new action.

### Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.


