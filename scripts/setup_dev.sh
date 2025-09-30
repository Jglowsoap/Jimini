#!/bin/bash

set -e  # Exit on error

echo "Setting up Jimini development environment..."

# Make all scripts executable
find scripts -name "*.py" -o -name "*.sh" | xargs chmod +x

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -e .

# Install additional dev dependencies if not present
pip install ruff pytest pytest-asyncio aiohttp

# Create necessary directories
mkdir -p logs

echo "✅ Setup complete! You can now run:"
echo "  • ruff check . (for linting)"
echo "  • PYTHONPATH=\$PWD pytest -q (to run tests)"
echo "  • uvicorn app.main:app --host 0.0.0.0 --port 9000 (to start the server)"
