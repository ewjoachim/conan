from django.db import models


class Concert(models.Model):
    """A concert and its preparation checklist.

    Checklist progress lives in ``state`` as a flat ``{key: value}`` dict; see
    ``concerts.checklist`` for the key scheme. ``progress`` is the derived
    completion percentage, denormalized so the concert list can show it cheaply.
    """

    name = models.CharField(max_length=200, default="", blank=True)
    date = models.DateField(null=True, blank=True)
    lieu = models.TextField(default="", blank=True)
    respo = models.CharField(max_length=100, default="", blank=True)
    mandataire = models.TextField(default="", blank=True)
    state = models.JSONField(default=dict, blank=True)
    archived = models.BooleanField(default=False)
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name or f"Concert #{self.pk}"
