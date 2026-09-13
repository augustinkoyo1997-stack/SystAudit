from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

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

    def test_target_volume_can_be_set(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-BITLOCKER-C",
            title="Remediate bitlocker C:",
            severity="MEDIUM",
            target_volume="C:",
        )

        self.assertEqual(
            remediation.target_volume,
            "C:",
        )

    def test_target_volume_is_optional(self):
        remediation = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-FIREWALL",
            title="Remediate firewall",
            severity="HIGH",
        )

        self.assertEqual(
            remediation.target_volume,
            "",
        )

    def test_bitlocker_requests_can_have_distinct_volumes(self):
        remediation_c = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-BITLOCKER-C",
            title="Remediate bitlocker C:",
            severity="MEDIUM",
            target_volume="C:",
        )

        remediation_d = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-BITLOCKER-D",
            title="Remediate bitlocker D:",
            severity="MEDIUM",
            target_volume="D:",
        )

        remediation_e = RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id="REM-BITLOCKER-E",
            title="Remediate bitlocker E:",
            severity="MEDIUM",
            target_volume="E:",
        )

        self.assertEqual(remediation_c.target_volume, "C:")
        self.assertEqual(remediation_d.target_volume, "D:")
        self.assertEqual(remediation_e.target_volume, "E:")

class RemediationRequestViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="view_test_user",
            password="test-password-123",
        )

        self.license = self.user.license

        self.device = LicensedDevice.objects.create(
            license=self.license,
            device_id="VIEW-TEST-DEVICE-001",
        )

        self.audit_report = AuditReport.objects.create(
            device=self.device,
            score=90,
            summary={
                "total_checks": 10,
                "passed": 9,
                "warnings": 1,
                "critical": 0,
            },
            findings=[],
            recommendations=[],
        )

        self.client.login(
            username="view_test_user",
            password="test-password-123",
        )

    def _create_bitlocker_request(self, volume):
        return RemediationRequest.objects.create(
            audit_report=self.audit_report,
            remediation_id=f"REM-BITLOCKER-{volume[0]}",
            title=f"Remediate bitlocker {volume}",
            description=(
                f"BitLocker protection is disabled on volume {volume}."
            ),
            severity="MEDIUM",
            target_volume=volume,
        )

    @patch(
        "remediation.views.analyze_bitlocker_state"
    )
    def test_execute_bitlocker_request_selects_c_volume(
        self,
        mock_analyze,
    ):
        request = self._create_bitlocker_request("C:")
        request.approve()

        mock_analyze.return_value = {
            "ready": False,
            "needs_remediation": True,
            "volumes": [
                {
                    "mount_point": "C:",
                    "encrypted": True,
                    "encryption_percentage": 100,
                    "protection_enabled": False,
                    "key_protectors": 0,
                    "reason": "No BitLocker key protector found.",
                },
                {
                    "mount_point": "D:",
                    "encrypted": True,
                    "encryption_percentage": 100,
                    "protection_enabled": False,
                    "key_protectors": 0,
                    "reason": "No BitLocker key protector found.",
                },
                {
                    "mount_point": "E:",
                    "encrypted": True,
                    "encryption_percentage": 100,
                    "protection_enabled": False,
                    "key_protectors": 0,
                    "reason": "No BitLocker key protector found.",
                },
            ],
        }

        response = self.client.post(
            reverse(
                "execute_remediation_request",
                args=[request.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        request.refresh_from_db()

        self.assertEqual(
            request.status,
            RemediationRequest.SUCCESS,
        )

        self.assertIn(
            "Remediation verification completed successfully.",
            request.result_message,
        )


    @patch(
        "remediation.views.analyze_bitlocker_state"
    )
    def test_dry_run_bitlocker_execution_is_allowed(
        self,
        mock_analyze,
    ):
        request = self._create_bitlocker_request("D:")

        request.execution_mode = RemediationRequest.DRY_RUN
        request.save(
            update_fields=[
                "execution_mode",
                "updated_at",
            ]
        )

        request.approve()

        mock_analyze.return_value = {
            "ready": False,
            "needs_remediation": True,
            "volumes": [
                {
                    "mount_point": "D:",
                    "encrypted": True,
                    "encryption_percentage": 100,
                    "protection_enabled": False,
                    "key_protectors": 0,
                    "reason": "No BitLocker key protector found.",
                },
            ],
        }

        response = self.client.post(
            reverse(
                "execute_remediation_request",
                args=[request.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        request.refresh_from_db()

        self.assertEqual(
            request.execution_mode,
            RemediationRequest.DRY_RUN,
        )

        self.assertEqual(
            request.status,
            RemediationRequest.SUCCESS,
        )

        self.assertIn(
            "Remediation verification completed successfully.",
            request.result_message,
        )


    @patch(
        "remediation.views.analyze_bitlocker_state"
    )
    def test_real_remediation_execution_is_blocked(
        self,
        mock_analyze,
    ):
        request = self._create_bitlocker_request("E:")

        request.execution_mode = RemediationRequest.REAL
        request.save(
            update_fields=[
                "execution_mode",
                "updated_at",
            ]
        )

        request.approve()

        response = self.client.post(
            reverse(
                "execute_remediation_request",
                args=[request.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        request.refresh_from_db()

        self.assertEqual(
            request.execution_mode,
            RemediationRequest.REAL,
        )

        self.assertEqual(
            request.status,
            RemediationRequest.FAILED,
        )

        self.assertIn(
            "Real remediation execution is currently disabled.",
            request.result_message,
        )

        mock_analyze.assert_not_called()
