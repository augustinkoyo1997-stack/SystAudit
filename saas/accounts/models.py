
import uuid
from datetime import timedelta

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


class WorkspaceInvitation(models.Model):
    """An email-confirmed invitation to join one workspace."""

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_invitations_sent",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} — {self.workspace}"


class ManagedComputer(models.Model):
    """A company workstation tracked from preparation through retirement."""

    STATUS_PREPARING = "preparing"
    STATUS_READY = "ready"
    STATUS_IN_USE = "in_use"
    STATUS_REPAIR = "repair"
    STATUS_RETIRED = "retired"
    STATUS_CHOICES = [
        (STATUS_PREPARING, "Préparation en cours"),
        (STATUS_READY, "Prêt à remettre"),
        (STATUS_IN_USE, "En service"),
        (STATUS_REPAIR, "En réparation"),
        (STATUS_RETIRED, "Retiré"),
    ]

    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="managed_computers"
    )
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="managed_computers",
        null=True, blank=True,
    )
    licensed_device = models.OneToOneField(
        "licensing.LicensedDevice",
        on_delete=models.SET_NULL,
        related_name="managed_computer",
        null=True,
        blank=True,
    )
    asset_tag = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=120)
    brand = models.CharField(max_length=80, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=120, blank=True)
    assigned_to = models.CharField(max_length=120, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost_xof = models.PositiveIntegerField(default=0)
    replacement_cost_xof = models.PositiveIntegerField(default=0)
    next_repair_estimate_xof = models.PositiveIntegerField(default=0)
    deployment_profile = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PREPARING)
    os_installed = models.BooleanField(default=False)
    drivers_installed = models.BooleanField(default=False)
    updates_installed = models.BooleanField(default=False)
    apps_installed = models.BooleanField(default=False)
    security_checked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "asset_tag"]

    def save(self, *args, **kwargs):
        if not self.asset_tag:
            self.asset_tag = f"OT-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_tag} — {self.name}"

    @property
    def repair_total_xof(self):
        return sum(item.cost_xof for item in self.interventions.all())

    @property
    def repair_count_last_year(self):
        since = timezone.localdate() - timedelta(days=365)
        return self.interventions.filter(performed_at__gte=since).count()

    @property
    def historical_spend_exceeds_purchase(self):
        return bool(self.purchase_cost_xof and self.repair_total_xof >= self.purchase_cost_xof)

    @property
    def replacement_guidance(self):
        """A transparent decision aid; historic spend alone is a review signal."""
        if not self.replacement_cost_xof:
            return "Renseigner le coût d’un poste équivalent"
        quote = self.next_repair_estimate_xof
        repeated = self.repair_count_last_year >= 3
        if quote >= self.replacement_cost_xof * 0.5:
            return "Comparer le devis au remplacement"
        if repeated and quote >= self.replacement_cost_xof * 0.25:
            return "Comparer la réparation au remplacement"
        if repeated:
            return "Pannes répétées : faire évaluer la fiabilité"
        if self.historical_spend_exceeds_purchase:
            return "Historique coûteux : évaluer la fiabilité avant réparation"
        return "Réparation envisageable selon le diagnostic"


class RepairIntervention(models.Model):
    computer = models.ForeignKey(
        ManagedComputer, on_delete=models.CASCADE, related_name="interventions"
    )
    performed_at = models.DateField(default=timezone.localdate)
    title = models.CharField(max_length=160)
    details = models.TextField(blank=True)
    cost_xof = models.PositiveIntegerField(default=0)
    downtime_hours = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    technician = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="repair_interventions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-performed_at", "-created_at"]

    def __str__(self):
        return f"{self.computer.asset_tag} — {self.title}"
