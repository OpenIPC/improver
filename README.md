# Improver

*Temporarily put on hold since the work being done to put this in Betaflight Menus and to work on Avalonia Configurator ([OpenIPC-Config](https://github.com/mikecarr/OpenIPC-Config)) MultiPlatform Configurator.*


OpenIPC Improver for setting up FPV and URLLC devices

I wanted an easy way to edit files and watch videos on the Radxa

## Screenshots
Home Page
![alt text](images/home.png)

Editor
![alt text](images/editor.png)

Video file selector
![alt text](images/v_select.png)

Player
![alt text](images/v_player.png)

Journalctl -f
![alt text](images/journal.png)

## Installation

* Download latest release, 2 files
    * improver_source.tar.gz
    * deploy_improver.sh

* transfer files to Radxa
    * ```scp improver_source.tar.gz deploy_improver.sh root@10.0.1.215:/tmp/```
    * ```chmod +x deploy_improver.sh```
    * ```./deploy_improver.sh```


## Network Setup 
This requires either a Wifi or Lan connection

* Ethernet
    * Navigate to http://radxaip:8080/improver
* Wifi (Hotspot setup)
    ```
    # run 'ip a' to determine which interface is your wifi address
    
    nmcli connection add type wifi ifname wlan1 con-name "MyWiFiNetwork" ssid "MyWiFiNetwork"
    
    nmcli connection modify "MyWiFiNetwork" wifi-sec.key-mgmt wpa-psk

    nmcli connection modify "MyWiFiNetwork" wifi-sec.psk "MyPassword123"

    nmcli connection up "MyWiFiNetwork"

    # You will also need to setup a static IP on the same subnet as your mobile device
    
    nmcli connection modify "MyWiFiNetwork" ipv4.addresses 192.168.1.100/24

    nmcli connection modify "MyWiFiNetwork" ipv4.gateway 192.168.1.1
    
    nmcli connection modify "MyWiFiNetwork" ipv4.dns 8.8.8.8,8.8.4.4

    nmcli connection modify "MyWiFiNetwork" ipv4.method manual
    ```

    then navigate to http://mobile-ip:8080/improver/


## Dev Setup and Running

* Use Docker, it will bring up the flask and nginx apps
    ```
    docker-compose up --build  
    ```
    Navigate to http://localhost/improver


## Screenshots
Home Page
![alt text](images/home.png)

![alt text](images/home_bottom.png)

Editor
![alt text](images/editor.png)

Video file selector
![alt text](images/v_select.png)

Player
![alt text](images/v_player.png)

Journalctl -f
![alt text](images/journal.png)


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

To manage the Improver Flask service, use the following commands:
 - Start the service:     ```sudo systemctl start improver.service```
 - Stop the service:      ```sudo systemctl stop improver.service```
 - Restart the service:   ```sudo systemctl restart improver.service```
 - Check status:          ```sudo systemctl status improver.service```

==============================================================


### Enable and Start the Service
    
<br><br>
<hr>
<h3>This is an open project, so you can help, too.</h3>

We try to collect, organize and share as much information regarding different aspects of the project as we can. But sometimes we overlook things that seem obvious to us, developers, but are not so obvious to end-users, people who are less familiar with nuts and bolts behind the scene. That is why we set up this wiki and let anyone having a GitHub account to make additions and improvements to the knowledgebase. Read [How to contribute](https://github.com/OpenIPC/wiki/blob/master/en/contribute.md).