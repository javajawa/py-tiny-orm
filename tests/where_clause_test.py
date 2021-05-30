#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tests for ORM: [description]"""

from __future__ import annotations

import sqlite3
import unittest
import orm.abc

from tests.models import Simple
from tests.mocks import MarkerObject


class Test(unittest.TestCase):
    """[description]"""

    def test_one_simple_arg(self) -> None:
        """[description]"""

        clauses = {"cat": 1}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("[cat] = :cat", clause)
        self.assertEqual({"cat": 1}, clauses)

    def test_one_null_arg(self) -> None:
        """[description]"""

        clauses = {"cat": None}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("[cat] IS NULL", clause)

    def test_one_null_arg_single_element_list(self) -> None:
        """[description]"""

        clauses = {"cat": [None]}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("[cat] IS NULL", clause)

    def test_two_simple_args(self) -> None:
        """[description]"""

        clauses = {"cat": 1, "bat": "arg"}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("[cat] = :cat", clause)
        self.assertEqual({"cat": 1, "bat": "arg"}, clauses)

    def test_one_simple_arg_single_element_list(self) -> None:
        """[description]"""

        clauses = {"cat": [1]}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("[cat] = :cat", clause)
        self.assertEqual({"cat": 1}, clauses)

    def test_one_simple_arg_list(self) -> None:
        """[description]"""

        clauses = {"cat": [1, 2]}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("([cat] IN (:cat__0, :cat__1))", clause)
        self.assertEqual(1, clauses["cat__0"])
        self.assertEqual(2, clauses["cat__1"])

    def test_one_simple_arg_list_with_nulls(self) -> None:
        """[description]"""

        clauses = {"cat": [1, None, 3]}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("([cat] IN (:cat__0, :cat__1) OR [cat] IS NULL)", clause)
        self.assertEqual(1, clauses["cat__0"])
        self.assertEqual(3, clauses["cat__1"])

    def test_one_simple_arg_list_with_all_nulls(self) -> None:
        """[description]"""

        clauses = {"cat": [None, None]}

        clause = orm.abc.BaseModel.where_clause("cat", clauses)

        self.assertEqual("[cat] IS NULL", clause)

    def test_basic_where_generation(self) -> None:
        """[description]"""

        clauses: orm.abc.Filters = {
            "type_id": [1, 2, 3],
            "is_cat": True,
            "bar": None,
        }

        sql, params = orm.abc.BaseModel().where({}, clauses)

        self.assertEqual(
            "([type_id] IN (:type_id__0, :type_id__1, :type_id__2)) "
            + "AND [is_cat] = :is_cat AND [bar] IS NULL",
            sql,
        )
        self.assertEqual(1, params["type_id__0"])
        self.assertEqual(2, params["type_id__1"])
        self.assertEqual(3, params["type_id__2"])
        self.assertEqual(True, params["is_cat"])
        self.assertEqual(None, params["bar"])

    def test_where_with_foreign_keys(self) -> None:
        """[description]"""

        cursor = MarkerObject().cast(sqlite3.Cursor)

        foreign = {"simple": ("simple_id", Simple.model(cursor).model)}

        clauses = {"simple": Simple(1)}

        sql, params = orm.abc.BaseModel().where(foreign, clauses)

        self.assertEqual("[simple_id] = :simple_id", sql)
        self.assertEqual(1, params["simple_id"])

    def test_where_with_many_foreign_keys(self) -> None:
        """[description]"""

        cursor = MarkerObject().cast(sqlite3.Cursor)

        foreign = {"simple": ("simple_id", Simple.model(cursor).model)}

        clauses: orm.abc.Filters = {"simple": (Simple(1), Simple(2))}

        sql, params = orm.abc.BaseModel().where(foreign, clauses)

        self.assertEqual("([simple_id] IN (:simple_id__0, :simple_id__1))", sql)
        self.assertEqual(1, params["simple_id__0"])
        self.assertEqual(2, params["simple_id__1"])

    def test_where_with_wrong_foreign_keys(self) -> None:
        """[description]"""

        cursor = MarkerObject().cast(sqlite3.Cursor)

        foreign = {"simple": ("simple_id", Simple.model(cursor).model)}

        clauses = {"simple": [1, 2]}

        with self.assertRaises(Exception, msg="Passed incorrect object to foreign key") as _:
            _, _ = orm.abc.BaseModel().where(foreign, clauses)


if __name__ == "__main__":
    unittest.main()
