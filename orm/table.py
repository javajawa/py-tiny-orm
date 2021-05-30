#!/usr/bin/env python3
# vim: fileencoding=utf-8 expandtab ts=4 nospell

# SPDX-FileCopyrightText: 2020-2021 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""
Abstract class and Model implementation for basic Tables in the ORM system.

Tables store an array of fields.
"""

from __future__ import annotations

from typing import (
    get_type_hints,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
)

import inspect
import logging
import re
import sqlite3
import typing_inspect  # type: ignore

from orm.exceptions import MissingIdField


ModelledTable = TypeVar("ModelledTable", bound="Table[Any]")
NoneType: Type[None] = type(None)

_LOGGER = logging.getLogger("tiny-orm")

_TYPE_MAP = {
    str: "TEXT",
    bytes: "BLOB",
    int: "INTEGER",
    float: "REAL",
    bool: "SMALLINT",
}

_UNIQUES = "__orm_uniques__"

_MODELS: Dict[Type[ModelledTable], TableModel[ModelledTable]] = {}  # type: ignore


def _get_model(data_class: Type[Table[Any]]) -> TableModel[ModelledTable]:
    """Gets the TableModel instance for a given class that extends Table."""

    if data_class not in _MODELS:
        # Prevent recursion problems with self-referential classes.
        _MODELS[data_class] = ...  # type: ignore
        _MODELS[data_class] = _make_model(data_class)

    return _MODELS[data_class]


def _make_model(data_class: Type[ModelledTable]) -> TableModel[ModelledTable]:
    """Gets the TableModel instance for a given class that extends Table."""

    if not inspect.isclass(data_class):
        raise TypeError("Can not make model data from non-class")

    if not issubclass(data_class, Table):
        raise TypeError("Data models can only be made from sub-classes of Table")

    table = data_class.__name__
    id_field = re.sub(r"(?<!^)(?=[A-Z])", "_", table).lower() + "_id"

    model = TableModel(data_class, table, id_field)
    types = get_type_hints(data_class)

    if id_field not in types:
        raise MissingIdField(f"ID field `{id_field}` missing in `{table}`")

    model.table_fields[id_field] = "INTEGER NOT NULL PRIMARY KEY"

    for _field, _type in types.items():
        if _field in [id_field]:
            continue

        _type, required = _decompose_type(_type)

        if not _is_valid_type(_type):
            raise Exception(f"Field `{_field}` in `{table}` is not a valid type")

        if _type not in _TYPE_MAP:
            if _type == data_class:
                sub_model = model
            else:
                sub_model = _get_model(_type)
                _field = sub_model.id_field

            model.foreigners[_field] = (sub_model.id_field, sub_model)
            _type = int

        model.table_fields[_field] = _TYPE_MAP[_type] + (" NOT NULL" if required else "")

    return model


def _decompose_type(_type: Type[Any]) -> Tuple[Type[Any], bool]:
    """Converts "Type" or "Optional[Type]" to Type + Required"""

    if not typing_inspect.is_optional_type(_type):
        return _type, True

    args: Set[Type[Any]] = set(typing_inspect.get_args(_type))
    args.remove(NoneType)

    if len(args) != 1:
        _type.__args__ = tuple(args)
        return _type, False

    return args.pop(), False


def _is_valid_type(_type: Type[Any]) -> bool:
    """Checks if a given type is recognised and usable with with the ORM system"""

    if _type in _TYPE_MAP:
        return True

    if not inspect.isclass(_type):
        return False

    return issubclass(_type, Table)


class Table(Generic[ModelledTable]):
    """
    Base class for defining a basic data table.

    Your tables should extend this class, with themselves as the genric parameter:

        class User(Table["User"]):

    This allows typing tools to determine that the model will return objects
    of this type.

    The fields of the table are dervived from the attributes of the class,
    using the type information for the following scalar types:

        str      => TEXT
        bytes    => BLOB
        int      => INTEGER
        float    => REAL
        bool     => SMALLINT

    Additionally, another type that extends Table can be used; this will be
    mapped to an INTEGER column with the other Table's ID field name, and a
    FOREIGN KEY will be added.

    You *must* specify the primary key field, which is the "{table}_id"
    (snake case)

        class User(Table["User"]):
            user_id: int
            name: str
            foo: OtherTable
    """

    def __init__(self, **kwargs: Any):
        """
        Creates a record of this table type.

        The init method of your class must support parameters for each of the
        fields listed in the class, using the same names.

        If you are using a dataclass as yout table type, this will be handled
        for you. Otherwise, you will need to override this method.

        This function uses **kwargs to prevent type checkers from complaining
        about this undescribable requirement.
        """

    @classmethod
    def model(cls, cursor: sqlite3.Cursor) -> ModelWrapper[ModelledTable]:
        """Get the model instance, using the supplied cursor"""

        return ModelWrapper(_get_model(cls), cursor)

    @classmethod
    def create_table(cls, cursor: sqlite3.Cursor) -> None:
        """
        Ensures that this table is created in the SQLite database backing
        the supplied cursor.

        It is recommended that you call this function as soon as you open the
        database, unless your program design guarantees the table will exist.

        Note that py-tiny-orm does not support altering existing tables.
        """

        _get_model(cls).create_table(cursor)


def unique(*fields: str) -> Callable[[Type[ModelledTable]], Type[ModelledTable]]:
    """Adds a unique key to a Table"""

    def _unique(cls: Type[ModelledTable]) -> Type[ModelledTable]:
        """Adds a unique key to a Table"""

        if not issubclass(cls, Table):
            raise Exception(f"{cls.__name__} is not a sub class of Table")

        model: TableModel[ModelledTable] = _get_model(cls)

        if not all([field in model.table_fields for field in fields]):
            raise Exception(f"{cls.__name__} does not have all fields specified in key")

        uniques: List[Set[str]] = getattr(cls, _UNIQUES, [])
        uniques.append(set(fields))
        setattr(cls, _UNIQUES, uniques)

        return cls

    return _unique


class TableModel(Generic[ModelledTable]):
    """The generated model for a given Table."""

    record: Type[ModelledTable]

    created: bool
    table: str
    id_field: str

    table_fields: Dict[str, str]
    foreigners: Dict[str, Tuple[str, TableModel[Any]]]

    def __init__(self, record: Type[ModelledTable], table: str, id_field: str):
        self.record = record
        self.table = table
        self.id_field = id_field
        self.created = False

        self.table_fields = {}
        self.foreigners = {}

    def create_table(self, cursor: sqlite3.Cursor) -> None:
        """Creates the table in SQLites"""

        if self.created:
            return

        self.created = True
        print(self.foreigners)

        for _, model in self.foreigners.values():
            model.create_table(cursor)

        compiled_sql = self._create_table_sql()

        print(compiled_sql)
        _LOGGER.debug(compiled_sql)

        cursor.execute(compiled_sql)

    def _create_table_sql(self) -> str:
        """CREATE TABLE Statement for this table"""

        sql: List[str] = [f"CREATE TABLE IF NOT EXISTS `{self.table}` ("]

        for _field, _type in self.table_fields.items():
            sql.append(f"[{_field}] {_type}, ")

        for _fields in getattr(self.record, _UNIQUES, []):
            sql.append(f"UNIQUE ([{'], ['.join(_fields)}]), ")

        for _field, (f_key, _model) in self.foreigners.items():
            sql.append(f"FOREIGN KEY ([{_field}]) REFERENCES [{_model.table}] ([{f_key}]), ")

        return "\n".join(sql).strip(", ") + "\n);"

    def all(self, cursor: sqlite3.Cursor) -> List[ModelledTable]:
        """
        Returns all records on the current table.

        Note: records will be loaded into memory before being returned,
        in order to optimise the number of queries to realted tables.
        """

        sql = f"SELECT {self.id_field} FROM [{self.table}]"

        _LOGGER.debug(sql)

        cursor.execute(sql)

        ids = [x[0] for x in cursor.fetchall()]

        return list(self.get_many(cursor, *ids).values())

    def get(self, cursor: sqlite3.Cursor, unique_id: int) -> Optional[ModelledTable]:
        """Gets a record by ID, or None if no record with that ID exists"""

        return self.get_many(cursor, unique_id).get(unique_id, None)

    def get_many(self, cursor: sqlite3.Cursor, *ids: int) -> Dict[int, ModelledTable]:
        """
        Gets all records that exist with ID in the supplied list.

        Entries in the dict are not generated for records which do not exist.
        """

        if not ids:
            return {}

        fields: List[str] = list(self.table_fields.keys())
        fields.append(self.id_field)

        sql = (
            f"SELECT [{'], ['.join(fields)}] FROM [{self.table}] "
            f"WHERE [{self.id_field}] IN ({', '.join(['?'] * len(ids))})"
        )

        _LOGGER.debug(sql)
        _LOGGER.debug(ids)

        cursor.execute(sql, tuple(ids))

        rows = cursor.fetchall()

        if not rows:
            return {}

        packed = [dict(zip(fields, row)) for row in rows]

        del rows

        for okey, (fkey, model) in self.foreigners.items():
            fids: Set[int] = {row[okey] for row in packed}
            frens = model.get_many(cursor, *fids)

            for row in packed:
                row[okey] = frens[row[fkey]]
                del row[fkey]

        output: Dict[int, ModelledTable] = {}

        for row in packed:
            output[row[self.id_field]] = self.record(**row)

        return output

    def search(self, cursor: sqlite3.Cursor, **kwargs: Any) -> List[ModelledTable]:
        """
        Gets records for this model which match the given filters.

        You can filter using any field in the table, or by a foreign object.

            class Foo(Table["Foo"]):
                foo_id: int

            class Bar(Table["Bar"]
                bar_id: int
                foo: Foo
                name: str

            # Search by standard field
            Bar.model(cursor).search(name="Hello")

            # Search by foreign ID
            Bar.model(cursor).search(foo_id=1)

            # Search by foreign object
            Bar.model(cursor).search(foo=Foo(1))

            # Search by local ID
            # NOTE: This is value, but using Model.get() is faster.
            Bar.model(cursor).search(bar_id=123)
        """

        for name, model in self.foreigners.values():
            if name in kwargs and isinstance(kwargs[name], model.record):
                kwargs[model.id_field] = getattr(kwargs[name], model.id_field)
                del kwargs[name]

        for key in kwargs:
            if key not in self.table_fields:
                raise AttributeError(f"{self.record.__name__} has no attribute {key}")

        def field(_field: str) -> str:
            return f"[{_field}] = :{_field}"

        sql = (
            f"SELECT {self.id_field} FROM [{self.table}] WHERE "
            f"{' AND '.join(map(field, kwargs))}"
        )

        _LOGGER.debug(sql)
        _LOGGER.debug(kwargs)

        cursor.execute(sql, kwargs)

        ids = [x[0] for x in cursor.fetchall()]

        return list(self.get_many(cursor, *ids).values())

    def store(self, cursor: sqlite3.Cursor, record: ModelledTable) -> bool:
        """
        Writes a record to the database.

        In all cases, this is done as an INSERT OR REPLACE statement.
        If the ID field is not set, this may cause the ID of a record to change,
        where it is matched via a unique key.

        The ID field will be updated with the inserted row's ID.
        """

        if not isinstance(record, self.record):
            raise Exception("Wrong type")

        fields = list(self.table_fields.keys())
        data: Dict[str, Any] = {}

        for field in fields:
            data[field] = getattr(record, field)

        for _field, (_attr, _model) in self.foreigners.items():
            data[_field] = data[_attr][_field]
            del data[_attr]

        if data[self.id_field] is None:
            fields.remove(self.id_field)
            del data[self.id_field]
        else:
            fields.append(self.id_field)

        sql = (
            f"INSERT OR REPLACE INTO [{self.table}] ([{'], ['.join(fields)}])"
            f" VALUES (:{', :'.join(fields)})"
        )

        _LOGGER.debug(sql)
        _LOGGER.debug(data)

        cursor.execute(sql, data)

        setattr(record, self.id_field, cursor.lastrowid)

        return True


class ModelWrapper(Generic[ModelledTable]):
    """
    Binding class between a Table, it's Model, and an SQL-Lite cursor.

    The Model for table "Foo" can be retrieved with

        Foo.model(cursor)
    """

    model: TableModel[ModelledTable]
    cursor: sqlite3.Cursor

    def __init__(self, model: TableModel[ModelledTable], cursor: sqlite3.Cursor):
        self.model = model
        self.cursor = cursor

    def all(self) -> List[ModelledTable]:
        """
        Returns all records on the current table.

        Note: records will be loaded into memory before being returned,
        in order to optimise the number of queries to realted tables.
        """

        return self.model.all(self.cursor)

    def get(self, unique_id: int) -> Optional[ModelledTable]:
        """Gets a record by ID, or None if no record with that ID exists"""

        return self.model.get(self.cursor, unique_id)

    def get_many(self, *ids: int) -> Dict[int, ModelledTable]:
        """
        Gets all records that exist with ID in the supplied list.

        Entries in the dict are not generated for records which do not exist.
        """

        return self.model.get_many(self.cursor, *ids)

    def search(self, **kwargs: Any) -> List[ModelledTable]:
        """
        Gets records for this model which match the given filters.

        You can filter using any field in the table, or by a foreign object.

            class Foo(Table["Foo"]):
                foo_id: int

            class Bar(Table["Bar"]
                bar_id: int
                foo: Foo
                name: str

            # Search by standard field
            Bar.model(cursor).search(name="Hello")

            # Search by foreign ID
            Bar.model(cursor).search(foo_id=1)

            # Search by foreign object
            Bar.model(cursor).search(foo=Foo(1))

            # Search by local ID
            # NOTE: This is value, but using Model.get() is faster.
            Bar.model(cursor).search(bar_id=123)
        """

        return self.model.search(self.cursor, **kwargs)

    def store(self, record: ModelledTable) -> bool:
        """
        Writes a record to the database.

        In all cases, this is done as an INSERT OR REPLACE statement.
        If the ID field is not set, this may cause the ID of a record to change,
        where it is matched via a unique key.

        The ID field will be updated with the inserted row's ID.
        """

        return self.model.store(self.cursor, record)
