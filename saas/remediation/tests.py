from django.contrib.auth.models import User
from django.test import TestCase

from licensing.models import AuditReport, LicensedDevice
from .models import RemediationRequest


class RemediationRequestModelTests(TestCase):

    def setUp(self):
        self.user = self._create_user()
        self.license = self.user.license

        self.device = LicensedDevice.objects.create(
            license=self.license,
            device_id="TEST-DEVICE-001",
        )

        self.audit_report = AuditReport.objects.create(
            device=self.device,
            score=70,
            summary={
                "total_checks": 10,
                "passed": 7,
                "warnings": 2,
                "critical": 1,
            },
            findings=[
                {
                    "title": "Firewall disabled",
                    "severity": "HIGH",
                    "description": "Windows Firewall is disabled.",
                }
            ],
            recommendations=[
                "Enable Windows Firewall.",
            ],
        )

    def _create_user(self):
        user = User.objects.create_user(
            username="remediation_test",
            password="test-password-123",
        )

        return user

    def test_remediation_request_creation(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            description="Enable Windows Firewall.",
            severity="HIGH",
        )

        self.assertEqual(
            remediation.status,
            RemediationRequest.PROPOSED,
        )

        self.assertEqual(
            remediation.audit_report,
            self.audit_report,
        )

    def test_default_status_is_proposed(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        self.assertEqual(
            remediation.status,
            RemediationRequest.PROPOSED,
        )

    def test_string_representation(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        self.assertEqual(
            str(remediation),
            "REM-FIREWALL - Remediate firewall",
        )

    def test_remediation_is_linked_to_audit_report(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        self.assertIn(
            remediation,
            self.audit_report.remediation_requests.all(),
        )

    def test_status_choices_are_defined(self):
        statuses = {
            choice[0]
            for choice in RemediationRequest.STATUS_CHOICES
        }

        expected_statuses = {
            RemediationRequest.PROPOSED,
            RemediationRequest.APPROVED,
            RemediationRequest.EXECUTING,
            RemediationRequest.SUCCESS,
            RemediationRequest.FAILED,
            RemediationRequest.ROLLED_BACK,
        }

        self.assertEqual(statuses, expected_statuses)

    def test_status_can_be_updated(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        remediation.status = RemediationRequest.APPROVED
        remediation.save(
            update_fields=["status", "updated_at"]
        )

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.APPROVED,
        )

    def test_proposed_can_be_approved(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        remediation.status = RemediationRequest.APPROVED
        remediation.save(
            update_fields=["status", "updated_at"]
        )

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.APPROVED,
        )

    def test_approved_can_start_execution(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.APPROVED,
        )

        remediation.status = RemediationRequest.EXECUTING
        remediation.save(
            update_fields=["status", "updated_at"]
        )

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.EXECUTING,
        )

    def test_executing_can_succeed(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.EXECUTING,
        )

        remediation.status = RemediationRequest.SUCCESS
        remediation.save(
            update_fields=["status", "updated_at"]
        )

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.SUCCESS,
        )

    def test_executing_can_fail(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.EXECUTING,
        )

        remediation.status = RemediationRequest.FAILED
        remediation.save(
            update_fields=["status", "updated_at"]
        )

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.FAILED,
        )

    def test_failed_can_be_rolled_back(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.FAILED,
        )

        remediation.status = RemediationRequest.ROLLED_BACK
        remediation.save(
            update_fields=["status", "updated_at"]
        )

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.ROLLED_BACK,
        )

    def test_approve_changes_proposed_to_approved(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        remediation.approve()

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.APPROVED,
        )

        self.assertIsNotNone(remediation.approved_at)

    def test_start_execution_requires_approval(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        with self.assertRaises(ValueError):
            remediation.start_execution()

    def test_start_execution_changes_approved_to_executing(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.APPROVED,
        )

        remediation.start_execution()

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.EXECUTING,
        )

    def test_mark_success_requires_execution(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        with self.assertRaises(ValueError):
            remediation.mark_success()

    def test_mark_success_changes_executing_to_success(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.EXECUTING,
        )

        remediation.mark_success()

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.SUCCESS,
        )

        self.assertIsNotNone(remediation.executed_at)

    def test_mark_failed_changes_executing_to_failed(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.EXECUTING,
        )

        remediation.mark_failed()

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.FAILED,
        )

        self.assertIsNotNone(remediation.executed_at)

    def test_rollback_requires_failed_status(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        with self.assertRaises(ValueError):
            remediation.rollback()

    def test_rollback_changes_failed_to_rolled_back(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.FAILED,
        )

        remediation.rollback()

        remediation.refresh_from_db()

        self.assertEqual(
            remediation.status,
            RemediationRequest.ROLLED_BACK,
        )

    def test_cannot_approve_already_approved(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.APPROVED,
        )

        with self.assertRaises(ValueError):
            remediation.approve()

    def test_cannot_start_execution_from_proposed(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        with self.assertRaises(ValueError):
            remediation.start_execution()

    def test_cannot_mark_success_from_approved(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.APPROVED,
        )

        with self.assertRaises(ValueError):
            remediation.mark_success()

    def test_cannot_mark_failed_from_proposed(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        with self.assertRaises(ValueError):
            remediation.mark_failed()

    def test_cannot_rollback_successful_remediation(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
            status=RemediationRequest.SUCCESS,
        )

        with self.assertRaises(ValueError):
            remediation.rollback()


    def test_direct_status_change_to_success_is_not_allowed(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        remediation.status = RemediationRequest.SUCCESS

        with self.assertRaises(ValueError):
            remediation.save()

    def test_direct_status_change_to_executing_is_not_allowed(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        remediation.status = RemediationRequest.EXECUTING

        with self.assertRaises(ValueError):
            remediation.save()
