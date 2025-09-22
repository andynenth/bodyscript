#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create necessary directories
mkdir -p backend/temp

echo "Build completed successfully!"