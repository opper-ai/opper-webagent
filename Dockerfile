# Use Python 3.12 as base image
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

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

# Copy package files
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .

# Create venv and install package
RUN uv sync --frozen

# Install playwright dependencies and chromium
RUN uv run playwright install --with-deps chromium

COPY src/ src/
COPY examples/ examples/

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the REST API
CMD ["uv", "run", "uvicorn", "examples.rest.app:app", "--host", "0.0.0.0", "--port", "8000"]
