#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Example showing how to set up and use a simple table"""


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


@dataclasses.dataclass
class Student(orm.Table["Student"]):
    """Basic Student table, with an ID and name"""

    name: str

    # Your table must have an int id field matching the table name
    student_id: Optional[int] = None


with sqlite3.connect(":memory:") as db:
    cursor = db.cursor()

    # Create the table in the database.
    Student.create_table(cursor)

    # Get a model view for the Student table
    model = Student.model(cursor)
    model.store(Student(name="Dave Smith"))

    print(model.all())  # [Student(name='Dave Smith', student_id=1)]
