FROM debian:bullseye

ENV DEBIAN_FRONTEND noninteractive
ARG http_proxy
ARG https_proxy
ARG no_proxy
ARG PIP_PROXY
ARG CERTIFICATE_NAME

RUN if [ -n "$http_proxy" ]; then echo "Acquire::http::Proxy \"$http_proxy\";" >> /etc/apt/apt.conf.d/01proxy; fi

ENV VENV_DIR="/root"

RUN apt-get -y update && apt-get -y upgrade

RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates
COPY *${CERTIFICATE_NAME} /usr/local/share/ca-certificates/
RUN update-ca-certificates
ENV PIP_CERT=/usr/local/share/ca-certificates/${CERTIFICATE_NAME}

RUN apt-get install -y tzdata

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    echo 'deb http://deb.debian.org/debian bullseye-backports main' > /etc/apt/sources.list.d/bullseye-backports.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libbz2-dev \
    libexpat1-dev \
    liblzma-dev \
    tk-dev \
    libffi-dev \
    curl \
    python2.7 \
    python2-dev \
    gcc \
    wget \
    g++ \
    make \
    git \
    bluez \
    dbus \
    bluetooth \
    usbutils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz && \
    tar -xf Python-3.10.0.tgz && \
    cd Python-3.10.0 && \
    ./configure --enable-optimizations && \
    make -j $(nproc) && \
    make altinstall

RUN python2.7 --version && python3.10 --version

RUN apt-get update && \
    wget https://bootstrap.pypa.io/pip/2.7/get-pip.py -O get-pip.py && \
    wget https://files.pythonhosted.org/packages/27/79/8a850fe3496446ff0d584327ae44e7500daf6764ca1a382d2d02789accf7/pip-20.3.4-py2.py3-none-any.whl -O pip-20.3.4-py2.py3-none-any.whl && \
    wget https://files.pythonhosted.org/packages/e1/b7/182161210a13158cd3ccc41ee19aadef54496b74f2817cc147006ec932b4/setuptools-44.1.1-py2.py3-none-any.whl -O setuptools-44.1.1-py2.py3-none-any.whl && \
    wget https://files.pythonhosted.org/packages/27/d6/003e593296a85fd6ed616ed962795b2f87709c3eee2bca4f6d0fe55c6d00/wheel-0.37.1-py2.py3-none-any.whl -O wheel-0.37.1-py2.py3-none-any.whl && \
    python2.7 get-pip.py "pip-20.3.4-py2.py3-none-any.whl" "setuptools-44.1.1-py2.py3-none-any.whl" "wheel-0.37.1-py2.py3-none-any.whl" --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org --trusted-host files.pythonhosted.org && \
    python2.7 -m pip install virtualenv && \
    rm -f get-pip.py && \
    apt-get install -y python3-pip && \
    python3.10 -m pip install --upgrade pip --index-url http://pypi.python.org/simple/ --trusted-host pypi.python.org --trusted-host files.pythonhosted.org && \
    python3.10 -m pip install virtualenv

RUN python3.10 -m virtualenv ${VENV_DIR}/venv3 && \
    python2.7 -m virtualenv ${VENV_DIR}/venv2

WORKDIR ${VENV_DIR}
ENV SBLEEDY_DIR=${VENV_DIR}/SbleedyGonzales
RUN git clone --recurse-submodules "https://github.com/b0rdst31n/SbleedyGonzales.git" ${SBLEEDY_DIR}

RUN . ${VENV_DIR}/venv2/bin/activate && \
    cd ${SBLEEDY_DIR}/modules/sweyntooth && \
    pip install -r requirements.txt && \
    cd libs/smp_server/ && make all && make install && cd ../../ && \
    deactivate

RUN . ${VENV_DIR}/venv3/bin/activate && \
    apt-get install -y libbluetooth-dev cmake libcairo2-dev pkg-config libgirepository1.0-dev libdbus-1-dev bluez-tools python3-cairo-dev \
    rfkill meson patchelf bluez adb python-is-python3 && \
    rm -rf /var/lib/apt/lists/* && \
    cd ${SBLEEDY_DIR}/helpers/pybluez && pip install . && cd ../../ && \
    cd ${SBLEEDY_DIR}/helpers/bluing && env CFLAGS="-lm" LDFLAGS="-ldl -pthread -lutil" pip install . && cd ../../ && \
    pip install -e ${SBLEEDY_DIR} && \
    deactivate

RUN rm -rf /usr/local/share/ca-certificates/${CERTIFICATE_NAME}

CMD ["/bin/bash"]