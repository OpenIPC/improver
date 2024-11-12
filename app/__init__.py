import logging
from flask import Flask, request
import json
import os
from importlib.metadata import version
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize logger
# Define the log file path
log_file = '/opt/improver/logs/improver_app.log'

# Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

logger = logging.getLogger(__name__)
logger.info("Flask app started and logging to /opt/improver/logs/improver_app.log")

def create_app():
    app = Flask(__name__)

    # Set the application root
    app.config['APPLICATION_ROOT'] = '/improver'

    # Apply ProxyFix to handle SCRIPT_NAME
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

    app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

    # Determine the settings file based on the environment
    if os.getenv('FLASK_ENV') == 'development':
        SETTINGS_FILE = os.path.expanduser('~/config/py-config-gs.json')
        app.config['GS_UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads_dev')
    else:
        SETTINGS_FILE = '/config/py-config-gs.json'
        app.config['GS_UPLOAD_FOLDER'] = '/etc/'

    # Ensure the upload folder exists
    os.makedirs(app.config['GS_UPLOAD_FOLDER'], exist_ok=True)
    logger.info(f"Upload folder set to: {app.config['GS_UPLOAD_FOLDER']}")

    # Load the app version
    try:
        app_version = version('improver')
    except Exception:
        app_version = 'unknown'
    app.config['APP_VERSION'] = app_version

    # Load settings.json
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
        app.config['CONFIG_FILES'] = settings['config_files']
        app.config['VIDEO_DIR'] = os.path.expanduser(settings['VIDEO_DIR'])
        app.config['SERVER_PORT'] = settings['SERVER_PORT']
        logger.debug(f'Loaded settings: {settings}')

    # Log SCRIPT_NAME for debugging
    # @app.before_request
    # def log_script_name():
    #     script_name = request.environ.get('SCRIPT_NAME', '')
    #     logger.debug(f"SCRIPT_NAME: {script_name}")
    #     logger.debug(f"PATH_INFO: {request.environ.get('PATH_INFO')}")

    # Import and register blueprints
    from .routes import main
    app.register_blueprint(main, url_prefix='/')

    return app