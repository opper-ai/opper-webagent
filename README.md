# Opperator - A Composable, Autonomous Compound AI Web Agent

🌐 This is a scriptable compound AI web agent designed to automate complex web tasks through natural language instructions. Built to run autonomously in the background and be interfaced with through code.

The agent is primarily designed to be used as a library or interacted with through its provided REST API. A set of example UIs are provided in the `examples` folder.

## Demo Video

[![Demo Video](https://img.youtube.com/vi/-0Tl9f3xtqI/0.jpg)](https://youtu.be/-0Tl9f3xtqI)

The console based multi task interface is available as an example interface in the `examples/multi` folder. See below for instructions.

## Key Features

- 🎯 **Natural Language Task Definition**: Define web tasks using plain English - no configuration required
- 🤖 **Headless Operation**: Run silently in the background or monitor real-time execution
- 📊 **Programmatic Integration**: Receive structured JSON output for seamless integration with your codebase
- 🔄 **Progress Monitoring**: Track agent progress through customizable callbacks
- 🔐 **Secure Authentication**: Safely handle credentials and sensitive data

## Technical Architecture

Opperator leverages multiple AI models via the Opper AI platform to perform the different tasks:

- 🔍 **Molmo**: An open-source model for visual analysis and web element detection
- 🤔 **Sonnet-3.5**: For strategic reflection and decision making
- 🎯 **Flash-1.5**: For fast content extraction and structured output

### System Flow

```sh
                  ┌─────────────┐
                  │    Goal     │
                  └──────┬──────┘
                         │
                         ▼
              ┌────────────────────────┐
        ┌────►│   Take Screenshot      │
        │     └──────────┬─────────--──┘
        │                │
        │                ▼
        │     ┌────────────────────────┐
        │     │  Observe Screenshot    │
        │     └──────────┬─────────--──┘
        │                │
        │                ▼
        │     ┌────────────────────────┐
        │     │  Reflect on Progress   │
        │     └──────────┬───────────-─┘
        │                │
        │                ▼
        │     ┌────────────────────────┐
        │     │   Choose Action        │──────┐
        │     └────────────────────────┘      │
        │                                     │
        └─────────────────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    End      │
                    └─────────────┘

```

### Supported Actions

The agent autonomously executes tasks using the following actions:

| Action                  | Description                                    |
|------------------------|------------------------------------------------|
| `navigate`             | Visit specified URLs                           |
| `look`                 | Analyze page content and structure             |
| `click`                | Interact with page elements                    |
| `type`                 | Input text and fill forms                      |
| `scroll_down`/`scroll_up` | Navigate page content vertically            |
| `wait`                 | Handle dynamic loading and state changes       |
| `finished`             | Complete task and return structured output     |

### Status Messages

The agent provides status updates through callback functions during task execution. Each status message contains:

| Field      | Description                                           |
|------------|-------------------------------------------------------|
| `action`   | The current action being performed (e.g. `navigate`, `click`) |
| `details`  | Additional context about the action and its outcome    |
| `screenshot`| Path to temporary image file                         |

## Getting Started

### Prerequisites

1. Sign up at [opper.ai](https://opper.ai/) to obtain an API key
2. The free tier includes $10 monthly credit for inference and tracing

### Option 1: Using Docker (Quickstart)

Run the web agent using Docker:

```shell
docker run --rm -ti \
  -e OPPER_API_KEY=op-<your-api-key> \
  -p 8000:8000 \
  ghcr.io/opper-ai/opper-webagent:latest
```

To issue tasks you can browse to `http://localhost:8000/` to use the web interface.

You may also interact with it over REST (API docs at http://127.0.0.1:8000/docs#/)

```
# Execute a web task (returns session id)
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Go to https://opper.ai and check the pricing",
    "response_schema": {
      "type": "object",
      "properties": {
        "has_free_tier": {"type": "boolean"},
        "pricing_details": {"type": "string"}
      },
      "required": ["has_free_tier", "pricing_details"]
    }
  }'

# Stream status updates
curl -N http://localhost:8000/status-stream/<session_id>
```

### Option 2: Local Installation

#### Environment Setup

Set your API key:

```shell
export OPPER_API_KEY=op-<your-api-key>
```

#### Installation

Install using [uv](https://github.com/astral-sh/uv):

```shell
# Install uv (if needed)
# For Unix-like systems:
curl -LsSf https://astral.sh/uv/install.sh | sh

# For MacOS:
brew install uv

# Install dependencies
uv sync --frozen
```

## Example Interfaces

### Asynchronous Multi-Task Example (from Demo)

Run the multi-task example:

```shell
uv run examples/multi/app.py
```

### Python Library Integration

```python
from opper_webagent import run

def print_status(action, details):
    print(f"{action}: {details}")

# Example: Verify blog post existence
result = run(
    goal="Go to https://opper.ai and verify that there is a blog post covering DeepSeek-R1 there",
    secrets=None,  # Optional: Add authentication credentials
    response_schema={
        "type": "object",
        "properties": {
            "is_posted": {"type": "boolean"},
            "post_title": {"type": "string"}
        }
    },
    status_callback=print_status  # Optional: Monitor progress
)

print(result["result"])
```

Example output:

```shell
starting: Go to https://opper.ai and verify that there is a blog post covering DeepSeek-R1 there
setup: Initializing browser
reflecting: Initialized successfully, ready to start navigation
navigating: Going to https://opper.ai
looking: Analyzing page content
reflecting: On homepage, need to find blog section
clicking: Clicking on "Blog" link
looking: Scanning blog posts
reflecting: In blog section, searching for DeepSeek-R1 post
finished: Found DeepSeek-R1 blog post
cleanup: Done with task, closing browser

{
    "is_posted": True,
    "post_title": "DeepSeek-R1 and Mistral Tiny"
}
```

### Web Interface

Launch the proof-of-concept web UI:

```shell
uv run examples/rest/app.py
# Access at http://localhost:8000
```

### Command Line Interface

Use the CLI tool:

```shell
uv run examples/cli/app.py
```

### Alternative Deployment Methods

#### Using Docker Compose

If you prefer using Docker Compose:

```shell
docker compose up --build
```

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

For major changes, open an issue first to discuss your proposed modifications.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

