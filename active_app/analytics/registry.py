from dataclasses import dataclass
from typing import Callable, Any

@dataclass(frozen=True)
class KPIDefinition:
    code: str
    name: str
    source_type: str
    unit: str
    aggregation: str
    calculator: Callable[..., Any]
    version: str = "1.0"
    active: bool = True

class KPIRegistry:
    def __init__(self):
        self._items = {}
    def register(self, definition):
        self._items[definition.code] = definition
    def get(self, code):
        return self._items[code]
    def all(self):
        return list(self._items.values())
