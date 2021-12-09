# Lab 3

## Usage

```sh
# Start VM
vagrant ssh

# Create mininet topology
cd lab3
./run.sh
```


## Run unit tests

```sh
vagrant ssh

cd lab3
python3 -m unittest

# individual
python3 -m unittest test_address.py
```
