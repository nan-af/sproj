from typing import Optional, Tuple


class cache(dict):
    def __init__(self, limit: Optional[int] = None) -> None:
        self.limit = limit

    def store(self, key: Tuple, value: str):
        self[key] = value
