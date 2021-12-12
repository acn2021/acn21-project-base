#!/bin/bash

export PYTHONPATH="$PYTHONPATH:$HOME/mininet"
sudo --preserve-env=PYTHONPATH python3 -m unittest

# To test one file individually:
# sudo --preserve-env=PYTHONPATH python3 -m unittest test_fattree.py
