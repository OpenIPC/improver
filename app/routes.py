from flask import Blueprint, render_template, request, redirect, jsonify,url_for, flash, Response, send_from_directory, current_app, abort
from importlib.metadata import version
import subprocess
import os
import platform
import logging
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

main = Blueprint('main', __name__)  # Define the Blueprint


try:
    app_version = version('improver')
except Exception:
    app_version = 'unknown'
    


@main.route('/health')
def health():
    return {"status": "ok"}, 200


# Add this function in routes.py
@main.route('/get_logs', methods=['GET'])
def get_logs():
    """Fetch the last 50 lines from journalctl."""
    try:
        if os.getenv("FLASK_ENV") != "development":
            # Run journalctl command to get the last 50 lines
            result = subprocess.run(
                ["journalctl", "-n", "50", "-u", "improver.service", "--no-pager"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                return jsonify({"logs": result.stdout.splitlines()})
            else:
                return jsonify({"error": result.stderr}), 500
        else:
            # Development mode: return a mock response
            return jsonify({"logs": ["Development mode: No logs available"]})
    except Exception as e:
        current_app.logger.error(f"Error fetching logs: {e}")
        return jsonify({"error": str(e)}), 500


@main.route('/journal')
def journal():
    return render_template('journal.html', version=app_version)


# Define the stream_journal function
def stream_journal():
    """Stream journalctl output in real-time."""
    if os.getenv("FLASK_ENV") != "development":
        process = subprocess.Popen(
            ["journalctl", "-n 100", "-f"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        while True:
            output = process.stdout.readline()
            if output:
                yield f"data: {output}\n\n"
            else:
                break
    else:
        logger.info("No data in DEVELOPMENT mode")
        yield "data: No data in DEVELOPMENT mode\n\n"
        
        
@main.route('/stream')
def stream():
    return Response(stream_journal(), content_type='text/event-stream')

@main.route('/')
def home():
    config_files = current_app.config['CONFIG_FILES']
    video_dir = current_app.config['VIDEO_DIR']
    app_version = current_app.config['APP_VERSION']

    services = ['openipc', 'wifibroadcast.service']
    service_statuses = {}

    # Check if running inside Docker
    is_docker = os.path.exists('/.dockerenv')

    # Check if the current system is Linux
    if is_docker:
        # Skip systemctl check inside Docker for each service
        for service in services:
            service_statuses[service] = 'unknown (Docker)'
    elif platform.system() == 'Linux':
        # Check service status using systemctl on Linux systems
        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-enabled', service],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                status = result.stdout.decode('utf-8').strip()
                service_statuses[service] = status
            except Exception as e:
                current_app.logger.error(f"Error checking service {service}: {e}")
                service_statuses[service] = 'error'
    else:
        # Skip systemctl checks on non-Linux systems
        service_statuses = {service: 'not applicable (non-Linux system)' for service in services}

    return render_template('home.html', config_files=config_files, version=app_version, services=service_statuses)


@main.route('/edit/<filename>', methods=['GET', 'POST'])
def edit(filename):
    try:
        # Get the config files from app configuration
        config_files = current_app.config['CONFIG_FILES']
        
        # Determine the file path based on the environment
        if platform.system() == 'Linux':
            file_path = next((item['path'] for item in config_files if item['name'] == filename), None)
        else:
            # Use a local path for development on macOS
            file_path = next((item['path'] for item in config_files if item['name'] == filename and '/etc/' not in item['path']), None)

        if not file_path or not os.path.exists(file_path):
            current_app.logger.error(f"Configuration file {filename} not found at {file_path}.")
            return abort(404, description="Configuration file not found")

        if request.method == 'POST':
            # Update the file content
            content = request.form['content']
            with open(file_path, 'w') as f:
                f.write(content)
            current_app.logger.debug(f'Updated configuration file: {filename}')
            return redirect(url_for('main.home'))

        # Read the file content for display
        with open(file_path, 'r') as f:
            content = f.read()

        return render_template('edit.html', filename=filename, content=content, version=current_app.config['APP_VERSION'])

    except Exception as e:
        current_app.logger.error(f'Error in edit route: {e}')
        return abort(500, description="Internal server error")
    

@main.route('/save/<filename>', methods=['POST'])
def save(filename):
    # Access CONFIG_FILES from app configuration
    config_files = current_app.config['CONFIG_FILES']
    file_path = next((item['path'] for item in config_files if item['name'] == filename), None)
    content = request.form['content']
    with open(file_path, 'w') as f:
        f.write(content)
    logger.debug(f'Saved configuration file: {filename}')
    return redirect(url_for('main.home'))

@main.route('/videos')
def videos():
    try:
        # Access VIDEO_DIR using current_app.config
        video_dir = current_app.config['VIDEO_DIR']
        video_files = [f for f in os.listdir(video_dir) if f.endswith(('.mp4', '.mkv', '.avi'))]

        current_app.logger.debug(f'VIDEO_DIR: {video_dir}')
        current_app.logger.debug(f'Video files found: {video_files}')
        
        return render_template('videos.html', video_files=video_files, version=current_app.config['APP_VERSION'])
    except Exception as e:
        current_app.logger.error(f'Error listing video files: {e}')
        return "Error listing video files", 500
    
    
@main.route('/play/<filename>')
def play(filename):
    try:
        # Retrieve VIDEO_DIR from app configuration
        video_dir = current_app.config.get('VIDEO_DIR')
        if not video_dir:
            current_app.logger.error("VIDEO_DIR is not set in app configuration.")
            return abort(500, description="Internal server error: VIDEO_DIR not configured")

        # Serve the file from VIDEO_DIR
        return send_from_directory(video_dir, filename)
    except FileNotFoundError:
        current_app.logger.error(f'Video file not found: {filename}')
        return abort(404, description="File not found")
    except Exception as e:
        current_app.logger.error(f'Error serving video file: {e}')
        return abort(500, description="Internal server error")


@main.route('/temperature')
def get_temperature():
    try:
        if platform.system() != 'Linux' or not os.path.exists('/sys/class/thermal'):
            return jsonify({
                'error': 'Temperature monitoring is only available on Linux systems.'
            }), 400
            
        soc_temp = int(open('/sys/class/thermal/thermal_zone0/temp').read().strip()) / 1000.0
        gpu_temp = int(open('/sys/class/thermal/thermal_zone1/temp').read().strip()) / 1000.0
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

@main.route('/backup')
def backup():
    for item in config_files:
        file_path = item['path']
        backup_path = file_path + '.bak'
        with open(file_path, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
    logger.debug('Backup created for configuration files.')
    return redirect(url_for('main.home'))

@main.route('/run_command', methods=['POST'])
def run_command():
    selected_command = request.form.get('command')

    cli_command = f"echo cli -s {selected_command} > /dev/udp/localhost/14550"
    logger.debug(f'Running command: {cli_command}')
    flash(f'Running command: {cli_command}', 'info')

    subprocess.run(cli_command, shell=True)
    subprocess.run("echo killall -1 majestic > /dev/udp/localhost/14550", shell=True)

    return redirect(url_for('main.home'))

@main.route('/service_action', methods=['POST'])
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

    return redirect(url_for('main.home'))

@main.route('/upload', methods=['GET', 'POST'])
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
            file_path = os.path.join(current_app.config['GS_UPLOAD_FOLDER'], 'gs.key')
            file.save(file_path)
            flash('File successfully uploaded')
            return redirect(url_for('main.home'))
    return render_template('upload.html')

# Function to check allowed file extensions
def allowed_file(filename):
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'key', 'cfg', 'conf', 'yaml'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions