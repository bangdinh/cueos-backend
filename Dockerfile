FROM python:3.10-slim

WORKDIR /app

# Install dependencies
# Note: we need libgl1-mesa-glx for opencv-python, but we might just use opencv-python-headless
# But to be safe and compatible with the current code, we install required system libs.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Ensure PYTHONPATH allows absolute imports from the root directory
ENV PYTHONPATH=/app

# The command will be overridden by docker-compose for each service
CMD ["python", "run_server.py"]
