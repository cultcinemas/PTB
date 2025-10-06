# Use official Python 3.12 image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y gcc python3-dev && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (optional if webhooks used)
EXPOSE 8080

# Command to run bot
CMD ["python", "main.py"]
