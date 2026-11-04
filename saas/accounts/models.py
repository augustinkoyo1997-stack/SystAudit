
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


class WorkspaceActivity(models.Model):
    ACTION_WORKSPACE_CREATED = "workspace_created"
    ACTION_INVITATION_SENT = "invitation_sent"
    ACTION_MEMBER_JOINED = "member_joined"
    ACTION_MEMBER_REMOVED = "member_removed"
    ACTION_COMPUTER_ADDED = "computer_added"
    ACTION_COMPUTER_UPDATED = "computer_updated"
    ACTION_REPAIR_RECORDED = "repair_recorded"
    ACTION_AUDIT_RECEIVED = "audit_received"

    ACTION_CHOICES = [
        (ACTION_WORKSPACE_CREATED, "a créé l’espace d’équipe"),
        (ACTION_INVITATION_SENT, "a envoyé une invitation à"),
        (ACTION_MEMBER_JOINED, "a rejoint l’équipe"),
        (ACTION_MEMBER_REMOVED, "a retiré le membre"),
        (ACTION_COMPUTER_ADDED, "a ajouté le poste"),
        (ACTION_COMPUTER_UPDATED, "a mis à jour le poste"),
        (ACTION_REPAIR_RECORDED, "a enregistré une intervention sur"),
        (ACTION_AUDIT_RECEIVED, "a reçu un audit pour"),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workspace_activities",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    target_label = models.CharField(max_length=254, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"], name="workspace_activity_recent_idx"),
        ]


class DeploymentProfile(models.Model):
    """A reusable, workspace-scoped recipe for a future network deployment."""

    LANGUAGE_CHOICES = [("fr-FR", "Français (France)"), ("en-US", "English (United States)")]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deployment_profiles")
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name="deployment_profiles"
    )
    name = models.CharField(max_length=100)
    windows_iso = models.CharField(max_length=180)
    image_index = models.PositiveSmallIntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="fr-FR")
    applications = models.JSONField(default=list, blank=True)
    office_product_id = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DeploymentBatch(models.Model):
    """A central request waiting for matching WinPE clients on the local network."""

    STATUS_QUEUED = "queued"
    STATUS_CHOICES = [(STATUS_QUEUED, "En attente des postes")]

    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, null=True, blank=True, related_name="deployment_batches"
    )
    profile = models.ForeignKey(DeploymentProfile, on_delete=models.PROTECT, related_name="batches")
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deployment_batches")
    target_count = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile.name} — {self.target_count} poste(s)"


class DeploymentRun(models.Model):
    """One target computer in a batch, enrolled by a short-lived bootstrap token."""

    STATUS_WAITING = "waiting"
    STATUS_CONNECTED = "connected"
    STATUS_CONFIRMATION = "awaiting_confirmation"
    STATUS_INSTALLING = "installing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_WAITING, "En attente du poste"),
        (STATUS_CONNECTED, "Poste connecté"),
        (STATUS_CONFIRMATION, "Confirmation requise"),
        (STATUS_INSTALLING, "Installation en cours"),
        (STATUS_COMPLETED, "Terminée"),
        (STATUS_FAILED, "Échec"),
    ]

    batch = models.ForeignKey(DeploymentBatch, on_delete=models.CASCADE, related_name="runs")
    token_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_WAITING)
    machine_name = models.CharField(max_length=100, blank=True)
    machine_model = models.CharField(max_length=160, blank=True)
    target_disk = models.CharField(max_length=120, blank=True)
    target_disk_size_gb = models.PositiveIntegerField(null=True, blank=True)
    current_step = models.CharField(max_length=120, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    operator_confirmed_at = models.DateTimeField(null=True, blank=True)
    failure_summary = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_seen = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.batch} — {self.machine_name or 'poste en attente'}"


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
