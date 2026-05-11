#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "🛑 Cleaning up any stale processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

echo "🚀 Starting FastAPI backend on internal port 8000..."
# Start the backend in the background. It listens on localhost so it's not exposed externally.
uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "⏳ Waiting for backend to be ready..."
sleep 3

echo "🌐 Starting Next.js frontend on port ${PORT:-3000}..."
# The frontend runs in the foreground and receives all external traffic.
# It uses rewrites to proxy /api requests to the backend.
cd frontend
export PORT=${PORT:-3000}
npm run start &
FRONTEND_PID=$!

# Wait for any process to exit
wait -n

echo "A process exited unexpectedly."
exit 1
