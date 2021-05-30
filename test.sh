#!/bin/sh

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

coverage run --context=manual -m unittest discover tests '*_test.py'
rm htmlcov -Rf
coverage html --fail-under=0
coverage report
