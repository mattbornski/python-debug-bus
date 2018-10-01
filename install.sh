#!/bin/bash

rm -rf env/
virtualenv --no-site-packages --python=python3.6 env/
source env/bin/activate
pip install --editable ".[test]"
