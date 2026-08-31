# Mycel Backend — Dockerfile
# Author: Kaushal Jindal
# Project: Mycel

FROM python:3.11-slim

WORKDIR /app

# Set India timezone (IST = UTC+5:30)
ENV TZ=Asia/Kolkata
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ /app/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start the Mycel API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]