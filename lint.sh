#!/bin/sh

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

black orm tests examples setup.py
flake8 orm tests examples setup.py
mypy --strict orm tests examples setup.py
pylint orm tests examples setup.py
