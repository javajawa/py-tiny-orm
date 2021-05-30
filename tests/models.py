#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tests for ORM: [description]"""

from typing import Optional

import orm


class Simple(orm.Table["Simple"]):
    """simpliest table -- just an id"""

    simple_id: int


class Simple2(orm.Table["Simple"]):
    """simpliest table -- just an id"""

    simple2_id: Optional[int]


class MissingId(orm.Table["MissingId"]):
    """Model with no ID (or other) fields"""


@orm.unique("username")
class User(orm.Table["User"]):
    """Example table: a User"""

    user_id: int
    username: str
    email: str
