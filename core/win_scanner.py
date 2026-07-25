"""
Edulytics Windows Scanner — WIA (Windows Image Acquisition) Module

Detects and drives scanners on Windows via the native WIA COM API
using pywin32 and Pillow. WIA ships with every Windows installation (7+), so
this module works on any Windows PC without additional driver software.

Prerequisites:
    pip install pywin32 pillow
"""

import os
import sys
import base64
import time
from typing import List, Dict, Any

_IS_WINDOWS = sys.platform == "win32"
PIPE_NAME = r'\\.\pipe\ScannerAgentPipe'

def is_wia_available() -> bool:
    """Check whether Windows Scanner Agent IPC is available."""
    return _IS_WINDOWS


def detect_devices() -> List[Dict[str, str]]:
    """Enumerate scanners via Agent (Mocked for now)."""
    if not _IS_WINDOWS:
        return []
    
    return [{
        "device_id": "ScannerAgent_001",
        "vendor": "Scanner",
        "model": "Agent IPC Scanner",
        "device_type": "Persistent Windows Agent",
    }]


def scan_page(
    device_id: str,
    dpi: int = 150,
    mode: str = "Color",
    format: str = "jpeg",
) -> Dict[str, Any]:
    """
    Execute a scan by communicating with the persistent C# Scanner Agent via Named Pipes.
    """
    if not _IS_WINDOWS:
        return {
            "status": "error",
            "message": "Scanner Agent requires Windows.",
        }

    images_b64 = []
    total_bytes = 0

    try:
        # Connect to the Named Pipe
        # We use a standard file open in Python to communicate with the Windows Named Pipe
        with open(PIPE_NAME, 'r+b') as pipe:
            # Send SCAN command
            pipe.write(b"SCAN\n")
            pipe.flush()

            while True:
                line = pipe.readline().decode('utf-8').strip()
                if not line:
                    break
                
                if line == "STATUS:STARTING":
                    print("Agent is starting hardware...")
                elif line.startswith("IMAGE:"):
                    # Extract the length of the binary image data
                    img_size = int(line.split(":")[1])
                    print(f"Receiving image of size {img_size} bytes...")
                    
                    # Read the exact amount of binary data
                    img_bytes = pipe.read(img_size)
                    total_bytes += len(img_bytes)
                    
                    # Base64 encode for the frontend
                    images_b64.append(base64.b64encode(img_bytes).decode("ascii"))
                    
                elif line == "STATUS:DONE":
                    print("Agent finished scanning.")
                    break
                elif line == "STATUS:UNKNOWN_COMMAND":
                    return {
                        "status": "error",
                        "message": "Agent did not recognize the SCAN command.",
                    }

        if not images_b64:
            return {
                "status": "error",
                "message": "Agent returned no images.",
            }

        return {
            "status": "success",
            "image_base64_list": images_b64,
            "image_base64": images_b64[0],
            "format": "jpeg",
            "dpi": dpi,
            "mode": mode,
            "device_id": device_id,
            "size_bytes": total_bytes,
            "filename": f"scan_{dpi}dpi.jpg",
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Scanner Agent is not running. Please ensure the Scanner Agent service is started.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"IPC Communication error: {str(e)}",
        }
