#!/bin/bash

# activates prepared virtual environment 
. ./.venv/bin/activate

export PYTHONPATH="${PYTHONPATH}:/app"

# generates secret key for application
export FLASK_SECRET_KEY="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 256)"

# runs the app
gunicorn --worker-class gevent -w 1 --bind 0.0.0.0:5000 -c logging_config.py 'app:create_app()' --log-level "${LOGGING_LEVEL}"
