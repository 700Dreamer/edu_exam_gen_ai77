#!/bin/bash

# Add local Node.js if present
if [ -d "$HOME/node-v20/bin" ]; then
    export PATH="$HOME/node-v20/bin:$PATH"
fi

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Kill anything on port 8000 (FastAPI) or 3000 (Next.js)
echo "[INFO] Cleaning up previous processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
pkill -f "uvicorn" 2>/dev/null

echo "[INFO] Starting Edulytics AI Engine (FastAPI)..."
if [ -f ".venv/bin/python" ]; then
    ./.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload --reload-dir core --reload-dir ui &
else
    python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload --reload-dir core --reload-dir ui &
fi

echo "[INFO] Starting Edulytics Studio Frontend (Next.js / webpack)..."
cd frontend && npm run dev -- -H 0.0.0.0 -p 3000

