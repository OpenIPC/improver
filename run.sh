#!/bin/bash

# Script to run the Flask app using Gunicorn
echo "Starting Flask app with Gunicorn..."
gunicorn -c gunicorn_config.py "app:create_app()"
