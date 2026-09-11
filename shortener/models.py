from django.db import models

from shortener.codes import CODE_LENGTH


class Link(models.Model):
    code = models.CharField(max_length=CODE_LENGTH)
    url = models.URLField(max_length=2048)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_link_code"),
        ]

    def __str__(self) -> str:
        return self.code
