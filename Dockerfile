# --- FINAL RECOMMENDED Dockerfile ---
FROM python:3.9-slim

WORKDIR /app

# The user setup is still good for permissions
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy and install requirements (no change here)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# This COPY command is for when you build without volumes (e.g., in production)
# It ensures the code is in the image itself.
COPY --chown=appuser:appuser PTB/ .

# The final, correct command to execute the main script
CMD ["python3", "main.py"]
