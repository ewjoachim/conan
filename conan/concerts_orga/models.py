from django.db import models


class OrgaConcert(models.Model):
    name = models.CharField(max_length=200, default="", blank=True)
    date = models.DateField(null=True, blank=True)
    respo = models.CharField(max_length=100, default="", blank=True)
    lieu = models.TextField(default="", blank=True)
    contact_salle = models.TextField(default="", blank=True)
    state = models.JSONField(default=dict, blank=True)
    archived = models.BooleanField(default=False)
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name or f"Concert orga #{self.pk}"
