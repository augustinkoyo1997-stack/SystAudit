import uuid

from django.contrib.auth.models import User
from django.db import models


class License(models.Model):
    PLAN_FREE = "free"
    PLAN_PREMIUM = "premium"

    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PREMIUM, "Premium"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="license",
    )

    key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default=PLAN_FREE,
    )

    is_active = models.BooleanField(default=True)

    max_devices = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.user.username} - {self.plan}"

    @property
    def is_premium(self):
        return (
            self.plan == self.PLAN_PREMIUM
            and self.is_active
        )