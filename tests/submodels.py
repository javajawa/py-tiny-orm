#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tests for ORM: [description]"""

from typing import Dict, List

import dataclasses
import sqlite3

import orm


class SubList(orm.Table["SubList"]):
    """Simple subtable for a list of strings"""

    sub_list_id: int
    main_table_id: int
    data: str


class SubDict(orm.Table["SubDict"]):
    """Simple subtable for a dict of strings"""

    sub_dict_id: int
    main_table_id: int
    key: str
    value: str


@orm.subtable("data", SubList)
@orm.subtable("datadict", SubDict, "value", "key")
@dataclasses.dataclass
class MainTable(orm.Table["MainTable"]):
    """A simple table with a list of SubList rows"""

    main_table_id: int
    data: List[str]
    datadict: Dict[str, str]


if __name__ == "__main__":
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()

    MainTable.create_table(cursor)
    model = MainTable.model(cursor)
    print(dataclasses.asdict(model.all()[0]))
