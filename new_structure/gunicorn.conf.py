#!/bin/bash
# Gunicorn configuration file for production deployment

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "twik_app"

# Daemon mode
daemon = False
pidfile = "logs/gunicorn.pid"

# User and group
user = "www-data"
group = "www-data"

# Temporary directory
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Environment variables
raw_env = [
    "FLASK_ENV=production",
]

# Preload application for better performance
preload_app = True

# Enable threading
threaded = False

# Worker memory management
worker_tmp_dir = "/dev/shm"

# Graceful timeout for worker shutdown
graceful_timeout = 30

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)