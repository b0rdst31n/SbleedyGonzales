#!/bin/bash

while [[ $# -gt 0 ]]; do
    case $1 in
        --http_proxy)
            http_proxy="$2"
            shift 2
            ;;
        --https_proxy)
            https_proxy="$2"
            shift 2
            ;;
        --no_proxy)
            no_proxy="$2"
            shift 2
            ;;
        --pip_proxy)
            PIP_PROXY="$2"
            shift 2
            ;;
        --pip_cert)
            PIP_CERT="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

export http_proxy
export https_proxy
export no_proxy
export PIP_PROXY

if [ -n "$http_proxy" ]; then
    echo "Acquire::http::Proxy \"$http_proxy\";" | sudo tee /etc/apt/apt.conf.d/01proxy
fi

sudo apt-get -y update #&& sudo apt-get -y upgrade

sudo apt-get install -y tzdata software-properties-common build-essential libssl-dev zlib1g-dev libncurses5-dev \
     libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev libbz2-dev libexpat1-dev liblzma-dev tk-dev libffi-dev \
     curl python2.7 python2-dev gcc wget g++ make git bluez bluetooth usbutils libbluetooth-dev cmake libcairo2-dev \
     pkg-config libgirepository1.0-dev libdbus-1-dev bluez-tools python3-cairo-dev rfkill meson patchelf bluez adb python-is-python3

sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

MAIN_DIR="$(dirname "$(realpath "$0")")/.."
MAIN_DIR="$(realpath "${MAIN_DIR}")"

TMP_DIR=$(mktemp -d)
cd $TMP_DIR

if ! command -v python3.10 &> /dev/null; then
    wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz
    tar -xf Python-3.10.0.tgz
    cd Python-3.10.0
    ./configure --enable-optimizations
    make -j $(nproc)
    sudo make altinstall
    cd ..
    #sudo rm -rf Python-3.10.0*
else
    echo "Python 3.10 is already installed."
fi

python2.7 --version
python3.10 --version

python2.7 -m pip config set global.cert "$PIP_CERT"
python3.10 -m pip config set global.cert "$PIP_CERT"

if ! command -v python2.7 -m pip &> /dev/null; then
    wget https://bootstrap.pypa.io/pip/2.7/get-pip.py -O get-pip.py
    wget https://files.pythonhosted.org/packages/27/79/8a850fe3496446ff0d584327ae44e7500daf6764ca1a382d2d02789accf7/pip-20.3.4-py2.py3-none-any.whl
    wget https://files.pythonhosted.org/packages/e1/b7/182161210a13158cd3ccc41ee19aadef54496b74f2817cc147006ec932b4/setuptools-44.1.1-py2.py3-none-any.whl
    wget https://files.pythonhosted.org/packages/27/d6/003e593296a85fd6ed616ed962795b2f87709c3eee2bca4f6d0fe55c6d00/wheel-0.37.1-py2.py3-none-any.whl

    python2.7 get-pip.py "pip-20.3.4-py2.py3-none-any.whl" "setuptools-44.1.1-py2.py3-none-any.whl" "wheel-0.37.1-py2.py3-none-any.whl" --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
    python2.7 -m pip install virtualenv
    rm -f get-pip.py
else
    echo "Pip for Python 2.7 is already installed."
    python2.7 -m pip install virtualenv
fi

if ! command -v python3.10 -m pip &> /dev/null; then
    sudo apt-get install -y python3-pip
    python3.10 -m pip install --upgrade pip --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
    python3.10 -m pip install virtualenv
else
    echo "Pip for Python 3.10 is already installed."
    python3.10 -m pip install virtualenv
fi

# Add /home/kali/.local/bin to the PATH if not already added
if [[ ":$PATH:" != *":/home/kali/.local/bin:"* ]]; then
    echo 'export PATH="$PATH:/home/kali/.local/bin"' >> ~/.bashrc
    source ~/.bashrc
fi

python3.10 -m virtualenv ${MAIN_DIR}/venv3
python2.7 -m virtualenv ${MAIN_DIR}/venv2

source ${MAIN_DIR}/venv2/bin/activate
cd ${MAIN_DIR}/modules/sweyntooth
pip install -r requirements.txt
cd libs/smp_server/
make all && make install
cd ../../
deactivate

source ${MAIN_DIR}/venv3/bin/activate
sudo rm -rf /var/lib/apt/lists/*
cd ${MAIN_DIR}/helpers/pybluez
pip install .
cd ../../helpers/bluing
env CFLAGS="-lm" LDFLAGS="-ldl -pthread -lutil" pip install .
cd ../../
pip install .
deactivate

cd $MAIN_DIR
sudo rm -rf $TMP_DIR

echo "Setup complete. You can now use the environments as needed."
