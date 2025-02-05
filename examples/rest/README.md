# Web Interface Example

This example provides a simple web interface for the Web Agent, allowing you to interact with it through your browser.

## Setup

1. From the root directory of the project, install the package in development mode:
```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install the main package in development mode
pip install -e .
```

2. Install the web interface dependencies:
```bash
cd examples/web_interface
pip install -r requirements.txt
```

## Running the Web Interface

1. Make sure your virtual environment is activated, then from the web_interface directory run:
```bash
python app.py
```

2. Open your browser and navigate to: `http://localhost:5000`

## Features

- Input your navigation goal
- Add optional login secrets
- Toggle headless mode
- Toggle debug mode
- View results including:
  - Final result
  - Duration
  - Full trajectory of actions taken

## Notes

- The web interface runs the agent in a separate process for each request
- Results are displayed in real-time once the navigation is complete
- The interface is designed to be simple and user-friendly
- Make sure you're running the interface from within the virtual environment where you installed the dependencies 