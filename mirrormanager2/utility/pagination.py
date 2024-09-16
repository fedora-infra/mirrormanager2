import math
from dataclasses import dataclass

from flask import current_app, request


@dataclass
class PaginationArgs:
    page_size: int
    page_number: int

    def __init__(self):
        default_page_size = current_app.config["ITEMS_PER_PAGE"]
        try:
            self.page_number = int(request.args.get("page_number"))
        except (TypeError, ValueError):
            self.page_number = 1

        try:
            self.page_size = int(request.args.get("page_size", default_page_size))
        except (TypeError, ValueError):
            self.page_size = default_page_size


class PagedResult:
    def __init__(self, items=None, total=None, page_size=None, page_number=None):
        self.items = items or []
        self.total = total or len(self.items)
        self.page_size = page_size
        self.page_number = page_number

    @property
    def total_pages(self):
        if self.page_size == 0:
            return 1
        return math.ceil(self.total / self.page_size)

    @property
    def has_previous_page(self):
        return self.page_number > 1

    @property
    def has_next_page(self):
        return self.page_number < self.total_pages

    def truncated_pages_list(self, margin=4):
        num_pages = (2 * margin) + 1

        if self.page_number <= margin + 1:
            # Current `self.page_number` is close to the beginning of `self.total_pages`
            min_page = 1
            max_page = min(self.total_pages, num_pages)
        elif (self.total_pages - self.page_number) >= margin:
            min_page = max(self.page_number - margin, 1)
            max_page = min(self.page_number + margin, self.total_pages)
        else:
            # Current `self.page_number` is close to the end of `self.total_pages`
            max_page = min(self.total_pages, self.page_number + margin)
            min_page = max(max_page - (num_pages - 1), 1)

        therange = list(range(min_page, max_page + 1))

        if max_page != self.total_pages:
            therange = therange + [None, self.total_pages]
        if min_page != 1:
            therange = [1, None] + therange

        return therange

    def page_url(self, page_number):
        if page_number < 1 or page_number > self.total_pages:
            return None
        qs = dict(request.args)
        qs.update({"page_size": self.page_size, "page_number": page_number})
        qs = "&".join(f"{k}={v}" for k, v in qs.items())
        return f"{request.script_root}{request.path}?{qs}"

    def __repr__(self):
        return f"<PagedResult items=[{len(self.items)} items] page={self.page_number}>"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError("Unsupported operation")
        return all(
            [
                getattr(self, attr) == getattr(other, attr)
                for attr in ["items", "total", "page_size", "page_number"]
            ]
        )

    def __len__(self):
        return self.total
