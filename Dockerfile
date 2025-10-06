# Use a smaller, more secure base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy requirements first to use Docker's cache efficiently
COPY --chown=appuser:appuser requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to the non-root user
USER appuser

# Copy the rest of your application code
COPY --chown=appuser:appuser . .

# --- THIS IS THE CORRECTED LINE ---
# Set the command to run your bot's main.py file
CMD ["python3", "-m", "PTB.main"]
