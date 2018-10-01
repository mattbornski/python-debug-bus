#!/bin/bash

source env/bin/activate
pytest --capture=no $@
