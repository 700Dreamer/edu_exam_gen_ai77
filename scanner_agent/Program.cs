using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

/// <summary>
/// Edulytics Scanner Agent — Native Windows WIA Scanner Helper
/// 
/// Runs a local HTTP server on port 8181 that the browser (edulytics.net)
/// talks to directly for high-speed document scanning via WIA.
/// 
/// Uses late-bound COM (no WIA interop DLL needed — works on any Windows).
/// 
/// Endpoints:
///   GET  /devices  — List connected WIA scanners
///   POST /scan     — Batch scan all pages from ADF at native speed
///   GET  /ping     — Health check
/// 
/// Build:
///   C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /out:scanner_agent\ScannerAgent.exe /target:exe /reference:System.Drawing.dll scanner_agent\Program.cs
/// </summary>
class ScannerAgent
{
    const int PORT = 8181;
    const string ALLOWED_ORIGINS = "https://edulytics.net,http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001";

    // WIA Constants
    const int WIA_DEVICE_TYPE_SCANNER = 1;
    const int WIA_DPS_DOCUMENT_HANDLING_CAPABILITIES = 3086;
    const int WIA_DPS_DOCUMENT_HANDLING_STATUS = 3087;
    const int WIA_DPS_DOCUMENT_HANDLING_SELECT = 3088;
    const int WIA_IPS_CUR_INTENT = 6146;
    const int WIA_IPS_XRES = 6147;
    const int WIA_IPS_YRES = 6148;
    const int WIA_FEEDER = 1;
    const int WIA_FLATBED = 2;
    const int WIA_FEED_READY = 1;
    const int WIA_INTENT_COLOR = 1;
    const int WIA_INTENT_GRAYSCALE = 2;
    const int WIA_INTENT_TEXT = 4;
    const string WIA_FORMAT_BMP = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}";
    const uint WIA_ERROR_PAPER_EMPTY = 0x80210003;

    static HttpListener _listener;
    static volatile bool _running = true;

    static void Main(string[] args)
    {
        try
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add(string.Format("http://127.0.0.1:{0}/", PORT));
            _listener.Prefixes.Add(string.Format("http://localhost:{0}/", PORT));
            _listener.Start();
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("Failed to start HTTP listener: " + ex.Message);
            Console.Error.WriteLine("Try running as Administrator, or check if port " + PORT + " is in use.");
            return;
        }

        Console.WriteLine("Edulytics Scanner Agent started on http://127.0.0.1:" + PORT + "/");
        Console.WriteLine("Waiting for scan requests from browser...");
        Console.WriteLine("Press Ctrl+C to stop.");

        Console.CancelKeyPress += delegate { _running = false; _listener.Stop(); };

        while (_running)
        {
            try
            {
                var ctx = _listener.GetContext();
                ThreadPool.QueueUserWorkItem(HandleRequest, ctx);
            }
            catch (HttpListenerException)
            {
                break;
            }
            catch (ObjectDisposedException)
            {
                break;
            }
        }
    }

    static void HandleRequest(object state)
    {
        var ctx = (HttpListenerContext)state;
        var req = ctx.Request;
        var res = ctx.Response;

        // CORS headers
        string origin = req.Headers["Origin"] ?? "";
        if (ALLOWED_ORIGINS.IndexOf(origin, StringComparison.OrdinalIgnoreCase) >= 0 || origin.EndsWith(".edulytics.net"))
        {
            res.Headers["Access-Control-Allow-Origin"] = origin;
        }
        else
        {
            res.Headers["Access-Control-Allow-Origin"] = "*";
        }
        res.Headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
        res.Headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization";
        res.Headers["Access-Control-Max-Age"] = "86400";

        // Handle preflight
        if (req.HttpMethod == "OPTIONS")
        {
            res.StatusCode = 204;
            res.Close();
            return;
        }

        string path = req.Url.AbsolutePath.TrimEnd('/').ToLower();

        try
        {
            switch (path)
            {
                case "/ping":
                    SendJson(res, 200, "{\"status\":\"ok\",\"agent\":\"edulytics-scanner\",\"version\":\"1.0\"}");
                    break;

                case "/devices":
                    HandleDevices(res);
                    break;

                case "/scan":
                    HandleScan(req, res);
                    break;

                default:
                    SendJson(res, 404, "{\"error\":\"Not found\"}");
                    break;
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("Request error: " + ex.Message);
            try { SendJson(res, 500, "{\"error\":\"" + EscapeJson(ex.Message) + "\"}"); }
            catch { }
        }
    }

    // ── Device Detection ──

    static void HandleDevices(HttpListenerResponse res)
    {
        Console.WriteLine("Device list requested...");
        var devices = new List<string>();

        try
        {
            Type wiaType = Type.GetTypeFromProgID("WIA.DeviceManager");
            dynamic devMgr = Activator.CreateInstance(wiaType);

            int count = devMgr.DeviceInfos.Count;
            for (int i = 1; i <= count; i++)
            {
                dynamic info = devMgr.DeviceInfos.Item(i);
                if ((int)info.Type != WIA_DEVICE_TYPE_SCANNER) continue;

                string devId = info.DeviceID;
                string name = GetDynPropertyByName(info, "Name", "Scanner");
                string mfg = GetDynPropertyByName(info, "Manufacturer", "");
                string desc = GetDynPropertyByName(info, "Description", "");

                string displayName = !string.IsNullOrEmpty(desc) ? desc : name;
                string vendor = !string.IsNullOrEmpty(mfg) ? mfg : (name.Contains(" ") ? name.Split(' ')[0] : "Scanner");

                devices.Add(string.Format(
                    "{{\"device_id\":\"{0}\",\"vendor\":\"{1}\",\"model\":\"{2}\",\"device_type\":\"Windows WIA Scanner\",\"display_name\":\"{3}\"}}",
                    EscapeJson(devId), EscapeJson(vendor), EscapeJson(displayName), EscapeJson(displayName)));
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("Device detection error: " + ex.Message);
        }

        string json = "{\"sane_installed\":true,\"platform\":\"windows\",\"devices\":[" + string.Join(",", devices) + "]}";
        SendJson(res, 200, json);
    }

    // ── Scanning ──

    static void HandleScan(HttpListenerRequest req, HttpListenerResponse res)
    {
        // Parse request body
        string body = "";
        using (var sr = new StreamReader(req.InputStream, Encoding.UTF8))
            body = sr.ReadToEnd();

        string deviceId = ExtractJsonString(body, "device_id");
        int dpi = ExtractJsonInt(body, "dpi", 150);
        string mode = ExtractJsonString(body, "mode") ?? "Color";

        if (string.IsNullOrEmpty(deviceId))
        {
            SendJson(res, 400, "{\"status\":\"error\",\"message\":\"device_id is required\"}");
            return;
        }

        Console.WriteLine("Scan request: device=" + deviceId + " dpi=" + dpi + " mode=" + mode);

        try
        {
            Type wiaType = Type.GetTypeFromProgID("WIA.DeviceManager");
            dynamic devMgr = Activator.CreateInstance(wiaType);

            // Connect to the specified device (or first scanner found)
            dynamic device = null;
            string actualDeviceId = deviceId;
            int devCount = devMgr.DeviceInfos.Count;

            for (int i = 1; i <= devCount; i++)
            {
                dynamic info = devMgr.DeviceInfos.Item(i);
                if ((int)info.Type != WIA_DEVICE_TYPE_SCANNER) continue;

                string thisId = info.DeviceID;
                if (thisId == deviceId)
                {
                    device = info.Connect();
                    break;
                }
                else if (device == null)
                {
                    device = info.Connect();
                    actualDeviceId = thisId;
                }
            }

            if (device == null)
            {
                SendJson(res, 500, "{\"status\":\"error\",\"message\":\"No scanner found. Check connection.\"}");
                return;
            }

            // Configure ADF feeder
            string source = ConfigureFeeder(device);
            Console.WriteLine("  Scan source: " + source);

            int itemCount = device.Items.Count;
            if (itemCount == 0)
            {
                SendJson(res, 500, "{\"status\":\"error\",\"message\":\"Scanner has no scan items available.\"}");
                return;
            }

            // Configure scan settings on the item
            dynamic item = device.Items.Item(1);
            SetDynProperty(item, WIA_IPS_XRES, dpi);
            SetDynProperty(item, WIA_IPS_YRES, dpi);

            int intent = WIA_INTENT_COLOR;
            if (mode.Equals("Gray", StringComparison.OrdinalIgnoreCase) || mode.Equals("Grayscale", StringComparison.OrdinalIgnoreCase))
                intent = WIA_INTENT_GRAYSCALE;
            else if (mode.Equals("Lineart", StringComparison.OrdinalIgnoreCase) || mode.Equals("BW", StringComparison.OrdinalIgnoreCase))
                intent = WIA_INTENT_TEXT;
            SetDynProperty(item, WIA_IPS_CUR_INTENT, intent);

            // ── TIGHT SCAN LOOP — This is where the speed comes from ──
            // No processing inside the loop. Just transfer raw data as fast as hardware allows.
            var rawPages = new List<byte[]>();
            int pageNum = 0;

            while (true)
            {
                pageNum++;
                try
                {
                    Console.WriteLine("  Scanning page " + pageNum + "...");
                    dynamic wiaImage = item.Transfer(WIA_FORMAT_BMP);
                    if (wiaImage == null) break;

                    // Grab raw bytes immediately — no processing, no disk I/O
                    byte[] rawData = (byte[])wiaImage.FileData.BinaryData;
                    rawPages.Add(rawData);
                }
                catch (COMException ex)
                {
                    uint hresult = (uint)ex.ErrorCode;
                    string msg = ex.Message ?? "";
                    if (hresult == WIA_ERROR_PAPER_EMPTY ||
                        msg.IndexOf("no documents left", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        // Normal end of paper — batch complete
                        if (pageNum == 1)
                        {
                            SendJson(res, 500, "{\"status\":\"error\",\"message\":\"No paper in the document feeder. Load paper and try again.\"}");
                            return;
                        }
                        break;
                    }
                    else if (pageNum == 1)
                    {
                        SendJson(res, 500, "{\"status\":\"error\",\"message\":\"Scan failed: " + EscapeJson(msg) + "\"}");
                        return;
                    }
                    else
                    {
                        // Got some pages, return what we have
                        break;
                    }
                }

                // Flatbed: only 1 page
                if (source == "flatbed" || source == "default")
                    break;
            }

            Console.WriteLine("  Physical scan complete. " + rawPages.Count + " pages captured.");

            if (rawPages.Count == 0)
            {
                SendJson(res, 500, "{\"status\":\"error\",\"message\":\"No pages were scanned.\"}");
                return;
            }

            // ── POST-SCAN PROCESSING — Convert BMP→JPEG and base64 encode ──
            Console.WriteLine("  Compressing to JPEG...");
            var b64Pages = new List<string>();
            long totalBytes = 0;

            ImageCodecInfo jpegCodec = GetJpegEncoder();
            var encoderParams = new EncoderParameters(1);
            encoderParams.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, 85L);

            foreach (var raw in rawPages)
            {
                using (var ms = new MemoryStream(raw))
                using (var bmp = new Bitmap(ms))
                using (var jpgStream = new MemoryStream())
                {
                    if (jpegCodec != null)
                        bmp.Save(jpgStream, jpegCodec, encoderParams);
                    else
                        bmp.Save(jpgStream, ImageFormat.Jpeg);

                    byte[] jpgBytes = jpgStream.ToArray();
                    b64Pages.Add(Convert.ToBase64String(jpgBytes));
                    totalBytes += jpgBytes.Length;
                }
            }

            Console.WriteLine("  Done. Sending " + b64Pages.Count + " pages (" + (totalBytes / 1024) + " KB) to browser.");

            // Build JSON response
            var sb = new StringBuilder();
            sb.Append("{\"status\":\"success\",\"image_base64_list\":[");
            for (int i = 0; i < b64Pages.Count; i++)
            {
                if (i > 0) sb.Append(",");
                sb.Append("\"").Append(b64Pages[i]).Append("\"");
            }
            sb.Append("],\"image_base64\":\"").Append(b64Pages[0]).Append("\"");
            sb.Append(",\"format\":\"jpeg\"");
            sb.Append(",\"dpi\":").Append(dpi);
            sb.Append(",\"mode\":\"").Append(EscapeJson(mode)).Append("\"");
            sb.Append(",\"device_id\":\"").Append(EscapeJson(actualDeviceId)).Append("\"");
            sb.Append(",\"size_bytes\":").Append(totalBytes);
            sb.Append(",\"filename\":\"scan_").Append(dpi).Append("dpi.jpg\"");
            sb.Append("}");

            SendJson(res, 200, sb.ToString());
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("Scan error: " + ex);
            SendJson(res, 500, "{\"status\":\"error\",\"message\":\"Scanner error: " + EscapeJson(ex.Message) + "\"}");
        }
    }

    // ── WIA Helpers (late-bound COM — no interop DLL needed) ──

    static string ConfigureFeeder(dynamic device)
    {
        int caps = GetDynProperty(device, WIA_DPS_DOCUMENT_HANDLING_CAPABILITIES, 0);
        int status = GetDynProperty(device, WIA_DPS_DOCUMENT_HANDLING_STATUS, 0);

        bool hasFeeder = (caps & WIA_FEEDER) != 0;
        bool hasFlatbed = (caps & WIA_FLATBED) != 0;
        bool feedReady = (status & WIA_FEED_READY) != 0;

        if (hasFeeder && (feedReady || !hasFlatbed))
        {
            SetDynProperty(device, WIA_DPS_DOCUMENT_HANDLING_SELECT, WIA_FEEDER);
            return "feeder";
        }
        else if (hasFlatbed)
        {
            SetDynProperty(device, WIA_DPS_DOCUMENT_HANDLING_SELECT, WIA_FLATBED);
            return "flatbed";
        }
        else
        {
            SetDynProperty(device, WIA_DPS_DOCUMENT_HANDLING_SELECT, WIA_FEEDER);
            return "feeder";
        }
    }

    static int GetDynProperty(dynamic obj, int propId, int defaultVal)
    {
        try
        {
            dynamic props = obj.Properties;
            int count = props.Count;
            for (int i = 1; i <= count; i++)
            {
                dynamic prop = props.Item(i);
                if ((int)prop.PropertyID == propId)
                    return (int)prop.Value;
            }
        }
        catch { }
        return defaultVal;
    }

    static void SetDynProperty(dynamic obj, int propId, object value)
    {
        try
        {
            dynamic props = obj.Properties;
            int count = props.Count;
            for (int i = 1; i <= count; i++)
            {
                dynamic prop = props.Item(i);
                if ((int)prop.PropertyID == propId)
                {
                    prop.Value = value;
                    return;
                }
            }
        }
        catch { }
    }

    static string GetDynPropertyByName(dynamic obj, string name, string defaultVal)
    {
        try
        {
            dynamic props = obj.Properties;
            int count = props.Count;
            for (int i = 1; i <= count; i++)
            {
                dynamic prop = props.Item(i);
                if ((string)prop.Name == name)
                    return prop.Value.ToString();
            }
        }
        catch { }
        return defaultVal;
    }

    static ImageCodecInfo GetJpegEncoder()
    {
        foreach (var codec in ImageCodecInfo.GetImageEncoders())
        {
            if (codec.MimeType == "image/jpeg")
                return codec;
        }
        return null;
    }

    // ── HTTP Helpers ──

    static void SendJson(HttpListenerResponse res, int statusCode, string json)
    {
        res.StatusCode = statusCode;
        res.ContentType = "application/json; charset=utf-8";
        byte[] buf = Encoding.UTF8.GetBytes(json);
        res.ContentLength64 = buf.Length;
        res.OutputStream.Write(buf, 0, buf.Length);
        res.Close();
    }

    static string EscapeJson(string s)
    {
        if (s == null) return "";
        return s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n").Replace("\r", "\\r").Replace("\t", "\\t");
    }

    // ── Simple JSON parsing (no external dependencies) ──

    static string ExtractJsonString(string json, string key)
    {
        string search = "\"" + key + "\"";
        int idx = json.IndexOf(search);
        if (idx < 0) return null;
        idx = json.IndexOf(":", idx + search.Length);
        if (idx < 0) return null;
        idx = json.IndexOf("\"", idx + 1);
        if (idx < 0) return null;
        int end = json.IndexOf("\"", idx + 1);
        if (end < 0) return null;
        return json.Substring(idx + 1, end - idx - 1);
    }

    static int ExtractJsonInt(string json, string key, int defaultVal)
    {
        string search = "\"" + key + "\"";
        int idx = json.IndexOf(search);
        if (idx < 0) return defaultVal;
        idx = json.IndexOf(":", idx + search.Length);
        if (idx < 0) return defaultVal;
        idx++;
        while (idx < json.Length && json[idx] == ' ') idx++;
        int end = idx;
        while (end < json.Length && (char.IsDigit(json[end]) || json[end] == '-')) end++;
        int val;
        if (int.TryParse(json.Substring(idx, end - idx), out val))
            return val;
        return defaultVal;
    }
}
