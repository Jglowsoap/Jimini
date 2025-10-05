#!/usr/bin/env python3
"""
Jimini Security Gateway - Replit Deployment Entry Point
=====================================================

This is the main entry point for running Jimini on Replit.
Handles environment setup and starts the FastAPI server.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Set default environment variables for Replit
def setup_replit_environment():
    """Configure environment variables for Replit deployment"""
    
    # Core Jimini settings
    os.environ.setdefault("JIMINI_API_KEY", "replit-secure-api-key-2025")
    os.environ.setdefault("JIMINI_RULES_PATH", "policy_rules.yaml")
    os.environ.setdefault("JIMINI_SHADOW", "0")  # Enforce mode by default
    
    # Paths and logging
    os.environ.setdefault("AUDIT_LOG_PATH", "logs/audit.jsonl")
    os.environ.setdefault("PYTHONPATH", str(Path.cwd()))
    
    # Replit-specific settings
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "5000")
    
    # Create required directories
    Path("logs").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)
    
    print("🔧 Environment configured for Replit deployment")

def start_jimini_gateway():
    """Start the Jimini Security Gateway server"""
    
    print("🛡️ Starting Jimini Security Gateway...")
    print("=" * 60)
    
    # Setup environment
    setup_replit_environment()
    
    # Import the FastAPI app
    try:
        from main import app
        print("✅ Jimini FastAPI app loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import Jimini app: {e}")
        sys.exit(1)
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    
    print(f"🌍 Server will start on: http://{host}:{port}")
    print(f"🔑 API Key: {os.getenv('JIMINI_API_KEY')[:10]}...")
    print(f"📋 Rules: {os.getenv('JIMINI_RULES_PATH')}")
    print(f"🛡️ Mode: {'ENFORCE' if os.getenv('JIMINI_SHADOW') == '0' else 'SHADOW'}")
    print("=" * 60)
    
    # Start the server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False  # Disable reload in production
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_jimini_gateway()