# gunicorn_config.py

# Bind to a socket file or an IP and port
bind = "0.0.0.0:5001"  # For a development setup; use a socket file in production, e.g., "unix:/tmp/simple_flask_app.sock"

# Number of worker processes (adjust based on your server’s CPU)
workers = 2  # Start with 2 workers; adjust based on your Radxa's resources

# Number of worker threads (in addition to worker processes)
threads = 2  # Additional threads to handle requests within each worker

# Log settings
loglevel = 'debug'
accesslog = "-"  # Log access information to stdout
errorlog = "-"   # Log error information to stdout

# Daemonize the Gunicorn process
# daemon = True  # Uncomment if you want Gunicorn to run in the background without using systemd

# Timeout settings
timeout = 60     # Increase if your app handles longer requests

# Security headers (optional)
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}
