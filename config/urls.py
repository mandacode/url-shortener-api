from django.urls import URLPattern, URLResolver, include, path

from shortener.views import LinkRedirectView

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/", include("shortener.api.urls")),
    path("shrt/<str:code>", LinkRedirectView.as_view(), name="link-redirect"),
]
