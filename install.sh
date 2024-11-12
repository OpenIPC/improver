#!/bin/bash

# Define paths
SERVICE_FILE="py_config_gs/systemd/py-config-gs.service"
TARGET_SERVICE_PATH="/etc/systemd/system/py-config-gs.service"
CONFIG_FILE="py_config_gs/settings.json"
TARGET_CONFIG_PATH="/etc/py-config-gs.json"

# Copy the systemd service file to the system location
echo "Installing systemd service file..."
sudo cp "$SERVICE_FILE" "$TARGET_SERVICE_PATH"

# Reload systemd and enable the service
echo "Reloading systemd and enabling py-config-gs service..."
sudo systemctl daemon-reload
sudo systemctl enable py-config-gs.service

# Copy the configuration file to /etc
echo "Installing configuration file..."
sudo cp "$CONFIG_FILE" "$TARGET_CONFIG_PATH"

# Set proper permissions for configuration file
sudo chmod 644 "$TARGET_CONFIG_PATH"

echo "Installation complete."
