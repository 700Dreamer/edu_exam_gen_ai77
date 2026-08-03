#!/bin/bash
# ---------------------------------------------------------------------------
# build_mac_agent.sh -- Compiles EdulyticsScanner.swift into a universal
# macOS binary (arm64 + x86_64) with zero dependencies.
#
# Usage:
#   ./scanner_agent/build_mac_agent.sh
#
# Output:
#   scanner_agent/EdulyticsScanner  (universal Mach-O binary)
# ---------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="${SCRIPT_DIR}/EdulyticsScanner.swift"
OUT="${SCRIPT_DIR}/EdulyticsScanner"
OUT_ARM64="${SCRIPT_DIR}/.build_arm64"
OUT_X86="${SCRIPT_DIR}/.build_x86_64"

echo ""
echo "  Edulytics Scanner Agent -- Build"
echo "  --------------------------------"
echo ""

# Verify source exists
if [ ! -f "${SRC}" ]; then
    echo "  [ERROR] Source not found: ${SRC}"
    exit 1
fi

# Check for Xcode command line tools
if ! command -v swiftc &> /dev/null; then
    echo "  [ERROR] swiftc not found. Install Xcode Command Line Tools:"
    echo "          xcode-select --install"
    exit 1
fi

SWIFT_VERSION=$(swiftc --version 2>&1 | head -1)
echo "  Compiler: ${SWIFT_VERSION}"
echo ""

# Compile for arm64 (Apple Silicon)
echo "  [1/4] Compiling for arm64..."
swiftc \
    -target arm64-apple-macos12.0 \
    -O \
    -whole-module-optimization \
    -framework Foundation \
    -framework Network \
    -framework ImageCaptureCore \
    -framework AppKit \
    -o "${OUT_ARM64}" \
    "${SRC}"
echo "        arm64 binary: $(du -h "${OUT_ARM64}" | cut -f1)"

# Compile for x86_64 (Intel)
echo "  [2/4] Compiling for x86_64..."
swiftc \
    -target x86_64-apple-macos12.0 \
    -O \
    -whole-module-optimization \
    -framework Foundation \
    -framework Network \
    -framework ImageCaptureCore \
    -framework AppKit \
    -o "${OUT_X86}" \
    "${SRC}"
echo "        x86_64 binary: $(du -h "${OUT_X86}" | cut -f1)"

# Create universal binary
echo "  [3/4] Creating universal binary..."
lipo -create "${OUT_ARM64}" "${OUT_X86}" -output "${OUT}"

# Strip debug symbols
echo "  [4/6] Stripping debug symbols..."
strip -x "${OUT}" 2>/dev/null || true

# Ad-hoc code sign (prevents Gatekeeper "damaged" rejection on other Macs)
echo "  [5/6] Ad-hoc code signing..."
codesign --force --sign - --timestamp=none "${OUT}" 2>/dev/null
SIGN_STATUS=$(codesign -dv "${OUT}" 2>&1 | grep "Signature" || echo "signed (ad-hoc)")
echo "        ${SIGN_STATUS}"

# Remove quarantine attribute if present (safe for distribution)
echo "  [6/6] Clearing quarantine attribute..."
xattr -cr "${OUT}" 2>/dev/null || true

# Clean intermediate files
rm -f "${OUT_ARM64}" "${OUT_X86}"

# Set executable permissions
chmod +x "${OUT}"

# Verify
UNIVERSAL_INFO=$(file "${OUT}")
FINAL_SIZE=$(du -h "${OUT}" | cut -f1)

echo ""
echo "  --------------------------------"
echo "  [OK] Build complete."
echo ""
echo "  Output: ${OUT}"
echo "  Size:   ${FINAL_SIZE}"
echo "  Type:   ${UNIVERSAL_INFO}"
echo ""
echo "  Run with:"
echo "    ${OUT}"
echo ""
echo "  Client installation:"
echo "    1. Send EdulyticsScanner to client"
echo "    2. Client runs:  xattr -cr EdulyticsScanner && chmod +x EdulyticsScanner"
echo "    3. Client runs:  ./EdulyticsScanner"
echo ""

