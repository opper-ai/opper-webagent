# Opperator

## A scriptable compound AI web agent that headlessly and autonomously executes tasks on the web

🌐 We built Opperator as a proof of concept for a new class of AI agents that can run headlessly and autonomously, focusing on automating tasks on the web.

## What Makes It Special

- 🎯 **Specify web task in natural language**: Simply tell it what you want - no complex configuration needed
- 🤖 **Have it run headlessly in the background**: Run silently in the background or watch the magic happen in real-time
- 📊 **Built to be operated from code**: Get results in precisely formatted JSON that that you can work with in code
- 🔄 **Get feedback on agent progress**: Specify a callback to monitor every step of the agents progress to build powerful interfaces.
- 🔐 **Pass authentication details**: Safely pass login credentials and sensitive data

## Under the Hood

The agent is a so called compound AI agent in that it utilizes differnt models for different parts of its subtasks. It accesses these models via the Opper AI platform: 

- 🔍 **Molmo**: An open source model specialized for visual analysis and web element detection
- 🤔 **Deepseek V3**: A large language model specialized for strategic reasoning and planning
- 🎯 **Mistral Large**: A large language model specialized for action determination and execution

Here is a high level overview of the agent's flow:

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



### Available Actions

The agent will autonomously reason its way through the task and may perform the following actions:

| Action | Description |
|--------|-------------|
| `navigate` | Visit any URL |
| `look` | Analyze page content |
| `click` | Interact with elements |
| `type` | Fill out forms |
| `scroll_down`/`scroll_up` | Navigate pages |
| `wait` | Handle loading states |
| `finished` | Complete with structured output |

## Installation

First sign up to Opper at https://opper.ai/ and create an API key to access models, tracing and more. **The Opper free tier allows for $10 of free credits for inference and tracing.** 

Export the API key as an environment variable:

```bash
export OPPER_API_KEY=op-xx
```

Then install the package using uv:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
. .venv/bin/activate
uv install -e .
```

## Use as a library

The web agent can be used directly in your Python code:

```python
from opper.web_agent import run

# Define a callback for monitoring progress
def print_status(action, details):
    print(f"{action}: {details}")

# Example: Scrape product information with authentication
result = run(

    # Describe your goal in natural language
    goal="Go to https://opper.ai and verify that there is a blog post covering DeepSeek-R1 there",
    
    # Provide credentials if needed
    secrets=None,
    
    # Define response schema using JSON Schema specification (see https://json-schema.org)
    response_schema={
        "type": "object",
        "properties": {
            "is_posted": {"type": "boolean"},
            "post_title": {"type": "string"}
        }
    },
    
    # Optionally provide a callback to monitor the agent's progress
    status_callback=print_status
)

# Access the results
print(result["result"])
```

Running this will yield something like the following where it continously print status updates until the goal is reached:

```python
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

## Use Docker container

Build the docker image:

```bash
docker build -t opperator .
```

Run the docker container and expose port 8000:

*Note: Remember to get an API key from Opper*

```bash
docker run -p 8000:8000 -e OPPER_API_KEY=<your-api-key> opperator
```

By default, this will start a REST API server on port 8000. You can interact with it using HTTP requests:

```bash
# Example: Run a web agent task
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Go to https://opper.ai and check the pricing",
    "response_schema": {
      "type": "object",
      "properties": {
        "has_free_tier": {"type": "boolean"},
        "pricing_details": {"type": "string"}
      }
    }
  }'
```

You can also stream status updates using:

```bash
curl -N http://localhost:8000/status-stream/<session_id>
```

This will stream real-time updates in Server-Sent Events (SSE) format:

```bash
data: {"action": "initializing", "details": "starting task"}
data: {"action": "navigating", "details": "Going to https://opper.ai"}
...etc
```

## Alternative Interfaces

### Web Interface

We also built a simple proof of concept web interface that you can use to invoke tasks with the agent:

```bash
pip install -r examples/web/requirements.txt

python examples/web/app.py
# Then open http://localhost:8001
```

### Command Line

As with the web interface, this command line interface is a proof of concept that you can use to invoke tasks with the agent:

```bash
pip install -r examples/cli/requirements.txt

python examples/cli/app.py
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.