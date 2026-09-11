from typing import Protocol

from shortener.models import Link


class LinkRepository(Protocol):
    def add(self, code: str, url: str) -> Link: ...

    def get_by_code(self, code: str) -> Link | None: ...


class DatabaseLinkRepository:
    def add(self, code: str, url: str) -> Link:
        return Link.objects.create(code=code, url=url)

    def get_by_code(self, code: str) -> Link | None:
        return Link.objects.filter(code=code).first()
