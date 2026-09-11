from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.views import View

from shortener.dependencies import build_shortener_service
from shortener.services import LinkNotFound


class LinkRedirectView(View):
    def get(self, request: HttpRequest, code: str) -> HttpResponse:
        try:
            link = build_shortener_service().expand(code)
        except LinkNotFound:
            raise Http404 from None
        return HttpResponseRedirect(link.url)
