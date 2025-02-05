FROM python:3.12-slim

# Install system dependencies for Chrome/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install

COPY examples/rest/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ src/
COPY examples/ examples/
COPY setup.py .

RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Define OPPER_API_KEY as a build argument and environment variable
ARG OPPER_API_KEY
ENV OPPER_API_KEY=${OPPER_API_KEY}

# Expose the port the app runs on
EXPOSE 8000

# Command to run the REST API
CMD ["uvicorn", "examples.rest.app:app", "--host", "0.0.0.0", "--port", "8000"]
