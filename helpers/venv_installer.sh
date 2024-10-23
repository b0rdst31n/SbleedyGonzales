#!/bin/bash

# Update the package list
sudo apt update

# Install prerequisites
sudo apt install -y software-properties-common

# Add deadsnakes PPA for Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.10 and Python 2.7
sudo apt install -y python3.10 python2.7

# Verify Python versions
python3.10 --version
python2.7 --version

# Install pip for Python 3.10 and Python 2.7
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3.10 get-pip.py
sudo python2.7 get-pip.py

# Install virtualenv for both Python versions
sudo python3.10 -m pip install virtualenv
sudo python2.7 -m pip install virtualenv

# Create virtual environment venv3 with Python 3.10
python3.10 -m virtualenv -p python3.10 venv3

# Create virtual environment venv2 with Python 2.7
python2.7 -m virtualenv -p python2.7 venv2

# Clean up
rm get-pip.py

# Confirm the virtual environments are created
echo "Virtual environments 'venv3' and 'venv2' have been created."
