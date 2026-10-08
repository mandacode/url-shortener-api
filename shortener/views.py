from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.views import View

from shortener.mixins import ShortenerServiceMixin
from shortener.services import LinkNotFound


class LinkRedirectView(ShortenerServiceMixin, View):
    def get(self, request: HttpRequest, code: str) -> HttpResponse:
        try:
            link = self.get_service().expand(code)
        except LinkNotFound:
            raise Http404 from None
        return HttpResponseRedirect(link.url)
