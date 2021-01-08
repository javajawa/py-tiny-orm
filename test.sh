#!/bin/sh

coverage run --context=manual -m unittest discover tests '*_test.py'
rm htmlcov -Rf
coverage html --fail-under=0
coverage report
