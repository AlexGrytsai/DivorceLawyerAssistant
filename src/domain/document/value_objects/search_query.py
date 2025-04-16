from typing import Union, NamedTuple


class SearchQuery(NamedTuple):
    """Object-value for the search parameters for documents"""

    field: str
    operator: str
    value: Union[str, int, float, bool]
