FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y wget gnupg unzip curl && \
    apt-get install -y libnss3 libatk-bridge2.0-0 libxss1 libasound2 libgbm-dev libgtk-3-0

# Install Playwright and Chromium
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt


# Copy everything else
COPY . .

# Default command
CMD ["python", "main.py"]
