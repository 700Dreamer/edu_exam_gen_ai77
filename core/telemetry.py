import asyncio
import json

# List of active queues for SSE clients
_listeners = []

def add_listener(q: asyncio.Queue):
    _listeners.append(q)

def remove_listener(q: asyncio.Queue):
    if q in _listeners:
        _listeners.remove(q)

def emit_progress(title: str, detail: str = ""):
    """Broadcasts a progress event to all connected SSE clients."""
    msg = json.dumps({"title": title, "detail": detail})
    for q in _listeners:
        try:
            q.put_nowait(msg)
        except Exception:
            pass
