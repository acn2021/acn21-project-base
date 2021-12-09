#!/bin/bash

export PYTHONPATH="$PYTHONPATH:$HOME/mininet"
sudo --preserve-env=PYTHONPATH python3 -m unittest
# sudo --preserve-env=PYTHONPATH python3 -m unittest test_fattree.py
