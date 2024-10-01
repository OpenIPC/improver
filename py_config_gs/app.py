import logging
from flask import Flask, render_template, request, Response, redirect, url_for, send_from_directory
import json
import os
import subprocess

# Configure logging
logging.basicConfig(level=logging.DEBUG,  # Set the log level to DEBUG
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

#SETTINGS_FILE = "/Users/mcarr/config/settings.json"
#SETTINGS_FILE = "/config/settings.json"
if os.getenv('FLASK_ENV') == 'development':
    # In development, use the home folder settings file
    SETTINGS_FILE = os.path.expanduser('~/config/settings.json')
else:
    # In production, use the config folder
    SETTINGS_FILE = '/config/settings.json'

# Log the SETTINGS_FILE path
logger.info(f'Settings file path: {SETTINGS_FILE}')

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
    return render_template('journal.html')

@app.route('/stream')
def stream():
    return Response(stream_journal(), content_type='text/event-stream')

@app.route('/')
def home():
    return render_template('home.html', config_files=config_files)

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
    
    return render_template('edit.html', filename=filename, content=content)

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
    return render_template('videos.html', video_files=video_files)


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
            'soc_temperature': f"{soc_temp:.1f} °C",
            'soc_temperature_f': f"{soc_temp_f:.1f} °F",
            'gpu_temperature': f"{gpu_temp:.1f} °C",
            'gpu_temperature_f': f"{gpu_temp_f:.1f} °F"
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

def main():
    app.run(host='0.0.0.0', port=SERVER_PORT)

if __name__ == '__main__':
    main()
