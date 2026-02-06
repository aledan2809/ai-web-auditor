FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright dependencies manually (fonts that work on Debian)
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-noto-color-emoji \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browser only (no deps since we installed them)
RUN playwright install chromium

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
