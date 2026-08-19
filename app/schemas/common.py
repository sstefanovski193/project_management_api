from enum import Enum


class SortOrder(str, Enum):
    """Sorting directions."""

    ASC = "asc"
    DESC = "desc"
