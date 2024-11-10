#!/bin/bash

VENV_DIR="${PWD}"
SUCCESS=()
ERRORS=()

# Function to print colored messages
print_message() {
    COLOR=$1
    MESSAGE=$2
    RESET='\033[0m'
    echo -e "${COLOR}${MESSAGE}${RESET}"
}

# Colors for messages
GREEN='\033[0;32m'
RED='\033[0;31m'

# Function to check if a Python version exists
check_python_version() {
    if command -v $1 &> /dev/null
    then
        print_message $GREEN "$1 is installed."
        SUCCESS+=("$1 is installed.")
    else
        print_message $RED "$1 is not installed."
        ERRORS+=("$1 is not installed.")
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

# Check and optionally install Python versions
check_and_install_python() {
    local python_version=$1
    local install_cmd=$2

    if ! command -v $python_version &> /dev/null; then
        if confirm "$python_version is not installed. Would you like to install it?"; then
            eval $install_cmd
            if command -v $python_version &> /dev/null; then
                print_message $GREEN "$python_version installed successfully."
                SUCCESS+=("$python_version installed.")
            else
                print_message $RED "Failed to install $python_version."
                ERRORS+=("Failed to install $python_version.")
            fi
        else
            print_message $RED "Skipping $python_version installation."
            ERRORS+=("Skipped $python_version installation.")
        fi
    fi
}

# Install Python 3.10 if not installed
check_and_install_python "python3.10" "sudo apt update && sudo apt install -y build-essential libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev libffi-dev curl && cd /usr/src && sudo curl -O https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz && sudo tar xzf Python-3.10.0.tgz && cd Python-3.10.0 && sudo ./configure --enable-optimizations && sudo make -j$(nproc) && sudo make altinstall && sudo rm -rf /usr/src/Python-3.10.0*"

# Install Python 2.7 if not installed
check_and_install_python "python2.7" "sudo apt update && sudo apt install -y python2.7"

# Install pip and virtualenv for Python versions if installed
install_pip_and_virtualenv() {
    local python_version=$1
    local get_pip_url=$2

    if command -v $python_version &> /dev/null; then
        curl -s $get_pip_url -o get-pip.py
        $python_version get-pip.py && $python_version -m pip install virtualenv
        rm -f get-pip.py
        print_message $GREEN "Pip and virtualenv installed for $python_version."
        SUCCESS+=("Pip and virtualenv installed for $python_version.")
    else
        ERRORS+=("$python_version is not available for pip/virtualenv installation.")
    fi
}

install_pip_and_virtualenv "python3.10" "https://bootstrap.pypa.io/get-pip.py"
install_pip_and_virtualenv "python2.7" "https://bootstrap.pypa.io/pip/2.7/get-pip.py"

# Check and create virtual environments
create_virtualenv() {
    local venv_name=$1
    local python_version=$2

    if [ ! -d "$VENV_DIR/$venv_name" ]; then
        if command -v $python_version &> /dev/null; then
            $python_version -m virtualenv -p $python_version "$VENV_DIR/$venv_name"
            print_message $GREEN "Created virtual environment $venv_name with $python_version at $VENV_DIR."
            SUCCESS+=("$venv_name created with $python_version.")
        else
            print_message $RED "$python_version is not available for virtual environment creation."
            ERRORS+=("$venv_name creation failed.")
        fi
    else
        print_message $GREEN "Virtual environment $venv_name already exists."
        SUCCESS+=("$venv_name already exists.")
    fi
}

create_virtualenv "venv3" "python3.10"
create_virtualenv "venv2" "python2.7"

# Install requirements in venv2 (Python 2.7)
if [ -d "$VENV_DIR/venv2" ]; then
    source "$VENV_DIR/venv2/bin/activate"
    cd "$VENV_DIR/modules/sweyntooth"
    sudo apt install python2-dev gcc g++ make -y
    pip install -r requirements.txt
    cd ./libs/smp_server/ && make clean && make build && make install && cd ../../
    SUCCESS+=("Dependencies installed in venv2.")
    deactivate
fi

# Install dependencies in venv3 (Python 3.10)
if [ -d "$VENV_DIR/venv3" ]; then
    source "$VENV_DIR/venv3/bin/activate"
    git submodule update --init --recursive
    if [ -d "$VENV_DIR/helpers/pybluez" ]; then
        cd "$VENV_DIR/helpers/pybluez" && pip install . && cd ../../
        SUCCESS+=("pybluez installed.")
    else
        print_message $RED "Error: helpers/pybluez directory not found."
        ERRORS+=("helpers/pybluez directory not found.")
    fi
    if [ -d "$VENV_DIR/helpers/bluing" ]; then
        cd "$VENV_DIR/helpers/bluing" && env CFLAGS="-lm" pip install . && cd ../../
        SUCCESS+=("bluing installed.")
    else
        print_message $RED "Error: bluing directory not found."
        ERRORS+=("bluing directory not found.")
    fi
    pip install .
    SUCCESS+=("Sbleedy installed in venv3.")
    deactivate
fi

# Summary of script completion
echo
echo "Summary of Installation:"
for msg in "${SUCCESS[@]}"; do
    print_message $GREEN "✔ $msg"
done
for msg in "${ERRORS[@]}"; do
    print_message $RED "✖ $msg"
done
