from django.conf import settings
from django.db import models

from accounts.models import License


class Payment(models.Model):
    PENDING = "pending"
    APPROVED = "approved"
    CANCELED = "canceled"
    FAILED = "failed"

    STATUS_CHOICES = [
        (PENDING, "En attente"),
        (APPROVED, "Approuvé"),
        (CANCELED, "Annulé"),
        (FAILED, "Échec"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=30, default="fedapay")
    provider_transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount_xof = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.amount_xof} XOF - {self.status}"
