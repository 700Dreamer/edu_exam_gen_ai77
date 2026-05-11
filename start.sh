#!/bin/bash

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Kill anything on port 8000 (FastAPI) or 3000 (Next.js)
echo "🛑 Cleaning up previous processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
pkill -f "streamlit run" 2>/dev/null

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

echo "🚀 Starting EduQuest AI Engine (FastAPI)..."
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 &

echo "🌐 Starting EduQuest Studio Frontend (Next.js)..."
cd frontend && npm run dev -- -H 0.0.0.0 -p 3000
