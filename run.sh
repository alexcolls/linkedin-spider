#!/usr/bin/env bash
#
# LinkedIn Spider - Run Script
#
# This script checks for installation and runs the CLI.
# If not installed, it runs install.sh first.
#
# Usage: ./run.sh [--help]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Installation markers
SYSTEM_MARKER="$SCRIPT_DIR/.system-installed"
DEV_MARKER="$SCRIPT_DIR/.dev-installed"

# Print functions
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Show help
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo -e "${CYAN}LinkedIn Spider - Run Script${NC}\n"
    echo "Usage:"
    echo "  ./run.sh          Run LinkedIn Spider (installs if needed)"
    echo "  ./run.sh --help   Show this help message"
    echo ""
    echo "Installation:"
    echo "  If not installed, this script will automatically run ./install.sh"
    echo "  to guide you through the installation process."
    echo ""
    echo "Manual installation:"
    echo "  ./install.sh --system  # System-wide installation"
    echo "  ./install.sh --dev     # Development installation"
    echo ""
    exit 0
fi

# Check for installation
if [[ ! -f "$SYSTEM_MARKER" ]] && [[ ! -f "$DEV_MARKER" ]]; then
    echo -e "${CYAN}╭──────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│                                                  │${NC}"
    echo -e "${CYAN}│  LinkedIn Spider - First Run Setup               │${NC}"
    echo -e "${CYAN}│                                                  │${NC}"
    echo -e "${CYAN}╰──────────────────────────────────────────────────╯${NC}\n"
    
    print_info "LinkedIn Spider is not installed yet."
    print_info "Starting installation process...\n"
    
    # Run install.sh
    if [[ -x "$SCRIPT_DIR/install.sh" ]]; then
        exec "$SCRIPT_DIR/install.sh"
    else
        print_error "install.sh not found or not executable"
        print_info "Please run: chmod +x install.sh && ./install.sh"
        exit 1
    fi
fi

# Check which installation type
if [[ -f "$DEV_MARKER" ]]; then
    # Development installation exists - prioritize it for run.sh
    
    # Show info if both installations are present
    if [[ -f "$SYSTEM_MARKER" ]]; then
        print_info "Both installations detected:"
        echo -e "  ${GREEN}✓${NC} System command: ${YELLOW}linkedin-spider${NC}"
        echo -e "  ${GREEN}✓${NC} Development mode: ${YELLOW}./run.sh${NC} (using this)"
        echo ""
    fi
    
    # Ensure Poetry is in PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    # Check if Poetry is available
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry not found"
        print_info "Please install Poetry: https://python-poetry.org/docs/#installation"
        exit 1
    fi
    
    # Run the CLI
    print_info "Starting LinkedIn Spider (development mode)...\n"
    exec poetry run python -m linkedin_spider "$@"
fi

# Only system installation exists
if [[ -f "$SYSTEM_MARKER" ]]; then
    print_error "Only system installation detected!"
    print_info "LinkedIn Spider is installed globally as '${GREEN}linkedin-spider${NC}'"
    echo ""
    print_info "Please use: ${GREEN}linkedin-spider${NC}"
    print_info "Not: ./run.sh"
    echo ""
    print_warning "Note: ./run.sh requires development installation"
    print_info "To install development mode: ${YELLOW}./install.sh --dev${NC}"
    echo ""
    exit 1
fi

# Should not reach here
print_error "Unknown installation state"
print_info "Please reinstall: ./install.sh"
exit 1
