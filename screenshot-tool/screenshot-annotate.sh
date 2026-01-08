#!/bin/bash
#
# screenshot-annotate.sh
# A macOS screenshot utility with ShareX-style window/element highlighting
#
# Usage:
#   ./screenshot-annotate.sh              - Take screenshot and save to disk
#   ./screenshot-annotate.sh --annotate   - Annotate screenshot and save to disk
#   ./screenshot-annotate.sh --no-save    - Take screenshot for clipboard only
#
# For hotkey setup, create an Automator Quick Action or use Hammerspoon/Raycast.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHAREX_SCRIPT="${SCRIPT_DIR}/screenshot-sharex.py"

# Use mise-managed Python (dynamically resolved for Alfred/Karabiner compatibility)
MISE="/opt/homebrew/bin/mise"
if [[ -x "$MISE" ]]; then
    PYTHON="$("$MISE" which python3 2>/dev/null)"
fi
# Fall back to system python3 if mise isn't available or didn't return a path
if [[ -z "$PYTHON" || ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

ANNOTATE_MODE=false
INSTALL_MODE=false
NO_SAVE_MODE=false
TIMEOUT=30

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --annotate|-a)
            ANNOTATE_MODE=true
            shift
            ;;
        --no-save)
            NO_SAVE_MODE=true
            shift
            ;;
        --install|-i)
            INSTALL_MODE=true
            shift
            ;;
        --timeout|-t)
            TIMEOUT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --annotate, -a       Open screenshot in Shottr for annotation before copying"
            echo "  --no-save            Do not save screenshot to disk (clipboard only)"
            echo "  --timeout, -t SECS   Timeout in seconds (default: 30, 0 = no timeout)"
            echo "  --install, -i        Install Python dependencies"
            echo "  --help, -h           Show this help message"
            echo ""
            echo "Controls:"
            echo "  - Move mouse to highlight (element if found, else window)"
            echo "  - Click to capture highlighted item"
            echo "  - Drag to select a custom region"
            echo "  - Space to cycle mode: Auto → Window → Element → Region"
            echo "  - Escape to cancel (or wait for timeout)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check script exists
if [[ ! -f "$SHAREX_SCRIPT" ]]; then
    echo "Error: Script not found at $SHAREX_SCRIPT"
    exit 1
fi

# Install mode
if [[ "$INSTALL_MODE" == true ]]; then
    exec "$PYTHON" "$SHAREX_SCRIPT" --install
fi

# Check for required Python modules - if missing, the Python script will prompt to install
if ! "$PYTHON" -c "import objc, Quartz, AppKit" 2>/dev/null; then
    echo "Dependencies not installed. Running setup..."
    exec "$PYTHON" "$SHAREX_SCRIPT"
fi

# Build arguments and run
ARGS="--timeout $TIMEOUT"
if [[ "$ANNOTATE_MODE" == true ]]; then
    ARGS="$ARGS --annotate"
fi
if [[ "$NO_SAVE_MODE" == true ]]; then
    ARGS="$ARGS --no-save"
fi
if [[ "$ANNOTATE_MODE" == false && "$NO_SAVE_MODE" == false ]]; then
    ARGS="$ARGS --check-shift"
fi

exec "$PYTHON" "$SHAREX_SCRIPT" $ARGS
