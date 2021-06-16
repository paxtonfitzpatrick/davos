from collections.abc import MutableMapping
from typing import Any, Literal

__all__ = list[Literal['DotDict', 'JS_FUNCTIONS']]

class DotDict(dict):
    def __init__(self, d: MutableMapping) -> None: ...
    def __delattr__(self, key: str) -> None: ...
    def __getattr__(self, item: str) -> Any: ...
    def __setattr__(self, key: str, value: Any) -> None: ...

JS_FUNCTIONS: DotDict