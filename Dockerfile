# ⚠️ CAUTION: CRITICAL DEPLOYMENT FILE
# Before modifying, please read DEVOPS_GUIDE.md
# ─────────────────────────────────────────────────────────────────────────────
# ── Stage 1: Build Next.js frontend ──────────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json* frontend/pnpm-lock.yaml* ./
RUN if [ -f pnpm-lock.yaml ]; then \
        npm install -g pnpm && pnpm install --no-frozen-lockfile; \
    else \
        npm ci; \
    fi

# Copy frontend source and build
COPY frontend/ ./
# We set API URL to empty so the client uses relative paths and Next.js proxies it to the backend
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build


# ── Stage 2: Final image with Python & Node.js ────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Install Node.js & WeasyPrint system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl build-essential libgomp1 lsof wget unzip \
        libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 \
        libffi-dev shared-mime-info \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

# Copy backend code
COPY server.py main.py build_vector_db.py extract_data.py start_railway.sh ./
COPY core/ ./core/
COPY ui/  ./ui/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Ensure startup script is executable
RUN chmod +x start_railway.sh

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend ./frontend

# Railway expects the container to listen on $PORT (defaults to 3000 if not set)
EXPOSE 3000

# Run the unified startup script
CMD ["./start_railway.sh"]
