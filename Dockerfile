FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y wget gnupg curl unzip xvfb libnss3 libxss1 libasound2 libatk1.0-0 libgtk-3-0 libgbm1

RUN pip install --upgrade pip

# Install Playwright and deps
RUN pip install -r requirements.txt && playwright install chromium

CMD ["python", "main.py"]
