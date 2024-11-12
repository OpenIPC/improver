import logging
import json
import os
import subprocess
from flask import (
    Flask,
    render_template,
    request,
    Response,
    redirect,
    url_for,
    send_from_directory,
    flash,
)

# Constants
ALLOWED_EXTENSIONS = {"key"}
GS_UPLOAD_FOLDER = "/etc"
VERSION_FILE = "version.txt"
DEV_SETTINGS_FILE = os.path.expanduser("~/config/py-config-gs.json")
PROD_SETTINGS_FILE = "/config/py-config-gs.json"

# Load version for footer
with open(VERSION_FILE, "r") as f:
    app_version = f.read().strip()

# Initialize global variables
settings = {}
config_files = []

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Set the settings file based on the environment
SETTINGS_FILE = (
    DEV_SETTINGS_FILE if os.getenv("FLASK_ENV") == "development" else PROD_SETTINGS_FILE
)
logger.info(f"Settings file path: {SETTINGS_FILE}")
logger.info(f"App version: {app_version}")


def load_config():
    """Load configuration settings from the settings file."""
    global settings, config_files
    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
        config_files = settings.get("config_files", [])
        logger.debug(f"Config files loaded: {config_files}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


load_config() 
VIDEO_DIR = os.path.expanduser(settings["VIDEO_DIR"])
SERVER_PORT = settings["SERVER_PORT"]

logger.debug(f"Loaded settings: {settings}")
logger.debug(f"VIDEO_DIR is set to: {VIDEO_DIR}")


def stream_journal():
    """Stream journalctl output in real-time."""
    if os.getenv("FLASK_ENV") != "development":
        process = subprocess.Popen(
            ["journalctl", "-f"],
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


@app.route("/journal")
def journal():
    return render_template("journal.html", version=app_version)


@app.route("/stream")
def stream():
    return Response(stream_journal(), content_type="text/event-stream")


@app.route("/")
def home():
    services = ["openipc", "wifibroadcast.service"]
    service_statuses = {}

    load_config()

    if os.getenv("FLASK_ENV") != "development":
        for service in services:
            result = subprocess.run(
                ["systemctl", "is-enabled", service],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            service_statuses[service] = result.stdout.decode("utf-8").strip()

    return render_template(
        "home.html",
        config_files=config_files,
        version=app_version,
        services=service_statuses,
    )


@app.route("/edit/<filename>", methods=["GET", "POST"])
def edit(filename):
    """Edit a configuration file."""
    load_config()
    logger.debug(f"Config files available: {config_files}")

    file_path = next(
        (item["path"] for item in config_files if item["name"] == filename), None
    )

    if file_path is None:
        logger.error(f"File path not found for: {filename}")
        flash(f"Configuration file not found: {filename}", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        content = request.form["content"]
        with open(file_path, "w") as f:
            f.write(content)
        logger.debug(f"Updated configuration file: {filename}")
        return redirect(url_for("home"))

    with open(file_path, "r") as f:
        content = f.read()

    return render_template(
        "edit.html", filename=filename, content=content, version=app_version
    )


@app.route("/videos")
def videos():
    
    global settings
    load_config() 
    VIDEO_DIR = os.path.expanduser(settings["VIDEO_DIR"])


    """List video files in the video directory."""
    video_files = [
        f for f in os.listdir(VIDEO_DIR) if f.endswith((".mp4", ".mkv", ".avi"))
    ]
    logger.debug(f"VIDEO_DIR: {VIDEO_DIR}")
    logger.debug(f"Video files found: {video_files}")
    flash(f"Loading from VIDEO_DIR: {VIDEO_DIR}", "info")
    return render_template("videos.html", video_files=video_files, version=app_version)


@app.route("/play/<filename>")
def play(filename):
    """Serve a video file."""
    try:
        return send_from_directory(VIDEO_DIR, filename)
    except FileNotFoundError:
        logger.error(f"Video file not found: {filename}")
        return "File not found", 404


@app.route("/temperature")
def get_temperature():
    """Get SOC and GPU temperatures."""
    try:
        if os.getenv("FLASK_ENV") != "development":
            soc_temp = (
                int(open("/sys/class/thermal/thermal_zone0/temp").read().strip())
                / 1000.0
            )
            gpu_temp = (
                int(open("/sys/class/thermal/thermal_zone1/temp").read().strip())
                / 1000.0
            )
        else:
            soc_temp = gpu_temp = 0

        return {
            "soc_temperature": f"{soc_temp:.1f}",
            "gpu_temperature": f"{gpu_temp:.1f}",
        }
    except Exception as e:
        logger.error(f"Error getting temperature: {e}")
        return {"error": str(e)}, 500


@app.route("/backup")
def backup():
    """Create backups of configuration files."""
    for item in config_files:
        file_path = item["path"]
        backup_path = f"{file_path}.bak"
        with open(file_path, "r") as f:
            content = f.read()
        with open(backup_path, "w") as f:
            f.write(content)
    logger.debug("Backup created for configuration files.")
    return redirect(url_for("home"))


@app.route("/run_command", methods=["POST"])
def run_command():
    """Run a selected command."""
    selected_command = request.form.get("command")
    cli_command = f"echo cli -s {selected_command} > /dev/udp/localhost/14550"
    logger.debug(f"Running command: {cli_command}")
    flash(f"Running command: {cli_command}", "info")

    subprocess.run(cli_command, shell=True)
    subprocess.run("echo killall -1 majestic > /dev/udp/localhost/14550", shell=True)

    return redirect(url_for("home"))


@app.route("/service_action", methods=["POST"])
def service_action():
    """Perform an action on a service."""
    service_name = request.form.get("service_name")
    action = request.form.get("action")

    if service_name and action:
        try:
            command = ["sudo", "systemctl", action, service_name]
            subprocess.run(command, check=True)
            flash(f"Service {service_name} {action}d successfully.", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Failed to {action} service {service_name}: {e}", "error")

    return redirect(url_for("home"))


def allowed_file(filename):
    """Check if the uploaded file is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    """Handle file upload."""
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            file_path = os.path.join(GS_UPLOAD_FOLDER, "gs.key")
            file.save(file_path)
            flash("File successfully uploaded")
            return redirect(url_for("home"))
    return render_template("upload.html")


@app.route("/settings", methods=["GET", "POST"])
def settings_view():
    """Manage application settings."""
    load_config()

    if request.method == "POST":
        try:
            current_config_files = settings.get("config_files", [])
            updated_config_files = current_config_files.copy()  # Start with the current files

            # Log all form data for debugging
            logger.debug(f"Form Data: {request.form}")

            # Handle deletion
            files_to_delete = request.form.getlist("delete_files")
            logger.debug(f"Files to delete: {files_to_delete}")
            if files_to_delete:
                updated_config_files = [
                    file for file in updated_config_files if file["name"] not in files_to_delete
                ]

            # Count how many config file inputs there are
            new_file_count = sum(1 for key in request.form.keys() if key.startswith("config_files[") and "][name]" in key)
            logger.debug(f"New config file count: {new_file_count}")

            for i in range(new_file_count):
                name = request.form.get(f'config_files[{i}][name]')
                path = request.form.get(f'config_files[{i}][path]')

                # Only add if both fields are filled, the name does not already exist, and it's not marked for deletion
                if name and path and name not in files_to_delete and not any(file['name'] == name for file in updated_config_files):
                    updated_config_files.append({"name": name, "path": path})
                    logger.debug(f"Added new config file: {name}, {path}")

            # Additional settings
            video_dir = request.form.get("VIDEO_DIR")
            server_port = request.form.get("SERVER_PORT")
            
            # Update the settings data
            settings_data = {
                "VIDEO_DIR": video_dir,
                "SERVER_PORT": server_port,
                "config_files": updated_config_files,
            }
            
            # Save the updated settings to the settings file
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings_data, f, indent=4)

            logger.debug("Settings saved successfully.")
            flash("Settings updated successfully.")
        except Exception as e:
            flash(f"Error saving settings: {e}", "error")

    return render_template("settings.html", settings=settings)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=SERVER_PORT)
