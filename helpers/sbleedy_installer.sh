#!/bin/bash

VENV_DIR="${PWD}"

# Function to check if a Python version exists
check_python_version() {
    if command -v $1 &> /dev/null
    then
        echo "$1 is installed."
    else
        echo "$1 is not installed."
    fi
}

# Ask for user confirmation to proceed
confirm() {
    read -p "$1 (y/n): " choice
    case "$choice" in 
      y|Y ) return 0;;
      * ) return 1;;
    esac
}

# Check if Python 3.10 is installed
check_python_version "python3.10"

# Check if Python 2.7 is installed
check_python_version "python2.7"

# Ask if user wants to install Python 3.10 if it's not installed
if ! command -v python3.10 &> /dev/null; then
    if confirm "Python 3.10 is not installed. Would you like to install it?"; then
        # Install required build dependencies for Python
        sudo apt update
        sudo apt install -y \
            build-essential \
            libssl-dev \
            zlib1g-dev \
            libncurses5-dev \
            libncursesw5-dev \
            libreadline-dev \
            libsqlite3-dev \
            libgdbm-dev \
            libdb5.3-dev \
            libbz2-dev \
            libexpat1-dev \
            liblzma-dev \
            tk-dev \
            libffi-dev \
            curl \
            bluez-tools \
            bluez-hcidump \
            libbluetooth-dev \
            git \
            gcc \
            python3-pip \
            python3-setuptools \
            python3-pydbus

        # Download Python 3.10 source code from python.org
        PYTHON_VERSION="3.10.0"
        cd /usr/src
        sudo curl -O https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz

        # Extract the downloaded tarball
        sudo tar xzf Python-$PYTHON_VERSION.tgz

        # Compile and install Python 3.10
        cd Python-$PYTHON_VERSION
        sudo ./configure --enable-optimizations
        sudo make -j$(nproc)
        sudo make altinstall

        # Clean up source files
        sudo rm -rf /usr/src/Python-$PYTHON_VERSION.tgz /usr/src/Python-$PYTHON_VERSION

        # Verify Python 3.10 installation
        python3.10 --version
    else
        echo "Skipping Python 3.10 installation."
    fi
fi

# Ask if user wants to install Python 2.7 if it's not installed
if ! command -v python2.7 &> /dev/null; then
    if confirm "Python 2.7 is not installed. Would you like to install it?"; then
        sudo apt update
        sudo apt install -y python2.7
        python2.7 --version
    else
        echo "Skipping Python 2.7 installation."
    fi
fi

# Install pip for Python 3.10 and Python 2.7 if they are installed
if command -v python3.10 &> /dev/null; then
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3.10 get-pip.py
    python3.10 -m pip install virtualenv
fi

if command -v python2.7 &> /dev/null; then
    curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
    python2.7 get-pip.py
    python2.7 -m pip install virtualenv
fi

# Ask user for confirmation to create virtual environments
if confirm "Would you like to create virtual environments (venv3 for Python 3.10 and venv2 for Python 2.7)?"; then
    # Create virtual environment venv3 with Python 3.10 in the current directory
    if command -v python3.10 &> /dev/null; then
        python3.10 -m virtualenv -p python3.10 "$VENV_DIR/venv3"
        echo "Created virtual environment venv3 with Python 3.10 at $VENV_DIR."
    fi

    # Create virtual environment venv2 with Python 2.7 in the current directory
    if command -v python2.7 &> /dev/null; then
        python2.7 -m pip install setuptools
        python2.7 -m virtualenv -p python2.7 "$VENV_DIR/venv2"
        echo "Created virtual environment venv2 with Python 2.7 at $VENV_DIR."
    fi
else
    echo "Skipping virtual environment creation."
fi

# Install dependencies in venv3 (Python 3.10)
if [ -d "$VENV_DIR/venv3" ]; then
    echo "Activating venv3..."
    source "$VENV_DIR/venv3/bin/activate"
    echo "Installing dependencies with pip in venv3..."
    python setup.py install && pip install .
    deactivate
    echo "Dependencies installed in venv3."
fi

# Install requirements in venv2 (Python 2.7)
if [ -d "$VENV_DIR/venv2" ]; then
    echo "Activating venv2..."
    source "$VENV_DIR/venv2/bin/activate"
    echo "Changing directory to modules/sweyntooth..."
    cd "$VENV_DIR/modules/sweyntooth"
    echo "Installing sweyntooth in venv2..."
    sudo ./install_sweyntooth.sh
    deactivate
    echo "Dependencies installed in venv2."
fi

# Clean up
rm -f "$VENV_DIR/get-pip.py"

echo "Script completed."
