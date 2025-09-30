FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install the package
RUN pip install -e .

# Expose the port
EXPOSE 9000

# Set environment variables
ENV JIMINI_API_KEY=changeme
ENV JIMINI_RULES_PATH=policy_rules.yaml
ENV JIMINI_SHADOW=1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]