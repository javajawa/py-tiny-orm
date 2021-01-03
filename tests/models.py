#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tests for ORM: [description]"""

from typing import Optional

import orm


class Simple(orm.Table["Simple"]):
    """simpliest table -- just an id"""

    simple_id: int


class SimpleIdOptional(orm.Table["Simple"]):
    """simpliest table -- just an id"""

    simple_id: Optional[int]


class MissingIdField(orm.Table["MissingIdField"]):
    """Model with no ID (or other) fields"""
