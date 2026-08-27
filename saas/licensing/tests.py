from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import License
from .models import LicensedDevice


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