#!/bin/bash
# ⚠️ CAUTION: CRITICAL DEPLOYMENT FILE
# Before modifying, please read DEVOPS_GUIDE.md
# ─────────────────────────────────────────────────────────────────────────────
# Exit immediately if a command exits with a non-zero status
set -e

echo "🛑 Cleaning up any stale processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

# ── Cloud Init: Auto-Download Databases ──
# If you attach a Persistent Volume in Railway, mount it at: /app/data_volume
DATA_DIR="/app"
if [ -d "/app/data_volume" ]; then
    DATA_DIR="/app/data_volume"
    echo "💾 Persistent volume detected at $DATA_DIR"
fi

if [ ! -d "$DATA_DIR/chroma_db" ]; then
    echo "📦 Databases missing. Downloading from Cloud Storage..."
    wget -qO $DATA_DIR/data.zip "https://storage.googleapis.com/scholar-bucket-n/data.zip"
    
    echo "🗜️ Extracting databases..."
    unzip -qo $DATA_DIR/data.zip -d $DATA_DIR/
    
    # Auto-detect where chroma_db was extracted and move the contents up
    CHROMA_PATH=$(find "$DATA_DIR" -maxdepth 3 -type d -name "chroma_db" | head -n 1)
    if [ -n "$CHROMA_PATH" ] && [ "$CHROMA_PATH" != "$DATA_DIR/chroma_db" ]; then
        PARENT_DIR=$(dirname "$CHROMA_PATH")
        echo "🗂️ Found nested data at $PARENT_DIR, moving to root..."
        mv "$PARENT_DIR"/* "$DATA_DIR"/ 2>/dev/null || true
        rm -rf "$PARENT_DIR"
    fi
    rm -f $DATA_DIR/data.zip
    echo "✅ Databases successfully downloaded and extracted!"
else
    echo "✅ Databases already present in $DATA_DIR."
fi

# Create symlinks & initialize persistent volume from committed repo database if missing
if [ "$DATA_DIR" != "/app" ]; then
    ln -sf $DATA_DIR/chroma_db /app/chroma_db
    if [ ! -f "$DATA_DIR/edulytics_history.db" ] && [ -f "/app/edulytics_history.db" ]; then
        echo "💾 Initializing persistent volume with committed edulytics_history.db..."
        cp /app/edulytics_history.db "$DATA_DIR/edulytics_history.db"
    fi
    [ -f "$DATA_DIR/edulytics_history.db" ] && ln -sf $DATA_DIR/edulytics_history.db /app/edulytics_history.db
fi

# ── Auto-Migrate SQLite (Railway Volume) -> PostgreSQL ──
if [ -n "$DATABASE_URL" ] && [ -f "/app/scripts/wipe_and_migrate.py" ] && [ -f "$DATA_DIR/edulytics_history.db" ]; then
    echo "Running wipe-and-migrate: $DATA_DIR/edulytics_history.db -> PostgreSQL..."
    python3 /app/scripts/wipe_and_migrate.py
    echo "Migration done."
else
    echo "Skipping migration (DATABASE_URL not set, script missing, or no SQLite volume db found)."
fi
# ─────────────────────────────────────────

echo "Starting FastAPI backend on internal port 8000..."
# Start the backend in the background. It listens on localhost so it's not exposed externally.
# --h11-max-incomplete-event-size: raise from default 16KB to 100MB to handle large file uploads
uvicorn main:app --host 127.0.0.1 --port 8000 --h11-max-incomplete-event-size 104857600 &
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
