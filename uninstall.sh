#!/usr/bin/env bash
#
# LinkedIn Spider - Uninstallation Script
#
# This script removes LinkedIn Spider installations.
# Supports both System and Development installations.
#
# Usage: ./uninstall.sh [--force]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Installation paths
SYSTEM_INSTALL_DIR="$HOME/.linkedin-spider-installation"
SYSTEM_COMMAND="$HOME/.local/bin/linkedin-spider"
SYSTEM_MARKER="$SCRIPT_DIR/.system-installed"
DEV_MARKER="$SCRIPT_DIR/.dev-installed"

# Print functions
print_header() {
    echo -e "\n${CYAN}================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================================${NC}\n"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Banner
print_header "LinkedIn Spider - Uninstallation"
echo -e "  🕷️  Removing LinkedIn Spider from your system\n"

# Check for force flag
FORCE=false
if [[ "$1" == "--force" ]]; then
    FORCE=true
    print_warning "Force mode enabled - skipping confirmations"
    echo ""
fi

# Detect installation type
SYSTEM_INSTALLED=false
DEV_INSTALLED=false

if [[ -f "$SYSTEM_MARKER" ]] || [[ -d "$SYSTEM_INSTALL_DIR" ]] || [[ -f "$SYSTEM_COMMAND" ]]; then
    SYSTEM_INSTALLED=true
fi

if [[ -f "$DEV_MARKER" ]]; then
    DEV_INSTALLED=true
fi

# Check if anything is installed
if [[ "$SYSTEM_INSTALLED" == false ]] && [[ "$DEV_INSTALLED" == false ]]; then
    print_warning "No LinkedIn Spider installation found"
    print_info "Nothing to uninstall"
    exit 0
fi

# Show what will be uninstalled
print_header "Detected Installations"

if [[ "$SYSTEM_INSTALLED" == true ]]; then
    echo -e "${CYAN}System Installation:${NC}"
    [[ -f "$SYSTEM_COMMAND" ]] && echo -e "  • Command: ${YELLOW}$SYSTEM_COMMAND${NC}"
    [[ -d "$SYSTEM_INSTALL_DIR" ]] && echo -e "  • Files: ${YELLOW}$SYSTEM_INSTALL_DIR${NC}"
    [[ -f "$SYSTEM_MARKER" ]] && echo -e "  • Marker: ${YELLOW}$SYSTEM_MARKER${NC}"
    echo ""
fi

if [[ "$DEV_INSTALLED" == true ]]; then
    echo -e "${CYAN}Development Installation:${NC}"
    echo -e "  • Poetry environment in project"
    echo -e "  • Marker: ${YELLOW}$DEV_MARKER${NC}"
    echo ""
fi

# Confirm uninstallation
if [[ "$FORCE" == false ]]; then
    echo -e "${RED}This will permanently remove LinkedIn Spider!${NC}"
    echo ""
    read -p "$(echo -e ${YELLOW}Continue with uninstallation? [y/N]: ${NC})" -n 1 -r
    echo ""
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Uninstallation cancelled"
        exit 0
    fi
fi

# Uninstall System Installation
if [[ "$SYSTEM_INSTALLED" == true ]]; then
    print_header "Removing System Installation"
    
    # Remove command
    if [[ -f "$SYSTEM_COMMAND" ]]; then
        print_step "Removing command: linkedin-spider"
        rm -f "$SYSTEM_COMMAND"
        print_success "Command removed"
    fi
    
    # Remove installation directory
    if [[ -d "$SYSTEM_INSTALL_DIR" ]]; then
        print_step "Removing installation directory..."
        rm -rf "$SYSTEM_INSTALL_DIR"
        print_success "Installation directory removed"
    fi
    
    # Remove marker
    if [[ -f "$SYSTEM_MARKER" ]]; then
        rm -f "$SYSTEM_MARKER"
        print_success "System installation marker removed"
    fi
    
    echo ""
fi

# Uninstall Development Installation
if [[ "$DEV_INSTALLED" == true ]]; then
    print_header "Removing Development Installation"
    
    # Check if Poetry is available
    if command -v poetry &> /dev/null; then
        print_step "Removing Poetry virtual environment..."
        
        # Ensure Poetry is in PATH
        export PATH="$HOME/.local/bin:$PATH"
        
        # Try to remove the virtual environment
        if poetry env list &> /dev/null; then
            poetry env remove --all 2>/dev/null || true
            print_success "Poetry virtual environment removed"
        else
            print_info "No Poetry virtual environment found"
        fi
    else
        print_warning "Poetry not found - skipping virtual environment removal"
    fi
    
    # Remove marker
    if [[ -f "$DEV_MARKER" ]]; then
        rm -f "$DEV_MARKER"
        print_success "Development installation marker removed"
    fi
    
    # Remove .env (with confirmation)
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        if [[ "$FORCE" == false ]]; then
            echo ""
            read -p "$(echo -e ${YELLOW}Remove .env file? [y/N]: ${NC})" -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$SCRIPT_DIR/.env"
                print_success ".env file removed"
            else
                print_info ".env file kept"
            fi
        else
            rm -f "$SCRIPT_DIR/.env"
            print_success ".env file removed"
        fi
    fi
    
    echo ""
fi

# Optional: Remove data directory
if [[ -d "$SCRIPT_DIR/data" ]]; then
    print_header "Data Directory Found"
    print_warning "Scraped data found at: $SCRIPT_DIR/data"
    
    if [[ "$FORCE" == false ]]; then
        echo ""
        read -p "$(echo -e ${YELLOW}"Remove data directory? [y/N]: "${NC})" -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$SCRIPT_DIR/data"
            print_success "Data directory removed"
        else
            print_info "Data directory kept"
        fi
    else
        rm -rf "$SCRIPT_DIR/data"
        print_success "Data directory removed"
    fi
    echo ""
fi

# Completion
print_header "Uninstallation Complete! 🎉"

echo -e "${GREEN}✓ LinkedIn Spider has been removed${NC}\n"

if [[ "$SYSTEM_INSTALLED" == true ]]; then
    print_info "System installation removed:"
    echo -e "  • ${YELLOW}linkedin-spider${NC} command is no longer available"
    echo ""
fi

if [[ "$DEV_INSTALLED" == true ]]; then
    print_info "Development installation removed:"
    echo -e "  • Poetry environment cleaned"
    echo -e "  • You can still reinstall with: ${YELLOW}./install.sh --dev${NC}"
    echo ""
fi

print_info "To reinstall LinkedIn Spider:"
echo -e "  ${YELLOW}./install.sh${NC}          # Interactive installation"
echo -e "  ${YELLOW}./install.sh --system${NC} # System installation"
echo -e "  ${YELLOW}./install.sh --dev${NC}    # Development installation"
echo ""

print_success "Thank you for using LinkedIn Spider!"
echo ""

exit 0
