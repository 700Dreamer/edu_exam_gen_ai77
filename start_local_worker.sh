#!/usr/bin/env bash

# Activate virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "============================================================"
echo "    STARTING EDULYTICS LOCAL DEV SERVER & BACKGROUND WORKER "
echo "============================================================"

# Start dedicated background worker in the background
python worker.py &
WORKER_PID=$!
echo "Background Worker launched with PID: $WORKER_PID"

# Start FastAPI server
echo "Starting FastAPI Server on http://0.0.0.0:8000..."
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Cleanup worker process on exit
trap "kill $WORKER_PID" EXIT
