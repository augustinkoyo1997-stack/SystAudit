from django.db import models
from django.utils import timezone

from licensing.models import AuditReport


class RemediationRequest(models.Model):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

    STATUS_CHOICES = [
        (PROPOSED, "Proposed"),
        (APPROVED, "Approved"),
        (EXECUTING, "Executing"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (ROLLED_BACK, "Rolled back"),
    ]

    audit_report = models.ForeignKey(
        AuditReport,
        on_delete=models.CASCADE,
        related_name="remediation_requests",
    )

    remediation_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    severity = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PROPOSED,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    executed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.remediation_id} - {self.title}"

    def save(self, *args, **kwargs):
        """
        Prevent direct status transitions.

        Status changes must go through the dedicated workflow
        methods: approve(), start_execution(), mark_success(),
        mark_failed(), and rollback().
        """

        if self.pk:
            previous = type(self).objects.get(pk=self.pk)

            if previous.status != self.status:
                allowed_transitions = {
                    self.PROPOSED: {self.APPROVED},
                    self.APPROVED: {self.EXECUTING},
                    self.EXECUTING: {
                        self.SUCCESS,
                        self.FAILED,
                    },
                    self.FAILED: {
                        self.ROLLED_BACK,
                    },
                    self.SUCCESS: set(),
                    self.ROLLED_BACK: set(),
                }

                allowed = allowed_transitions.get(
                    previous.status,
                    set(),
                )

                if self.status not in allowed:
                    raise ValueError(
                        f"Invalid remediation status transition: "
                        f"{previous.status} -> {self.status}"
                    )

        super().save(*args, **kwargs)

    def approve(self):
        if self.status != self.PROPOSED:
            raise ValueError(
                "Only proposed remediations can be approved."
            )

        self.status = self.APPROVED
        self.approved_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "approved_at",
                "updated_at",
            ]
        )

    def start_execution(self):
        if self.status != self.APPROVED:
            raise ValueError(
                "Only approved remediations can start execution."
            )

        self.status = self.EXECUTING

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    def mark_success(self):
        if self.status != self.EXECUTING:
            raise ValueError(
                "Only executing remediations can succeed."
            )

        self.status = self.SUCCESS
        self.executed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "executed_at",
                "updated_at",
            ]
        )

    def mark_failed(self):
        if self.status != self.EXECUTING:
            raise ValueError(
                "Only executing remediations can fail."
            )

        self.status = self.FAILED
        self.executed_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "executed_at",
                "updated_at",
            ]
        )

    def rollback(self):
        if self.status != self.FAILED:
            raise ValueError(
                "Only failed remediations can be rolled back."
            )

        self.status = self.ROLLED_BACK

        self.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )
        