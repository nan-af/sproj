import requests
from peer import cache


class get():
    def __init__(self) -> None:
        self.cache = cache.cache()

    def get(self, server: str, id: int, size: int):
        if not (data := self.cache.get((server, id, size))):
            data = requests.get(server, {'id': id, 'size': size}).text
            self.cache.store((server, id, size), data)

        return data
