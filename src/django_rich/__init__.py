from __future__ import annotations

from itertools import islice
from typing import Any

import rich
from django.db.models.query import QuerySet
from rich.table import Table


def tabulate(
    queryset: dict[Any, Any] | QuerySet[Any] | Any,
    limit: int | None = 10,
) -> None:
    if isinstance(queryset, dict):
        table = Table(*queryset.keys())
        table.add_row(*map(str, queryset.values()))
        rich.print(table)
    elif isinstance(queryset, QuerySet):
        title = queryset.model._meta.verbose_name_plural.title()
        if len(queryset) == 0:
            rich.print("")
            return
        if isinstance(queryset[0], dict):
            table = Table(*queryset[0].keys(), title=title)
            for row in islice(queryset, limit):
                table.add_row(*map(str, row.values()))
        else:
            fields, is_deferred = queryset.query.deferred_loading
            if is_deferred:
                headers = [
                    key for key in queryset.values()[0].keys() if key not in fields
                ]
            else:
                headers = [key for key in queryset.values()[0].keys() if key in fields]
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
        dataset_len = len(queryset)
        if limit and limit < dataset_len:
            table.caption = f"{limit} of {dataset_len} records shown. Use `limit=None` to show all records."
            table.add_row(*["…"] * len(headers))
        rich.print(table)
    else:
        rich.print(queryset)
