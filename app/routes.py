# app/routes.py
from flask import Blueprint, render_template, request, redirect, jsonify,url_for, flash, Response, send_from_directory, current_app, abort
from importlib.metadata import version
from werkzeug.utils import secure_filename
import subprocess
import os
import platform
import logging
import time

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)  # Define the Blueprint


@main.route('/health')
def health():
    return {"status": "ok"}, 200


# Add this function in routes.py
@main.route('/get_logs', methods=['GET'])
def get_logs():
    """Fetch the last 50 lines from journalctl."""
    
    logger.debug("Fetching logs...")
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
    app_version = current_app.config.get('APP_VERSION', 'unknown')
    
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

    return render_template('home.html', config_files=config_files, version=app_version, is_docker=is_docker, services=service_statuses)


@main.route('/edit/<filename>', methods=['GET', 'POST'])
def edit(filename):
    try:
        # Get the config files from app configuration
        config_files = current_app.config['CONFIG_FILES']
        
        # Determine the file path based on the environment
        running_env = os.getenv('FLASK_ENV', 'production')
        
        if running_env == 'development':
            # Use a local path for development
            file_path = next((item['path'] for item in config_files if item['name'] == filename and '/etc/' not in item['path']), None)
        else:
            # Use standard path in production
            file_path = next((item['path'] for item in config_files if item['name'] == filename), None)

        # If file is not found, set content to None and log the error
        if not file_path or not os.path.exists(file_path):
            current_app.logger.error(f"Configuration file {filename} not found at {file_path}.")
            content = None
        else:
            # If a POST request, update the file content
            if request.method == 'POST':
                content = request.form['content']
                with open(file_path, 'w') as f:
                    f.write(content)
                current_app.logger.debug(f'Updated configuration file: {filename}')
                return redirect(url_for('main.home'))

            # Otherwise, read the file content for display
            current_app.logger.debug(f'Reading configuration file: {file_path}')
            with open(file_path, 'r') as f:
                content = f.read()

        # Render the template, passing content (None if file not found)
        return render_template('edit.html', filename=filename, content=content, version=current_app.config['APP_VERSION'])

    except Exception as e:
        current_app.logger.error(f'Error in edit route: {e}')
        return render_template('edit.html', filename=filename, content=None, version=current_app.config['APP_VERSION'])

    

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

from datetime import datetime

@main.route('/videos')
def videos():
    try:
        # Access VIDEO_DIR using current_app.config
        video_dir = current_app.config['VIDEO_DIR']
        video_files = []

        # Get list of video files with their sizes and creation dates
        for f in os.listdir(video_dir):
            if f.endswith(('.mp4', '.mkv', '.avi')):
                file_path = os.path.join(video_dir, f)
                file_size = os.path.getsize(file_path)
                file_stat = os.stat(file_path)
                
                # Get the creation time of the file (or last metadata change on some systems)
                created_date = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                
                video_files.append({
                    'name': f,
                    'size': file_size,
                    'created_date': created_date
                })

        current_app.logger.debug(f'VIDEO_DIR: {video_dir}')
        current_app.logger.debug(f'Video files found: {video_files}')
        
        return render_template(
            'videos.html',
            video_files=video_files,
            version=current_app.config['APP_VERSION']
        )
    except Exception as e:
        current_app.logger.error(f'Error listing video files: {e}')
        return "Error listing video files", 500

    
@main.route('/delete_video', methods=['POST'])
def delete_video():
    try:
        # Get the video directory from app configuration
        video_dir = current_app.config.get('VIDEO_DIR')

        # Check if VIDEO_DIR is properly set
        if not video_dir:
            current_app.logger.error('VIDEO_DIR is not set in the app configuration.')
            return jsonify({'error': 'Internal server error: VIDEO_DIR not configured'}), 500

        # Get the filename from the request JSON
        request_data = request.get_json()
        filename = request_data.get('filename')

        # Validate filename
        if not filename:
            current_app.logger.error('No filename provided in the request.')
            return jsonify({'error': 'No filename provided'}), 400

        # Construct the full path of the file to be deleted
        file_path = os.path.join(video_dir, filename)

        # Check if the file exists
        if not os.path.exists(file_path):
            current_app.logger.error(f'File not found: {file_path}')
            return jsonify({'error': 'File not found'}), 404

        # Delete the file
        # os.remove(file_path)
        command = ['sudo', 'rm', file_path]
        subprocess.run(command, check=True)
        
        current_app.logger.info(f'File deleted: {file_path}')
        
        flash('File deleted successfully', 'success')

        return jsonify({'message': 'File deleted successfully'}), 200

    except Exception as e:
        current_app.logger.error(f'Error deleting video: {e}')
        return jsonify({'error': 'Internal server error'}), 500



def generate_file_chunks(file_path):
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            yield chunk

@main.route('/play/<filename>')
def play(filename):
    try:
        filename = secure_filename(filename)
        video_dir = current_app.config.get('VIDEO_DIR')
        file_path = os.path.join(video_dir, filename)
        current_app.logger.debug(f"Serving video file: {file_path}")
        return send_from_directory(video_dir, filename, mimetype='video/mp4')
    except FileNotFoundError:
        current_app.logger.error(f"Video file not found: {filename}")
        return abort(404, description="File not found")
    except Exception as e:
        current_app.logger.error(f"Error serving video file: {e}")
        return abort(500, description="Internal server error")
    
        
# @main.route('/play/<filename>')
# def play(filename):
#     try:
#         filename = secure_filename(filename)
#         video_dir = current_app.config.get('VIDEO_DIR')
#         if not video_dir:
#             return abort(500, description="VIDEO_DIR not configured")
        
#         file_path = os.path.join(video_dir, filename)
#         if not os.path.exists(file_path):
#             return abort(404, description="File not found")
        
#         return Response(
#             generate_file_chunks(file_path),
#             content_type="video/mp4",
#         )
#     except Exception as e:
#         current_app.logger.error(f"Error serving video file: {e}")
#         return abort(500, description="Internal server error")

@main.route('/video/<filename>')
def show_video(filename):
    return render_template('play.html', filename=filename)

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
            # Determine if running inside Docker
            is_docker = os.path.exists('/.dockerenv')

            # Use 'sudo' if not running inside Docker
            if is_docker:
                command_prefix = []
            else:
                command_prefix = ['sudo']

            # Prepare the command based on the action
            if action == 'enable':
                command = command_prefix + ['systemctl', 'enable', service_name]
                subprocess.run(command, check=True)
                flash(f'Service {service_name} enabled successfully.', 'success')
            elif action == 'disable':
                command = command_prefix + ['systemctl', 'disable', service_name]
                subprocess.run(command, check=True)
                flash(f'Service {service_name} disabled successfully.', 'success')
            elif action == 'restart':
                command = command_prefix + ['systemctl', 'restart', service_name]
                subprocess.run(command, check=True)
                flash(f'Service {service_name} restarted successfully.', 'success')
            else:
                flash('Invalid action.', 'error')
        except subprocess.CalledProcessError as e:
            current_app.logger.error(f'Failed to {action} service {service_name}: {e}')
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