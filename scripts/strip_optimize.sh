#!/bin/bash

# Strip Optimization Script for pandoc-ui
# Safely reduces binary size while preserving PySide6/Qt functionality
# 
# Usage:
#   ./scripts/strip_optimize.sh [binary_path] [level]
#   
# Levels:
#   conservative (default) - Only remove debug symbols, safest for PySide6
#   moderate               - Remove more symbols, test before production use
#   aggressive            - Maximum compression, high risk for Qt applications

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SUFFIX=".pre-strip"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Show usage
show_usage() {
    cat << EOF
Strip Optimization Tool for pandoc-ui

USAGE:
    $0 [OPTIONS] [binary_path] [level]

ARGUMENTS:
    binary_path     Path to the binary file to optimize (required)
    level          Optimization level (optional, default: conservative)

OPTIMIZATION LEVELS:
    conservative   Remove only debug symbols (recommended for PySide6)
                  - Safe for production use
                  - 5-15% size reduction
                  - No functionality risk
                  
    moderate      Remove debug + some non-essential symbols  
                  - Test before production use
                  - 10-25% size reduction
                  - Low functionality risk
                  
    aggressive    Maximum symbol removal
                  - High risk for Qt applications
                  - 15-40% size reduction
                  - Use only for testing

OPTIONS:
    -h, --help     Show this help message
    -v, --verbose  Enable verbose output
    -b, --backup   Create backup before stripping (default: yes)
    --no-backup    Skip backup creation
    --test         Test mode - show what would be done
    --verify       Verify binary functionality after stripping

EXAMPLES:
    $0 dist/linux/pandoc-ui-linux-1.0.0
    $0 dist/linux/pandoc-ui-linux-1.0.0 conservative
    $0 --verbose --verify dist/linux/pandoc-ui-linux-1.0.0 moderate
    $0 --test dist/linux/pandoc-ui-linux-1.0.0 aggressive

EOF
}

# Parse arguments
BINARY_PATH=""
STRIP_LEVEL="conservative"
VERBOSE=false
CREATE_BACKUP=true
TEST_MODE=false
VERIFY_AFTER=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -b|--backup)
            CREATE_BACKUP=true
            shift
            ;;
        --no-backup)
            CREATE_BACKUP=false
            shift
            ;;
        --test)
            TEST_MODE=true
            shift
            ;;
        --verify)
            VERIFY_AFTER=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [[ -z "$BINARY_PATH" ]]; then
                BINARY_PATH="$1"
            elif [[ "$1" =~ ^(conservative|moderate|aggressive)$ ]]; then
                STRIP_LEVEL="$1"
            else
                log_error "Invalid argument: $1"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$BINARY_PATH" ]]; then
    log_error "Binary path is required"
    show_usage
    exit 1
fi

if [[ ! -f "$BINARY_PATH" ]]; then
    log_error "Binary file not found: $BINARY_PATH"
    exit 1
fi

# Check if strip is available
if ! command -v strip &> /dev/null; then
    log_error "strip command not found. Please install binutils package:"
    echo "  Ubuntu/Debian: sudo apt-get install binutils"
    echo "  Fedora/CentOS: sudo dnf install binutils"
    echo "  macOS: xcode-select --install"
    exit 1
fi

# Detect platform and set appropriate strip options
PLATFORM="$(uname -s)"
case "$PLATFORM" in
    Linux*)
        STRIP_CMD="strip"
        ;;
    Darwin*)
        STRIP_CMD="strip"
        log_info "Detected macOS - using system strip"
        ;;
    *)
        log_error "Unsupported platform: $PLATFORM"
        exit 1
        ;;
esac

# Define strip levels
declare -A STRIP_OPTIONS
STRIP_OPTIONS[conservative]="--strip-debug"
STRIP_OPTIONS[moderate]="--strip-debug --strip-unneeded"
STRIP_OPTIONS[aggressive]="--strip-all"

# Get strip options for selected level
STRIP_ARGS="${STRIP_OPTIONS[$STRIP_LEVEL]}"

if [[ -z "$STRIP_ARGS" ]]; then
    log_error "Invalid strip level: $STRIP_LEVEL"
    log_error "Valid levels: conservative, moderate, aggressive"
    exit 1
fi

# macOS-specific adjustments
if [[ "$PLATFORM" == "Darwin" ]]; then
    case "$STRIP_LEVEL" in
        conservative)
            STRIP_ARGS="-S"  # Strip debug symbols
            ;;
        moderate)
            STRIP_ARGS="-S -x"  # Strip debug and local symbols
            ;;
        aggressive)
            STRIP_ARGS="-s"  # Strip all symbols
            ;;
    esac
fi

# Display operation details
log_info "Strip Optimization Details:"
echo "  Binary: $BINARY_PATH"
echo "  Level: $STRIP_LEVEL"
echo "  Platform: $PLATFORM"
echo "  Strip command: $STRIP_CMD $STRIP_ARGS"
echo "  Backup: $([ "$CREATE_BACKUP" = true ] && echo "Yes" || echo "No")"
echo "  Test mode: $([ "$TEST_MODE" = true ] && echo "Yes" || echo "No")"
echo ""

# Get original file info
ORIGINAL_SIZE=$(stat -c%s "$BINARY_PATH" 2>/dev/null || stat -f%z "$BINARY_PATH")
ORIGINAL_SIZE_MB=$(echo "scale=2; $ORIGINAL_SIZE / 1024 / 1024" | bc)

log_info "Original file size: ${ORIGINAL_SIZE_MB} MB"

# Check if this is a PySide6/Qt application (safety check)
if file "$BINARY_PATH" | grep -i qt > /dev/null || strings "$BINARY_PATH" 2>/dev/null | grep -i "pyside\|qt" > /dev/null; then
    log_warning "Detected Qt/PySide6 application"
    if [[ "$STRIP_LEVEL" == "aggressive" ]]; then
        log_warning "Aggressive stripping may break Qt applications!"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled"
            exit 0
        fi
    fi
fi

# Test mode - show what would be done
if [[ "$TEST_MODE" = true ]]; then
    log_info "TEST MODE - No changes will be made"
    echo "Would execute: $STRIP_CMD $STRIP_ARGS $BINARY_PATH"
    if [[ "$CREATE_BACKUP" = true ]]; then
        echo "Would create backup: $BINARY_PATH$BACKUP_SUFFIX"
    fi
    exit 0
fi

# Create backup if requested
if [[ "$CREATE_BACKUP" = true ]]; then
    log_info "Creating backup..."
    cp "$BINARY_PATH" "$BINARY_PATH$BACKUP_SUFFIX"
    log_success "Backup created: $BINARY_PATH$BACKUP_SUFFIX"
fi

# Perform the strip operation
log_info "Stripping binary with level: $STRIP_LEVEL"

if [[ "$VERBOSE" = true ]]; then
    echo "Executing: $STRIP_CMD $STRIP_ARGS $BINARY_PATH"
fi

# Execute strip command
if $STRIP_CMD $STRIP_ARGS "$BINARY_PATH"; then
    # Get new file size
    NEW_SIZE=$(stat -c%s "$BINARY_PATH" 2>/dev/null || stat -f%z "$BINARY_PATH")
    NEW_SIZE_MB=$(echo "scale=2; $NEW_SIZE / 1024 / 1024" | bc)
    
    # Calculate reduction
    SIZE_REDUCTION=$((ORIGINAL_SIZE - NEW_SIZE))
    REDUCTION_PERCENT=$(echo "scale=1; $SIZE_REDUCTION * 100 / $ORIGINAL_SIZE" | bc)
    REDUCTION_MB=$(echo "scale=2; $SIZE_REDUCTION / 1024 / 1024" | bc)
    
    log_success "Strip operation completed successfully!"
    echo ""
    echo "📊 Size Reduction Summary:"
    echo "  Original size: ${ORIGINAL_SIZE_MB} MB"
    echo "  New size: ${NEW_SIZE_MB} MB"
    echo "  Reduction: ${REDUCTION_MB} MB (${REDUCTION_PERCENT}%)"
    echo ""
    
    # Verify binary functionality if requested
    if [[ "$VERIFY_AFTER" = true ]]; then
        log_info "Verifying binary functionality..."
        
        # Basic file integrity check
        if [[ ! -x "$BINARY_PATH" ]]; then
            log_error "Binary is no longer executable!"
            if [[ "$CREATE_BACKUP" = true ]]; then
                log_info "Restoring from backup..."
                cp "$BINARY_PATH$BACKUP_SUFFIX" "$BINARY_PATH"
                log_warning "Binary restored from backup"
            fi
            exit 1
        fi
        
        # Try to run --help (if supported)
        if timeout 5 "$BINARY_PATH" --help >/dev/null 2>&1; then
            log_success "Binary verification passed (--help works)"
        else
            log_warning "Binary verification failed (--help test)"
            log_warning "This may be normal for GUI-only applications"
            log_info "Manual testing recommended"
        fi
    fi
    
    # Clean up backup if operation was successful and not requested to keep
    if [[ "$CREATE_BACKUP" = true ]] && [[ "$VERIFY_AFTER" = true ]]; then
        read -p "Remove backup file? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$|^$ ]]; then
            rm -f "$BINARY_PATH$BACKUP_SUFFIX"
            log_info "Backup file removed"
        else
            log_info "Backup kept: $BINARY_PATH$BACKUP_SUFFIX"
        fi
    fi
    
    log_success "Optimization complete!"
    
else
    log_error "Strip operation failed!"
    
    # Restore backup if it exists
    if [[ "$CREATE_BACKUP" = true ]] && [[ -f "$BINARY_PATH$BACKUP_SUFFIX" ]]; then
        log_info "Restoring from backup..."
        cp "$BINARY_PATH$BACKUP_SUFFIX" "$BINARY_PATH"
        log_warning "Binary restored from backup"
    fi
    
    exit 1
fi