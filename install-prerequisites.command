#!/bin/bash
# HiBob MCP Extension — Prerequisites Installer
# Run this once before installing the .mcpb extension
#
# Usage: bash install-prerequisites.sh

set -e

echo "================================================"
echo "  HiBob MCP Extension — Prerequisites Installer"
echo "================================================"
echo ""

# Check if Homebrew is installed
if ! command -v brew &>/dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo "Homebrew installed."
else
    echo "Homebrew — already installed."
fi

# Check Python version
NEED_PYTHON=true
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        echo "Python $PY_VERSION — OK."
        NEED_PYTHON=false
    else
        echo "Python $PY_VERSION found, but 3.10+ is required."
    fi
fi

if [ "$NEED_PYTHON" = true ]; then
    echo "Installing Python 3.12..."
    brew install python@3.12
    # Ensure python3 points to 3.12
    if [ -f /opt/homebrew/bin/python3.12 ] && ! [ -f /opt/homebrew/bin/python3 ]; then
        ln -sf /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3
    fi
    echo "Python 3.12 installed."
fi

# Check uv
if command -v uv &>/dev/null || [ -f /opt/homebrew/bin/uv ]; then
    echo "uv — already installed."
else
    echo "Installing uv..."
    brew install uv
    echo "uv installed."
fi

echo ""
echo "================================================"
echo "  All prerequisites installed!"
echo ""
echo "  Next steps:"
echo "  1. Double-click hibob-readonly-1.1.0.mcpb"
echo "  2. Enter the credentials when prompted"
echo "  3. Restart Claude Desktop (Cmd+Q, then reopen)"
echo "  4. Use Code mode to query HiBob"
echo "================================================"
