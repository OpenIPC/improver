#!/bin/bash


rm -rf ./dist

python3 -m build

pip install dist/py_config_gs-1.0.6.dev29+gff5cf10.d20241108-py3-none-any.whl --force-reinstall