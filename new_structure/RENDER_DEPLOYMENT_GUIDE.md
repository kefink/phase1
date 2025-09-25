# Render.com Deployment Guide for Hillview School Management System

## Prerequisites
- GitHub account with your code pushed
- Render account (free tier available)
- Basic understanding of environment variables

## Step 1: Prepare Your Repository

### 1.1 Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git branch -M main
git remote add origin https://github.com/yourusername/hillview-sms.git
git push -u origin main
```

### 1.2 Files Created for Render
- `app.py` - WSGI entry point
- `requirements-render.txt` - Production dependencies
- `gunicorn.conf.py` - Updated for Render
- `.env.render` - Environment template

## Step 2: Create Render Services

### 2.1 Create PostgreSQL Database
1. Log into [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "PostgreSQL"
3. Configure:
   - Name: `hillview-db`
   - Database: `hillview_sms`
   - User: `hillview_user`
   - Region: Choose closest to your users
   - Plan: Free tier for testing
4. Click "Create Database"
5. **Save the connection details** - you'll need them

### 2.2 Create Web Service
1. In Render Dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure the service:

**Basic Settings:**
- Name: `hillview-sms`
- Region: Same as database
- Branch: `main`
- Runtime: `Python 3`

**Build & Deploy:**
- Build Command: 
  ```
  pip install -r requirements-render.txt
  ```
- Start Command:
  ```
  gunicorn --config gunicorn.conf.py app:app
  ```

**Advanced Settings:**
- Plan: Free (for testing)
- Auto-Deploy: Yes

## Step 3: Configure Environment Variables

In your Render web service settings, add these environment variables:

### Required Variables:
```
FLASK_ENV=production
DATABASE_URL=[Your PostgreSQL URL from Step 2.1]
SECRET_KEY=[Generate a strong secret key]
WTF_CSRF_SECRET_KEY=[Generate another secret key]
```

### Optional Variables:
```
FORCE_HTTPS=true
ALLOW_IN_MEMORY_LIMITS=true
RATELIMIT_ENABLED=true
LOG_LEVEL=INFO
APP_NAME=Hillview School Management System
CSP_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
```

### Generate Secret Keys:
```python
import secrets
print("SECRET_KEY:", secrets.token_hex(32))
print("WTF_CSRF_SECRET_KEY:", secrets.token_hex(32))
```

## Step 4: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Start your application
3. Monitor the deployment logs for any issues

## Step 5: Initialize Database

Once deployed, you'll need to initialize the database:

1. Use Render's Shell feature or create a one-time job
2. Run database initialization:
```python
from app import app
from new_structure.utils.database_init import initialize_database_completely

with app.app_context():
    result = initialize_database_completely()
    print("Database initialized:", result)
```

## Step 6: Access Your Application

1. Your app will be available at: `https://your-app-name.onrender.com`
2. Default login credentials:
   - **Headteacher:** `headteacher` / `admin123`
   - **Class Teacher:** `kevin` / `kev123`
   - **Subject Teacher:** `telvo` / `telvo123`

## Step 7: Test Mobile Access

1. Open the URL on your phone
2. Test all login pages:
   - `/admin_login`
   - `/classteacher_login` 
   - `/teacher_login`
3. Verify logos and styling work correctly

## Troubleshooting

### Common Issues:

**Build Fails:**
- Check `requirements-render.txt` for version conflicts
- Ensure all dependencies are listed

**App Crashes on Start:**
- Check environment variables are set correctly
- Verify DATABASE_URL format
- Check logs for specific error messages

**Database Connection Issues:**
- Ensure DATABASE_URL is correctly formatted
- Check if database service is running
- Verify network connectivity between services

**Static Files Not Loading:**
- Ensure static files are in the correct directory
- Check CSP_POLICY allows necessary resources

### Debugging Commands:

Access shell in Render dashboard and run:
```bash
# Check environment variables
env | grep -E "(FLASK|DATABASE|SECRET)"

# Test database connection
python -c "from app import app; print('App created successfully')"

# Check logs
tail -f /opt/render/project/src/logs/app.log
```

## Step 8: Custom Domain (Optional)

1. In service settings, go to "Settings" → "Custom Domains"
2. Add your domain
3. Configure DNS records as shown
4. Render will automatically provision SSL certificates

## Security Notes

- Change all default passwords immediately
- Use strong, unique secret keys
- Enable all security headers
- Regularly update dependencies
- Monitor application logs

## Scaling for Production

When ready for real hosting:
1. Upgrade to paid Render plans
2. Add Redis service for session storage
3. Configure proper backup strategy
4. Set up monitoring and alerts
5. Configure CDN for static assets

## Support

- Render Docs: https://render.com/docs
- GitHub Issues: Create issues in your repository
- Flask Documentation: https://flask.palletsprojects.com/