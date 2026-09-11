import logging

from shortener.codes import generate_code
from shortener.models import Link
from shortener.repositories import CodeAlreadyExists, LinkRepository

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


class LinkNotFound(Exception):
    pass


class CodeGenerationError(Exception):
    pass


class ShortenerService:
    def __init__(self, link_repository: LinkRepository) -> None:
        self._link_repository = link_repository

    def shorten(self, url: str) -> Link:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return self._link_repository.add(generate_code(), url)
            except CodeAlreadyExists:
                logger.warning("short code collision on attempt %s", attempt)
        logger.error("no free short code after %s attempts", MAX_ATTEMPTS)
        raise CodeGenerationError

    def expand(self, code: str) -> Link:
        link = self._link_repository.get_by_code(code)
        if link is None:
            raise LinkNotFound
        return link
