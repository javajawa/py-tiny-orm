# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Tests for ORM: [description]"""

# pylint: disable=protected-access

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Union

import unittest

import orm
import orm.table
import orm.exceptions

from tests.models import Simple, Simple2, MissingId, User


types: List[Tuple[Any, Any, bool, bool]] = [
    (int, int, True, True),
    (str, str, True, True),
    (None, None, True, False),
    (Union[None, int], int, False, True),
    (Optional[int], int, False, True),
    (Union[int, str], Union[int, str], True, False),
    (Optional[Union[int, str]], Union[int, str], False, False),
    (Simple, Simple, True, True),
    (Optional[Simple], Simple, False, True),
    ("hello", "hello", True, False),
]


class Test(unittest.TestCase):
    """[description]"""

    def test_type_decomposition(self) -> None:
        """Tests for _decompose_type"""

        for intype, exp_type, exp_required, exp_valid in types:
            with self.subTest(msg=f"Test decomposition of {intype}"):
                act_type, act_required = orm.table._decompose_type(intype)

                self.assertEqual(exp_type, act_type)
                self.assertEqual(exp_required, act_required)
                self.assertEqual(exp_valid, orm.table._is_valid_type(act_type))

    def test_model_generation_nonclass(self) -> None:
        """Test that creating a model from a non-class"""

        with self.assertRaises(TypeError, msg="Can not make model data from non-class"):
            orm.table._get_model(1)  # type: ignore

    def test_model_generation_wrong_class(self) -> None:
        """Test that creating a model from a non-Table class"""

        with self.assertRaises(
            TypeError, msg="Data models can only be made from sub-classes of Table"
        ):
            orm.table._get_model(Test)  # type: ignore

    def test_model_generation_missing_id(self) -> None:
        """Test Exception from creating a model that lacks an ID field"""

        with self.assertRaises(
            orm.exceptions.MissingIdField, msg="ID field `{id_field}` missing in `{table}"
        ):
            orm.table._get_model(MissingId)

    def test_model_generation_simple(self) -> None:
        """Test that a trivial model is created correctly"""

        model = orm.table._make_model(Simple)

        self.assertEqual("Simple", model.table)
        self.assertEqual(Simple, model.record)
        self.assertFalse(model.created)

        self.assertEqual({"simple_id": "INTEGER NOT NULL PRIMARY KEY"}, model.table_fields)
        self.assertEqual({}, model.foreigners)

    def test_model_generation_simple2(self) -> None:
        """Test that a trivial model is created correctly"""

        model = orm.table._make_model(Simple2)

        self.assertEqual("Simple2", model.table)
        self.assertEqual(Simple2, model.record)
        self.assertFalse(model.created)

        self.assertEqual({"simple2_id": "INTEGER NOT NULL PRIMARY KEY"}, model.table_fields)
        self.assertEqual({}, model.foreigners)

    def test_model_generation_user(self) -> None:
        """Test that a trivial model is created correctly"""

        model = orm.table._make_model(User)

        self.assertEqual("User", model.table)
        self.assertEqual(User, model.record)
        self.assertFalse(model.created)

        self.assertEqual(
            {
                "user_id": "INTEGER NOT NULL PRIMARY KEY",
                "username": "TEXT NOT NULL",
                "email": "TEXT NOT NULL",
            },
            model.table_fields,
        )
        self.assertEqual({}, model.foreigners)

    def test_model_reentry(self) -> None:
        """Test that repeated calls to _get_model return the same object"""

        model1: orm.table.TableModel[Simple] = orm.table._get_model(Simple)
        model2: orm.table.TableModel[Simple] = orm.table._get_model(Simple)

        self.assertIs(model1, model2)
        self.assertIs(model1, orm.table._MODELS[Simple])


if __name__ == "__main__":
    unittest.main()
