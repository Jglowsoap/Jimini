FROM python:3.11-slim

# Multi-stage build for optimized production image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=production

# Create app directory and user for security
WORKDIR /app
RUN groupadd -r jimini && useradd -r -g jimini -d /app -s /bin/bash jimini

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/
COPY jimini_cli/ ./jimini_cli/
COPY packs/ ./packs/
COPY templates/ ./templates/
COPY policy_rules.yaml .
COPY setup.py .
COPY pyproject.toml .
COPY README.md .
COPY LICENSE .

# Install the package
RUN pip install -e .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R jimini:jimini /app

# Switch to non-root user for security
USER jimini

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:9000/health || exit 1

# Expose the port
EXPOSE 9000

# Production environment variables
ENV JIMINI_API_KEY=changeme \
    JIMINI_RULES_PATH=policy_rules.yaml \
    JIMINI_SHADOW=1

# Run the application with production settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]