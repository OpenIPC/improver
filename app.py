# app.py (root of your project, outside the app/ folder)
from app import create_app
import logging

app = create_app()

if __name__ == '__main__':
    app.run()
