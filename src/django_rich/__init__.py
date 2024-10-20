from __future__ import annotations

from itertools import islice
from typing import Any

import rich
from django.db.models.query import QuerySet
from django.db.models.query import ValuesIterable
from rich.table import Table


def tabulate(
    queryset: dict[Any, Any] | QuerySet[Any] | Any,
    limit: int | None = 10,
) -> None:
    if isinstance(queryset, dict):
        table = Table(*queryset.keys())
        table.add_row(*[str(v) for v in queryset.values()])
        rich.print(table)
    elif isinstance(queryset, QuerySet):
        title = queryset.model._meta.verbose_name_plural.title()
        if issubclass(queryset._iterable_class, ValuesIterable):
            # QuerySet.values(), yielding dicts
            table = Table(*queryset[0].keys(), title=title)
            for row in islice(queryset, limit):
                table.add_row(*map(str, row.values()))
        # todo: RawModelIterable, ValuesListIterable, NamedValuesListIterable, FlatValuesListIterable?
        else:
            try:
                first = queryset.values()[0]
            except IndexError:
                # Empty QuerySet
                fields: frozenset[str] | set[str] = frozenset()
                is_deferred = False
                headers = []
            else:
                fields, is_deferred = queryset.query.deferred_loading
                if is_deferred:
                    headers = [key for key in first.keys() if key not in fields]
                else:
                    headers = [key for key in first.keys() if key in fields]
            table = Table(*headers, title=title)
            for row in islice(queryset.values_list(named=True), limit):
                if is_deferred:
                    data = (
                        str(data)
                        for field, data in zip(row._fields, row)
                        if field not in fields
                    )
                else:
                    data = (
                        str(data)
                        for field, data in zip(row._fields, row)
                        if field in fields
                    )
                table.add_row(*data)
        if not table.rows:
            rich.print("[i]Empty QuerySet.[/i]")
        else:
            dataset_len = len(queryset)
            if limit and limit < dataset_len:
                table.add_row(*["…"] * len(table.columns))
                table.caption = f"{limit} of {dataset_len} records shown. Use `limit=None` to show all records."
                table.min_width = 20
            rich.print(table)
    else:
        rich.print(queryset)
