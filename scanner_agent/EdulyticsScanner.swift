/// ---------------------------------------------------------------------------
/// Edulytics Scanner Agent -- macOS Native Scanner Bridge
///
/// A standalone local HTTP server on port 8181 that the browser (edulytics.net)
/// talks to directly for high-speed document scanning via Apple ImageCaptureCore.
///
/// Uses NWListener (Network.framework) for non-blocking async HTTP and
/// ImageCaptureCore for native EPSON scanner access -- zero dependencies.
///
/// Endpoints:
///   GET  /ping     -- Health check
///   GET  /devices  -- List connected ICA scanners
///   POST /scan     -- Batch scan all pages from ADF at native speed
///
/// Build:
///   ./scanner_agent/build_mac_agent.sh
/// ---------------------------------------------------------------------------

import Foundation
import Network
import ImageCaptureCore
import AppKit

// MARK: - Configuration

let AGENT_VERSION = "1.0"
let AGENT_PORT: UInt16 = 8181
let ALLOWED_ORIGINS = [
    "https://edulytics.net",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
]

// MARK: - Console Helpers

enum ConsoleColor: String {
    case reset   = "\u{001B}[0m"
    case red     = "\u{001B}[31m"
    case green   = "\u{001B}[32m"
    case yellow  = "\u{001B}[33m"
    case cyan    = "\u{001B}[36m"
    case white   = "\u{001B}[37m"
    case darkGray = "\u{001B}[90m"
    case darkCyan = "\u{001B}[36;2m"
}

func colorPrint(_ text: String, _ color: ConsoleColor = .reset) {
    print("\(color.rawValue)\(text)\(ConsoleColor.reset.rawValue)")
}

func logRequest(_ method: String, _ path: String, _ status: Int) {
    let timestamp = ISO8601DateFormatter().string(from: Date())
    let statusColor: ConsoleColor = status < 400 ? .green : .red
    print("\(ConsoleColor.darkGray.rawValue)  \(timestamp)\(ConsoleColor.reset.rawValue)  \(method) \(path)  \(statusColor.rawValue)\(status)\(ConsoleColor.reset.rawValue)")
}

// MARK: - JSON Helpers

func escapeJSON(_ s: String) -> String {
    return s
        .replacingOccurrences(of: "\\", with: "\\\\")
        .replacingOccurrences(of: "\"", with: "\\\"")
        .replacingOccurrences(of: "\n", with: "\\n")
        .replacingOccurrences(of: "\r", with: "\\r")
        .replacingOccurrences(of: "\t", with: "\\t")
}

func jsonString(_ dict: [String: Any]) -> String {
    guard let data = try? JSONSerialization.data(withJSONObject: dict, options: []),
          let str = String(data: data, encoding: .utf8) else {
        return "{}"
    }
    return str
}

func parseJSONBody(_ body: String) -> [String: Any] {
    guard let data = body.data(using: .utf8),
          let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
        return [:]
    }
    return obj
}

// MARK: - Scanner Manager (ImageCaptureCore)

class ScannerManager: NSObject, ICDeviceBrowserDelegate, ICScannerDeviceDelegate, ICDeviceDelegate {
    // Shared instance for device list caching only (never used for scanning)
    static let shared = ScannerManager()

    // Create a fresh instance for each scan to avoid ICA stale-state issues.
    // ICA's ICDeviceBrowser and ICScannerDevice objects accumulate internal state
    // that prevents session re-acquisition in a long-lived process.
    static func newScanInstance() -> ScannerManager {
        return ScannerManager()
    }

    let browser = ICDeviceBrowser()
    private var discoveredDevices: [ICScannerDevice] = []
    private var foundFirstDevice = false
    private var cachedDeviceList: [[String: String]] = []
    private var lastDiscoveryTime: Date = .distantPast
    private let discoveryLock = NSLock()

    // Scan state (per-scan, reset before each scan)
    private var scanSuccess = false
    private var scanCompleted = false
    private var scanErrorMessage: String?
    private var scannedFiles: [String] = []
    private var rawScannedURLs: [URL] = []
    private var jobDirectoryURL: URL?
    private var sessionOpen = false
    private var outputPath: String?
    private var paperSize: String = "a4"

    override init() {
        super.init()
        browser.delegate = self
        browser.browsedDeviceTypeMask = ICDeviceTypeMask(rawValue:
            ICDeviceTypeMask.scanner.rawValue |
            ICDeviceLocationTypeMask.local.rawValue |
            ICDeviceLocationTypeMask.shared.rawValue |
            ICDeviceLocationTypeMask.bonjour.rawValue
        )!
    }

    // -- Device Discovery --

    func getDevices(forceRefresh: Bool = false) -> [[String: String]] {
        discoveryLock.lock()
        defer { discoveryLock.unlock() }

        let age = Date().timeIntervalSince(lastDiscoveryTime)
        if !forceRefresh && !cachedDeviceList.isEmpty && age < 30.0 {
            return cachedDeviceList
        }

        let freshDevices = discoverDevices(timeout: 3.0)
        var jsonList: [[String: String]] = []
        for d in freshDevices {
            let devName = d.name ?? "mac_scanner"
            let vendor = devName.components(separatedBy: " ").first ?? "Scanner"
            jsonList.append([
                "device_id": devName,
                "vendor": vendor,
                "model": devName,
                "device_type": "macOS Scanner",
                "display_name": devName,
            ])
        }
        cachedDeviceList = jsonList
        lastDiscoveryTime = Date()
        return jsonList
    }

    private func discoverDevices(timeout: TimeInterval = 3.0) -> [ICScannerDevice] {
        discoveredDevices.removeAll()
        foundFirstDevice = false
        browser.start()

        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.1))
            if foundFirstDevice {
                // Grace period for additional devices
                let grace = Date().addingTimeInterval(0.2)
                while Date() < grace {
                    RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.05))
                }
                break
            }
        }
        browser.stop()
        return discoveredDevices
    }

    // -- ICDeviceBrowserDelegate --

    func deviceBrowser(_ browser: ICDeviceBrowser, didAdd device: ICDevice, moreComing: Bool) {
        if let scanner = device as? ICScannerDevice {
            if !discoveredDevices.contains(where: { $0.name == scanner.name }) {
                discoveredDevices.append(scanner)
                foundFirstDevice = true
            }
        }
    }

    func deviceBrowser(_ browser: ICDeviceBrowser, didRemove device: ICDevice, moreGoing: Bool) {}

    // -- ICDeviceDelegate --

    func didRemove(_ device: ICDevice) {}

    // -- Scan Execution --

    func performScan(deviceName: String?, dpi: Int = 150, mode: String = "Color", paperSize: String = "a4") -> [String: Any] {
        // Reset scan state (fresh instance, but belt-and-suspenders)
        self.scanSuccess = false
        self.scanCompleted = false
        self.scanErrorMessage = nil
        self.scannedFiles = []
        self.rawScannedURLs = []
        self.jobDirectoryURL = nil
        self.sessionOpen = false
        self.paperSize = paperSize

        // Create temp output path
        let tmpDir = NSTemporaryDirectory()
        let scanID = UUID().uuidString
        let outPath = "\(tmpDir)edulytics_scan_\(scanID).jpg"
        self.outputPath = outPath

        // Discover devices
        discoveredDevices.removeAll()
        foundFirstDevice = false
        browser.start()

        let discoverDeadline = Date().addingTimeInterval(4.0)
        while Date() < discoverDeadline {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.02))
            if let targetName = deviceName,
               discoveredDevices.contains(where: { $0.name?.contains(targetName) == true }) {
                break
            } else if foundFirstDevice {
                let grace = Date().addingTimeInterval(0.2)
                while Date() < grace {
                    RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.02))
                }
                break
            }
        }

        // CRITICAL: Do NOT stop the browser before requestOpenSession.
        // The browser must remain active to hold the device reference valid.
        // It is stopped after scan completion, mirroring mac_scanner.swift.

        guard let scanner = discoveredDevices.first(where: {
            deviceName == nil || $0.name == deviceName || $0.name?.contains(deviceName!) == true
        }) ?? discoveredDevices.first else {
            browser.stop()
            return ["status": "error", "message": "No scanner found. Check the USB connection and ensure the scanner is powered on."]
        }

        let actualDeviceID = scanner.name ?? "unknown"
        scanner.delegate = self

        fputs("  Requesting session for: \(actualDeviceID)\n", stderr)
        scanner.requestOpenSession()

        // Wait for scan to complete (timeout: 300s for large ADF batches)
        let scanDeadline = Date().addingTimeInterval(300.0)
        while Date() < scanDeadline && !scanCompleted && scanErrorMessage == nil {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.1))
        }

        // Stop browser only after scan is done (mirrors mac_scanner.swift)
        browser.stop()

        if !scanSuccess {
            let msg = scanErrorMessage ?? "Scan timed out. Ensure paper is loaded in the document feeder."
            return ["status": "error", "message": msg]
        }

        // Convert scanned files to base64 JPEG
        var imagesBase64: [String] = []
        var totalBytes: Int = 0

        for filePath in scannedFiles {
            guard FileManager.default.fileExists(atPath: filePath),
                  let fileData = FileManager.default.contents(atPath: filePath),
                  fileData.count > 0 else {
                continue
            }

            // If already JPEG, use directly; otherwise convert
            let ext = (filePath as NSString).pathExtension.lowercased()
            let jpegData: Data?

            if ext == "jpg" || ext == "jpeg" {
                jpegData = fileData
            } else if let imageRep = NSBitmapImageRep(data: fileData) {
                jpegData = imageRep.representation(
                    using: .jpeg,
                    properties: [.compressionFactor: 0.85]
                )
            } else {
                jpegData = fileData
            }

            if let data = jpegData {
                imagesBase64.append(data.base64EncodedString())
                totalBytes += data.count
            }

            // Clean up temp file
            try? FileManager.default.removeItem(atPath: filePath)
        }

        if imagesBase64.isEmpty {
            return ["status": "error", "message": "No pages were scanned. Ensure paper is loaded."]
        }

        fputs("  Scan complete. \(imagesBase64.count) page(s), \(totalBytes / 1024) KB total.\n", stderr)

        return [
            "status": "success",
            "image_base64_list": imagesBase64,
            "image_base64": imagesBase64[0],
            "format": "jpeg",
            "dpi": dpi,
            "mode": mode,
            "device_id": actualDeviceID,
            "size_bytes": totalBytes,
            "filename": "scan_\(dpi)dpi.jpg",
        ]
    }

    // -- ICScannerDeviceDelegate --

    func device(_ device: ICDevice, didOpenSessionWithError error: Error?) {
        if let error = error {
            fputs("  [ERROR] Session open failed: \(error.localizedDescription)\n", stderr)
            scanErrorMessage = "Failed to open scanner session: \(error.localizedDescription)"
            return
        }
        sessionOpen = true
        fputs("  [OK] Session opened. Waiting for scanner hardware...\n", stderr)

        // Dedicated job subfolder to prevent file overwriting
        let uniqueID = UUID().uuidString
        let jobDir = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("scan_job_\(uniqueID)")
        try? FileManager.default.createDirectory(at: jobDir, withIntermediateDirectories: true)
        self.jobDirectoryURL = jobDir
        fputs("  [OK] Job directory: \(jobDir.path)\n", stderr)

        if let scanner = device as? ICScannerDevice {
            scanner.downloadsDirectory = jobDir
            scanner.documentName = "scanned_page"
            scanner.transferMode = .fileBased
        }
    }

    func scannerDeviceDidBecomeAvailable(_ scanner: ICScannerDevice) {
        fputs("  Scanner hardware ready. Available units: \(scanner.availableFunctionalUnitTypes)\n", stderr)

        let unitTypes = scanner.availableFunctionalUnitTypes

        // Prefer Document Feeder (ADF) for sheet-fed scanners like EPSON DS-870
        if unitTypes.contains(NSNumber(value: ICScannerFunctionalUnitType.documentFeeder.rawValue)) {
            fputs("  Selecting Document Feeder (ADF)\n", stderr)
            scanner.requestSelect(.documentFeeder)
        } else if unitTypes.contains(NSNumber(value: ICScannerFunctionalUnitType.flatbed.rawValue)) {
            fputs("  Selecting Flatbed\n", stderr)
            scanner.requestSelect(.flatbed)
        } else if let firstType = unitTypes.first,
                  let unitType = ICScannerFunctionalUnitType(rawValue: (firstType as NSNumber).uintValue) {
            scanner.requestSelect(unitType)
        } else {
            scanErrorMessage = "Scanner has no available scanning units."
        }
    }

    func scannerDevice(_ scanner: ICScannerDevice, didSelect functionalUnit: ICScannerFunctionalUnit, error: Error?) {
        if let error = error {
            scanErrorMessage = "Failed to select scanner unit: \(error.localizedDescription)"
            return
        }

        // Configure ADF settings
        if let adf = functionalUnit as? ICScannerFunctionalUnitDocumentFeeder {
            if adf.supportsDuplexScanning {
                adf.duplexScanningEnabled = true
            }

            let requestedSize = paperSize.lowercased()
            if requestedSize.contains("letter") {
                adf.documentType = .typeUSLetter
            } else if requestedSize.contains("legal") {
                adf.documentType = .typeUSLegal
            } else {
                adf.documentType = .typeA4
            }
        }

        fputs("  Functional unit selected. Starting scan...\n", stderr)
        scanner.requestScan()
    }

    func device(_ device: ICDevice, didCloseSessionWithError error: Error?) {}

    func scannerDevice(_ scanner: ICScannerDevice, didScanTo url: URL) {
        fputs("  [PAGE] Received scan page: \(url.lastPathComponent) (\(url.path))\n", stderr)
        rawScannedURLs.append(url)
    }

    func scannerDevice(_ scanner: ICScannerDevice, didCompleteScanWithError error: Error?) {
        if let error = error {
            fputs("  [WARN] Scan completed with error: \(error.localizedDescription)\n", stderr)
        } else {
            fputs("  [OK] Scan completed without error.\n", stderr)
        }

        fputs("  [DEBUG] rawScannedURLs count: \(rawScannedURLs.count)\n", stderr)
        for (i, url) in rawScannedURLs.enumerated() {
            fputs("  [DEBUG]   rawURL[\(i)]: \(url.path)\n", stderr)
        }
        fputs("  [DEBUG] jobDirectoryURL: \(jobDirectoryURL?.path ?? "NIL")\n", stderr)

        // List job directory contents before processing
        if let jobDir = jobDirectoryURL {
            if let contents = try? FileManager.default.contentsOfDirectory(atPath: jobDir.path) {
                fputs("  [DEBUG] Job directory contents (\(contents.count) files):\n", stderr)
                for f in contents {
                    let fullPath = jobDir.appendingPathComponent(f).path
                    let size = (try? FileManager.default.attributesOfItem(atPath: fullPath)[.size] as? Int) ?? 0
                    fputs("  [DEBUG]   \(f) (\(size) bytes)\n", stderr)
                }
            } else {
                fputs("  [DEBUG] Could not list job directory!\n", stderr)
            }
        }

        processAndOrderScannedFiles()

        fputs("  [DEBUG] scannedFiles count after processing: \(scannedFiles.count)\n", stderr)
        for f in scannedFiles {
            fputs("  [DEBUG]   processed: \(f)\n", stderr)
        }

        if scannedFiles.isEmpty {
            let msg = error != nil
                ? "Scan error: \(error!.localizedDescription)"
                : "No pages scanned. Ensure paper is loaded in the feeder."
            fputs("  [ERROR] \(msg)\n", stderr)
            scanErrorMessage = msg
            scanSuccess = false
        } else {
            fputs("  [OK] ADF batch finished. \(scannedFiles.count) page(s) captured.\n", stderr)
            scanSuccess = true
        }

        scanCompleted = true
        scanner.requestCloseSession()
    }

    private func processAndOrderScannedFiles() {
        guard let jobDir = jobDirectoryURL else {
            fputs("  [ERROR] processAndOrderScannedFiles: jobDirectoryURL is NIL\n", stderr)
            return
        }
        let fm = FileManager.default
        guard let urls = try? fm.contentsOfDirectory(
            at: jobDir,
            includingPropertiesForKeys: [.creationDateKey],
            options: .skipsHiddenFiles
        ) else {
            fputs("  [ERROR] processAndOrderScannedFiles: Could not list job directory at \(jobDir.path)\n", stderr)
            return
        }

        fputs("  [DEBUG] processAndOrderScannedFiles: found \(urls.count) files in job directory\n", stderr)

        // Sort files by creation date, then by natural filename order
        let sortedURLs = urls.sorted { (url1, url2) -> Bool in
            let date1 = (try? url1.resourceValues(forKeys: [.creationDateKey]))?.creationDate ?? .distantPast
            let date2 = (try? url2.resourceValues(forKeys: [.creationDateKey]))?.creationDate ?? .distantPast
            if date1 != date2 { return date1 < date2 }
            return url1.path.localizedStandardCompare(url2.path) == .orderedAscending
        }

        for (idx, rawURL) in sortedURLs.enumerated() {
            let pageIndex = idx + 1
            fputs("  [DEBUG] Processing page \(pageIndex): \(rawURL.lastPathComponent)\n", stderr)

            if let dest = outputPath {
                let destBase = (dest as NSString).deletingPathExtension
                let destExt = (dest as NSString).pathExtension.lowercased()
                let pageDestPath = "\(destBase)_\(pageIndex).\(destExt)"
                let destURL = URL(fileURLWithPath: pageDestPath)
                try? fm.removeItem(at: destURL)

                do {
                    if destExt == "jpg" || destExt == "jpeg" || destExt == "png" {
                        guard let imageData = try? Data(contentsOf: rawURL) else {
                            fputs("  [ERROR] Could not read image data from \(rawURL.path)\n", stderr)
                            continue
                        }
                        fputs("  [DEBUG] Read \(imageData.count) bytes from \(rawURL.lastPathComponent)\n", stderr)

                        guard let imageRep = NSBitmapImageRep(data: imageData) else {
                            fputs("  [ERROR] Could not create NSBitmapImageRep from \(rawURL.lastPathComponent)\n", stderr)
                            continue
                        }

                        let outputData: Data?
                        if destExt == "png" {
                            outputData = imageRep.representation(using: .png, properties: [:])
                        } else {
                            outputData = imageRep.representation(
                                using: .jpeg,
                                properties: [.compressionFactor: 0.85]
                            )
                        }

                        guard let finalData = outputData else {
                            fputs("  [ERROR] Image conversion failed for page \(pageIndex)\n", stderr)
                            continue
                        }
                        try finalData.write(to: destURL)
                        fputs("  [OK] Page \(pageIndex) -> \(pageDestPath) (\(finalData.count) bytes)\n", stderr)
                    } else {
                        try fm.moveItem(at: rawURL, to: destURL)
                        fputs("  [OK] Page \(pageIndex) moved to \(pageDestPath)\n", stderr)
                    }
                    scannedFiles.append(pageDestPath)
                } catch {
                    fputs("  [ERROR] Failed to process page \(pageIndex): \(error.localizedDescription)\n", stderr)
                }
            } else {
                scannedFiles.append(rawURL.path)
            }
        }

        // Clean up temporary job subfolder
        try? fm.removeItem(at: jobDir)
    }

}


// MARK: - HTTP Server (Network.framework)

class ScannerHTTPServer {
    let port: UInt16
    let queue = DispatchQueue(label: "net.edulytics.scanner-agent", qos: .userInteractive)
    var listener: NWListener?

    init(port: UInt16) {
        self.port = port
    }

    func start() {
        let params = NWParameters.tcp
        params.allowLocalEndpointReuse = true

        guard let listener = try? NWListener(using: params, on: NWEndpoint.Port(rawValue: port)!) else {
            colorPrint("  [ERROR] Failed to create listener on port \(port).", .red)
            exit(1)
        }

        self.listener = listener

        listener.stateUpdateHandler = { state in
            switch state {
            case .ready:
                break  // Splash already printed
            case .failed(let error):
                colorPrint("  [ERROR] Listener failed: \(error.localizedDescription)", .red)
                colorPrint("  Check if port \(self.port) is already in use.", .red)
                exit(1)
            default:
                break
            }
        }

        listener.newConnectionHandler = { [weak self] connection in
            self?.handleConnection(connection)
        }

        listener.start(queue: queue)
    }

    private func handleConnection(_ connection: NWConnection) {
        connection.start(queue: queue)
        receiveData(connection: connection, accumulated: Data())
    }

    private func receiveData(connection: NWConnection, accumulated: Data) {
        connection.receive(minimumIncompleteLength: 1, maximumLength: 1_048_576) { [weak self] content, _, isComplete, error in
            guard let self = self else { return }

            var data = accumulated
            if let content = content {
                data.append(content)
            }

            if error != nil {
                connection.cancel()
                return
            }

            // Check if we have the complete HTTP request
            if let requestString = String(data: data, encoding: .utf8) {
                // For GET requests: complete when we see \r\n\r\n
                // For POST requests: complete when we have Content-Length bytes of body
                if requestString.contains("\r\n\r\n") {
                    let parts = requestString.components(separatedBy: "\r\n\r\n")
                    let headers = parts[0]
                    let body = parts.count > 1 ? parts[1...].joined(separator: "\r\n\r\n") : ""

                    // Check Content-Length for POST requests
                    if headers.uppercased().contains("POST") {
                        if let clRange = headers.range(of: "Content-Length:", options: .caseInsensitive) {
                            let afterCL = headers[clRange.upperBound...]
                            let lineEnd = afterCL.firstIndex(of: "\r") ?? afterCL.endIndex
                            let clValue = afterCL[..<lineEnd].trimmingCharacters(in: .whitespaces)
                            if let contentLength = Int(clValue), body.utf8.count < contentLength {
                                // Need more data
                                if !isComplete {
                                    self.receiveData(connection: connection, accumulated: data)
                                }
                                return
                            }
                        }
                    }

                    self.routeRequest(requestString, connection: connection)
                    return
                }
            }

            if isComplete {
                if !data.isEmpty, let requestString = String(data: data, encoding: .utf8) {
                    self.routeRequest(requestString, connection: connection)
                } else {
                    connection.cancel()
                }
            } else {
                self.receiveData(connection: connection, accumulated: data)
            }
        }
    }

    private func routeRequest(_ raw: String, connection: NWConnection) {
        // Parse HTTP request line
        let lines = raw.components(separatedBy: "\r\n")
        guard let requestLine = lines.first else {
            sendResponse(connection: connection, status: 400, body: "{\"error\":\"Bad request\"}")
            return
        }

        let tokens = requestLine.split(separator: " ")
        guard tokens.count >= 2 else {
            sendResponse(connection: connection, status: 400, body: "{\"error\":\"Bad request\"}")
            return
        }

        let method = String(tokens[0]).uppercased()
        let rawPath = String(tokens[1])
        let path = rawPath.split(separator: "?").first.map(String.init) ?? rawPath
        let cleanPath = path.lowercased().trimmingCharacters(in: CharacterSet(charactersIn: "/"))

        // Extract Origin header for CORS
        let origin = extractHeader(from: raw, name: "Origin") ?? ""

        // Handle preflight
        if method == "OPTIONS" {
            logRequest(method, path, 204)
            sendResponse(connection: connection, status: 204, body: "", origin: origin)
            return
        }

        // Route
        switch cleanPath {
        case "ping":
            logRequest(method, path, 200)
            let json = jsonString([
                "status": "ok",
                "agent": "edulytics-scanner",
                "version": AGENT_VERSION,
                "platform": "macos",
            ])
            sendResponse(connection: connection, status: 200, body: json, origin: origin)

        case "devices":
            logRequest(method, path, 200)
            handleDevices(connection: connection, origin: origin)

        case "scan":
            if method != "POST" {
                logRequest(method, path, 405)
                sendResponse(connection: connection, status: 405, body: "{\"error\":\"Method not allowed. Use POST.\"}", origin: origin)
                return
            }
            handleScan(raw: raw, connection: connection, origin: origin)

        default:
            logRequest(method, path, 404)
            sendResponse(connection: connection, status: 404, body: "{\"error\":\"Not found\"}", origin: origin)
        }
    }

    // -- /devices --

    private func handleDevices(connection: NWConnection, origin: String) {
        // Run discovery on main thread (ICA requires RunLoop)
        DispatchQueue.main.async {
            let devices = ScannerManager.shared.getDevices()
            let response: [String: Any] = [
                "sane_installed": true,
                "platform": "macos",
                "devices": devices,
            ]
            let json = jsonString(response)
            self.sendResponse(connection: connection, status: 200, body: json, origin: origin)
        }
    }

    // -- /scan --

    private func handleScan(raw: String, connection: NWConnection, origin: String) {
        // Parse body
        let bodyParts = raw.components(separatedBy: "\r\n\r\n")
        let body = bodyParts.count > 1 ? bodyParts[1...].joined(separator: "\r\n\r\n") : ""
        let params = parseJSONBody(body)

        let deviceId = params["device_id"] as? String ?? ""
        let dpi = params["dpi"] as? Int ?? 150
        let mode = params["mode"] as? String ?? "Color"

        fputs("\n  Scan request: device=\(deviceId) dpi=\(dpi) mode=\(mode)\n", stderr)

        // CRITICAL: Run the scan in a SUBPROCESS.
        // ICA (ImageCaptureCore) accumulates stale state at the process level.
        // After one scan, the ICA objects cannot open a new session in the same process.
        // Spawning a subprocess gives each scan a completely fresh ICA context,
        // exactly like the proven mac_scanner CLI pattern.
        DispatchQueue.global(qos: .userInitiated).async {
            let execPath = ProcessInfo.processInfo.arguments[0]

            let task = Process()
            task.executableURL = URL(fileURLWithPath: execPath)
            task.arguments = [
                "--scan-subprocess",
                "--device", deviceId,
                "--dpi", String(dpi),
                "--mode", mode,
            ]

            let stdoutPipe = Pipe()
            let stderrPipe = Pipe()
            task.standardOutput = stdoutPipe
            task.standardError = stderrPipe

            do {
                try task.run()
            } catch {
                let errJson = jsonString(["status": "error", "message": "Failed to launch scan subprocess: \(error.localizedDescription)"])
                logRequest("POST", "/scan", 500)
                fputs("  [ERROR] Subprocess launch failed: \(error.localizedDescription)\n", stderr)
                self.sendResponse(connection: connection, status: 500, body: errJson, origin: origin)
                return
            }

            // CRITICAL: Read both pipes concurrently BEFORE calling waitUntilExit.
            // If we call waitUntilExit first, the subprocess blocks writing to stdout
            // when the OS pipe buffer fills (~64KB). With 10 pages of base64 JPEG
            // (~7MB), the buffer fills immediately causing a permanent deadlock.
            var stdoutData = Data()
            var stderrData = Data()
            let group = DispatchGroup()

            group.enter()
            DispatchQueue.global(qos: .utility).async {
                stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
                group.leave()
            }

            group.enter()
            DispatchQueue.global(qos: .utility).async {
                stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()
                group.leave()
            }

            group.wait()
            task.waitUntilExit()

            // Forward subprocess stderr to our stderr
            if let stderrStr = String(data: stderrData, encoding: .utf8), !stderrStr.isEmpty {
                fputs(stderrStr, stderr)
            }

            // Parse subprocess stdout as JSON result
            guard let stdoutStr = String(data: stdoutData, encoding: .utf8),
                  !stdoutStr.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                let errJson = jsonString(["status": "error", "message": "Scan subprocess produced no output (exit code \(task.terminationStatus))"])
                logRequest("POST", "/scan", 500)
                fputs("  [ERROR] Subprocess produced no stdout output\n", stderr)
                self.sendResponse(connection: connection, status: 500, body: errJson, origin: origin)
                return
            }

            // Extract JSON from stdout (skip any non-JSON lines)
            let trimmed = stdoutStr.trimmingCharacters(in: .whitespacesAndNewlines)
            let jsonOutput: String
            if let startIdx = trimmed.firstIndex(of: "{"),
               let endIdx = trimmed.lastIndex(of: "}") {
                jsonOutput = String(trimmed[startIdx...endIdx])
            } else {
                jsonOutput = trimmed
            }

            let status = task.terminationStatus == 0 ? 200 : 500
            logRequest("POST", "/scan", status)

            if status == 500 {
                fputs("  [ERROR] Scan subprocess exited with code \(task.terminationStatus)\n", stderr)
            }

            self.sendResponse(connection: connection, status: status, body: jsonOutput, origin: origin)
        }
    }


    // -- HTTP Response --

    private func sendResponse(connection: NWConnection, status: Int, body: String, origin: String = "") {
        let statusText: String
        switch status {
        case 200: statusText = "OK"
        case 204: statusText = "No Content"
        case 400: statusText = "Bad Request"
        case 404: statusText = "Not Found"
        case 405: statusText = "Method Not Allowed"
        case 500: statusText = "Internal Server Error"
        default:  statusText = "Unknown"
        }

        // CORS origin matching
        let corsOrigin: String
        if ALLOWED_ORIGINS.contains(origin) || origin.hasSuffix(".edulytics.net") {
            corsOrigin = origin
        } else {
            corsOrigin = "*"
        }

        let bodyData = body.data(using: .utf8) ?? Data()

        var response = "HTTP/1.1 \(status) \(statusText)\r\n"
        response += "Content-Type: application/json; charset=utf-8\r\n"
        response += "Content-Length: \(bodyData.count)\r\n"
        response += "Access-Control-Allow-Origin: \(corsOrigin)\r\n"
        response += "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        response += "Access-Control-Allow-Headers: Content-Type, Authorization\r\n"
        response += "Access-Control-Max-Age: 86400\r\n"
        response += "Connection: close\r\n"
        response += "\r\n"

        var fullData = response.data(using: .utf8) ?? Data()
        fullData.append(bodyData)

        connection.send(content: fullData, completion: .contentProcessed({ _ in
            connection.cancel()
        }))
    }

    // -- Header Parsing --

    private func extractHeader(from raw: String, name: String) -> String? {
        let searchKey = name.lowercased() + ":"
        for line in raw.components(separatedBy: "\r\n") {
            if line.lowercased().hasPrefix(searchKey) {
                return line.dropFirst(searchKey.count).trimmingCharacters(in: .whitespaces)
            }
        }
        return nil
    }
}


// MARK: - Splash Screen & Entry Point

func printSplash() {
    print("")
    colorPrint("   ___  ____  __    ____  _  _  ____     ___  ___  ____  ____  ", .cyan)
    colorPrint("  / _ \\|  _ \\| |  |_  _|| \\| |/ ___)   / __>/ _ \\|  _ \\|  _ \\ ", .cyan)
    colorPrint(" ( (_) )    /| |_  _)(_  )  ( \\___ \\  ( (__( (_) )    /)(   / ", .cyan)
    colorPrint("  \\___/|_|\\_\\|___|____||_|\\_|(____/   \\___>\\___/|_|\\_\\ |_|\\_\\ ", .cyan)

    colorPrint("  ----------------------------------------------------------------", .darkCyan)
    colorPrint("    Scanner Agent  |  v\(AGENT_VERSION)  |  ICA  |  macOS Native", .white)
    colorPrint("  ----------------------------------------------------------------", .darkCyan)

    print("")
    print("\(ConsoleColor.green.rawValue)  [OK]\(ConsoleColor.reset.rawValue) Listening on  http://127.0.0.1:\(AGENT_PORT)/")
    print("\(ConsoleColor.green.rawValue)  [OK]\(ConsoleColor.reset.rawValue) Serving       https://edulytics.net")

    print("")
    colorPrint("  Endpoints:", .darkGray)
    colorPrint("    GET  /ping     health check", .darkGray)
    colorPrint("    GET  /devices  list connected scanners", .darkGray)
    colorPrint("    POST /scan     batch-scan all ADF pages", .darkGray)
    print("")
    colorPrint("  Press Ctrl+C to stop.", .darkGray)
    colorPrint("  ----------------------------------------------------------------", .darkCyan)
    print("")
}

// -- Graceful shutdown --

signal(SIGINT) { _ in
    colorPrint("\n  [STOPPED] Scanner Agent shut down cleanly.", .yellow)
    exit(0)
}

signal(SIGTERM) { _ in
    colorPrint("\n  [STOPPED] Scanner Agent shut down cleanly.", .yellow)
    exit(0)
}

// -- Main --

let args = CommandLine.arguments

// ── Subprocess scan mode ──
// When invoked with --scan-subprocess, run a single scan and exit.
// This gives each scan a completely fresh ICA process context.
if args.contains("--scan-subprocess") {
    let devName = args.firstIndex(of: "--device").flatMap { $0 + 1 < args.count ? args[$0 + 1] : nil }
    let dpiStr = args.firstIndex(of: "--dpi").flatMap { $0 + 1 < args.count ? args[$0 + 1] : nil }
    let mode = args.firstIndex(of: "--mode").flatMap { $0 + 1 < args.count ? args[$0 + 1] : nil } ?? "Color"
    let dpi = Int(dpiStr ?? "150") ?? 150

    let manager = ScannerManager()
    let result = manager.performScan(
        deviceName: devName,
        dpi: dpi,
        mode: mode,
        paperSize: "a4"
    )

    // Output result as JSON to stdout
    let json = jsonString(result)
    print(json)

    let success = (result["status"] as? String) == "success"
    exit(success ? 0 : 1)
}

// ── Device list mode (--list) ──
if args.contains("--list") {
    let manager = ScannerManager()
    let devices = manager.getDevices(forceRefresh: true)
    let json = jsonString(["sane_installed": true, "platform": "macos", "devices": devices])
    print(json)
    exit(0)
}

// ── HTTP Server mode (default) ──

printSplash()

let server = ScannerHTTPServer(port: AGENT_PORT)
server.start()

// Keep the main RunLoop alive (required for ICA delegate callbacks on /devices)
RunLoop.current.run()
