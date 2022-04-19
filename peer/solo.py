import requests

from . import cache


class Solo():
    def __init__(self) -> None:
        self.out=[]
        self.cache = cache.Cache()

    def get(self, server: str, id: int, size: int):
        if not (data := self.cache.get((server, id, size))):
            data = self.get_from_server(server, id, size)

        return data

    def get_from_server(self, server: str, id: int, size: int):
        data = requests.get(server, {'id': id, 'size': size}).text
        self.cache.store((server, id, size), data)

        return data
