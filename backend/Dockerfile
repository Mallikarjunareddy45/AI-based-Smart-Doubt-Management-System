# Use official python-slim base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set container working directory
WORKDIR /backend

# Install system dependencies (build-essential needed for compiling C-extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source files
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Expose backend REST/WebSocket port
EXPOSE 8000

# Run startup script
CMD ["./start.sh"]
