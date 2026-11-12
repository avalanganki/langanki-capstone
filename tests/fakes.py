"""Shared test doubles. No real Supabase is ever contacted in tests."""

from unittest.mock import MagicMock

from postgrest.exceptions import APIError


class FakeClient:
    """In-memory stand-in for the Supabase client.

    Tables: `entries` (one entry per date), `oura_connection` (upsert on id), and
    `nights` (upsert on night_date).
    """

    def __init__(self, rows=(), connection=None):
        self.tables = {"entries": [], "oura_connection": [], "nights": []}
        self._next_id = 1
        for row in rows:
            self._add(dict(row))
        if connection:
            self.tables["oura_connection"].append({"id": 1, **connection})

    @property
    def rows(self):
        return self.tables["entries"]

    @property
    def connection_rows(self):
        return self.tables["oura_connection"]

    @property
    def night_rows(self):
        return self.tables["nights"]

    def _add(self, row):
        row["id"] = self._next_id
        self._next_id += 1
        self.tables["entries"].append(row)

    def table(self, name):
        assert name in self.tables, name
        self._name = name
        self._query = {"op": None, "eq": None, "order": None, "desc": None, "limit": None}
        return self

    def insert(self, row):
        self._query.update(op="insert", row=row)
        return self

    def upsert(self, row, on_conflict="id"):
        self._query.update(op="upsert", row=row, key=on_conflict)
        return self

    def delete(self):
        self._query["op"] = "delete"
        return self

    def update(self, changes):
        self._query.update(op="update", changes=changes)
        return self

    def select(self, columns):
        self._query["op"] = "select"
        return self

    def order(self, column, desc=False):
        self._query.update(order=column, desc=desc)
        return self

    def eq(self, column, value):
        self._query["eq"] = (column, value)
        return self

    def limit(self, n):
        self._query["limit"] = n
        return self

    def execute(self):
        q = self._query
        table = self.tables[self._name]
        if q["op"] == "insert":
            row = dict(q["row"])
            if any(r["entry_date"] == row["entry_date"] for r in table):
                raise APIError({"code": "23505", "message": "duplicate key"})
            self._add(row)
            return MagicMock(data=[row])
        if q["op"] == "upsert":
            new = [dict(r) for r in (q["row"] if isinstance(q["row"], list) else [q["row"]])]
            keys = {r[q["key"]] for r in new}
            self.tables[self._name] = [r for r in table if r[q["key"]] not in keys] + new
            return MagicMock(data=new)
        rows = list(table)
        if q["eq"]:
            column, value = q["eq"]
            rows = [r for r in rows if r[column] == value]
        if q["op"] == "delete":
            self.tables[self._name] = [r for r in table if r not in rows]
            return MagicMock(data=rows)
        if q["op"] == "update":
            for r in rows:
                r.update(q["changes"])
            return MagicMock(data=rows)
        if q["order"] is not None:
            rows.sort(key=lambda r: r[q["order"]], reverse=q["desc"])
        if q["limit"] is not None:
            rows = rows[: q["limit"]]
        return MagicMock(data=rows)
