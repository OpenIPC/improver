import logging
from flask import Flask, render_template, request, Response, redirect, url_for, send_from_directory, flash
import json
import os
import subprocess
from importlib.metadata import version


# read version for footer
#app_version = version('py-config-gs')
with open('version.txt', 'r') as f:
    app_version = f.read().strip()


# Configure logging
logging.basicConfig(level=logging.DEBUG,  # Set the log level to DEBUG
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Define the upload folder
GS_UPLOAD_FOLDER = '/etc'
ALLOWED_EXTENSIONS = {'key'}
app.config['GS_UPLOAD_FOLDER'] = GS_UPLOAD_FOLDER

if os.getenv('FLASK_ENV') == 'development':
    # In development, use the home folder settings file
    SETTINGS_FILE = os.path.expanduser('~/config/py-config-gs.json')
else:
    # In production, use the config folder
    SETTINGS_FILE = '/config/py-config-gs.json'

# Log the SETTINGS_FILE path
logger.info(f'Settings file path: {SETTINGS_FILE}')
logger.info(f'App version: {app_version}')

# Load settings.json
with open(SETTINGS_FILE, 'r') as f:
    settings = json.load(f)

# Access configuration files and video directory
config_files = settings['config_files']
VIDEO_DIR = os.path.expanduser(settings['VIDEO_DIR']) 
SERVER_PORT = settings['SERVER_PORT']

logger.debug(f'Loaded settings: {settings}')
logger.debug(f'VIDEO_DIR is set to: {VIDEO_DIR}')

def stream_journal():
    """Stream journalctl output in real-time."""
    process = subprocess.Popen(
        ['journalctl', '-f'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    while True:
        output = process.stdout.readline()
        if output:
            yield f"data: {output}\n\n"
        else:
            break

@app.route('/journal')
def journal():
    return render_template('journal.html', version=app_version)

@app.route('/stream')
def stream():
    return Response(stream_journal(), content_type='text/event-stream')

@app.route('/')
def home():
    # List of services that you want to control
    services = ['openipc',"wifibroadcast.service"]
    service_statuses = {}
    
    # Fetches the current status (enabled/disabled) for each service.
    for service in services:
        # Check if the service is enabled or disabled
        result = subprocess.run(['systemctl', 'is-enabled', service], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = result.stdout.decode('utf-8').strip()
        service_statuses[service] = status

    return render_template('home.html', config_files=config_files, version=app_version, services=service_statuses )

@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit(filename):
    file_path = next((item['path'] for item in config_files if item['name'] == filename), None)
    
    if request.method == 'POST':
        content = request.form['content']
        with open(file_path, 'w') as f:
            f.write(content)
        logger.debug(f'Updated configuration file: {filename}')
        return redirect(url_for('home'))

    with open(file_path, 'r') as f:
        content = f.read()
    
    return render_template('edit.html', filename=filename, content=content, version=app_version)

@app.route('/save/<filename>', methods=['POST'])
def save(filename):
    file_path = next((item['path'] for item in config_files if item['name'] == filename), None)
    content = request.form['content']
    with open(file_path, 'w') as f:
        f.write(content)
    logger.debug(f'Saved configuration file: {filename}')
    return redirect(url_for('home'))

@app.route('/videos')
def videos():
    video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(('.mp4', '.mkv', '.avi'))]
    logger.debug(f'VIDEO_DIR: {VIDEO_DIR}')
    logger.debug(f'Video files found: {video_files}')
    return render_template('videos.html', video_files=video_files, version=app_version)


@app.route('/play/<filename>')
def play(filename):
    try:
        # Ensure the file exists in the VIDEO_DIR and is served from there
        return send_from_directory(VIDEO_DIR, filename)
    except FileNotFoundError:
        logger.error(f'Video file not found: {filename}')
        return "File not found", 404

@app.route('/temperature')
def get_temperature():
    try:
        soc_temp = int(open('/sys/class/thermal/thermal_zone0/temp').read().strip()) / 1000.0  # Convert to °C
        gpu_temp = int(open('/sys/class/thermal/thermal_zone1/temp').read().strip()) / 1000.0  # Convert to °C
        soc_temp_f = (soc_temp * 9/5) + 32
        gpu_temp_f = (gpu_temp * 9/5) + 32
        
        return {
            'soc_temperature': f"{soc_temp:.1f}",
            'soc_temperature_f': f"{soc_temp_f:.1f}",
            'gpu_temperature': f"{gpu_temp:.1f}",
            'gpu_temperature_f': f"{gpu_temp_f:.1f}"
        }
        
    except Exception as e:
        logger.error(f'Error getting temperature: {e}')
        return {'error': str(e)}, 500

@app.route('/backup')
def backup():
    for item in config_files:
        file_path = item['path']
        backup_path = file_path + '.bak'
        with open(file_path, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
    logger.debug('Backup created for configuration files.')
    return redirect(url_for('home'))

@app.route('/run_command', methods=['POST'])
def run_command():
    selected_command = request.form.get('command')

    # Construct the first command based on the dropdown value
    cli_command = f"echo cli -s {selected_command} > /dev/udp/localhost/14550"
    logger.debug(f'Running command: {cli_command}')
    flash(f'Running command: {cli_command}', 'info')

    # Run the commands
    subprocess.run(cli_command, shell=True)
    subprocess.run("echo killall -1 majestic > /dev/udp/localhost/14550", shell=True)

    # Redirect back to the home page after the commands are run
    return redirect(url_for('home'))

@app.route('/service_action', methods=['POST'])
def service_action():
    service_name = request.form.get('service_name')
    action = request.form.get('action')

    if service_name and action:
        try:
            if action == 'enable':
                subprocess.run(['sudo', 'systemctl', 'enable', service_name], check=True)
                flash(f'Service {service_name} enabled successfully.', 'success')
            elif action == 'disable':
                subprocess.run(['sudo', 'systemctl', 'disable', service_name], check=True)
                flash(f'Service {service_name} disabled successfully.', 'success')
            elif action == 'restart':
                subprocess.run(['sudo', 'systemctl', 'restart', service_name], check=True)
                flash(f'Service {service_name} restarted successfully.', 'success')
            else:
                flash('Invalid action.', 'error')
        except subprocess.CalledProcessError as e:
            flash(f'Failed to {action} service {service_name}: {e}', 'error')

    return redirect(url_for('home'))

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config['GS_UPLOAD_FOLDER'], 'gs.key')
            file.save(file_path)  # Save the uploaded file
            flash('File successfully uploaded')
            return redirect(url_for('home'))
    return render_template('upload.html')  # A separate template for file upload

def main():
    app.run(host='0.0.0.0', port=SERVER_PORT)

if __name__ == '__main__':
    main()
