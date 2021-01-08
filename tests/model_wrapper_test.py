#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tests for ORM: [description]"""

from __future__ import annotations

import sqlite3
import unittest

from orm.table import ModelWrapper, TableModel

from tests.models import Simple
from tests.mocks import CallableMock, MarkerObject


class ModelWrapperTest(unittest.TestCase):
    """Tests that the model wrapper works"""

    def test_call_all(self) -> None:
        """Tests that the "all" call propogrates to the model"""

        expected = MarkerObject()
        cursor = MarkerObject().cast(sqlite3.Cursor)

        mock = CallableMock(self)
        mock.expect("all", expected, cursor)

        model = ModelWrapper(mock.cast(TableModel), cursor)
        result = model.all()

        self.assertEqual(expected, result)

    def test_call_get(self) -> None:
        """Tests that the "get" call propogrates to the model"""

        expected = MarkerObject()
        cursor = MarkerObject().cast(sqlite3.Cursor)
        entity_id = 1

        mock = CallableMock(self)
        mock.expect("get", expected, cursor, entity_id)

        model = ModelWrapper(mock.cast(TableModel), cursor)
        result = model.get(entity_id)

        self.assertEqual(expected, result)

    def test_call_get_many(self) -> None:
        """Tests that the "get_many" call propogrates to the model"""

        expected = MarkerObject()
        cursor = MarkerObject().cast(sqlite3.Cursor)
        entities = [1, 2, 3]

        mock = CallableMock(self)
        mock.expect("get_many", expected, cursor, *entities)

        model = ModelWrapper(mock.cast(TableModel), cursor)
        result = model.get_many(*entities)

        self.assertEqual(expected, result)

    def test_call_store(self) -> None:
        """Tests that the "store" call propogrates to the model"""

        expected = True
        cursor = MarkerObject().cast(sqlite3.Cursor)
        entity = Simple()

        mock = CallableMock(self)
        mock.expect("store", expected, cursor, entity)

        model = ModelWrapper(mock.cast(TableModel), cursor)
        result = model.store(entity)

        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
