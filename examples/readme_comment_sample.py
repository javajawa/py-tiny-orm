#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Example showing how to set up and use a simple table"""

from __future__ import annotations

from typing import Optional

import dataclasses
import sqlite3
import orm

# Define a table called "Student"
#
# The self-parameter to the "Table" supertype allows type checkers to
# understand that model calls will return objects of this class.
#
# Here we use dataclasses to generate the __init__ and other function for us.


@orm.unique("username")
@orm.unique("email")
@dataclasses.dataclass
class User(orm.Table["User"]):
    """Basic Student table, with an ID and name"""

    email: str
    username: str

    # Your table must have an int id field matching the table name
    user_id: Optional[int] = None


@dataclasses.dataclass
class Comment(orm.Table["Comment"]):
    """Nested comment class, with parent and root references"""

    comment_id: Optional[int]
    root: Optional[Comment]
    parent: Optional[Comment]

    user: User
    content: str


with sqlite3.connect(":memory:") as db:
    cursor = db.cursor()

    # Create the table in the database.
    Comment.create_table(cursor)
