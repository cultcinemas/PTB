# FINAL CORRECT DOCKERFILE
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for web scraping
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security (this is still a good practice)
RUN useradd --create-home appuser

# Copy requirements file first to use Docker's cache
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project code
COPY --chown=appuser:appuser . .

# Create logs directory with proper permissions
RUN mkdir -p /tmp/logs && chown -R appuser:appuser /tmp/logs

# Switch to the non-root user
USER appuser

# Set environment variable for log file location
ENV LOG_FILE=/tmp/logs/bot.log

# Directly run the main script using its correct path
CMD ["python3", "main.py"]
