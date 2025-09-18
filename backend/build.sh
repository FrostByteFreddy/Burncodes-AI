#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install all Python dependencies from requirements.txt
pip install -r requirements.txt

# 2. Install Playwright's browser binaries AND its system dependencies
# The --with-deps flag is the key part that installs the missing libraries
playwright install --with-deps
