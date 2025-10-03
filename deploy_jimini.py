#!/usr/bin/env python3
"""
🚀 JIMINI DEPLOYMENT & STARTUP SCRIPTS
=====================================

Production deployment configuration and startup automation for Jimini Gateway.
"""

import asyncio
import subprocess
import time
import os
import signal
import sys
from pathlib import Path
import json
import yaml
from datetime import datetime

# 🔧 **DEPLOYMENT CONFIGURATION**

class JiminiDeploymentConfig:
    """Configuration for Jimini deployment"""
    
    def __init__(self, environment="production"):
        self.environment = environment
        self.base_dir = Path(__file__).parent
        self.config = self._load_config()
    
    def _load_config(self):
        """Load environment-specific configuration"""
        configs = {
            "development": {
                "gateway": {
                    "host": "127.0.0.1",
                    "port": 8000,
                    "reload": True,
                    "log_level": "debug"
                },
                "database": {
                    "url": "sqlite:///./jimini_dev.db"
                },
                "redis": {
                    "url": "redis://localhost:6379/0"
                },
                "security": {
                    "allowed_origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                    "api_keys": ["dev-key-12345"]
                }
            },
            "production": {
                "gateway": {
                    "host": "0.0.0.0",
                    "port": 8000,
                    "reload": False,
                    "log_level": "info",
                    "workers": 4
                },
                "database": {
                    "url": "postgresql://jimini:password@db:5432/jimini_prod"
                },
                "redis": {
                    "url": "redis://redis:6379/0"
                },
                "security": {
                    "allowed_origins": ["https://dashboard.agency.gov"],
                    "api_keys_env": "JIMINI_API_KEYS"
                },
                "pki_systems": {
                    "ldap": {
                        "servers": ["ldap://ldap1.agency.gov", "ldap://ldap2.agency.gov"],
                        "bind_dn": "cn=jimini,ou=services,dc=agency,dc=gov",
                        "password_env": "LDAP_BIND_PASSWORD"
                    },
                    "entrust_idg": {
                        "api_url": "https://idg.agency.gov/api",
                        "api_key_env": "ENTRUST_API_KEY"
                    },
                    "ums": {
                        "api_url": "https://ums.agency.gov/api",
                        "auth_token_env": "UMS_AUTH_TOKEN"
                    },
                    "db2": {
                        "connection_string_env": "DB2_CONNECTION_STRING"
                    },
                    "servicenow": {
                        "instance": "agency.service-now.com",
                        "username_env": "SNOW_USERNAME", 
                        "password_env": "SNOW_PASSWORD"
                    }
                }
            }
        }
        
        return configs.get(self.environment, configs["production"])
    
    def get_env_vars(self):
        """Get required environment variables"""
        env_vars = {
            "JIMINI_ENVIRONMENT": self.environment,
            "JIMINI_HOST": self.config["gateway"]["host"],
            "JIMINI_PORT": str(self.config["gateway"]["port"]),
            "JIMINI_LOG_LEVEL": self.config["gateway"]["log_level"],
        }
        
        # Add production-specific env vars
        if self.environment == "production":
            env_vars.update({
                "JIMINI_WORKERS": str(self.config["gateway"]["workers"]),
                "DATABASE_URL": self.config["database"]["url"],
                "REDIS_URL": self.config["redis"]["url"],
            })
        
        return env_vars
    
    def create_docker_compose(self):
        """Create Docker Compose configuration"""
        compose_config = {
            "version": "3.8",
            "services": {
                "jimini-gateway": {
                    "build": {
                        "context": ".",
                        "dockerfile": "Dockerfile"
                    },
                    "ports": [f"{self.config['gateway']['port']}:8000"],
                    "environment": self.get_env_vars(),
                    "depends_on": ["redis", "db"] if self.environment == "production" else [],
                    "volumes": [
                        "./logs:/app/logs",
                        "./config:/app/config"
                    ],
                    "restart": "unless-stopped",
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                }
            }
        }
        
        # Add production services
        if self.environment == "production":
            compose_config["services"].update({
                "redis": {
                    "image": "redis:7-alpine",
                    "ports": ["6379:6379"],
                    "volumes": ["redis_data:/data"],
                    "restart": "unless-stopped"
                },
                "db": {
                    "image": "postgres:15-alpine",
                    "environment": {
                        "POSTGRES_DB": "jimini_prod",
                        "POSTGRES_USER": "jimini",
                        "POSTGRES_PASSWORD": "password"
                    },
                    "volumes": ["postgres_data:/var/lib/postgresql/data"],
                    "restart": "unless-stopped"
                },
                "nginx": {
                    "image": "nginx:alpine",
                    "ports": ["80:80", "443:443"],
                    "volumes": [
                        "./nginx.conf:/etc/nginx/nginx.conf",
                        "./ssl:/etc/ssl/certs"
                    ],
                    "depends_on": ["jimini-gateway"],
                    "restart": "unless-stopped"
                }
            })
            
            compose_config["volumes"] = {
                "redis_data": {},
                "postgres_data": {}
            }
        
        return compose_config

# 🐳 **DOCKERFILE GENERATOR**

def create_dockerfile():
    """Create optimized Dockerfile for Jimini Gateway"""
    dockerfile_content = """
# 🛡️ Jimini Gateway Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app user
RUN groupadd -r jimini && useradd -r -g jimini jimini

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs && chown -R jimini:jimini logs

# Switch to non-root user
USER jimini

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "jimini_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content.strip())
    
    print("✅ Dockerfile created")

# 🌐 **NGINX CONFIGURATION**

def create_nginx_config():
    """Create Nginx reverse proxy configuration"""
    nginx_config = """
events {
    worker_connections 1024;
}

http {
    upstream jimini_backend {
        server jimini-gateway:8000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        listen 80;
        server_name dashboard.agency.gov;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name dashboard.agency.gov;
        
        # SSL configuration
        ssl_certificate /etc/ssl/certs/server.crt;
        ssl_certificate_key /etc/ssl/certs/server.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
        
        # API proxy
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://jimini_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Health check
        location /health {
            proxy_pass http://jimini_backend;
            access_log off;
        }
        
        # Static files (dashboard)
        location / {
            root /var/www/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
    }
}
"""
    
    with open("nginx.conf", "w") as f:
        f.write(nginx_config.strip())
    
    print("✅ Nginx configuration created")

# 📋 **SYSTEMD SERVICE**

def create_systemd_service():
    """Create systemd service for Jimini Gateway"""
    service_content = """
[Unit]
Description=Jimini Policy Gateway
After=network.target

[Service]
Type=exec
User=jimini
Group=jimini
WorkingDirectory=/opt/jimini
Environment=PATH=/opt/jimini/venv/bin
ExecStart=/opt/jimini/venv/bin/python -m uvicorn jimini_gateway:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
    
    with open("jimini-gateway.service", "w") as f:
        f.write(service_content.strip())
    
    print("✅ Systemd service file created")

# 🚀 **DEPLOYMENT AUTOMATION**

class JiminiDeployment:
    """Automated deployment manager"""
    
    def __init__(self, environment="production"):
        self.environment = environment
        self.config = JiminiDeploymentConfig(environment)
        self.processes = {}
    
    def create_deployment_files(self):
        """Create all deployment configuration files"""
        print(f"🚀 Creating deployment files for {self.environment}...")
        
        # Create Docker Compose
        compose_config = self.config.create_docker_compose()
        with open("docker-compose.yml", "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        print("✅ docker-compose.yml created")
        
        # Create other files
        create_dockerfile()
        create_nginx_config()
        create_systemd_service()
        
        # Create environment file
        env_vars = self.config.get_env_vars()
        with open(f".env.{self.environment}", "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        print(f"✅ .env.{self.environment} created")
        
        # Create requirements.txt if it doesn't exist
        if not os.path.exists("requirements.txt"):
            requirements = [
                "fastapi==0.104.1",
                "uvicorn[standard]==0.24.0",
                "pydantic==2.5.0",
                "httpx==0.25.2",
                "redis==5.0.1",
                "psycopg2-binary==2.9.7",
                "python-multipart==0.0.6",
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4",
                "pytest==7.4.3",
                "pytest-asyncio==0.21.1"
            ]
            
            with open("requirements.txt", "w") as f:
                f.write("\n".join(requirements))
            print("✅ requirements.txt created")
    
    def start_development(self):
        """Start development environment"""
        print("🔧 Starting development environment...")
        
        try:
            # Start Jimini Gateway
            gateway_cmd = [
                "python", "-m", "uvicorn", "jimini_gateway:app",
                "--host", self.config.config["gateway"]["host"],
                "--port", str(self.config.config["gateway"]["port"]),
                "--reload",
                "--log-level", self.config.config["gateway"]["log_level"]
            ]
            
            self.processes["gateway"] = subprocess.Popen(
                gateway_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            print(f"✅ Jimini Gateway started on {self.config.config['gateway']['host']}:{self.config.config['gateway']['port']}")
            
            # Wait for startup
            time.sleep(3)
            
            # Test health endpoint
            import httpx
            try:
                response = httpx.get(f"http://localhost:{self.config.config['gateway']['port']}/health")
                if response.status_code == 200:
                    print("✅ Health check passed")
                else:
                    print(f"⚠️ Health check failed: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Health check error: {e}")
            
        except Exception as e:
            print(f"❌ Failed to start development environment: {e}")
            self.stop_all()
    
    def start_production(self):
        """Start production environment using Docker Compose"""
        print("🏭 Starting production environment...")
        
        try:
            # Build and start services
            subprocess.run(["docker-compose", "build"], check=True)
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            
            print("✅ Production services started")
            
            # Wait for services to be ready
            time.sleep(10)
            
            # Check service status
            result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
            print("📊 Service Status:")
            print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start production environment: {e}")
    
    def stop_all(self):
        """Stop all running processes"""
        print("🛑 Stopping all services...")
        
        # Stop development processes
        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"  Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        # Stop Docker Compose services
        if os.path.exists("docker-compose.yml"):
            try:
                subprocess.run(["docker-compose", "down"], check=True)
                print("✅ Docker services stopped")
            except subprocess.CalledProcessError:
                print("⚠️ Failed to stop Docker services")
    
    def monitor_logs(self):
        """Monitor service logs"""
        if self.environment == "development":
            # Monitor development logs
            if "gateway" in self.processes:
                process = self.processes["gateway"]
                print("📋 Monitoring Gateway Logs (Ctrl+C to stop):")
                print("-" * 50)
                
                try:
                    for line in process.stdout:
                        print(f"[Gateway] {line.strip()}")
                except KeyboardInterrupt:
                    print("\n🛑 Log monitoring stopped")
        else:
            # Monitor Docker logs
            try:
                subprocess.run(["docker-compose", "logs", "-f"], check=True)
            except KeyboardInterrupt:
                print("\n🛑 Log monitoring stopped")

# 🎮 **INTERACTIVE DEPLOYMENT MANAGER**

def main():
    """Interactive deployment management"""
    print("🛡️ Jimini Gateway Deployment Manager")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        sys.exit(1)
    
    while True:
        print("\nSelect deployment action:")
        print("1. 🔧 Create deployment files")
        print("2. 🚀 Start development environment")
        print("3. 🏭 Start production environment")
        print("4. 📋 Monitor logs")
        print("5. 🛑 Stop all services")
        print("6. 🧪 Run integration tests")
        print("7. ❌ Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == "1":
            env = input("Environment (development/production) [production]: ").strip() or "production"
            deployment = JiminiDeployment(env)
            deployment.create_deployment_files()
            
        elif choice == "2":
            deployment = JiminiDeployment("development")
            deployment.create_deployment_files()
            deployment.start_development()
            
            print("\n🎯 Development environment is running!")
            print("  • Gateway: http://localhost:8000")
            print("  • Health: http://localhost:8000/health")
            print("  • API Docs: http://localhost:8000/docs")
            
            input("Press Enter to stop...")
            deployment.stop_all()
            
        elif choice == "3":
            deployment = JiminiDeployment("production")
            deployment.create_deployment_files()
            deployment.start_production()
            
        elif choice == "4":
            env = input("Environment (development/production) [development]: ").strip() or "development"
            deployment = JiminiDeployment(env)
            deployment.monitor_logs()
            
        elif choice == "5":
            env = input("Environment (development/production) [development]: ").strip() or "development"
            deployment = JiminiDeployment(env)
            deployment.stop_all()
            
        elif choice == "6":
            print("🧪 Running integration tests...")
            try:
                subprocess.run(["python", "test_jimini_integration.py"], check=True)
            except subprocess.CalledProcessError:
                print("❌ Tests failed")
            except FileNotFoundError:
                print("❌ Test file not found")
                
        elif choice == "7":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down...")
        deployment = JiminiDeployment()
        deployment.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run main interface
    main()