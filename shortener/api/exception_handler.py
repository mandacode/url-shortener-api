from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from shortener.services import CodeGenerationError, LinkNotFound

DOMAIN_RESPONSES: dict[type[Exception], tuple[int, str]] = {
    LinkNotFound: (
        status.HTTP_404_NOT_FOUND,
        "No link with this code.",
    ),
    CodeGenerationError: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Could not generate a unique short code, please retry.",
    ),
}


def domain_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    mapped = DOMAIN_RESPONSES.get(type(exc))
    if mapped is None:
        return exception_handler(exc, context)
    code, detail = mapped
    return Response({"detail": detail}, status=code)
