# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /opt/improver

# Install dependencies
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    curl \
    ; \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /opt/improver/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Create necessary directories
RUN mkdir /opt/improver/logs
RUN mkdir /config

# Copy config file
#COPY config/py-config-gs.json /config/py-config-gs.json

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variables for Flask
# Pointing to the app directory
ENV FLASK_APP=app
# Change to "development" or "production" if necessary
ENV FLASK_ENV=development  

# Run Gunicorn to serve the app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:create_app()"]
