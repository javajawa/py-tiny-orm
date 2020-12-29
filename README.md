<!--
SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>

SPDX-License-Identifier: BSD-2-Clause
-->

# py-tiny-orm - A Minimal SQLite ORM

`py-tiny-orm` is a minimal Object-relational mapping system which stores
python classes in SQLite.

Classes in your code extend the base classes provided by this module, and
a backing model is automatically generated. This model can then be applied
to an SQLite cursor, and data read, updated, or searched.

See the [quick start exmaple](examples/readme_student_sample.py).

- [(Simple) Tables](#-simple--tables)
  * ["Table" Data Class](#-table--data-class)
  * ["TableModel" Model Class](#-tablemodel--model-class)
    + [`TableModel.all`](#-tablemodelall-)
    + [`TableModel.get`](#-tablemodelget-)
    + [`TableModel.get_many`](#-tablemodelget-many-)
    + [`TableModel.search`](#-tablemodelsearch-)
    + [`TableModel.store`](#-tablemodelstore-)
- [Join Tables](#join-tables)
  * ["JoinTable" Data Class](#-jointable--data-class)
  * ["JoinModel" Model Class](#-joinmodel--model-class)
    + [`JoinModel.of_left` / `of_right`](#-joinmodelof-left-----of-right-)
    + [`JoinModel.ids_for_left` / `ids_for_right`](#-joinmodelids-for-left-----ids-for-right-)
    + [`JoinModel.from_left` / `from_right`](#-joinmodelfrom-left-----from-right-)
    + [`JoinModel.clear_left` / `clear_right`](#-joinmodelclear-left-----clear-right-)
    + [`JoinModel.store`](#-joinmodelstore-)
    + [`JoinModel.remove`](#-joinmodelremove-)

# (Simple) Tables

## "Table" Data Class

A "Table" is a data structure that contains program defined fields.
They MUST inherited from `orm.Table` and contain typed properties, so that the
model can be generated.

The following data types can be used:

| Python Type     | SQLite Type                |
|-----------------|----------------------------|
| `int`           | INTEGER                    |
| `str`           | TEXT                       |
| `bytes`         | BLOB                       |
| `float`         | REAL                       |
| `bool`          | SMALLINT                   |
| `Optional[ x ]` | x will not have `NOT NULL` |
| `Table`         | `INT` + `FOREIGN KEY`      |

## "TableModel" Model Class

The Model generated for these tables is of the type `TableModel`.
You retrieved this from the Table class method `model` passing a sqlite cursor.
`Table.create_tables` method generates the table in the database.

```python
with sqlite3.connect(":memory:") as conn:
    cursor = conn.cursor()

    MyJoinTable.create_table(cursor)
    model = MyJoinTalbe.model(cursor)
```

### `TableModel.all`

`all(self) -> 'List[ModelledTable]'`

Returns all records on the current table.

Note: records will be loaded into memory before being returned,
in order to optimise the number of queries to realted tables.

### `TableModel.get`
`get(self, unique_id: int) -> Optional[T]`

Gets a record by ID, or None if no record with that ID exists.

### `TableModel.get_many`

`get_many(self, *ids: int) -> Dict[int, T]`

Gets all records that exist with ID in the supplied list.

Entries in the dict are not generated for records which do not exist.

### `TableModel.search`
`search(self, **kwargs: Any) -> List[T]`

Gets records for this model which match the given filters.

You can filter using any field in the table, or by a foreign object.

```python
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
```

### `TableModel.store`

`store(self, record: T) -> bool`

Writes a record to the database.

In all cases, this is done as an INSERT OR REPLACE statement.
If the ID field is not set, this may cause the ID of a record to change,
where it is matched via a unique key.

The ID field will be updated with the inserted row's ID.

# Join Tables

A Join table represents a many-to-many mapping between two simple Tables.
These tables are referred to as the `Left` and `Right` tables; operations
are however bi-directional.

## "JoinTable" Data Class

The data entity for a 'Join' Table.

A JoinTable has precisely two fields, which are foreign keys to two other
regular Tables, called Left and Right.

```python
    class RoleMapping(JoinTable[User, Role]):
        user: User
        role: Role
```

Note that the JoinModel does not currently return instances of the
JoinTable, but future features might; instead functions will return
sequences of the "Left" or "Right" Tables, based on the calls made.

## "JoinModel" Model Class

As with `Table`, the model is retrieved from the class method
`model` using an sqlite3 cursor, and a `create_tables` method
is available to generate the table in the database.

```python
with sqlite3.connect(":memory:") as conn:
    cursor = conn.cursor()

    MyJoinTable.create_table(cursor)
    model = MyJoinTalbe.model(cursor)
```

### `JoinModel.of_left` / `of_right`

`of_left(self, left: Left) -> List[Right]`
`of_right(self, right: Right) -> List[Left]`

Returns all records which map to a given record.

### `JoinModel.ids_for_left` / `ids_for_right`

`ids_for_left(self, left: Left) -> List[int]`
`ids_for_right(self, left: Right) -> List[int]`

Returns all `id`s present which map to a given record.

This is the same extracting the IDs from the records returned by
the `of_left`/`of_right` function, but saves the overhead of doing
any extra foreign key lookups.

### `JoinModel.from_left` / `from_right`

`from_left(self, **kwargs: Any) -> List[Right]`
`from_right(self, **kwargs: Any) -> List[Left]`

Returns all unique Right records which map to Left records that match
the given search criteria. No information about which Left they
matched is maintained.

This will have the same result as:

```python
    rights = Left.model().search(**kwargs)
    lefts = {}

    for right in right:
        lefts = join_model.of_right(right)
        lefts.update({l.left_id: l for l in lefts})

    return lefts.values()
```

but this function will be considerably more efficient.

### `JoinModel.clear_left` / `clear_right`

`clear_left(self, left: Left) -> None`
`clear_right(self, right: Right) -> None`

Deletes all records in the join table that feature the given record

### `JoinModel.store`

`store(self, left: Left, right: Right) -> bool`

Adds a mapping between the supplied Left and Right

No action is taken if this mapping already exists

### `JoinModel.remove`

`remove(self, left: Left, right: Right) -> bool`

Removes a mapping between the supplied Left and Right.

No action is taken if this mapping does not exist.
