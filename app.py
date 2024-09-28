from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add your secret key for session management

# Define the directory for video files and configuration files
VIDEO_DIR = '/home/radxa/Videos'
CONFIG_DIR = '/etc'  # Adjust this as necessary
SETTINGS_FILE = 'settings.json'  # Path to your settings.json

# Load the configuration files from settings.json
def load_settings():
    with open('settings.json') as f:
        data = json.load(f)
        return data["config_files"]  # Return the list of config files

@app.route('/')
def home():
    config_files = load_settings()  # Load config files from settings.json
    return render_template('home.html', config_files=config_files)

@app.route('/videos')
def videos():
    # Scan the video directory for files
    video_files = []
    try:
        for filename in os.listdir(VIDEO_DIR):
            if filename.endswith(('.mp4', '.h265', '.mkv')):  # Video extensions to look for
                video_files.append({
                    'name': filename,
                    'path': os.path.join(VIDEO_DIR, filename)
                })
    except Exception as e:
        flash(f"Error loading videos: {e}", 'danger')

    return render_template('videos.html', videos=video_files)

@app.route('/play/<filename>')
def play(filename):
    # Serve the video file
    video_path = os.path.join(VIDEO_DIR, filename)
    if os.path.exists(video_path):
        return render_template('play.html', video_path=video_path)
    else:
        flash(f"Video {filename} not found!", 'danger')
        return redirect(url_for('videos'))

@app.route('/video/<filename>')
def video(filename):
    video_path = os.path.join(VIDEO_DIR, filename)
    if os.path.exists(video_path):
        return send_file(video_path)  # Serve the video file
    else:
        flash(f"Video {filename} not found!", 'danger')
        return redirect(url_for('videos'))

# Route to edit a configuration file
@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit(filename):
    # Find the config file based on the filename
    config_files = load_settings()
    config_file = next((cfg for cfg in config_files if cfg['name'] == filename), None)
    
    if request.method == 'POST':
        # Save the updated content back to the file
        content = request.form['content']
        with open(config_file['path'], 'w') as f:
            f.write(content)
        return redirect(url_for('home'))  # Redirect back to home after saving

    # Load the current content of the file
    if config_file:
        with open(config_file['path']) as f:
            content = f.read()
        return render_template('edit.html', filename=filename, content=content)
    else:
        return redirect(url_for('home'))  # Redirect if file not found

@app.route('/settings')
def settings():
    config_files = load_settings()
    return render_template('settings.html', config_files=config_files)

# Optionally, add a route to save settings if needed
@app.route('/save_settings', methods=['POST'])
def save_settings():
    # Logic for saving settings can go here
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Run the app

