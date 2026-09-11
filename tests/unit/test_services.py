import pytest

from shortener.codes import CODE_LENGTH
from shortener.models import Link
from shortener.repositories import CodeAlreadyExists
from shortener.services import (
    MAX_ATTEMPTS,
    CodeGenerationError,
    LinkNotFound,
    ShortenerService,
)


class InMemoryLinkRepository:
    def __init__(self) -> None:
        self.links: dict[str, Link] = {}

    def add(self, code: str, url: str) -> Link:
        if code in self.links:
            raise CodeAlreadyExists(code)
        link = Link(code=code, url=url)
        self.links[code] = link
        return link

    def get_by_code(self, code: str) -> Link | None:
        return self.links.get(code)


class CollidingLinkRepository(InMemoryLinkRepository):
    def __init__(self, collisions: int) -> None:
        super().__init__()
        self._remaining = collisions

    def add(self, code: str, url: str) -> Link:
        if self._remaining:
            self._remaining -= 1
            raise CodeAlreadyExists(code)
        return super().add(code, url)


def test_shorten_stores_the_url_under_a_new_code() -> None:
    repository = InMemoryLinkRepository()
    link = ShortenerService(repository).shorten("http://example.com/a")
    assert link.url == "http://example.com/a"
    assert len(link.code) == CODE_LENGTH
    assert repository.links[link.code] is link


def test_shorten_gives_the_same_url_two_different_codes() -> None:
    service = ShortenerService(InMemoryLinkRepository())
    first = service.shorten("http://example.com/a")
    second = service.shorten("http://example.com/a")
    assert first.code != second.code


def test_shorten_retries_after_a_collision() -> None:
    repository = CollidingLinkRepository(collisions=1)
    link = ShortenerService(repository).shorten("http://example.com/a")
    assert link.code in repository.links


def test_shorten_gives_up_after_max_attempts() -> None:
    repository = CollidingLinkRepository(collisions=MAX_ATTEMPTS)
    with pytest.raises(CodeGenerationError):
        ShortenerService(repository).shorten("http://example.com/a")


def test_expand_returns_the_stored_link() -> None:
    service = ShortenerService(InMemoryLinkRepository())
    created = service.shorten("http://example.com/a")
    assert service.expand(created.code) is created


def test_expand_raises_when_the_code_is_unknown() -> None:
    with pytest.raises(LinkNotFound):
        ShortenerService(InMemoryLinkRepository()).expand("zzzzzzz")
