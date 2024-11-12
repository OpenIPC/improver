#!/bin/bash

NGINX_CONFIG="/etc/nginx/sites-available/default"
BACKUP_CONFIG="/etc/nginx/sites-available/default.bak"
SUDOERS_FILE="/etc/sudoers"
ARCHIVE_NAME="improver_source.tar.gz"
DEST_DIR="/opt/improver"
CONFIG_DIR="/opt/improver/config"
SCRIPTS_DIR="/opt/improver/scripts"
LOG_DIR="/opt/improver/logs"
SYSTEMD_SERVICE="openipc"

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or use sudo."
    exit 1
fi

# Step 1: Create necessary directories
echo "Creating necessary directories..."
sudo mkdir -p "$DEST_DIR"
sudo mkdir -p "$SCRIPTS_DIR"
sudo mkdir -p "$LOG_DIR"

# Step 2: Install required packages
echo "Installing gunicorn..."
sudo pip install gunicorn

# Step 3: Extract the archive
if [ ! -f "$ARCHIVE_NAME" ]; then
    echo "Archive file $ARCHIVE_NAME not found."
    exit 1
fi

echo "Extracting $ARCHIVE_NAME to $DEST_DIR..."
sudo tar xzvf "$ARCHIVE_NAME" -C "$DEST_DIR"
sudo chown -R root:root "$DEST_DIR"
sudo chmod -R 755 "$DEST_DIR"

# Step 4: Configure Nginx
echo "Creating a backup of the Nginx configuration..."
cp "$NGINX_CONFIG" "$BACKUP_CONFIG"

if grep -q "location /improver/" "$NGINX_CONFIG"; then
    echo "Configuration block for /improver already exists. Updating..."
    sed -i '/location \/improver\//,/}/d' "$NGINX_CONFIG"
fi

echo "Updating Nginx configuration..."
# Insert the updated configuration block before the closing } of the server block
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

# Step 5: Add sudo permissions for www-data user
echo "Adding sudo permissions for www-data..."
if ! sudo grep -q "www-data.*systemctl" "$SUDOERS_FILE"; then
    echo "Adding sudo permissions for www-data..."
    echo "www-data ALL=(ALL) NOPASSWD: /bin/systemctl restart wifibroadcast.service, /bin/systemctl restart openipc, /bin/systemctl stop openipc, /bin/systemctl start openipc" | sudo tee -a "$SUDOERS_FILE"
else
    echo "www-data already has necessary sudo permissions."
fi

# Step 6: Verify the deployment
echo "Verifying the deployment..."
if [ -f "$DEST_DIR/run.sh" ]; then
    echo "Run script found. You can start the application with:"
    echo "sudo $DEST_DIR/run.sh"
else
    echo "Run script not found. Please check the extracted files."
fi

echo "chnging perms on $LOG_DIR"
sudo chown -R www-data:www-data "$LOG_DIR"
sudo chmod -R 755 "$LOG_DIR"


echo "Deployment completed successfully."
