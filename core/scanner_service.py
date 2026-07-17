"""
Edulytics Scanner Service — SANE CLI Wrapper

Detects flatbed scanners connected to the host machine and drives them
via the `scanimage` command-line tool (part of sane-backends).

Install prerequisites:
    macOS:   brew install sane-backends
    Ubuntu:  sudo apt-get install sane-utils
    Fedora:  sudo dnf install sane-backends

The module degrades gracefully when SANE is not installed — it simply
returns an empty device list and a descriptive error on scan attempts.
"""

import subprocess
import shutil
import re
import tempfile
import os
import time
import threading
from dataclasses import dataclass, asdict
from typing import List, Optional
import base64


@dataclass
class ScannerDevice:
    """Represents a detected SANE scanner device."""
    device_id: str      # e.g. "plustek:libusb:001:005"
    vendor: str          # e.g. "Plustek"
    model: str           # e.g. "OpticSlim 2610+"
    device_type: str     # e.g. "flatbed scanner"

    @property
    def display_name(self) -> str:
        return f"{self.vendor} {self.model}" if self.vendor else self.model or self.device_id


def is_sane_installed() -> bool:
    """Check whether the `scanimage` binary is on PATH."""
    return shutil.which("scanimage") is not None


def detect_scanners() -> List[ScannerDevice]:
    """
    Detect connected scanners by running `scanimage -L`.

    Returns an empty list if SANE is not installed or no scanners are found.

    Example `scanimage -L` output:
        device `plustek:libusb:001:005' is a Plustek OpticSlim 2610 flatbed scanner
        device `hp:libusb:001:003' is a Hewlett-Packard Scanjet 4850 flatbed scanner
    """
    if not is_sane_installed():
        return []

    try:
        result = subprocess.run(
            ["scanimage", "-L"],
            capture_output=True,
            text=True,
            timeout=15,  # scanner detection can be slow
        )
        output = result.stdout + result.stderr  # some SANE builds write to stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    devices: List[ScannerDevice] = []
    # Parse lines like: device `plustek:libusb:001:005' is a Plustek OpticSlim 2610 flatbed scanner
    pattern = re.compile(
        r"device\s+[`']([^'`]+)[`']\s+is\s+a\s+(.+)",
        re.IGNORECASE,
    )
    for line in output.splitlines():
        m = pattern.search(line)
        if m:
            device_id = m.group(1).strip()
            description = m.group(2).strip()

            # Try to split "Vendor Model type scanner"
            parts = description.rsplit(" ", 2)  # e.g. ["Plustek OpticSlim 2610", "flatbed", "scanner"]
            if len(parts) >= 3 and parts[-1].lower() == "scanner":
                name_part = parts[0]
                device_type = f"{parts[-2]} {parts[-1]}"
            elif len(parts) >= 2 and parts[-1].lower() == "scanner":
                name_part = parts[0]
                device_type = parts[-1]
            else:
                name_part = description
                device_type = "scanner"

            # Split vendor from model
            name_tokens = name_part.split(" ", 1)
            vendor = name_tokens[0] if len(name_tokens) > 1 else ""
            model = name_tokens[1] if len(name_tokens) > 1 else name_tokens[0]

            devices.append(ScannerDevice(
                device_id=device_id,
                vendor=vendor,
                model=model,
                device_type=device_type,
            ))

    return devices


_cached_devices: List[ScannerDevice] = []
_last_detection_time: float = 0.0
_detection_lock = threading.Lock()

def detect_scanners_cached(force_refresh: bool = False) -> List[ScannerDevice]:
    """
    Returns detected scanners immediately using a cache to avoid blocking requests.
    Refreshes in the background if the cache is older than 30 seconds.
    """
    global _cached_devices, _last_detection_time
    
    now = time.time()
    if force_refresh or not _cached_devices or (now - _last_detection_time > 30.0):
        if _cached_devices and not force_refresh:
            # Trigger background refresh
            def refresh_bg():
                if _detection_lock.acquire(blocking=False):
                    try:
                        global _cached_devices, _last_detection_time
                        devices = detect_scanners()
                        _cached_devices = devices
                        _last_detection_time = time.time()
                    finally:
                        _detection_lock.release()
            
            t = threading.Thread(target=refresh_bg)
            t.daemon = True
            t.start()
            return _cached_devices
        
        # Block and fetch on initial call or force refresh
        with _detection_lock:
            if force_refresh or not _cached_devices or (time.time() - _last_detection_time > 30.0):
                devices = detect_scanners()
                _cached_devices = devices
                _last_detection_time = time.time()
                
    return _cached_devices


def scan_page(
    device_id: str,
    dpi: int = 300,
    mode: str = "Color",
    format: str = "png",
) -> dict:
    """
    Execute a scan using `scanimage` and return the result.

    Args:
        device_id: SANE device identifier (from detect_scanners)
        dpi: Resolution in DPI (150, 300, 600)
        mode: Color mode — "Color", "Gray", or "Lineart"
        format: Output format — "png" or "tiff"

    Returns:
        dict with keys:
            status: "success" or "error"
            image_base64: base64-encoded image data (on success)
            message: error description (on failure)
            filename: suggested filename
    """
    if not is_sane_installed():
        return {
            "status": "error",
            "message": "SANE is not installed. Run: brew install sane-backends",
        }

    # Auto-fallback to the only connected scanner if requested device is missing/offline
    active_device_id = device_id
    detected = detect_scanners()
    detected_ids = [d.device_id for d in detected]
    if device_id not in detected_ids and len(detected) == 1:
        active_device_id = detected[0].device_id

    # Validate mode
    mode_map = {
        "color": "Color",
        "gray": "Gray",
        "grayscale": "Gray",
        "bw": "Lineart",
        "lineart": "Lineart",
        "black & white": "Lineart",
    }
    sane_mode = mode_map.get(mode.lower(), mode)

    # Validate DPI
    dpi = max(75, min(1200, dpi))

    # Create temp file for output
    suffix = f".{format}"
    fd, tmppath = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    try:
        cmd = [
            "scanimage",
            f"--device-name={active_device_id}",
            f"--resolution={dpi}",
            f"--mode={sane_mode}",
            f"--format={format}",
            f"--output-file={tmppath}",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # scanning can take a while at 600 DPI
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown scan error"
            
            # If Lineart mode is not supported by this scanner, try falling back to Gray
            if sane_mode == "Lineart" and "option --mode" in error_msg:
                cmd_fallback = [arg.replace("--mode=Lineart", "--mode=Gray") for arg in cmd]
                result = subprocess.run(
                    cmd_fallback,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    sane_mode = "Gray"
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown scan error"
                    return {
                        "status": "error",
                        "message": f"Scan failed: {error_msg}",
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Scan failed: {error_msg}",
                }

        # Read the scanned image
        with open(tmppath, "rb") as f:
            image_bytes = f.read()

        if len(image_bytes) == 0:
            return {
                "status": "error",
                "message": "Scanner produced an empty file. Check paper placement.",
            }

        image_b64 = base64.b64encode(image_bytes).decode("ascii")

        return {
            "status": "success",
            "image_base64": image_b64,
            "format": format,
            "dpi": dpi,
            "mode": sane_mode,
            "device_id": active_device_id,
            "size_bytes": len(image_bytes),
            "filename": f"scan_{dpi}dpi.{format}",
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Scan timed out after 120 seconds. The scanner may be unresponsive.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
        }
    finally:
        # Clean up temp file
        try:
            os.unlink(tmppath)
        except OSError:
            pass
