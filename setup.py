from setuptools import setup, find_packages

setup(
    name='py-config-gs',
    use_scm_version=True,  # This tells setuptools to use scm for version
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'blinker==1.8.2',
        'click==8.1.7',
        'importlib-metadata==8.5.0; python_version<"3.8"',
        'itsdangerous==2.2.0',
        'jinja2==3.1.4',
        'MarkupSafe==2.1.5',
        'werkzeug==3.0.4',
        'zipp==3.20.2',
        'setuptools-scm==8.1.0',
        'gunicorn>=20.0',
    ],
    entry_points={
        'console_scripts': [
            'py-config-gs=py_config_gs.app:main',  # Entry point to start the application
        ],
    },
    package_data={
        'py_config_gs': ['settings.json', 'systemd/py-config-gs.service'],  # Include these files in the package
    },
    options={
        "bdist_wheel": {
            "universal": False,  # Set to False if only targeting Python 3
        },
    },
)
