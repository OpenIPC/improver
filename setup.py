import os
from setuptools import setup, find_packages

# Define the relative path for the settings file and systemd service file
settings_file = 'py_config_gs/settings.json'  # Ensure this is a relative path
service_file = 'py_config_gs/systemd/py-config-gs.service'  # Ensure this is a relative path

setup(
    name='py-config-gs',
    use_scm_version=True,  # This tells setuptools to use scm for version
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    include_package_data=True,  # Include files from MANIFEST.in
    install_requires=[
        'Flask',
        'blinker==1.8.2',
        'click==8.1.7',
        'flask==3.0.3',
        'importlib-metadata==8.5.0',
        'itsdangerous==2.2.0',
        'jinja2==3.1.4',
        'MarkupSafe==2.1.5',
        'werkzeug==3.0.4',
        'zipp==3.20.2',
        'setuptools-scm==8.1.0'
    ],
    entry_points={
        'console_scripts': [
            'py-config-gs=py_config_gs.app:main',  # Adjust this if needed
        ],
    },
    # data_files is not recommended for package data; prefer package_data or MANIFEST.in
    data_files=[
        ('/config', ['py_config_gs/settings.json']),
        ('/etc/systemd/system', ['systemd/py-config-gs.service']),  # Systemd service file
    ],
)
