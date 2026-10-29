
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


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

    @property
    def is_valid(self):
        """Vérifie si la licence est active et non expirée."""
        if not self.is_active or not self.user.is_active:
            return False

        if (
            self.expires_at is not None
            and self.expires_at <= timezone.now()
        ):
            return False

        return True


class Workspace(models.Model):
    """A shared company space backed by its owner's existing license."""

    name = models.CharField(max_length=120)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_workspaces",
    )
    license = models.OneToOneField(
        License,
        on_delete=models.CASCADE,
        related_name="workspace",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkspaceMembership(models.Model):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    ROLE_CHOICES = [
        (OWNER, "Propriétaire"),
        (ADMIN, "Administrateur"),
        (MEMBER, "Membre"),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_membership",
    )
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user} — {self.workspace} ({self.role})"
