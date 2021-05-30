#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""
Support for sub table expansion in models
"""

from __future__ import annotations

from typing import (
    get_type_hints,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import logging
import sqlite3

from orm.table import ModelledTable, Table, TableModel, _get_model, _SUBTABLES
from orm.abc import BaseModel, MutableFilters as Filters, PrimitiveTypes


_LOGGER = logging.getLogger("tiny-orm")

SecondTable = TypeVar("SecondTable", bound="Table[Any]")


def subtable(
    field: str,
    table: Type[ModelledTable],
    subfield: Optional[str] = None,
    pivot: Optional[str] = None,
    selectors: Optional[Dict[str, PrimitiveTypes]] = None,
) -> Callable[[Type[SecondTable]], Type[SecondTable]]:
    """Registers a field as a subtable to a Table"""

    if not subfield:
        subfield = field

    if not selectors:
        selectors = dict()

    sub: SubTable[ModelledTable] = SubTable(table, subfield, pivot, selectors)

    def _subtable(cls: Type[SecondTable]) -> Type[SecondTable]:
        """Adds a subtable key to a Table"""

        if not issubclass(cls, Table):
            raise Exception(f"{cls.__name__} is not a sub class of Table")

        subtables: Dict[str, SubTable[ModelledTable]] = getattr(cls, _SUBTABLES, {})
        subtables[field] = sub
        setattr(cls, _SUBTABLES, subtables)

        return cls

    return _subtable


class SubTable(Generic[ModelledTable], BaseModel):
    """
    Class which represents a request for the ORM tools to expand a field
    with the values in a sub table
    """

    model: TableModel[ModelledTable]
    field: str
    connector: Optional[str]
    pivot: Optional[str]
    selector: Dict[str, PrimitiveTypes]

    def __init__(
        self,
        source: Type[ModelledTable],
        field: str,
        pivot: Optional[str],
        selectors: Dict[str, PrimitiveTypes],
    ) -> None:
        # This is the model that the actual data for the sub tables is storeed in.
        self.model = _get_model(source)

        # Field is the output field mapped into new parent table
        self.field = field

        # Selectors are filters on the sub-table beyond the foreign key
        # of the parent type. This is used when you want to store two
        # different sub-types of data in one sub table.
        self.selectors = selectors

        # If this sub-table is being mapped into a dictionary, this is
        # the field to use as the key for that dictionary.
        self.pivot = pivot

        self.connector = None

        # Validate the settings we have so far (this will not include
        # the foreign key relation to the parent)
        self.validate()

    def validate(self) -> None:
        """Check if this subtable has a valid configuration.

        This includes:
          - That the underlying table model has the correct data, connector,
            and (where appropriate) pivot fields
          - That the parent table, once connected, has the correct fields in
            the model.
        """

        if self.field not in self.model.table_fields:
            raise ValueError(f"Value field {self.field} not present in {self.model.table}")

        if self.pivot:
            if self.pivot not in self.model.table_fields:
                raise ValueError(
                    f"Pivot field {self.pivot} not present in {self.model.table}"
                )

        if self.connector:
            if self.connector not in self.model.table_fields:
                raise ValueError(
                    f"Connector field {self.connector} not present in {self.model.table}"
                )

        for field in self.selectors:
            if field not in self.model.table_fields:
                raise ValueError(f"Selector field {field} not present in {self.model.table}")

    def connect_to(self, parent: TableModel[Any]) -> None:
        """Connects this sub-table to a its parent.

        The validity of the join is checked at this time.

        This method will fail if it has been connected already."""
        if self.connector:
            raise Exception("Attempting to connect an already connected sub-table instance")

        # Confirm that the source table has a relation to the parent table
        # that is now claiming us as a sub-table
        if parent.id_field not in self.model.table_fields:
            raise ValueError(
                f"Can not use {self.model.table} as a sub-table of {parent.table}, "
                f"as it has no foreign key to {parent.table}"
            )

        self.connector = parent.id_field
        self.model.foreigners[parent.id_field] = (parent.id_field, parent)
        self.validate()

    def get_expected_type(self) -> Type[Any]:
        """Determines the expected type of the sub-field in the parent
        ype definition, based off the parameters to this helper class.

        This will either be a List[] or Dict[] depending on whether a
        pivot has been specified. The types will be taken fomr the completed
        model of this sub-table."""
        types = get_type_hints(self.model.record)

        if self.pivot:
            return Dict[types[self.pivot], types[self.field]]  # type: ignore

        return List[types[self.field]]  # type: ignore

    def select(
        self, cursor: sqlite3.Cursor, *connector_value: int
    ) -> Mapping[int, Union[Mapping[PrimitiveTypes, PrimitiveTypes], List[PrimitiveTypes]]]:
        """Selects the sub table values for a set of parent objects."""

        if not self.connector:
            raise Exception(f"{self.model.table} has not been attached to a model")

        if self.pivot:
            return self.select_pivot(cursor, connector_value)

        return self.select_column(cursor, connector_value)

    def select_column(
        self, cursor: sqlite3.Cursor, connector_value: Tuple[int, ...]
    ) -> Mapping[int, List[PrimitiveTypes]]:
        """Selects the sub table values for a set of parent objects

        This is a sub-call of select(), for use when the sub table is a List[] type."""

        if not self.connector:
            raise Exception(f"{self.model.table} has not been attached to a model")

        where: Filters = dict(self.selectors)
        where[self.connector] = connector_value

        sql, params = self.where({}, where)
        sql = (
            f"SELECT [{self.connector}], [{self.field}] FROM [{self.model.table}] WHERE "
            + sql
        )

        _LOGGER.debug(sql)
        _LOGGER.debug(params)

        cursor.execute(sql, params)

        result: Dict[int, List[Any]] = dict(zip(connector_value, [[]] * len(connector_value)))

        for connected, value in cursor.fetchall():
            result[connected].append(value)

        return result

    def select_pivot(
        self, cursor: sqlite3.Cursor, connector_value: Tuple[int, ...]
    ) -> Dict[int, Dict[PrimitiveTypes, PrimitiveTypes]]:
        """Selects the sub table values for a set of parent objects

        This is a sub-call of select(), for use when the sub table is a Dict[] type."""

        if not self.connector:
            raise Exception(f"{self.model.table} has not been attached to a model")

        where: Filters = dict(self.selectors)
        where[self.connector] = connector_value

        sql, params = self.where({}, where)
        sql = (
            f"SELECT [{self.connector}], [{self.pivot}], [{self.field}] "
            + "FROM [{self.model.table}] WHERE "
            + sql
        )

        _LOGGER.debug(sql)
        _LOGGER.debug(params)

        cursor.execute(sql, params)

        result: Dict[int, Dict[PrimitiveTypes, PrimitiveTypes]] = dict(
            zip(connector_value, [{}] * len(connector_value))
        )

        for connected, key, value in cursor.fetchall():
            result[connected][key] = value

        return result

    def store(
        self, cursor: sqlite3.Cursor, connector_value: int, values: PrimitiveTypes
    ) -> None:
        """Stores a list of values for a single parent objct in the sub table"""
