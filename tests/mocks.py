#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""
Abstract class and Model implementation for basic Tables in the ORM system.

Tables store an array of fields.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar

import unittest


Target = TypeVar("Target")


class CallableMock:
    """Mocking class that can accept any fuction call"""

    testcase: unittest.TestCase
    next_function: str
    response: Any
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    def __init__(self, test: unittest.TestCase) -> None:
        self.testcase = test
        self.next_function = ""
        self.response = None
        self.args = tuple()
        self.kwargs = dict()

    def expect(self, function: str, response: Any, *args: Any, **kwargs: Any) -> None:
        """Sets up what the next function call this Mock should expect next"""

        self.next_function = function
        self.response = response
        self.args = args
        self.kwargs = kwargs

    def __getattr__(self, name: str) -> Optional[Callable[[Any], Any]]:
        expected = self.next_function

        self.testcase.assertEqual(
            expected, name, f"Mock was not expecting a call to '{name}'"
        )

        return self.magic_call

    def magic_call(self, *args: Any, **kwargs: Any) -> Any:
        """Fakes a call to the given function"""

        self.testcase.assertEqual(self.args, args)
        self.testcase.assertEqual(self.kwargs, kwargs)

        return self.response

    def cast(self, target: Type[Target]) -> Target:
        """'Casts' this object to a given type, to make type checkers ignore it."""

        if not target:
            raise ValueError("Missing type")

        return self  # type: ignore


class MarkerObject:
    """Unique objects for testing with. Equal instantiated object will be unique"""

    _counter: int = 0
    marker: int

    def __init__(self) -> None:
        MarkerObject._counter += 1
        self.marker = MarkerObject._counter

    def __eq__(self, other: Any) -> bool:
        """Check if this is object is equal"""

        if not isinstance(other, MarkerObject):
            return False

        return self.marker == other.marker

    def cast(self, target: Type[Target]) -> Target:
        """'Casts' this object to a given type, to make type checkers ignore it."""

        if not target:
            raise ValueError("Missing type")

        return self  # type: ignore
