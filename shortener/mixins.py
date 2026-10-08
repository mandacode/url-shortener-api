from shortener.dependencies import build_shortener_service
from shortener.services import ShortenerService


class ShortenerServiceMixin:
    service_factory = staticmethod(build_shortener_service)

    def get_service(self) -> ShortenerService:
        return self.service_factory()
