#!/bin/bash
# Replit Deployment Helper Script
# Prepares Jimini for deployment to Replit

echo "🚀 Preparing Jimini for Replit Deployment..."
echo "=" * 60

# Create deployment package
echo "📦 Creating deployment package..."

# Copy essential files
mkdir -p replit-deployment
cp -r app/ replit-deployment/
cp -r packs/ replit-deployment/
cp -r frontend/ replit-deployment/
cp replit_main.py replit-deployment/main.py
cp .replit replit-deployment/
cp replit.nix replit-deployment/
cp requirements.txt replit-deployment/

# Create logs directory
mkdir -p replit-deployment/logs

# Create config directory  
mkdir -p replit-deployment/config

echo "✅ Deployment package created in: replit-deployment/"
echo ""

echo "📋 Next Steps:"
echo "1. Create new Replit project"  
echo "2. Upload contents of 'replit-deployment/' folder"
echo "3. Set environment variables in Replit Secrets"
echo "4. Click Run to start Jimini Gateway"
echo ""

echo "🔗 Required Replit Secrets:"
echo "JIMINI_API_KEY=your-secure-api-key"
echo "JIMINI_RULES_PATH=packs/government/v1_fixed.yaml"  
echo "JIMINI_SHADOW=0"
echo ""

echo "🌍 Your Jimini Gateway will be available at:"
echo "https://your-repl-name.username.repl.co"
echo ""

echo "🎉 Deployment package ready!"