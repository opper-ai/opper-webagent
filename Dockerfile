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
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY setup.py .
COPY README.md .
COPY opper/ opper/
COPY requirements.txt .
COPY examples/ examples/

# Install package and requirements
RUN pip install -e .
RUN pip install -r examples/rest/requirements.txt

# Install playwright
RUN playwright install

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the REST API
CMD ["uvicorn", "examples.rest.app:app", "--host", "0.0.0.0", "--port", "8000"]
