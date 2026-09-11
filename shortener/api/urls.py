from django.urls import path
from django.urls.resolvers import URLPattern

from shortener.api.views import LinkCreateView, LinkDetailView

urlpatterns: list[URLPattern] = [
    path("links/", LinkCreateView.as_view(), name="link-create"),
    path("links/<str:code>/", LinkDetailView.as_view(), name="link-detail"),
]
