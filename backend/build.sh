#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Update the package manager and install system dependencies
# This is the key step to fix the "missing libraries" error
apt-get update && apt-get install -y \
    libgtk-4-1 \
    libgraphene-1.0-0 \
    libgstgl-1.0-0 \
    libgstcodecparsers-1.0-0 \
    libenchant-2-2 \
    libsecret-1-0 \
    libmanette-0.2-0 \
    libgles2 \
    # Add any other missing libraries from your error log here

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browser binaries (without the --with-deps flag)
playwright install