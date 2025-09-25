#!/usr/bin/env python3
# Gunicorn configuration file for Render deployment

# Server socket - Render uses PORT environment variable
import os
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
backlog = 2048

# Worker processes - Keep lightweight for Render
workers = 2
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 100

# Logging - Render handles log collection
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Preload application for better performance  
preload_app = True

# Environment variables for production
raw_env = [
    "FLASK_ENV=production",
]