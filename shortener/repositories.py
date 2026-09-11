from typing import Protocol

from django.db import IntegrityError, transaction

from shortener.models import Link


class CodeAlreadyExists(Exception):
    pass


class LinkRepository(Protocol):
    def add(self, code: str, url: str) -> Link: ...

    def get_by_code(self, code: str) -> Link | None: ...


class DatabaseLinkRepository:
    def add(self, code: str, url: str) -> Link:
        try:
            # savepoint: an IntegrityError would poison the surrounding transaction
            with transaction.atomic():
                return Link.objects.create(code=code, url=url)
        except IntegrityError as exc:
            raise CodeAlreadyExists(code) from exc

    def get_by_code(self, code: str) -> Link | None:
        return Link.objects.filter(code=code).first()
