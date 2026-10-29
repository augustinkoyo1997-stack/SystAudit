from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.db import close_old_connections
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory, APITestCase
from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from accounts.models import License
from .models import AuditReport, LicensedDevice


class PublicApiThrottleTests(SimpleTestCase):
    def test_public_api_rate_limit_returns_429(self):
        cache.clear()
        request_factory = APIRequestFactory()
        api_view = APIView()
        throttle = AnonRateThrottle()
        throttle.rate = "1/minute"
        throttle.num_requests, throttle.duration = throttle.parse_rate(throttle.rate)
        first_raw = request_factory.post("/api/license/validate/", REMOTE_ADDR="198.51.100.75")
        second_raw = request_factory.post("/api/license/validate/", REMOTE_ADDR="198.51.100.75")
        first_raw.user = AnonymousUser()
        second_raw.user = AnonymousUser()
        first = Request(first_raw)
        second = Request(second_raw)
        self.assertTrue(throttle.allow_request(first, api_view))
        self.assertFalse(throttle.allow_request(second, api_view))


class LicenseActivationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="activation_user",
            password="TestPassword123!",
        )

        self.license = License.objects.get(user=self.user)
        self.license.plan = License.PLAN_PREMIUM
        self.license.is_active = True
        self.license.max_devices = 2
        self.license.expires_at = None
        self.license.save()

        self.url = "/api/license/activate/"

    def test_activate_new_device(self):
        response = self.client.post(
            self.url,
            {
                "key": str(self.license.key),
                "device_id": "PC-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["activated"])
        self.assertEqual(response.data["device_id"], "PC-001")
        self.assertEqual(response.data["devices_used"], 1)
        self.assertEqual(response.data["max_devices"], 2)

        self.assertTrue(
            LicensedDevice.objects.filter(
                license=self.license,
                device_id="PC-001",
            ).exists()
        )

    def test_activate_already_registered_device(self):
        LicensedDevice.objects.create(
            license=self.license,
            device_id="PC-001",
        )

        response = self.client.post(
            self.url,
            {
                "key": str(self.license.key),
                "device_id": "PC-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["activated"])
        self.assertEqual(
            response.data["message"],
            "Device already activated.",
        )
        self.assertEqual(response.data["devices_used"], 1)

    def test_activate_device_when_limit_is_reached(self):
        LicensedDevice.objects.create(
            license=self.license,
            device_id="PC-001",
        )
        LicensedDevice.objects.create(
            license=self.license,
            device_id="PC-002",
        )

        response = self.client.post(
            self.url,
            {
                "key": str(self.license.key),
                "device_id": "PC-003",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.data["activated"])
        self.assertEqual(
            response.data["error"],
            "Maximum number of devices reached.",
        )
        self.assertEqual(response.data["devices_used"], 2)
        self.assertEqual(response.data["max_devices"], 2)

    def test_activate_with_invalid_license(self):
        response = self.client.post(
            self.url,
            {
                "key": "00000000-0000-0000-0000-000000000000",
                "device_id": "PC-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["activated"])
        self.assertEqual(
            response.data["error"],
            "Invalid license.",
        )

    def test_activate_inactive_license(self):
        self.license.is_active = False
        self.license.save(update_fields=["is_active"])

        response = self.client.post(
            self.url,
            {
                "key": str(self.license.key),
                "device_id": "PC-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["activated"])
        self.assertEqual(
            response.data["error"],
            "License is inactive.",
        )

    def test_activate_expired_license(self):
        self.license.expires_at = timezone.now() - timedelta(days=1)
        self.license.save(update_fields=["expires_at"])

        response = self.client.post(
            self.url,
            {
                "key": str(self.license.key),
                "device_id": "PC-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["activated"])
        self.assertEqual(
            response.data["error"],
            "License expired.",
        )

    def test_activate_requires_license_key(self):
        response = self.client.post(
            self.url,
            {
                "device_id": "PC-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["activated"])
        self.assertEqual(
            response.data["error"],
            "License key is required.",
        )

    def test_activate_requires_device_id(self):
        response = self.client.post(
            self.url,
            {
                "key": str(self.license.key),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["activated"])
        self.assertEqual(
            response.data["error"],
            "Device ID is required.",
        )


class LicenseActivationConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            username="activation_concurrency_user",
            password="TestPassword123!",
        )

        self.license = License.objects.get(user=self.user)
        self.license.plan = License.PLAN_PREMIUM
        self.license.is_active = True
        self.license.max_devices = 2
        self.license.expires_at = None
        self.license.save()

        # Un appareil est déjà activé : il ne reste qu'une place.
        LicensedDevice.objects.create(
            license=self.license,
            device_id="PC-EXISTING",
        )

        self.url = "/api/license/activate/"
        self.license_key = str(self.license.key)

    def test_concurrent_activations_respect_device_limit(self):
        barrier = Barrier(2)

        def activate(device_id):
            close_old_connections()
            try:
                client = APIClient()

                # Les deux threads démarrent leur requête ensemble.
                barrier.wait(timeout=10)

                response = client.post(
                    self.url,
                    {
                        "key": self.license_key,
                        "device_id": device_id,
                    },
                    format="json",
                )
                return response.status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_1 = executor.submit(activate, "PC-CONCURRENT-001")
            future_2 = executor.submit(activate, "PC-CONCURRENT-002")

            status_codes = [
                future_1.result(timeout=20),
                future_2.result(timeout=20),
            ]

        self.assertCountEqual(status_codes, [201, 409])

        self.assertEqual(
            LicensedDevice.objects.filter(
                license=self.license,
            ).count(),
            2,
        )


class AuditReportModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="audit_user",
            password="TestPassword123!",
        )

        self.license = License.objects.get(user=self.user)

        self.device = LicensedDevice.objects.create(
            license=self.license,
            device_id="PC-AUDIT-001",
        )

    def test_create_audit_report(self):
        report = AuditReport.objects.create(
            device=self.device,
            score=90,
            summary={
                "total_findings": 1,
                "high": 0,
                "medium": 1,
                "low": 0,
            },
            findings=[
                {
                    "risk": "medium",
                    "reason": "BitLocker protection is disabled.",
                }
            ],
            recommendations=[
                {
                    "risk": "medium",
                    "reason": "BitLocker protection is disabled.",
                    "recommendation": "Enable BitLocker protection.",
                }
            ],
        )

        self.assertEqual(report.device, self.device)
        self.assertEqual(report.score, 90)
        self.assertEqual(report.summary["medium"], 1)
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(len(report.recommendations), 1)

    def test_audit_reports_are_ordered_by_newest_first(self):
        older_report = AuditReport.objects.create(
            device=self.device,
            score=80,
        )

        newer_report = AuditReport.objects.create(
            device=self.device,
            score=95,
        )

        reports = list(
            AuditReport.objects.filter(device=self.device)
        )

        self.assertEqual(reports[0], newer_report)
        self.assertEqual(reports[1], older_report)

    def test_deleting_device_deletes_audit_reports(self):
        AuditReport.objects.create(
            device=self.device,
            score=90,
        )

        self.device.delete()

        self.assertFalse(
            AuditReport.objects.filter(
                device_id=self.device.pk
            ).exists()
        )


class AuditReportAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="report_user",
            password="TestPassword123!",
        )

        self.license = License.objects.get(user=self.user)
        self.license.plan = License.PLAN_PREMIUM
        self.license.is_active = True
        self.license.max_devices = 1
        self.license.expires_at = None
        self.license.save()

        self.device = LicensedDevice.objects.create(
            license=self.license,
            device_id="PC-REPORT-001",
        )

        self.url = "/api/license/audit/report/"

        self.payload = {
            "key": str(self.license.key),
            "device_id": self.device.device_id,
            "score": 90,
            "summary": {
                "total_findings": 1,
                "high": 0,
                "medium": 1,
                "low": 0,
            },
            "findings": [
                {
                    "risk": "medium",
                    "reason": "BitLocker protection is disabled.",
                }
            ],
            "recommendations": [
                {
                    "risk": "medium",
                    "reason": "BitLocker protection is disabled.",
                    "recommendation": "Enable BitLocker protection.",
                }
            ],
        }

    def test_submit_audit_report_success(self):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["saved"])
        self.assertEqual(
            response.data["device_id"],
            "PC-REPORT-001",
        )
        self.assertEqual(response.data["score"], 90)

        self.assertTrue(
            AuditReport.objects.filter(
                device=self.device,
                score=90,
            ).exists()
        )

    def test_submit_audit_report_rejects_unknown_device(self):
        payload = {
            **self.payload,
            "device_id": "UNKNOWN-DEVICE",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["saved"])
        self.assertEqual(
            response.data["error"],
            "Device is not authorized for this license.",
        )

        self.assertEqual(
            AuditReport.objects.count(),
            0,
        )

    def test_submit_audit_report_rejects_invalid_license(self):
        payload = {
            **self.payload,
            "key": "00000000-0000-0000-0000-000000000000",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["saved"])
        self.assertEqual(
            response.data["error"],
            "Invalid license.",
        )

    def test_submit_audit_report_rejects_invalid_score(self):
        payload = {
            **self.payload,
            "score": 101,
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["saved"])
        self.assertEqual(
            response.data["error"],
            "Score must be between 0 and 100.",
        )

    def test_submit_audit_report_requires_license_key(self):
        payload = {
            **self.payload,
        }
        payload.pop("key")

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["saved"])
        self.assertEqual(
            response.data["error"],
            "License key is required.",
        )

    def test_submit_audit_report_requires_device_id(self):
        payload = {
            **self.payload,
        }
        payload.pop("device_id")

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["saved"])
        self.assertEqual(
            response.data["error"],
            "Device ID is required.",
        )
