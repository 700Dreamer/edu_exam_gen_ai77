# 🛠 EduQuest AI — DevOps & Deployment Guide

Welcome! This guide is intended for developers working on the EduQuest AI project. It outlines the infrastructure, Docker setup, and deployment workflow to ensure the production environment remains stable.

---

## 🏗 System Architecture

EduQuest AI consists of two main services:
1.  **Backend (FastAPI)**: Handles AI logic, vector search (ChromaDB), and data extraction.
2.  **Frontend (Next.js)**: The user interface.

In production (Railway), both services run inside a **single container** to simplify routing and reduce costs.

---

## 📂 Critical Files (Do Not Modify Without Caution)

The following files control the deployment and infrastructure. Changing them might break the build or deployment:

| File | Purpose | Why it's critical |
| :--- | :--- | :--- |
| `Dockerfile` | Multi-stage build for production | Controls how the unified image is built for Railway. |
| `Dockerfile.backend` | Backend-only build | Used for local development via Docker Compose. |
| `docker-compose.yml` | Local Dev Orchestration | Connects the backend and frontend locally. |
| `Procfile` | Railway Entry Point | Tells Railway to execute `start_railway.sh`. |
| `start_railway.sh` | Production Startup Script | Orchestrates process startup and database hydration. |
| `frontend/Dockerfile` | Frontend-only build | Used for local development via Docker Compose. |

---

## 🚀 Deployment Workflow (Railway)

We use **Railway** for hosting. The deployment is triggered automatically on push to the `main` branch.

### 1. Unified Startup (`start_railway.sh`)
When the container starts in production, it executes `start_railway.sh`. This script:
-   Checks for a persistent volume at `/app/data_volume`.
-   **Hydrates Databases**: If databases are missing, it downloads a `data.zip` from Cloud Storage and extracts it.
-   Starts the Backend in the background (`port 8000`).
-   Starts the Frontend in the foreground (`port $PORT`).

### 2. Environment Variables
Ensure these are set in the Railway dashboard:
-   `OPENAI_API_KEY`: Required for AI features.
-   `PORT`: Provided by Railway (defaults to 3000).
-   `NEXT_PUBLIC_API_URL`: Should usually be empty in production (proxied via Next.js).

---

## 💻 Local Development

### Using Docker (Recommended)
This is the closest environment to production.
```bash
# Start everything
docker compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Manual (No Docker)
If you prefer running services manually:
1.  **Backend**: `pip install -r requirements.txt && uvicorn main:app --reload`
2.  **Frontend**: `cd frontend && npm install && npm run dev`

---

## 💾 Data Persistence

### ChromaDB & SQLite
-   **Locally**: Data is persisted in named Docker volumes (`chroma_data`, `db_data`).
-   **Production**: Data should be stored in `/app/data_volume` if a Railway Volume is attached. If not, changes will be lost on restart unless you update the `data.zip` source.

---

## ⚠️ Important Rules for Developers

1.  **Don't kill the proxy**: The frontend proxies `/api` requests to the backend. If you change the backend port (8000), update `start_railway.sh` and the frontend proxy config.
2.  **Database Updates**: If you update the local `chroma_db` and want it in production, it must be zipped and uploaded to the Cloud Storage bucket referenced in `start_railway.sh`.
3.  **Dependency Management**: 
    -   Add backend deps to `requirements.txt`.
    -   Add frontend deps to `frontend/package.json`.
4.  **Test Before Pushing**: Always run `docker compose up --build` locally before pushing to `main` to ensure the container build doesn't fail.

---

*Questions? Contact the lead dev before touching the `.sh` or `Dockerfile` files.*
