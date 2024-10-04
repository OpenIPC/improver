# py-config.gs


I wanted an easy way to edit files and watch videos on the Radxa

### Dev Setup and Running
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "FLASK_ENV=development > .env"
```


### Screenshots
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


### Packaging
```bash
python setup.py sdist bdist_wheel
```

check dist/


###

Virtual Environment: If you are working in a virtual environment, ensure it is activated before running the pip install command:

```
# Install virtualenv if not installed
pip install virtualenv

# Create a virtual environment
virtualenv venv

# Activate the virtual environment
source venv/bin/activate  # For Linux/Mac

pip install .
or
python setup.py install


```
## config file
```
cp /usr/local/lib/python3.9/dist-packages/config/py-config-gs.json /config
cp /usr/local/lib/python3.9/dist-packages/etc/systemd/system/py-config-gs.service /etc/systemd/system/
sudo systemctl daemon-reload

sudo systemctl start py-config-gs

# Optional, you can always run the command above out in the field if you are worried about resource consumption
sudo systemctl enable py-config-gs
```




### Uninstall
```
pip uninstall py_config_gs-0.1-py3-none-any.whl
```
