# Use Python 3.12 as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Chrome/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy package files
COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY examples/ examples/

# Create venv and install package
RUN uv venv
RUN . .venv/bin/activate && uv install -e .

# Install playwright
RUN . .venv/bin/activate && playwright install

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the REST API
CMD ["uvicorn", "examples.rest.app:app", "--host", "0.0.0.0", "--port", "8000"]
