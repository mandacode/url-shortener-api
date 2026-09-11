from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shortener.api.serializers import LinkSerializer, ShortenRequestSerializer
from shortener.dependencies import build_shortener_service
from shortener.services import CodeGenerationError, LinkNotFound


class LinkCreateView(APIView):
    def post(self, request: Request) -> Response:
        serializer = ShortenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            link = build_shortener_service().shorten(serializer.validated_data["url"])
        except CodeGenerationError:
            return Response(
                {"detail": "Could not generate a unique short code, please retry."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(LinkSerializer(link).data, status=status.HTTP_201_CREATED)


class LinkDetailView(APIView):
    def get(self, request: Request, code: str) -> Response:
        try:
            link = build_shortener_service().expand(code)
        except LinkNotFound:
            return Response(
                {"detail": "No link with this code."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(LinkSerializer(link).data)
