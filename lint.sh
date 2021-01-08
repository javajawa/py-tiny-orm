#!/bin/sh

black orm tests examples setup.py
flake8 orm tests examples setup.py
mypy --strict orm tests examples setup.py
pylint orm tests examples setup.py
