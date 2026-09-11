from django.conf import settings
from django.core.validators import URLValidator
from django.urls import reverse
from rest_framework import serializers

from shortener.models import MAX_URL_LENGTH, Link


class ShortenRequestSerializer(serializers.Serializer[dict[str, str]]):
    url = serializers.CharField(
        max_length=MAX_URL_LENGTH,
        validators=[URLValidator(schemes=["http", "https"])],
    )


class LinkSerializer(serializers.ModelSerializer[Link]):
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = Link
        fields = ["code", "short_url", "url"]

    def get_short_url(self, link: Link) -> str:
        return f"{settings.SHORT_URL_BASE}{reverse('link-redirect', args=[link.code])}"
