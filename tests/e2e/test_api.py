import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from shortener.codes import CODE_LENGTH
from shortener.models import Link

pytestmark = pytest.mark.django_db

LINKS_URL = "/api/v1/links/"
TARGET = "http://example.com/very-very/long/url/even-longer"


def test_shorten_returns_a_short_link(api_client: APIClient) -> None:
    response = api_client.post(LINKS_URL, {"url": TARGET}, format="json")
    assert response.status_code == 201
    body = response.json()
    assert body["url"] == TARGET
    assert len(body["code"]) == CODE_LENGTH
    assert body["short_url"].endswith(f"/shrt/{body['code']}")


def test_expand_returns_the_original_url(api_client: APIClient) -> None:
    code = api_client.post(LINKS_URL, {"url": TARGET}, format="json").json()["code"]
    response = api_client.get(f"{LINKS_URL}{code}/")
    assert response.status_code == 200
    assert response.json()["url"] == TARGET


def test_short_link_redirects_to_the_original(api_client: APIClient) -> None:
    code = api_client.post(LINKS_URL, {"url": TARGET}, format="json").json()["code"]
    response = api_client.get(f"/shrt/{code}")
    assert response.status_code == 302
    assert response["Location"] == TARGET


def test_the_same_url_gets_two_working_codes(api_client: APIClient) -> None:
    first = api_client.post(LINKS_URL, {"url": TARGET}, format="json").json()
    second = api_client.post(LINKS_URL, {"url": TARGET}, format="json").json()
    assert first["code"] != second["code"]
    assert api_client.get(f"{LINKS_URL}{first['code']}/").json()["url"] == TARGET
    assert api_client.get(f"{LINKS_URL}{second['code']}/").json()["url"] == TARGET


def test_unknown_code_is_not_found(api_client: APIClient) -> None:
    assert api_client.get(f"{LINKS_URL}zzzzzzz/").status_code == 404


def test_unknown_short_link_is_not_found(api_client: APIClient) -> None:
    assert api_client.get("/shrt/zzzzzzz").status_code == 404


def test_a_non_http_scheme_is_rejected(api_client: APIClient) -> None:
    payload = {"url": "javascript:alert(1)"}
    assert api_client.post(LINKS_URL, payload, format="json").status_code == 400


def test_a_missing_url_is_rejected(api_client: APIClient) -> None:
    assert api_client.post(LINKS_URL, {}, format="json").status_code == 400


def test_the_database_rejects_a_duplicate_code() -> None:
    Link.objects.create(code="abc1234", url=TARGET)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Link.objects.create(code="abc1234", url=TARGET)
