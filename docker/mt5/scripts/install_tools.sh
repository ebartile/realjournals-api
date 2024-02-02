#!/bin/bash

# Check if Wine is installed, if not, install it
if ! command -v wine &>/dev/null; then
    echo "Wine is not installed. Installing Wine..."
    # Insert commands to install Wine here based on your Ubuntu focal setup
    # For example: sudo apt install wine
fi

# Set Python version
PYTHON_VERSION="3.9.2"  # Replace with your desired Python version

# Add i386 architecture and update apt
dpkg --add-architecture i386

cd /dockerstartup

# Download and install Python components
for msifile in core dev exe lib path pip tcltk tools; do
    wget -nv "https://www.python.org/ftp/python/$PYTHON_VERSION/amd64/${msifile}.msi"
    wine64 msiexec /i "${msifile}.msi" /qb TARGETDIR=/dockerstartup/
    rm "${msifile}.msi"
done