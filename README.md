# Improver



Explanation of Makefile Targets
* build: Builds the Docker images as specified in docker-compose.yml.
* run: Builds (if needed) and runs the containers in the foreground.
* run-detached: Builds (if needed) and runs the containers in detached mode (background).
* stop: Stops all running containers defined in docker-compose.yml.
* logs: Shows real-time logs from all services for debugging.
* clean: Stops containers and removes all images, volumes, and orphaned containers associated with this Docker Compose setup.

## Usage
1. Build the Images:
```
make build
```
2. Run the Containers in Foreground:
```
make run
```
3. Run the Containers in Detached Mode:
```
make run-detached
```
4. Stop the Containers:
```
make stop
```
5. View Logs:
```
make logs
```
6. Clean Up Containers and Images:
```
make clean
```

With this Makefile, you can easily manage the lifecycle of your multi-container setup for testing the Flask app with Nginx in Docker. Let me know if you need more customization!


## Service file

Copy file to /etc/systemd/system/improver.service

### Enable and Start the Service

* Reload the systemd daemon to pick up the new service:
    ```
    sudo systemctl daemon-reload
    ```
* Enable the service to start on boot:
    ```
    sudo systemctl enable improver.service
    ```
* Start the service:
    ```
    sudo systemctl start improver.service
    ```
* Check the status of the service:
    ```
        sudo systemctl status improver.service
    ```
* Logs
    To view the logs for your Flask app service, use:
    ```
    journalctl -u improver.service -f
    ```
### Troubleshooting Tips
* If the service fails to start, check the logs using journalctl.
* Ensure the ExecStart path to Gunicorn (/usr/bin/gunicorn) is correct. You can verify it using:
    ```
    which gunicorn
    ```
* Make sure your Flask app works when you run it manually before setting it up as a systemd service:
    ```
    /usr/bin/gunicorn -w 4 -b 127.0.0.1:5001 "app:create_app()"
    ```