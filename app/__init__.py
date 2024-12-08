# app/__init__.py
import logging
from flask import Flask, request
import json
import os
from importlib.metadata import version
from werkzeug.middleware.proxy_fix import ProxyFix
from logging.handlers import TimedRotatingFileHandler

# Define the log file path
log_file = '/opt/improver/logs/improver_app.log'

# Create a TimedRotatingFileHandler to rotate the log file every day
handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

# Get the root logger and set the level
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Clear only if there are default handlers
if logger.hasHandlers():
    logger.handlers.clear()

# Re-add the TimedRotatingFileHandler
logger.addHandler(handler)

# Log a startup message to verify logging works

logger.info("Flask app started and logging to /opt/improver/logs/improver_app.log")



def get_app_version():
    # Assuming __file__ is within a sub-directory (e.g., /app), navigate to the project root
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    version_file = os.path.join(root_dir, 'VERSION')
    try:
        with open(version_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'unknown'
    

def format_duration(seconds):
    """Convert seconds to hh:mm:ss format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"

def create_app():
    app = Flask(__name__)

    # Load the app version
    app_version = get_app_version()
    app.config['APP_VERSION'] = app_version
    
    logger.debug(f"********************************************************************************")
    logger.debug(f"Starting app version: {app_version}")
    logger.debug(f"********************************************************************************")
    
    # Register the format_duration filter
    app.jinja_env.filters['format_duration'] = format_duration
    
    # Set the application root
    app.config['APPLICATION_ROOT'] = '/improver'

    # Apply ProxyFix to handle SCRIPT_NAME
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

    app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

    if os.getenv('FLASK_ENV') == 'development':
        SETTINGS_FILE = os.getenv('SETTINGS_FILE', '/config/py-config-gs-dev.json')
    else:
        SETTINGS_FILE = os.getenv('SETTINGS_FILE', '/config/py-config-gs.json')
     
    logger.info(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
    logger.info(f"SETTINGS_FILE: {os.getenv('SETTINGS_FILE')}")
    logger.info(f"Loading settings from: {SETTINGS_FILE}")
      
    with open(SETTINGS_FILE, 'r') as f:
        # Load settings.json
        settings = json.load(f)
        app.config['CONFIG_FILES'] = settings['config_files']
        app.config['VIDEO_DIR'] = os.path.expanduser(settings['VIDEO_DIR'])
        app.config['SERVER_PORT'] = settings['SERVER_PORT']
        logger.debug(f'Loaded settings: {settings}')

    
    # Determine the settings file based on the environment
    if os.getenv('FLASK_ENV') == 'development':
        #SETTINGS_FILE = os.path.expanduser('/config/py-config-gs.json')
        app.config['GS_UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads_dev')
    else:
        #SETTINGS_FILE = '/config/py-config-gs.json'
        app.config['GS_UPLOAD_FOLDER'] = '/etc/'

    # Ensure the upload folder exists
    os.makedirs(app.config['GS_UPLOAD_FOLDER'], exist_ok=True)
    logger.info(f"Upload folder set to: {app.config['GS_UPLOAD_FOLDER']}")

    
    # Log SCRIPT_NAME for debugging
    # @app.before_request
    # def log_script_name():
    #     script_name = request.environ.get('SCRIPT_NAME', '')
    #     logger.debug(f"SCRIPT_NAME: {script_name}")
    #     logger.debug(f"PATH_INFO: {request.environ.get('PATH_INFO')}")

    # Import and register blueprints
    # Determine the blueprint prefix based on the environment
    if os.getenv('FLASK_ENV') == 'development':
        url_prefix = '/improver'  # Development uses '/improver' for testing
    else:
        url_prefix = '/'  # Production uses root

    # Register blueprint with the correct prefix
    from .routes import main
    app.register_blueprint(main, url_prefix=url_prefix)
    
    
    return app