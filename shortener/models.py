from django.db import models

from shortener.codes import CODE_LENGTH

MAX_URL_LENGTH = 2048


class Link(models.Model):
    code = models.CharField(max_length=CODE_LENGTH)
    url = models.URLField(max_length=MAX_URL_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_link_code"),
        ]

    def __str__(self) -> str:
        return self.code
