FROM python:3.11-slim

WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl gnupg2 \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 xdg-utils libgbm1 libgtk-3-0 libxss1 libxshmfence1 \
    libxext6 libxi6 libxrender1 libxtst6 \
    chromium chromium-driver

# Add Chromium to PATH
ENV PATH="/usr/lib/chromium/:${PATH}"
ENV GOOGLE_CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of your app
COPY . .

CMD ["python", "main.py"]
