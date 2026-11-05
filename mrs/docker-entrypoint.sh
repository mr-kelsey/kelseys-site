#!/bin/sh
set -e

# The data/ volume may already exist from earlier deploys that ran as
# root; fix its ownership before dropping privileges so the app user can
# still write to it.
chown -R appuser:appuser /app/data

exec su -s /bin/sh -c '.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080' appuser
