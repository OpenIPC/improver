from flask import Flask, render_template, request, Response, redirect, url_for, send_from_directory
import json
import os
import subprocess

app = Flask(__name__)

SETTINGS_FILE = "/config/settings.json"

# Load settings.json
with open(SETTINGS_FILE, 'r') as f:
    settings = json.load(f)

# Access configuration files and video directory
config_files = settings['config_files']
VIDEO_DIR = settings['VIDEO_DIR']

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
    return redirect(url_for('home'))

@app.route('/videos')
def videos():
    video_files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(('.mp4', '.mkv', '.avi'))]
    return render_template('videos.html', video_files=video_files)

@app.route('/play/<filename>')
def play(filename):
    return send_from_directory(VIDEO_DIR, filename)

@app.route('/get_temperature')
def get_temperature():
    try:
        # Adjust the command to get temperatures in Celsius and Fahrenheit
        output = subprocess.check_output("cat /sys/class/thermal/thermal_zone*/temp", shell=True)
        temperatures = output.decode().strip().splitlines()
        soc_temp = int(temperatures[0]) / 1000  # Example for the SoC temperature
        gpu_temp = int(temperatures[1]) / 1000  # Example for the GPU temperature
        soc_temp_f = (soc_temp * 9/5) + 32
        gpu_temp_f = (gpu_temp * 9/5) + 32
        
        return {
            'soc_temp_c': f"{soc_temp:.1f} °C",
            'soc_temp_f': f"{soc_temp_f:.1f} °F",
            'gpu_temp_c': f"{gpu_temp:.1f} °C",
            'gpu_temp_f': f"{gpu_temp_f:.1f} °F"
        }
    except Exception as e:
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
    return redirect(url_for('home'))

def main():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
