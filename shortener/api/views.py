from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shortener.api.serializers import LinkSerializer, ShortenRequestSerializer
from shortener.mixins import ShortenerServiceMixin


class LinkCreateView(ShortenerServiceMixin, APIView):
    @extend_schema(
        request=ShortenRequestSerializer,
        responses={
            201: LinkSerializer,
            400: OpenApiResponse(description="Missing url, or not an http(s) address."),
            503: OpenApiResponse(description="Could not generate a free short code."),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = ShortenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = self.get_service().shorten(serializer.validated_data["url"])
        return Response(LinkSerializer(link).data, status=status.HTTP_201_CREATED)


class LinkDetailView(ShortenerServiceMixin, APIView):
    @extend_schema(
        responses={
            200: LinkSerializer,
            404: OpenApiResponse(description="No link with this code."),
        },
    )
    def get(self, request: Request, code: str) -> Response:
        link = self.get_service().expand(code)
        return Response(LinkSerializer(link).data)
