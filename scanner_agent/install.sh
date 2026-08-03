#!/bin/bash
# ---------------------------------------------------------------------------
# install.sh -- Edulytics Scanner Agent Installer for macOS
#
# Clients run this after downloading to clear Gatekeeper restrictions
# and install the scanner agent for easy access.
#
# Usage:
#   curl -sL <download_url>/install.sh | bash
#   -- or --
#   bash install.sh
# ---------------------------------------------------------------------------

set -euo pipefail

AGENT_NAME="EdulyticsScanner"
INSTALL_DIR="${HOME}/.edulytics"

NC='\033[0m'
CYAN='\033[36m'
GREEN='\033[32m'
RED='\033[31m'
GRAY='\033[90m'
WHITE='\033[37m'
DKCYAN='\033[36;2m'

echo ""
echo -e "${CYAN}   ___  ____  __    ____  _  _  ____     ___  ___  ____  ____  ${NC}"
echo -e "${CYAN}  / _ \\|  _ \\| |  |_  _|| \\| |/ ___)   / __>/ _ \\|  _ \\|  _ \\ ${NC}"
echo -e "${CYAN} ( (_) )    /| |_  _)(_  )  ( \\___ \\  ( (__( (_) )    /)(   / ${NC}"
echo -e "${CYAN}  \\___/|_|\\_\\|___|____||_|\\_|(____/   \\___>\\___/|_|\\_\\ |_|\\_\\ ${NC}"
echo -e "${DKCYAN}  ----------------------------------------------------------------${NC}"
echo -e "${WHITE}    Scanner Agent Installer  |  macOS${NC}"
echo -e "${DKCYAN}  ----------------------------------------------------------------${NC}"
echo ""

# Locate the binary (same directory as this script, or current dir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_PATH=""

if [ -f "${SCRIPT_DIR}/${AGENT_NAME}" ]; then
    AGENT_PATH="${SCRIPT_DIR}/${AGENT_NAME}"
elif [ -f "./${AGENT_NAME}" ]; then
    AGENT_PATH="$(pwd)/${AGENT_NAME}"
elif [ -f "${HOME}/Downloads/${AGENT_NAME}" ]; then
    AGENT_PATH="${HOME}/Downloads/${AGENT_NAME}"
else
    echo -e "  ${RED}[ERROR]${NC} Cannot find ${AGENT_NAME}."
    echo -e "  Place it in the same folder as this script, or in ~/Downloads."
    exit 1
fi

echo -e "  ${GREEN}[1/4]${NC} Found agent: ${AGENT_PATH}"

# Clear quarantine attribute (Gatekeeper)
echo -e "  ${GREEN}[2/4]${NC} Clearing Gatekeeper quarantine..."
xattr -cr "${AGENT_PATH}" 2>/dev/null || true

# Set executable permissions
echo -e "  ${GREEN}[3/4]${NC} Setting executable permissions..."
chmod +x "${AGENT_PATH}"

# Install to ~/.edulytics
echo -e "  ${GREEN}[4/4]${NC} Installing to ${INSTALL_DIR}/..."
mkdir -p "${INSTALL_DIR}"
cp "${AGENT_PATH}" "${INSTALL_DIR}/${AGENT_NAME}"
chmod +x "${INSTALL_DIR}/${AGENT_NAME}"
xattr -cr "${INSTALL_DIR}/${AGENT_NAME}" 2>/dev/null || true

echo ""
echo -e "  ${DKCYAN}----------------------------------------------------------------${NC}"
echo -e "  ${GREEN}[OK]${NC} Installation complete."
echo ""
echo -e "  ${WHITE}To start the scanner agent:${NC}"
echo ""
echo -e "    ${CYAN}${INSTALL_DIR}/${AGENT_NAME}${NC}"
echo ""
echo -e "  ${GRAY}Then visit https://edulytics.net/ -- your scanner will be${NC}"
echo -e "  ${GRAY}detected automatically. Keep this terminal open while scanning.${NC}"
echo -e "  ${DKCYAN}----------------------------------------------------------------${NC}"
echo ""

# Ask if they want to start now
read -p "  Start the scanner agent now? [Y/n] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo ""
    exec "${INSTALL_DIR}/${AGENT_NAME}"
fi
