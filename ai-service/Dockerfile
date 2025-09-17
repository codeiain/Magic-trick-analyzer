FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI service code
COPY . .

# Create non-root user for security
RUN groupadd -r aiuser && useradd -r -g aiuser aiuser

# Set proper permissions
RUN chown -R aiuser:aiuser /app

# Switch to non-root user
USER aiuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/app/models
ENV SENTENCE_TRANSFORMERS_HOME=/app/models/sentence-transformers

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; import redis; sys.exit(0)"

# Default command - RQ worker for AI queue
CMD ["python", "worker.py"]