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
import json


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


def get_mac_scanner_bin() -> Optional[str]:
    """Return path to compiled mac_scanner binary if available."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mac_bin = os.path.join(base_dir, "bin", "mac_scanner")
    if os.path.exists(mac_bin) and os.access(mac_bin, os.X_OK):
        return mac_bin
    return None


def is_sane_installed() -> bool:
    """Check whether `scanimage` binary or native `mac_scanner` is available."""
    return shutil.which("scanimage") is not None or get_mac_scanner_bin() is not None


def detect_scanners() -> List[ScannerDevice]:
    """
    Detect connected scanners via native macOS ImageCapture helper or SANE `scanimage -L`.
    """
    devices: List[ScannerDevice] = []

    # 1. Try macOS Native ImageCapture helper first if on macOS
    mac_bin = get_mac_scanner_bin()
    if mac_bin:
        try:
            res = subprocess.run([mac_bin, "--list"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                mac_devs = json.loads(res.stdout)
                for d in mac_devs:
                    devices.append(ScannerDevice(
                        device_id=d.get("device_id", "mac_scanner"),
                        vendor=d.get("vendor", "AppleICA"),
                        model=d.get("model", "Scanner"),
                        device_type=d.get("device_type", "macOS Scanner")
                    ))
        except Exception as e:
            print(f"mac_scanner detection error: {e}")

    # 2. Try SANE scanimage -L if installed
    if shutil.which("scanimage"):
        try:
            result = subprocess.run(
                ["scanimage", "-L"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = result.stdout + result.stderr
            pattern = re.compile(
                r"device\s+[`']([^'`]+)[`']\s+is\s+a\s+(.+)",
                re.IGNORECASE,
            )
            for line in output.splitlines():
                m = pattern.search(line)
                if m:
                    device_id = m.group(1).strip()
                    description = m.group(2).strip()

                    parts = description.rsplit(" ", 2)
                    if len(parts) >= 3 and parts[-1].lower() == "scanner":
                        name_part = parts[0]
                        device_type = f"{parts[-2]} {parts[-1]}"
                    elif len(parts) >= 2 and parts[-1].lower() == "scanner":
                        name_part = parts[0]
                        device_type = parts[-1]
                    else:
                        name_part = description
                        device_type = "scanner"

                    name_tokens = name_part.split(" ", 1)
                    vendor = name_tokens[0] if len(name_tokens) > 1 else ""
                    model = name_tokens[1] if len(name_tokens) > 1 else name_tokens[0]

                    if not any(existing.device_id == device_id for existing in devices):
                        devices.append(ScannerDevice(
                            device_id=device_id,
                            vendor=vendor,
                            model=model,
                            device_type=device_type,
                        ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

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
    if not active_device_id:
        detected = detect_scanners_cached()
        if len(detected) == 1:
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

    mac_bin = get_mac_scanner_bin()
    
    try:
        # Check if mac_scanner should handle this scan (use cached devices to avoid redundant 3s discovery)
        use_mac_scanner = False
        if mac_bin:
            cached = detect_scanners_cached()
            if any(d.device_id == active_device_id for d in cached if d.device_type == "macOS ICA Scanner"):
                use_mac_scanner = True
            elif not shutil.which("scanimage"):
                use_mac_scanner = True

        if use_mac_scanner and mac_bin:
            # Release background Epson drivers that may lock the USB connection
            try:
                subprocess.run(["pkill", "-f", "EPSON Scanner 2"], capture_output=True)
                subprocess.run(["pkill", "-f", "EEventManager"], capture_output=True)
                subprocess.run(["pkill", "-f", "Epson Scanner Monitor"], capture_output=True)
                time.sleep(0.1)
            except Exception:
                pass

            # Use .jpg extension so mac_scanner converts TIFF→JPEG automatically
            fd_jpg, tmppath_jpg = tempfile.mkstemp(suffix=".jpg")
            os.close(fd_jpg)
            mac_cmd = [mac_bin, "--scan", tmppath_jpg, "--device", active_device_id, "--paper-size", "a4"]
            res_mac = subprocess.run(mac_cmd, capture_output=True, text=True, timeout=300) # Increased timeout for multi-page batch
            if res_mac.returncode == 0:
                out_str = res_mac.stdout.strip()
                try:
                    # Slice between first '{' and last '}' to isolate JSON
                    start_idx = out_str.find("{")
                    end_idx = out_str.rfind("}")
                    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                        json_payload = out_str[start_idx:end_idx+1]
                    else:
                        json_payload = out_str

                    out_data = json.loads(json_payload)
                    files = out_data.get("files", [])
                    if files:
                        images_b64 = []
                        total_bytes = 0
                        for fpath in files:
                            if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
                                with open(fpath, "rb") as f:
                                    img_bytes = f.read()
                                images_b64.append(base64.b64encode(img_bytes).decode("ascii"))
                                total_bytes += len(img_bytes)
                                try:
                                    os.unlink(fpath)
                                except OSError:
                                    pass
                        
                        if images_b64:
                            return {
                                "status": "success",
                                "image_base64_list": images_b64,
                                "image_base64": images_b64[0],
                                "format": "jpeg",
                                "dpi": dpi,
                                "mode": sane_mode,
                                "device_id": active_device_id,
                                "size_bytes": total_bytes,
                                "filename": f"scan_{dpi}dpi.jpg",
                            }
                except Exception as e:
                    err_out = res_mac.stdout.strip() or res_mac.stderr.strip()
                    return {"status": "error", "message": f"Scan parsing exception ({type(e).__name__}: {e}). Output: {err_out}"}
                
                # Fallback if parsing failed but we know the scan worked
                err_out = res_mac.stdout.strip() or res_mac.stderr.strip()
                return {"status": "error", "message": f"Scan parsing failed (no images found). Output: {err_out}"}
            else:
                err_out = res_mac.stdout.strip() or res_mac.stderr.strip()
                err_msg = "Scan failed."
                if "Failed to open a connection" in err_out or "Failed to open session" in err_out:
                    err_msg = "Scanner session is locked by another app. Please QUIT the 'Image Capture' or 'Epson Scan 2' desktop app."
                elif err_out:
                    try:
                        err_json = json.loads(err_out)
                        err_msg = err_json.get("message", err_out)
                    except Exception:
                        err_msg = err_out
                return {
                    "status": "error",
                    "message": f"macOS Scan Error: {err_msg}"
                }

        # Fallback / standard scanimage command
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
            
            # If default scan failed, try common document feeder (ADF) options for sheet-fed scanners like Epson DS-870
            if "Document feeder" in error_msg or "option --source" in error_msg or "invalid option" in error_msg.lower():
                for adf_source in ["ADF", "ADF Front", "Automatic Document Feeder"]:
                    cmd_adf = cmd + [f"--source={adf_source}"]
                    res_adf = subprocess.run(cmd_adf, capture_output=True, text=True, timeout=120)
                    if res_adf.returncode == 0:
                        result = res_adf
                        break
            
            # If Lineart mode is not supported by this scanner, try falling back to Gray
            if result.returncode != 0 and sane_mode == "Lineart" and "option --mode" in error_msg:
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
            elif result.returncode != 0:
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
