#!/bin/bash
# Deploy to Render - Local testing script

echo "🚀 Preparing Hillview SMS for Render deployment..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Run this script from the project root."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local
.env.development
.env.production

# Instance folder
instance/

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Uploads
uploads/
static/uploads/

# Backups
*.backup
backups/
EOF
fi

# Copy environment template
echo "🔧 Setting up environment template..."
cp .env.render .env.example 2>/dev/null || echo "Environment template already exists"

# Generate secret keys
echo "🔐 Generate these secret keys for your Render environment variables:"
python3 -c "
import secrets
print('SECRET_KEY=' + secrets.token_hex(32))
print('WTF_CSRF_SECRET_KEY=' + secrets.token_hex(32))
"

# Test the app locally with production settings
echo "🧪 Testing production app locally..."
export FLASK_ENV=production
export SECRET_KEY="test-secret-key-for-local-testing"
export DATABASE_URL="sqlite:///test.db"
export ALLOW_IN_MEMORY_LIMITS=true

python3 -c "
from app import app
print('✅ Production app creates successfully!')
print('📍 App name:', app.config.get('APP_NAME', 'Unknown'))
print('🔒 Security validation:', app.config.get('SECURITY_VALIDATION_STRICT', False))
"

echo ""
echo "✅ Render preparation complete!"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Prepare for Render deployment'"
echo "   git remote add origin https://github.com/yourusername/hillview-sms.git"
echo "   git push -u origin main"
echo ""
echo "2. Follow the RENDER_DEPLOYMENT_GUIDE.md for full deployment steps"
echo ""
echo "3. Use these generated secret keys in your Render environment variables"