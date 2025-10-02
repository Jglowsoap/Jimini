#!/usr/bin/env python3
"""
Jimini Services Automation Script
==================================

This script manages the complete Jimini platform integration for React/Flask dashboards.
It handles:
- Starting the Jimini platform service with proper rules loading
- Starting the Flask integration gateway
- Health monitoring and verification
- Automated troubleshooting

Usage:
    python start_jimini_services.py [--rules RULES_PATH] [--shadow] [--port PORT]
"""

import os
import sys
import time
import json
import signal
import subprocess
import requests
import argparse
from pathlib import Path


class ServiceManager:
    """Manages Jimini platform and Flask gateway services"""
    
    def __init__(self, rules_path="policy_rules.yaml", shadow_mode=False, port=9000):
        self.rules_path = rules_path
        self.shadow_mode = shadow_mode
        self.port = port
        self.jimini_process = None
        self.flask_process = None
        self.repo_root = Path(__file__).parent.absolute()
        
    def check_rules_exist(self):
        """Verify rules file exists"""
        rules_file = self.repo_root / self.rules_path
        if not rules_file.exists():
            print(f"❌ Rules file not found: {rules_file}")
            print(f"📋 Available rule packs:")
            packs_dir = self.repo_root / "packs"
            if packs_dir.exists():
                for pack in packs_dir.iterdir():
                    if pack.is_dir():
                        print(f"   • packs/{pack.name}/v1.yaml")
            return False
        print(f"✅ Rules file found: {rules_file}")
        return True
    
    def start_jimini_platform(self):
        """Start the Jimini platform service"""
        print("\n🚀 Starting Jimini Platform Service...")
        print("=" * 70)
        
        # Set environment variables
        env = os.environ.copy()
        env["JIMINI_RULES_PATH"] = str(self.repo_root / self.rules_path)
        env["JIMINI_API_KEY"] = env.get("JIMINI_API_KEY", "changeme")
        env["JIMINI_SHADOW"] = "1" if self.shadow_mode else "0"
        env["PYTHONPATH"] = str(self.repo_root)
        
        print(f"📋 Configuration:")
        print(f"   • Rules: {env['JIMINI_RULES_PATH']}")
        print(f"   • API Key: {env['JIMINI_API_KEY']}")
        print(f"   • Shadow Mode: {env['JIMINI_SHADOW']}")
        print(f"   • Port: {self.port}")
        
        # Start uvicorn with Jimini app
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(self.port),
            "--log-level", "info"
        ]
        
        try:
            self.jimini_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(self.repo_root),
                text=True,
                bufsize=1
            )
            
            print(f"\n⏳ Waiting for Jimini to start on http://localhost:{self.port}...")
            
            # Wait for service to be ready
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get(f"http://localhost:{self.port}/health", timeout=2)
                    if response.status_code == 200:
                        health_data = response.json()
                        print(f"\n✅ Jimini Platform is RUNNING!")
                        print(f"   • Status: {health_data.get('status', 'unknown')}")
                        print(f"   • Version: {health_data.get('version', 'unknown')}")
                        print(f"   • Rules Loaded: {health_data.get('loaded_rules', 0)}")
                        print(f"   • Shadow Mode: {health_data.get('shadow_mode', False)}")
                        
                        if health_data.get('loaded_rules', 0) == 0:
                            print("\n⚠️  WARNING: 0 rules loaded!")
                            print("   This may indicate a problem with rule loading.")
                            print("   Check the logs above for errors.")
                        
                        return True
                except requests.exceptions.ConnectionError:
                    time.sleep(1)
                    if attempt % 5 == 0 and attempt > 0:
                        print(f"   Still waiting... ({attempt}/{max_attempts})")
            
            print(f"\n❌ Jimini failed to start after {max_attempts} seconds")
            return False
            
        except Exception as e:
            print(f"\n❌ Error starting Jimini: {e}")
            return False
    
    def start_flask_gateway(self):
        """Start the Flask integration gateway"""
        print("\n🌐 Starting Flask Integration Gateway...")
        print("=" * 70)
        
        flask_script = self.repo_root / "flask_jimini_platform_integration.py"
        if not flask_script.exists():
            print(f"⚠️  Flask integration script not found: {flask_script}")
            print("   Skipping Flask gateway startup.")
            return False
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.repo_root)
        
        try:
            self.flask_process = subprocess.Popen(
                [sys.executable, str(flask_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(self.repo_root),
                text=True,
                bufsize=1
            )
            
            print("⏳ Waiting for Flask gateway to start on http://localhost:5001...")
            
            # Wait for Flask to be ready
            max_attempts = 15
            for attempt in range(max_attempts):
                try:
                    response = requests.get("http://localhost:5001/api/jimini/health", timeout=2)
                    if response.status_code == 200:
                        health_data = response.json()
                        print(f"\n✅ Flask Gateway is RUNNING!")
                        print(f"   • Status: {health_data.get('status', 'unknown')}")
                        print(f"   • Jimini Connected: {health_data.get('jimini_connected', False)}")
                        print(f"   • Service Version: {health_data.get('version', 'unknown')}")
                        return True
                except requests.exceptions.ConnectionError:
                    time.sleep(1)
                    if attempt % 3 == 0 and attempt > 0:
                        print(f"   Still waiting... ({attempt}/{max_attempts})")
            
            print(f"\n⚠️  Flask gateway may not have started properly")
            return False
            
        except Exception as e:
            print(f"\n❌ Error starting Flask gateway: {e}")
            return False
    
    def test_integration(self):
        """Test the complete integration"""
        print("\n🧪 Testing Integration...")
        print("=" * 70)
        
        test_cases = [
            {
                "name": "Safe Text",
                "text": "Hello, this is a safe message",
                "expected": "allow"
            },
            {
                "name": "SSN Detection",
                "text": "My SSN is 123-45-6789",
                "expected": "block"
            },
            {
                "name": "Email Detection",
                "text": "Contact me at john.doe@example.com",
                "expected": "flag"
            }
        ]
        
        print("\n1️⃣  Testing Jimini Platform Directly:")
        for test in test_cases:
            try:
                response = requests.post(
                    f"http://localhost:{self.port}/v1/evaluate",
                    json={
                        "api_key": os.environ.get("JIMINI_API_KEY", "changeme"),
                        "agent_id": "test",
                        "text": test["text"]
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    decision = result.get("action", "unknown")
                    rule_ids = result.get("rule_ids", [])
                    
                    status = "✅" if decision == test["expected"] or self.shadow_mode else "⚠️"
                    print(f"   {status} {test['name']}: {decision.upper()}")
                    if rule_ids:
                        print(f"      Rules: {', '.join(rule_ids)}")
                else:
                    print(f"   ❌ {test['name']}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {test['name']}: {e}")
        
        # Test Flask gateway if available
        try:
            response = requests.get("http://localhost:5001/api/jimini/health", timeout=2)
            if response.status_code == 200:
                print(f"\n2️⃣  Testing Flask Gateway:")
                
                test_text = "Test message for gateway"
                try:
                    response = requests.post(
                        "http://localhost:5001/api/jimini/evaluate",
                        json={
                            "text": test_text,
                            "user_id": "test_user",
                            "endpoint": "/test"
                        },
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"   ✅ Gateway Evaluation: {result.get('decision', 'unknown')}")
                        print(f"   ✅ Audit Logged: {result.get('audit_logged', False)}")
                        print(f"   ✅ Enterprise Features: Active")
                    else:
                        print(f"   ❌ Gateway Test Failed: HTTP {response.status_code}")
                except Exception as e:
                    print(f"   ❌ Gateway Test Error: {e}")
        except:
            pass
        
        print("\n" + "=" * 70)
    
    def monitor_services(self):
        """Monitor running services and show logs"""
        print("\n📊 Services Running - Press Ctrl+C to stop")
        print("=" * 70)
        print("\n📡 Jimini Platform Endpoints:")
        print(f"   • Health: http://localhost:{self.port}/health")
        print(f"   • Evaluate: http://localhost:{self.port}/v1/evaluate")
        print(f"   • Metrics: http://localhost:{self.port}/v1/metrics")
        print(f"   • Audit: http://localhost:{self.port}/v1/audit/verify")
        
        if self.flask_process:
            print("\n📡 Flask Gateway Endpoints:")
            print("   • Health: http://localhost:5001/api/jimini/health")
            print("   • Evaluate: http://localhost:5001/api/jimini/evaluate")
            print("   • Metrics: http://localhost:5001/api/jimini/metrics")
            print("   • Government APIs: http://localhost:5001/api/government/*")
        
        print("\n📋 Logs (showing last few lines):")
        print("-" * 70)
        
        try:
            while True:
                # Show Jimini logs
                if self.jimini_process and self.jimini_process.stdout:
                    line = self.jimini_process.stdout.readline()
                    if line:
                        print(f"[Jimini] {line.strip()}")
                
                # Show Flask logs
                if self.flask_process and self.flask_process.stdout:
                    line = self.flask_process.stdout.readline()
                    if line:
                        print(f"[Flask] {line.strip()}")
                
                # Check if processes are still running
                if self.jimini_process.poll() is not None:
                    print("\n⚠️  Jimini process exited")
                    break
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down services...")
    
    def stop_services(self):
        """Stop all running services"""
        if self.jimini_process:
            print("   • Stopping Jimini Platform...")
            self.jimini_process.terminate()
            try:
                self.jimini_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.jimini_process.kill()
        
        if self.flask_process:
            print("   • Stopping Flask Gateway...")
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
        
        print("✅ All services stopped")
    
    def run(self):
        """Run the complete service management workflow"""
        try:
            print("\n" + "=" * 70)
            print("🏛️  JIMINI PLATFORM SERVICE MANAGER")
            print("=" * 70)
            
            # Check rules file
            if not self.check_rules_exist():
                return False
            
            # Start Jimini platform
            if not self.start_jimini_platform():
                return False
            
            # Start Flask gateway
            self.start_flask_gateway()
            
            # Test the integration
            self.test_integration()
            
            # Monitor services
            self.monitor_services()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            return False
        finally:
            self.stop_services()


def main():
    parser = argparse.ArgumentParser(
        description="Start and manage Jimini platform services for React/Flask integration"
    )
    parser.add_argument(
        "--rules",
        default="policy_rules.yaml",
        help="Path to rules file (default: policy_rules.yaml)"
    )
    parser.add_argument(
        "--shadow",
        action="store_true",
        help="Enable shadow mode (downgrades block/flag to allow)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="Port for Jimini service (default: 9000)"
    )
    
    args = parser.parse_args()
    
    manager = ServiceManager(
        rules_path=args.rules,
        shadow_mode=args.shadow,
        port=args.port
    )
    
    success = manager.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
