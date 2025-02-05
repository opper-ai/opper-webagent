# Scriptable AI-Powered Compound Web Agent

This project implements an AI-powered web navigation agent built to autonomously and headlessly browse websites to accomplish tasks such as scraping data, automating form submissions, and more. It is focused on being scriptable and implemented as a backend service, but examples exists to build interfaces around it. It is a compound agent in that it uses specific models for different parts of the agents tasks.

## Features

- **Set Goal with Natural Language**: Simply describe what you want the agent to do with a web browser
- **Headless Operation**: Run invisibly in the background or watch the agent work with browser visibility
- ** Structured Completion Output**: Define JSON schemas to format the extracted data exactly how want it to make it easy to programmatically parse agent runs. 
- **Callback for monitoring progress**: Monitor the agent's progress through a callback function
- **Pass Authentication details**: Pass login credentials and sensitive data for authenticated sessions
- **Example Interfaces**: Use through Python API, web interface, CLI.

## About the Agent

The agent is powered by the Opper API and the Opper AI platform to access models, perform tracing and more. The agent is a so called compound agent that utilizes specific models for different tasks.

* Molmo for interpreting images and finding where to click
* Deepseek V3 for reflection, reasoning and planning
* Mistral Large for determining and specifying actions

The agent can perform the following actions:
* `navigate`: Go to a specific URL
* `look`: Analyze page content
* `click`: Click at specific coordinates
* `type`: Enter text in forms 
* `scroll_down`/`scroll_up`: Scroll the page
* `wait`: Pause execution
* `finished`: Finish the goal with structured output results

## Installation

First sign up to Opper at https://opper.ai/ and create an API key to access models, tracing and more. Opper free tier allows for $10 of free credits to get started.

Export the API key as an environment variable:

```bash
export OPPER_API_KEY=<your-api-key>
```

Then install the required packages:

```bash
pip install -r requirements.txt
```

## Quick Start

The web agent can be used directly in your Python code:

```python
from web_agent import run

# Define a callback for monitoring progress
def print_status(action, details):
    print(f"{action}: {details}")

# Example: Scrape product information with authentication
result = run(
    # Describe your goal in natural language
    goal="Go to https://opper.ai and verify that there is a blog post covering DeepSeek-R1 there",
    
    # Provide credentials if needed
    secrets=None,
    
    # Define the structure of the data you want
    response_schema={
        "type": "object",
        "properties": {
            "is_posted": {"type": "boolean"},
            "post_title": {"type": "string"}
        }
    },
    
    # Monitor the agent's progress
    status_callback=print_status
)

# Access the results
print(result["result"])
```

Will yeild something like where it continous to print status updates until the goal is reached:

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

## Alternative Interfaces

### Web Interface

Runs a web interface on localhost:5000 where you can enter your goal and see the agent work:

```bash
python examples/web_interface/app.py
# Then open http://localhost:5000
```

### Command Line

Runs a command line interface where you can enter your goal and see the agent work:

```bash
python examples/console_interface/app.py
```


## Supported Actions

The agent can perform these actions:
- `navigate`: Go to a specific URL
- `look`: Analyze page content
- `click`: Click at specific coordinates
- `type`: Enter text and press Enter/Tab
- `scroll_down`/`scroll_up`: Scroll the page
- `wait`: Pause execution
- `finished`: Complete the goal

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.