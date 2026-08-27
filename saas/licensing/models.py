from django.db import models

from accounts.models import License


class LicensedDevice(models.Model):
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    device_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["license", "device_id"],
                name="unique_license_device",
            )
        ]

    def __str__(self):
        return f"{self.license.key} - {self.device_id}"