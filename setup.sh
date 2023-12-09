#!/bin/bash
sudo apt-get update
sudo apt-get dist-upgrade -y
sudo apt-get install python3-dev python3-virtualenv libevent-dev virtualenv git -y
git clone https://github.com/ChristianYaglenski/kiln-controller
cd kiln-controller
virtualenv -p python3 venv
source venv/bin/activate
export CFLAGS=-fcommon
pip3 install --upgrade setuptools
pip3 install greenlet bottle gevent gevent-websocket
cd kiln-controller
virtualenv -p python3 venv
source venv/bin/activate
export CFLAGS=-fcommon
pip3 install -r requirements.txt
/home/pi/kiln-controller/start-on-boot
source venv/bin/activate
./kiln-controller.py
