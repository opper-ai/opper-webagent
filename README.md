# AI Web Navigation Agent

This project implements an AI-powered web navigation agent that can autonomously browse websites to accomplish specified goals.

## Overview

The project consists of two main parts:
1. A core `web_agent` library in the `src` directory
2. Example implementations in the `examples` directory showing different ways to use the agent

The web agent can:
- Navigate to web pages
- Analyze page content using computer vision
- Make decisions about next actions
- Interact with pages through clicking, typing, and scrolling
- Track progress toward goals

## Quick Start

The easiest way to try out the web agent is through the web interface:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the web interface
python examples/web_interface/app.py
```

Then open your browser to `http://localhost:8000`. The web interface provides:
- A simple form to enter your navigation goals
- Real-time feedback on the agent's actions
- Visual preview of what the agent sees
- Easy configuration of credentials and settings

## Other Usage Options

### 1. Web Agent Library

Import and use the web agent directly in your Python code:

```python
from web_agent import navigate_with_ai

result = navigate_with_ai(
    goal="Your navigation goal",
    secrets="optional credentials"
)
```

### 2. Command Line Script
```bash
python examples/cli.py "Your goal here"
```

### 3. REST API Service
```bash
python examples/service.py
```

Then send requests to the service:
```bash
curl -X POST http://localhost:8000/navigate \
  -H "Content-Type: application/json" \
  -d '{"goal": "Your goal here", "secrets": "optional credentials"}'
```

### Supported Actions

The agent can perform these actions:
- `navigate`: Go to a specific URL
- `look`: Analyze page content
- `click`: Click at specific coordinates
- `type`: Enter text and press Enter/Tab
- `scroll_down`/`scroll_up`: Scroll the page
- `wait`: Pause execution
- `finished`: Complete the goal

### Example Usage

Here's how to use the web agent library in your code:

```python
from web_agent import navigate_with_ai

# Simple navigation
result = navigate_with_ai("Navigate to example.com and click the login button")

# Navigation with credentials
result = navigate_with_ai(
    goal="Log in to example.com",
    secrets={
        "username": "your_username",
        "password": "your_password"
    }
)
```

### Configuration

You can configure the agent's behavior through environment variables or when initializing the agent:

```python
from web_agent import navigate_with_ai, WebAgentConfig

config = WebAgentConfig(
    debug=True,
    timeout=30,
    headless=False
)

result = navigate_with_ai("Your goal", config=config)
```

### Logging

Logs are generated to help you understand the agent's decisions and actions. You can find logs in the `logs/` directory.

### Extending the Agent

The agent's capabilities can be extended by adding new actions or improving existing ones. To add a new action:

1. Define the action in `src/web_agent/models/schemas.py`
2. Implement the action logic in `src/web_agent/ai/coordinator.py`
3. Update the main navigation loop to handle the new action

### Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.
