from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from shortener.views import LinkRedirectView

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/", include("shortener.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("shrt/<str:code>", LinkRedirectView.as_view(), name="link-redirect"),
]
