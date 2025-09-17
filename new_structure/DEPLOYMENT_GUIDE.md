# Production Deployment Guide

## Pre-Deployment Checklist

### ✅ Completed

- [x] Production configuration with MySQL database
- [x] Security hardening (CSRF, HSTS, security headers)
- [x] Rate limiting with Redis fallback
- [x] Comprehensive test suite (118/119 tests passing)
- [x] Alembic migrations setup
- [x] Environment variable template (.env.example)
- [x] WSGI application entry point
- [x] Logging configuration
- [x] Dependency management (requirements.txt)

### ⚠️ Security Concerns

- [ ] **CRITICAL**: Set a strong MySQL password and update `DATABASE_URL` (no defaults shipped)
- [ ] Generate strong SECRET_KEY for production
- [ ] Review and customize security headers
- [ ] Verify Redis security configuration

### 🔧 Infrastructure Requirements

- [ ] MySQL 5.7+ server running on localhost:3306
- [ ] Redis server for rate limiting and caching
- [ ] Python 3.8+ environment
- [ ] Web server (Nginx recommended as reverse proxy)
- [ ] Process manager (systemd service recommended)

## Deployment Steps

### 1. Environment Setup

```bash
# Create production environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create production database
mysql -u root -p
CREATE DATABASE hillview_demo001 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hillview_user'@'localhost' IDENTIFIED BY 'SECURE_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON hillview_demo001.* TO 'hillview_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Run migrations
alembic upgrade head
```

### 3. Environment Configuration

```bash
# Copy and customize environment file
cp .env.example .env
# Edit .env with production values:
# - DATABASE_URL with actual credentials
# - Strong SECRET_KEY (64+ random characters)
# - MAIL_* settings for email functionality
# - Security flags enabled
```

### 4. Production Server Deployment

#### Option A: Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Start application
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 300 wsgi:application
```

#### Option B: uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Start application
uwsgi --http :8000 --wsgi-file wsgi.py --callable application --processes 4
```

### 5. Nginx Reverse Proxy (Recommended)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (if serving directly)
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 6. Systemd Service (Linux)

```ini
[Unit]
Description=Twik Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/venv/bin
ExecStart=/path/to/your/app/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 4 wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## Health Monitoring

The application includes health check endpoints:

- `GET /health` - Basic health status
- `GET /health/ready` - Readiness probe (database connectivity)

## Security Hardening

### Production Security Features

- CSRF protection enabled
- HSTS headers in production
- Secure cookie flags
- XSS protection headers
- Content Security Policy
- Rate limiting (100 requests/hour by default)
- Password hashing with Werkzeug
- Optional data encryption with Fernet

### Additional Recommendations

1. **Firewall**: Restrict access to MySQL and Redis ports
2. **SSL/TLS**: Use HTTPS in production (Let's Encrypt recommended)
3. **Monitoring**: Set up application and server monitoring
4. **Backups**: Implement automated database backups
5. **Updates**: Establish security update process

## Performance Optimization

### Database

- Connection pooling configured (pool_size=20, max_overflow=0)
- MySQL optimized with utf8mb4 charset
- Indexes on key lookup columns

### Caching

- Redis for rate limiting and session storage
- Static file caching via web server

### Application

- Gunicorn with multiple workers
- Request timeout configuration
- Compression via reverse proxy

## Monitoring & Logging

### Log Files

- Application logs: `logs/twik.log` (rotating, 10MB max)
- Error tracking via Flask's built-in logging
- Request correlation IDs for debugging

### Key Metrics to Monitor

- Response times
- Error rates (4xx, 5xx)
- Database connection pool
- Redis connectivity
- Memory usage
- Disk space

## Backup Strategy

### Database Backups

```bash
# Daily backup script
mysqldump -u hillview_user -p hillview_demo001 > backup_$(date +%Y%m%d).sql

# Automated with cron
0 2 * * * /usr/local/bin/backup_db.sh
```

### Application Backups

- Configuration files
- Uploaded files (if any)
- Log files for troubleshooting

## Troubleshooting

### Common Issues

1. **Database Connection**: Check credentials and MySQL service
2. **Redis Connection**: Verify Redis service and configuration
3. **Import Errors**: Ensure virtual environment is activated
4. **Permission Errors**: Check file/directory permissions
5. **Port Conflicts**: Verify no other services on ports 8000/80

### Debug Mode

Never enable debug mode in production. Use logging and monitoring instead.

## Rollback Plan

1. Stop application service
2. Restore previous database backup
3. Revert to previous application version
4. Restart services
5. Verify functionality

---

**⚠️ CRITICAL SECURITY REMINDER**:

- Change default MySQL password before deployment
- Generate unique SECRET_KEY for production
- Review all security configurations
- Test thoroughly in staging environment first
