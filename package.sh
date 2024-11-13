#!/bin/bash

# Script to package the Flask app for deployment to Radxa

APP_NAME="improver"
ARCHIVE_NAME="${APP_NAME}_source.tar.gz"
VERSION_FILE="VERSION"

GIT_VERSION=$(git describe --tags --always)
echo "Packaging version $GIT_VERSION"
echo $GIT_VERSION > $VERSION_FILE

# Step 1: Create a compressed tarball of the source code
echo "Packaging source code..."
tar czvf $ARCHIVE_NAME \
    app/ \
    requirements.txt \
    gunicorn_config.py \
    run.sh \
    update_nginx.sh \
    improver.service \
    config/


# Step 2: Display the packaged file
echo "Packaged application into: $ARCHIVE_NAME"

# Step 3: Instructions for deployment
echo "To deploy on Radxa, transfer $ARCHIVE_NAME and update_nginx.sh using SCP:"
echo "scp $ARCHIVE_NAME deploy_improver.sh root@radxa:/tmp/"
