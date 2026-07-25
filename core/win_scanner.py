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
import tempfile
import time
import base64
from typing import List, Optional, Dict, Any

try:
    from PIL import Image
    _pil_available = True
except ImportError:
    _pil_available = False

# WIA Constants
WIA_DEVICE_TYPE_SCANNER = 1

# Property IDs
WIA_IPA_DATATYPE = 4103          # Data type (BW=0, Gray=1, Color=2 or 3)
WIA_IPS_CUR_INTENT = 6146        # Scan intent (Color=1, Gray=2, Text=4)
WIA_IPS_XRES = 6147              # Horizontal resolution
WIA_IPS_YRES = 6148              # Vertical resolution

WIA_DPS_DOCUMENT_HANDLING_CAPABILITIES = 3086  # Capabilities
WIA_DPS_DOCUMENT_HANDLING_STATUS = 3087        # Paper status
WIA_DPS_DOCUMENT_HANDLING_SELECT = 3088        # Source select

# Select flags
WIA_FEEDER = 1
WIA_FLATBED = 2
WIA_DUPLEX = 4

# Status flags
WIA_FEED_READY = 1

# Intent flags
WIA_INTENT_IMAGE_TYPE_COLOR = 1
WIA_INTENT_IMAGE_TYPE_GRAYSCALE = 2
WIA_INTENT_IMAGE_TYPE_TEXT = 4

# GUIDs
WIA_FORMAT_BMP = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"

# Error codes
WIA_ERROR_PAPER_EMPTY = -2145320957       # 0x80210003
WIA_ERROR_PAPER_JAM = -2145320958         # 0x80210002
WIA_ERROR_COVER_OPEN = -2145320956        # 0x80210004
WIA_ERROR_DEVICE_COMMUNICATION = -2145320959  # 0x80210001
WIA_ERROR_DEVICE_LOCKED = -2145320955     # 0x80210005
WIA_ERROR_OFFLINE = -2145320953           # 0x80210007
WIA_ERROR_BUSY = -2145320954              # 0x80210006

_IS_WINDOWS = sys.platform == "win32"

_wia_available = False
if _IS_WINDOWS:
    try:
        import win32com.client
        import pythoncom
        _wia_available = True
    except ImportError:
        pass


def is_wia_available() -> bool:
    """Check whether WIA scanning is available on this machine."""
    return _wia_available


def _get_wia_device_manager():
    """Create and return a WIA DeviceManager COM object."""
    if not _wia_available:
        return None
    try:
        pythoncom.CoInitialize()
        return win32com.client.Dispatch("WIA.DeviceManager")
    except Exception:
        return None


def _get_property(obj, prop_id, default=None):
    """Safely read a WIA property by ID."""
    try:
        props = obj.Properties
        for i in range(1, props.Count + 1):
            prop = props.Item(i)
            if prop.PropertyID == prop_id:
                return prop.Value
    except Exception:
        pass
    return default


def _set_property(obj, prop_id, value) -> bool:
    """Safely set a WIA property by ID."""
    try:
        props = obj.Properties
        for i in range(1, props.Count + 1):
            prop = props.Item(i)
            if prop.PropertyID == prop_id:
                prop.Value = value
                return True
    except Exception:
        pass
    return False


def _get_property_by_name(obj, name, default=None):
    """Safely read a WIA property by name."""
    try:
        props = obj.Properties
        for i in range(1, props.Count + 1):
            prop = props.Item(i)
            if prop.Name == name:
                return prop.Value
    except Exception:
        pass
    return default


def detect_devices() -> List[Dict[str, str]]:
    """Enumerate all WIA-connected scanners on Windows."""
    if not _wia_available:
        return []

    devices = []
    try:
        dm = _get_wia_device_manager()
        if dm is None:
            return []

        dev_infos = dm.DeviceInfos
        for i in range(1, dev_infos.Count + 1):
            try:
                info = dev_infos.Item(i)
                if info.Type != WIA_DEVICE_TYPE_SCANNER:
                    continue

                device_id = info.DeviceID
                name = _get_property_by_name(info, "Name", "Scanner")
                manufacturer = _get_property_by_name(info, "Manufacturer", "")
                description = _get_property_by_name(info, "Description", "")

                devices.append({
                    "device_id": device_id,
                    "vendor": manufacturer or (name.split(" ")[0] if " " in name else "Scanner"),
                    "model": description or name or device_id,
                    "device_type": "Windows WIA Scanner",
                })
            except Exception as e:
                print(f"WIA detect error for device {i}: {e}")
                continue

    except Exception as e:
        print(f"WIA device detection error: {e}")

    return devices


def _configure_document_handling(device) -> str:
    """Configure scan source (ADF vs Flatbed) safely on device."""
    caps = _get_property(device, WIA_DPS_DOCUMENT_HANDLING_CAPABILITIES, 0)
    select_prop = _get_property(device, WIA_DPS_DOCUMENT_HANDLING_SELECT)

    if select_prop is not None:
        has_feeder = bool(caps & WIA_FEEDER) or caps == 0 or bool(select_prop & WIA_FEEDER)
        has_flatbed = bool(caps & WIA_FLATBED)

        status = _get_property(device, WIA_DPS_DOCUMENT_HANDLING_STATUS, 0)
        feeder_ready = bool(status & WIA_FEED_READY)

        if has_feeder and (feeder_ready or not has_flatbed):
            _set_property(device, WIA_DPS_DOCUMENT_HANDLING_SELECT, WIA_FEEDER)
            return "feeder"
        elif has_flatbed:
            _set_property(device, WIA_DPS_DOCUMENT_HANDLING_SELECT, WIA_FLATBED)
            return "flatbed"
        else:
            _set_property(device, WIA_DPS_DOCUMENT_HANDLING_SELECT, WIA_FEEDER)
            return "feeder"
    return "default"


def _configure_scan_item(item, dpi: int = 150, mode: str = "Color"):
    """Configure DPI resolution and color intent on WIA item."""
    _set_property(item, WIA_IPS_XRES, dpi)
    _set_property(item, WIA_IPS_YRES, dpi)

    mode_lower = mode.lower()
    if mode_lower in ("color",):
        _set_property(item, WIA_IPS_CUR_INTENT, WIA_INTENT_IMAGE_TYPE_COLOR)
    elif mode_lower in ("gray", "grayscale"):
        _set_property(item, WIA_IPS_CUR_INTENT, WIA_INTENT_IMAGE_TYPE_GRAYSCALE)
    elif mode_lower in ("lineart", "bw", "black & white"):
        _set_property(item, WIA_IPS_CUR_INTENT, WIA_INTENT_IMAGE_TYPE_TEXT)


def _extract_error_code(e: Exception) -> int:
    """Extract WIA HRESULT error code from COM exception."""
    if hasattr(e, "args") and len(e.args) >= 3 and isinstance(e.args[2], tuple) and len(e.args[2]) >= 6:
        return e.args[2][5]
    if hasattr(e, "hresult"):
        return e.hresult
    return 0


def _friendly_wia_error(error_code: int, raw_err_str: str = "") -> str:
    """Convert WIA HRESULT error codes to user-friendly messages."""
    if error_code == WIA_ERROR_PAPER_EMPTY or "no documents left in the document feeder" in raw_err_str.lower():
        return "No paper in the document feeder. Please load paper into the tray and try again."
    
    error_map = {
        WIA_ERROR_PAPER_EMPTY: "No paper in the document feeder. Please load paper into the tray and try again.",
        WIA_ERROR_PAPER_JAM: "Paper jam detected. Please clear the jam and try again.",
        WIA_ERROR_COVER_OPEN: "Scanner cover is open. Please close it and try again.",
        WIA_ERROR_DEVICE_COMMUNICATION: "Cannot communicate with the scanner. Check the USB connection.",
        WIA_ERROR_DEVICE_LOCKED: "Scanner is locked or in use by another application. Close other scanning apps and retry.",
        WIA_ERROR_OFFLINE: "Scanner is offline. Check power and USB connection.",
        WIA_ERROR_BUSY: "Scanner is busy. Please wait a moment and try again.",
    }
    return error_map.get(error_code, "Check scanner power, USB cable, and paper placement in feeder tray.")


def scan_page(
    device_id: str,
    dpi: int = 150,
    mode: str = "Color",
    format: str = "jpeg",
) -> Dict[str, Any]:
    """
    Execute a scan on Windows via WIA and return base64-encoded JPEG image(s).
    """
    if not _wia_available:
        return {
            "status": "error",
            "message": "WIA scanner support requires pywin32. Install with: pip install pywin32",
        }

    dpi = max(75, min(1200, dpi))

    mode_map = {
        "color": "Color",
        "gray": "Gray",
        "grayscale": "Gray",
        "bw": "Lineart",
        "lineart": "Lineart",
        "black & white": "Lineart",
    }
    sane_mode = mode_map.get(mode.lower(), mode)

    try:
        pythoncom.CoInitialize()
        dm = win32com.client.Dispatch("WIA.DeviceManager")

        device = None
        dev_infos = dm.DeviceInfos
        for i in range(1, dev_infos.Count + 1):
            info = dev_infos.Item(i)
            if info.DeviceID == device_id and info.Type == WIA_DEVICE_TYPE_SCANNER:
                device = info.Connect()
                break

        if device is None:
            for i in range(1, dev_infos.Count + 1):
                info = dev_infos.Item(i)
                if info.Type == WIA_DEVICE_TYPE_SCANNER:
                    device = info.Connect()
                    device_id = info.DeviceID
                    break

        if device is None:
            return {
                "status": "error",
                "message": "No WIA scanner found. Make sure your scanner is connected and turned on.",
            }

        handling_source = _configure_document_handling(device)

        if device.Items.Count == 0:
            return {
                "status": "error",
                "message": "Scanner has no scan sources available.",
            }

        item = device.Items.Item(1)
        _configure_scan_item(item, dpi=dpi, mode=sane_mode)

        transfer_format = WIA_FORMAT_BMP
        if hasattr(item, "Formats") and item.Formats.Count > 0:
            transfer_format = item.Formats.Item(1)

        scanned_files = []
        raw_pages_bytes = []
        total_bytes = 0
        page_num = 0

        while True:
            page_num += 1
            bmp_path = None
            jpg_path = None
            try:
                wia_image = item.Transfer(transfer_format)
                if wia_image is None:
                    break

                if _pil_available and hasattr(wia_image, "FileData"):
                    # Save raw binary data immediately to avoid any processing delays
                    raw_pages_bytes.append(wia_image.FileData.BinaryData)
                else:
                    fd_bmp, bmp_path = tempfile.mkstemp(suffix=".bmp", prefix=f"wia_raw_p{page_num}_")
                    os.close(fd_bmp)
                    try:
                        os.unlink(bmp_path)
                    except OSError:
                        pass
                    wia_image.SaveFile(bmp_path)

                    if os.path.exists(bmp_path) and os.path.getsize(bmp_path) > 0:
                        fd_jpg, jpg_path = tempfile.mkstemp(suffix=".jpg", prefix=f"wia_scan_p{page_num}_")
                        os.close(fd_jpg)
                        try:
                            os.unlink(jpg_path)
                        except OSError:
                            pass

                        if _pil_available:
                            with Image.open(bmp_path) as pil_img:
                                pil_img.save(jpg_path, "JPEG", quality=85)
                        else:
                            os.replace(bmp_path, jpg_path)

                        if os.path.exists(jpg_path) and os.path.getsize(jpg_path) > 0:
                            scanned_files.append(jpg_path)
                            total_bytes += os.path.getsize(jpg_path)

            except Exception as e:
                err_code = _extract_error_code(e)
                err_str = str(e)
                if err_code == WIA_ERROR_PAPER_EMPTY or "no documents left in the document feeder" in err_str.lower():
                    # Feeder tray ran out of paper naturally — this completes the batch!
                    if page_num == 1:
                        return {
                            "status": "error",
                            "message": _friendly_wia_error(WIA_ERROR_PAPER_EMPTY, err_str),
                        }
                    break
                elif page_num == 1:
                    msg = _friendly_wia_error(err_code, err_str)
                    return {
                        "status": "error",
                        "message": f"Scan failed: {msg}",
                    }
                else:
                    # An error occurred after scanning 1+ pages, return what we have
                    break
            finally:
                if bmp_path and os.path.exists(bmp_path):
                    try:
                        os.unlink(bmp_path)
                    except OSError:
                        pass

            # If flatbed or default single page scan source, exit loop after 1 page
            if handling_source == "flatbed" or handling_source == "default":
                break

        # Process raw in-memory pages to JPEG format after the physical scan completes
        images_bytes = []
        if raw_pages_bytes:
            import io
            for raw_data in raw_pages_bytes:
                try:
                    with Image.open(io.BytesIO(raw_data)) as pil_img:
                        buf = io.BytesIO()
                        pil_img.save(buf, format="JPEG", quality=85)
                        jpeg_bytes = buf.getvalue()
                        images_bytes.append(jpeg_bytes)
                        total_bytes += len(jpeg_bytes)
                except Exception as e:
                    print(f"Error compressing raw in-memory WIA page to JPEG: {e}")

        if not images_bytes and not scanned_files:
            return {
                "status": "error",
                "message": "No paper in the document feeder. Please load paper into the tray and try again.",
            }

        images_b64 = []
        for img_bytes in images_bytes:
            images_b64.append(base64.b64encode(img_bytes).decode("ascii"))

        for fpath in scanned_files:
            try:
                with open(fpath, "rb") as f:
                    img_bytes = f.read()
                images_b64.append(base64.b64encode(img_bytes).decode("ascii"))
            except Exception:
                pass
            finally:
                try:
                    os.unlink(fpath)
                except OSError:
                    pass

        if not images_b64:
            return {
                "status": "error",
                "message": "Failed to encode scanned images.",
            }

        return {
            "status": "success",
            "image_base64_list": images_b64,
            "image_base64": images_b64[0],
            "format": "jpeg",
            "dpi": dpi,
            "mode": sane_mode,
            "device_id": device_id,
            "size_bytes": total_bytes,
            "filename": f"scan_{dpi}dpi.jpg",
        }

    except Exception as e:
        err_code = _extract_error_code(e)
        msg = _friendly_wia_error(err_code, str(e))
        return {
            "status": "error",
            "message": f"Windows scan error: {msg}",
        }
