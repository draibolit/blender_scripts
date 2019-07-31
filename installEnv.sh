#!/bin/bash

pip3 install --user vitualenv
virtualenv --system-site-packages pythonenv
source ./pythonenv/bin/activate
if [ $? -eq 0 ]; then
		pip install -r requirements.txt
else 
		echo "virtualenv is not installed properly"
fi

#https://virtualenv.pypa.io/en/latest/installation/
#https://medium.com/python-pandemonium/better-python-dependency-and-package-management-b5d8ea29dff1

