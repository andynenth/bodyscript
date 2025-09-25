# Multi-stage build for smaller image
FROM public.ecr.aws/docker/library/python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY backend/requirements.txt /tmp/
RUN pip install --user --no-cache-dir -r /tmp/requirements.txt

# Final stage
FROM public.ecr.aws/docker/library/python:3.9-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set up working directory
WORKDIR /app

# Copy backend code
COPY backend/ /app/

# Copy CLI code (needed by backend)
COPY cli/ /cli/

# Copy frontend for serving
COPY frontend/ /frontend/

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Create temp directory
RUN mkdir -p /app/temp && chmod 755 /app/temp

# Default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]