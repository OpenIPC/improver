#!/bin/bash

# Script to package the Flask app for deployment to Radxa

APP_NAME="improver"
ARCHIVE_NAME="${APP_NAME}_source.tar.gz"
VERSION=$(date +%Y%m%d%H%M)

# Step 1: Create a compressed tarball of the source code
echo "Packaging source code..."
tar czvf $ARCHIVE_NAME \
    app/ \
    requirements.txt \
    gunicorn_config.py \
    run.sh \
    update_nginx.sh \
    improver.service \
    py-config-gs.json


# Step 2: Display the packaged file
echo "Packaged application into: $ARCHIVE_NAME"

# Step 3: Instructions for deployment
echo "To deploy on Radxa, transfer $ARCHIVE_NAME and update_nginx.sh using SCP:"
echo "scp $ARCHIVE_NAME update_nginx.sh deploy_improver.sh root@radxa:/tmp/"
