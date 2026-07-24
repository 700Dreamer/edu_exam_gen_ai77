import Foundation
import ImageCaptureCore
import AppKit

class ScannerManager: NSObject, ICDeviceBrowserDelegate, ICScannerDeviceDelegate, ICDeviceDelegate {
    let browser = ICDeviceBrowser()
    var devices: [ICScannerDevice] = []
    var foundFirstDevice = false
    
    var outputPath: String?
    var paperSize: String = "a4"
    var scanSuccess = false
    var scanCompleted = false
    var scanErrorMessage: String?
    var scannedFiles: [String] = []
    var rawScannedURLs: [URL] = []
    var jobDirectoryURL: URL?
    var sessionOpen = false

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

    func discoverDevices(timeout: TimeInterval = 3.0) -> [ICScannerDevice] {
        devices.removeAll()
        foundFirstDevice = false
        browser.start()
        
        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.1))
            // Exit early once we've found at least one device (wait 200ms for stragglers)
            if foundFirstDevice {
                let grace = Date().addingTimeInterval(0.2)
                while Date() < grace {
                    RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.05))
                }
                break
            }
        }
        browser.stop()
        return devices
    }

    // MARK: - ICDeviceBrowserDelegate
    func deviceBrowser(_ browser: ICDeviceBrowser, didAdd device: ICDevice, moreComing: Bool) {
        if let scanner = device as? ICScannerDevice {
            if !devices.contains(where: { $0.name == scanner.name }) {
                devices.append(scanner)
                foundFirstDevice = true
            }
        }
    }

    func deviceBrowser(_ browser: ICDeviceBrowser, didRemove device: ICDevice, moreGoing: Bool) {}

    // MARK: - ICDeviceDelegate
    func didRemove(_ device: ICDevice) {}

    // MARK: - Scan Execution
    func performScan(deviceName: String?, targetPath: String, paperSize: String = "a4", timeout: TimeInterval = 90.0) -> Bool {
        self.paperSize = paperSize
        devices.removeAll()
        foundFirstDevice = false
        browser.start()
        
        // Allow device browser to discover devices — exit immediately when target device is found
        let discoverDeadline = Date().addingTimeInterval(4.0)
        while Date() < discoverDeadline {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.02))
            if let targetName = deviceName, devices.contains(where: { $0.name?.contains(targetName) == true }) {
                break
            } else if foundFirstDevice {
                let grace = Date().addingTimeInterval(0.1)
                while Date() < grace {
                    RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.02))
                }
                break
            }
        }

        guard let scanner = devices.first(where: { deviceName == nil || $0.name == deviceName || $0.name?.contains(deviceName!) == true }) ?? devices.first else {
            scanErrorMessage = "No matching scanner found."
            browser.stop()
            return false
        }

        self.outputPath = targetPath
        scanner.delegate = self
        
        fputs("DEBUG: Requesting open session for: \(scanner.name ?? "unknown")\n", stderr)
        scanner.requestOpenSession()

        let deadline = Date().addingTimeInterval(timeout)
        while Date() < deadline && !scanCompleted && scanErrorMessage == nil {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.1))
        }
        
        browser.stop()

        if !scanSuccess && scanErrorMessage == nil {
            scanErrorMessage = "Scan timed out. Ensure paper is loaded in the document feeder."
            return false
        }
        return scanSuccess
    }

    // MARK: - ICScannerDeviceDelegate

    // Step 1: Session opened successfully
    func device(_ device: ICDevice, didOpenSessionWithError error: Error?) {
        if let error = error {
            scanErrorMessage = "Failed to open session: \(error.localizedDescription)"
            return
        }
        sessionOpen = true
        fputs("DEBUG: Session opened successfully. Waiting for scanner to become available...\n", stderr)
        
        // Configure download destination with a dedicated job subfolder to prevent file overwriting
        let uniqueID = UUID().uuidString
        let jobDir = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("scan_job_\(uniqueID)")
        try? FileManager.default.createDirectory(at: jobDir, withIntermediateDirectories: true)
        self.jobDirectoryURL = jobDir

        if let scanner = device as? ICScannerDevice {
            scanner.downloadsDirectory = jobDir
            scanner.documentName = "scanned_page"
            scanner.transferMode = .fileBased
        }
        // Now we wait for scannerDeviceDidBecomeAvailable callback
    }
    
    // Step 2: Scanner hardware is ready — select functional unit (ADF or Flatbed)
    func scannerDeviceDidBecomeAvailable(_ scanner: ICScannerDevice) {
        fputs("DEBUG: Scanner became available. Functional unit types: \(scanner.availableFunctionalUnitTypes)\n", stderr)
        
        let unitTypes = scanner.availableFunctionalUnitTypes
        
        // Prefer Document Feeder (ADF) for sheet-fed scanners like Epson DS-870
        if unitTypes.contains(NSNumber(value: ICScannerFunctionalUnitType.documentFeeder.rawValue)) {
            fputs("DEBUG: Selecting Document Feeder (ADF) unit\n", stderr)
            scanner.requestSelect(.documentFeeder)
        } else if unitTypes.contains(NSNumber(value: ICScannerFunctionalUnitType.flatbed.rawValue)) {
            fputs("DEBUG: Selecting Flatbed unit\n", stderr)
            scanner.requestSelect(.flatbed)
        } else if let firstType = unitTypes.first as? NSNumber,
                  let unitType = ICScannerFunctionalUnitType(rawValue: firstType.uintValue) {
            fputs("DEBUG: Selecting first available unit type: \(firstType)\n", stderr)
            scanner.requestSelect(unitType)
        } else {
            fputs("DEBUG: No functional unit types available!\n", stderr)
            scanErrorMessage = "Scanner has no available scanning units."
        }
    }
    
    // Step 3: Functional unit selected — now trigger the actual scan
    func scannerDevice(_ scanner: ICScannerDevice, didSelect functionalUnit: ICScannerFunctionalUnit, error: Error?) {
        if let error = error {
            fputs("DEBUG: Failed to select functional unit: \(error.localizedDescription)\n", stderr)
            scanErrorMessage = "Failed to select scanner unit: \(error.localizedDescription)"
            return
        }
        
        if let adf = functionalUnit as? ICScannerFunctionalUnitDocumentFeeder {
            fputs("DEBUG: Initial ADF documentType: \(adf.documentType.rawValue)\n", stderr)
            if adf.supportsDuplexScanning {
                fputs("DEBUG: Enabling Duplex Scanning on ADF\n", stderr)
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
            fputs("DEBUG: Updated ADF documentType to: \(adf.documentType.rawValue)\n", stderr)
        }
        
        fputs("DEBUG: Functional unit selected (type=\(functionalUnit.type.rawValue)). Triggering scan...\n", stderr)
        scanner.requestScan()
    }

    func device(_ device: ICDevice, didCloseSessionWithError error: Error?) {
        fputs("DEBUG: Session closed\n", stderr)
    }

    // Step 4: Scanned page received
    func scannerDevice(_ scanner: ICScannerDevice, didScanTo url: URL) {
        fputs("DEBUG: Received raw hardware scan: \(url.lastPathComponent)\n", stderr)
        rawScannedURLs.append(url)
    }

    func scannerDevice(_ scanner: ICScannerDevice, didCompleteScanWithError error: Error?) {
        if let error = error {
            fputs("DEBUG: Scan completed with error: \(error.localizedDescription)\n", stderr)
        }
        
        // Sort and convert all collected files in exact sequential creation order
        processAndOrderScannedFiles()

        if scannedFiles.isEmpty {
            scanErrorMessage = error != nil ? "Scan error: \(error!.localizedDescription)" : "No pages scanned. Ensure paper is loaded in the feeder."
            scanSuccess = false
        } else {
            fputs("DEBUG: ADF batch finished. Processed \(scannedFiles.count) pages in correct sequence.\n", stderr)
            scanSuccess = true
        }
        
        scanCompleted = true
        scanner.requestCloseSession()
    }

    func processAndOrderScannedFiles() {
        guard let jobDir = jobDirectoryURL else { return }
        let fm = FileManager.default
        guard let urls = try? fm.contentsOfDirectory(at: jobDir, includingPropertiesForKeys: [URLResourceKey.creationDateKey], options: .skipsHiddenFiles) else { return }
        
        // Sort files by creation date, then by natural filename numerical order
        let sortedURLs = urls.sorted { (url1, url2) -> Bool in
            let date1 = (try? url1.resourceValues(forKeys: [URLResourceKey.creationDateKey]))?.creationDate ?? Date.distantPast
            let date2 = (try? url2.resourceValues(forKeys: [URLResourceKey.creationDateKey]))?.creationDate ?? Date.distantPast
            if date1 != date2 {
                return date1 < date2
            }
            return url1.path.localizedStandardCompare(url2.path) == .orderedAscending
        }
        
        fputs("DEBUG: Sorting \(sortedURLs.count) raw files for conversion...\n", stderr)
        
        for (idx, rawURL) in sortedURLs.enumerated() {
            let pageIndex = idx + 1
            if let dest = outputPath {
                let destExt = (dest as NSString).pathExtension.lowercased()
                let destBase = (dest as NSString).deletingPathExtension
                let pageDestPath = "\(destBase)_\(pageIndex).\(destExt)"
                let destURL = URL(fileURLWithPath: pageDestPath)
                try? fm.removeItem(at: destURL)
                
                do {
                    if destExt == "jpg" || destExt == "jpeg" || destExt == "png" {
                        guard let imageData = try? Data(contentsOf: rawURL),
                              let imageRep = NSBitmapImageRep(data: imageData) else {
                            fputs("DEBUG: Failed to read image data for \(rawURL.lastPathComponent)\n", stderr)
                            continue
                        }
                        
                        let outputData: Data?
                        if destExt == "png" {
                            outputData = imageRep.representation(using: NSBitmapImageRep.FileType.png, properties: [:])
                        } else {
                            outputData = imageRep.representation(using: NSBitmapImageRep.FileType.jpeg, properties: [NSBitmapImageRep.PropertyKey.compressionFactor: 0.85])
                        }
                        
                        guard let finalData = outputData else { continue }
                        try finalData.write(to: destURL)
                        fputs("DEBUG: Converted page \(pageIndex) (\(rawURL.lastPathComponent)) -> \(pageDestPath)\n", stderr)
                    } else {
                        try fm.moveItem(at: rawURL, to: destURL)
                    }
                    scannedFiles.append(pageDestPath)
                } catch {
                    fputs("DEBUG: Failed to process page \(pageIndex): \(error.localizedDescription)\n", stderr)
                }
            } else {
                scannedFiles.append(rawURL.path)
            }
        }
        
        // Clean up temporary job subfolder
        try? fm.removeItem(at: jobDir)
    }
}

// MARK: - CLI Entry
let args = CommandLine.arguments

if args.contains("--list") {
    let manager = ScannerManager()
    let list = manager.discoverDevices(timeout: 3.0)
    var jsonList: [[String: String]] = []
    for d in list {
        let devName = d.name ?? "mac_scanner"
        let vendor = devName.components(separatedBy: " ").first ?? "Epson"
        jsonList.append([
            "device_id": devName,
            "vendor": vendor,
            "model": devName,
            "device_type": "macOS ICA Scanner"
        ])
    }
    if let data = try? JSONSerialization.data(withJSONObject: jsonList, options: .prettyPrinted),
       let str = String(data: data, encoding: .utf8) {
        print(str)
    } else {
        print("[]")
    }
    exit(0)
} else if let scanIdx = args.firstIndex(of: "--scan"), scanIdx + 1 < args.count {
    let outPath = args[scanIdx + 1]
    let devName = args.firstIndex(of: "--device").flatMap { $0 + 1 < args.count ? args[$0 + 1] : nil }
    let paperSize = args.firstIndex(of: "--paper-size").flatMap { $0 + 1 < args.count ? args[$0 + 1] : nil } ?? "a4"
    
    let manager = ScannerManager()
    let ok = manager.performScan(deviceName: devName, targetPath: outPath, paperSize: paperSize)
    if ok {
        let filePathsStr = manager.scannedFiles.map { "\"\($0)\"" }.joined(separator: ", ")
        print("{\"status\": \"success\", \"files\": [\(filePathsStr)]}")
        exit(0)
    } else {
        let msg = manager.scanErrorMessage ?? "Unknown scan error"
        print("{\"status\": \"error\", \"message\": \"\(msg)\"}")
        exit(1)
    }
} else {
    print("Usage: mac_scanner --list OR mac_scanner --scan <output_path> [--device <device_name>]")
    exit(1)
}
