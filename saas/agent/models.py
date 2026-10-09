import secrets
import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from licensing.models import LicensedDevice


class Agent(models.Model):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    REVOKED = "REVOKED"

    STATUS_CHOICES = [
        (ONLINE, "Online"),
        (OFFLINE, "Offline"),
        (REVOKED, "Revoked"),
    ]

    device = models.OneToOneField(
        LicensedDevice,
        on_delete=models.CASCADE,
        related_name="agent",
    )

    agent_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    secret_hash = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=OFFLINE,
    )

    last_seen = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def set_secret(self, secret):
        """
        Hash et enregistre le secret de l'Agent.
        Le secret original n'est jamais stocke en base.
        """
        self.secret_hash = make_password(secret)


    def check_secret(self, secret):
        """
        VÃ©rifie le secret uniquement si un hash est configurÃ©.
        """
        if not self.secret_hash or not isinstance(secret, str) or not secret:
            return False

        return check_password(secret, self.secret_hash)

    @staticmethod
    def generate_secret():
        """
        Genere un secret aleatoire securise.
        """
        return secrets.token_urlsafe(32)

    def __str__(self):
        return f"{self.agent_id} - {self.device.device_id}"
