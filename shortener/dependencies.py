from shortener.repositories import DatabaseLinkRepository, LinkRepository
from shortener.services import ShortenerService


def build_shortener_service() -> ShortenerService:
    repository: LinkRepository = DatabaseLinkRepository()
    return ShortenerService(repository)
