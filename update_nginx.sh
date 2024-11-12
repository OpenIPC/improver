#!/bin/bash

NGINX_CONFIG="/etc/nginx/sites-available/default"
BACKUP_CONFIG="/etc/nginx/sites-available/default.bak"

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or use sudo."
    exit 1
fi

# Check if the Nginx configuration file exists
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "Nginx configuration file not found: $NGINX_CONFIG"
    exit 1
fi

# Backup the existing Nginx configuration
echo "Creating a backup of the Nginx configuration..."
cp "$NGINX_CONFIG" "$BACKUP_CONFIG"

# Check if the configuration block for /improver/ is already present
if grep -q "location /improver/" "$NGINX_CONFIG"; then
    echo "Configuration block for /improver already exists. Updating..."
    sed -i '/location \/improver\//,/}/d' "$NGINX_CONFIG"
else
    echo "Adding configuration block for /improver..."
fi

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
    # Custom error page for server errors\\
    error_page 500 502 503 504 /50x.html;\\
    location = /50x.html {\\
        root /usr/share/nginx/html;\\
    }" "$NGINX_CONFIG"

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Reloading Nginx..."
    systemctl reload nginx
    echo "Nginx reloaded successfully."
else
    echo "Nginx configuration test failed. Restoring the backup..."
    cp "$BACKUP_CONFIG" "$NGINX_CONFIG"
    nginx -t
    exit 1
fi

echo "Nginx configuration updated successfully."
