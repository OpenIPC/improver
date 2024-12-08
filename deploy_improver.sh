#!/bin/bash

NGINX_CONFIG="/etc/nginx/sites-available/default"
BACKUP_CONFIG="/etc/nginx/sites-available/default.bak"
SUDOERS_FILE="/etc/sudoers"
ARCHIVE_NAME="improver_source.tar.gz"
DEST_DIR="/opt/improver"
LOG_DIR="/opt/improver/logs"
VENV_DIR="$DEST_DIR/venv"
CONFIG_SRC="$DEST_DIR/config/py-config-gs.json"
CONFIG_DEST="/config/py-config-gs.json"
CONFIG_BACKUP="/config/py-config-gs.json.bak"

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or use sudo."
    exit 1
fi

# Step 1: Create necessary directories
echo "Creating necessary directories..."
mkdir -p "$DEST_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "/config"

# Step 2: Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv "$VENV_DIR"


apt install ffmpeg -y

# Step 3: Activate the virtual environment
echo "Activating the virtual environment..."
source "$VENV_DIR/bin/activate"

# Step 4: Install required packages in the virtual environment
echo "Installing required packages..."
pip install --upgrade pip
pip install gunicorn

# Step 5: Extract the archive
if [ ! -f "$ARCHIVE_NAME" ]; then
    echo "Archive file $ARCHIVE_NAME not found."
    exit 1
fi

echo "Extracting $ARCHIVE_NAME to $DEST_DIR..."
tar xzvf "$ARCHIVE_NAME" -C "$DEST_DIR"
chown -R root:root "$DEST_DIR"
chmod -R 755 "$DEST_DIR"

# Step 6: Install application dependencies from requirements.txt
if [ -f "$DEST_DIR/requirements.txt" ]; then
    echo "Installing application dependencies..."
    pip install -r "$DEST_DIR/requirements.txt"
else
    echo "requirements.txt not found in $DEST_DIR. Skipping dependency installation."
fi

# Step 7: Configure Nginx
echo "Creating a backup of the Nginx configuration..."
cp "$NGINX_CONFIG" "$BACKUP_CONFIG"

if grep -q "location /improver/" "$NGINX_CONFIG"; then
    echo "Configuration block for /improver already exists. Updating..."
    sed -i '/location \/improver\//,/}/d' "$NGINX_CONFIG"
fi

echo "Updating Nginx configuration..."
sed -i "/^}/i \\
    # Improver Flask App Configuration\\
    location /improver/ {\\
        proxy_pass http://127.0.0.1:5001;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_set_header SCRIPT_NAME /improver;\\
        proxy_buffering off;\\
        proxy_cache off;\\
    }\\
    \\n\\
    # Serve static files for the Flask app\\
    location /improver/static/ {\\
        alias /opt/improver/app/static/;\\
        expires 30d;\\
        add_header Cache-Control \"public, max-age=2592000\";\\
    }\\
    \\n\\
    " "$NGINX_CONFIG"

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Reloading Nginx..."
    systemctl reload nginx
else
    echo "Nginx configuration test failed. Restoring backup..."
    cp "$BACKUP_CONFIG" "$NGINX_CONFIG"
    nginx -t
    exit 1
fi

# Step 8: Add sudo permissions for www-data user
echo "Adding sudo permissions for www-data..."
if ! grep -q "www-data.*systemctl" "$SUDOERS_FILE"; then
    echo "Adding sudo permissions for www-data..."
    echo "www-data ALL=(ALL) NOPASSWD: /usr/bin/journalctl, /bin/systemctl restart wifibroadcast.service, /bin/systemctl restart openipc, /bin/rm /media/*" | tee -a "$SUDOERS_FILE"
else
    echo "www-data already has necessary sudo permissions."
fi

# Step 9: Copy the configuration file to /config
echo "Copying configuration file to /config..."
if [ -f "$CONFIG_DEST" ]; then
    echo "Configuration file already exists. Creating a backup at $CONFIG_BACKUP..."
    cp "$CONFIG_DEST" "$CONFIG_BACKUP"
fi
cp "$CONFIG_SRC" "$CONFIG_DEST"

# Step 10: Verify the deployment
echo "Verifying the deployment..."
if [ -f "$DEST_DIR/run.sh" ]; then
    echo "Run script found. You can start the application with:"
    echo "sudo $DEST_DIR/run.sh"
else
    echo "Run script not found. Please check the extracted files."
fi

echo "Changing permissions on $LOG_DIR"
chown -R www-data:www-data "$LOG_DIR"
chmod -R 755 "$LOG_DIR"

# Step 11: Provide instructions for creating and managing the systemd service
SERVICE_FILE_PATH="/etc/systemd/system/improver.service"

if [ ! -f "$SERVICE_FILE_PATH" ]; then
    echo "Creating systemd service file at $SERVICE_FILE_PATH..."

    cat <<EOL > $SERVICE_FILE_PATH
[Unit]
Description=Improver Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/improver
ExecStart=/opt/improver/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 app:create_app()
Restart=always
Environment="FLASK_ENV=production"
Environment="SETTINGS_FILE=/config/py-config-gs.json"

[Install]
WantedBy=multi-user.target
EOL

    echo "Reloading systemd to recognize the new service..."
    systemctl daemon-reload

    echo "Enabling the Improver service to start on boot..."
    systemctl enable improver.service

    echo "Starting the Improver service..."
    systemctl start improver.service

    echo "Service created and started successfully."
else
    echo "Service file $SERVICE_FILE_PATH already exists. Skipping creation."
fi

echo
echo "=============================================================="
echo "Deployment completed successfully."
echo
echo "To manage the Improver Flask service, use the following commands:"
echo " - Start the service:     sudo systemctl start improver.service"
echo " - Stop the service:      sudo systemctl stop improver.service"
echo " - Restart the service:   sudo systemctl restart improver.service"
echo " - Check status:          sudo systemctl status improver.service"
echo "=============================================================="
echo .
echo "OpenIPC kick ass!"
