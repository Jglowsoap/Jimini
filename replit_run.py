#!/usr/bin/env python3
"""
🚀 REPLIT DEPLOYMENT SCRIPT FOR JIMINI
=====================================

Lightweight deployment script optimized for Replit's storage constraints.
Uses requirements_deploy.txt to avoid heavy ML dependencies.

Usage in Replit:
1. Set this as your main file in .replit config
2. Click "Run" button
3. Your Jimini API will be available at the Replit URL

Environment Variables (set in Replit Secrets):
- JIMINI_API_KEY: Your API key (default: changeme)
- OPENAI_API_KEY: OpenAI API key for LLM rules (optional)
- JIMINI_RULES_PATH: Path to rules file (default: policy_rules.yaml)
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_deployment_requirements():
    """Check if we're using the lightweight requirements."""
    deploy_reqs = Path("requirements_deploy.txt")
    full_reqs = Path("requirements.txt")
    
    print("🔍 Checking deployment configuration...")
    
    if deploy_reqs.exists():
        print("✅ Found requirements_deploy.txt (lightweight)")
        return "requirements_deploy.txt"
    elif full_reqs.exists():
        print("⚠️  Using requirements.txt (may include heavy packages)")
        return "requirements.txt"
    else:
        print("❌ No requirements file found")
        return None

def install_dependencies(requirements_file):
    """Install dependencies from the specified requirements file."""
    print(f"📦 Installing dependencies from {requirements_file}...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_environment():
    """Check and display environment configuration."""
    print("\n🔧 Environment Configuration:")
    
    api_key = os.getenv("JIMINI_API_KEY", "changeme")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    rules_path = os.getenv("JIMINI_RULES_PATH", "policy_rules.yaml")
    
    print(f"   API Key: {'SET' if api_key != 'changeme' else 'DEFAULT (changeme)'}")
    print(f"   OpenAI Key: {'SET' if openai_key else 'NOT SET (LLM rules disabled)'}")
    print(f"   Rules Path: {rules_path}")
    
    # Check if rules file exists
    if Path(rules_path).exists():
        print(f"   Rules File: ✅ Found {rules_path}")
    else:
        print(f"   Rules File: ⚠️  {rules_path} not found")

def start_server():
    """Start the Jimini FastAPI server."""
    print("\n🚀 Starting Jimini Policy Gateway...")
    
    # Set default environment variables for Replit
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8080")  # Replit default port
    os.environ.setdefault("JIMINI_API_KEY", "changeme")
    os.environ.setdefault("JIMINI_RULES_PATH", "policy_rules.yaml")
    
    host = os.environ["HOST"]
    port = os.environ["PORT"]
    
    print(f"   Server: {host}:{port}")
    print(f"   API Endpoint: https://{os.getenv('REPL_SLUG', 'your-repl')}.{os.getenv('REPL_OWNER', 'username')}.repl.co/v1/evaluate")
    print(f"   Health Check: https://{os.getenv('REPL_SLUG', 'your-repl')}.{os.getenv('REPL_OWNER', 'username')}.repl.co/health")
    print("\n" + "="*60)
    
    try:
        # Import and run the FastAPI app
        from app.main import app
        import uvicorn
        
        uvicorn.run(
            app,
            host=host,
            port=int(port),
            access_log=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        print("💡 Make sure dependencies are installed correctly")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

def main():
    """Main deployment function."""
    print("🛡️  JIMINI AI POLICY GATEWAY - REPLIT DEPLOYMENT")
    print("=" * 60)
    
    # Check requirements
    requirements_file = check_deployment_requirements()
    if not requirements_file:
        print("❌ No requirements file found. Cannot proceed.")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(requirements_file):
        print("❌ Dependency installation failed. Cannot proceed.")
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Give a moment for setup to complete
    print("\n⏳ Initializing server...")
    time.sleep(2)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()