from rest_framework.test import APITestCase
import json

from licensing.models import LicensedDevice
from .models import Agent
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User

class AgentHeartbeatTests(APITestCase):

    def setUp(self):
        self.user = self._create_user()

        self.device = LicensedDevice.objects.create(
            license=self.user.license,
            device_id="TEST-AGENT-001",
        )

        self.agent = Agent.objects.create(
            device=self.device,
        )

        self.secret = Agent.generate_secret()
        self.agent.set_secret(self.secret)
        self.agent.save()

        self.url = "/api/agent/heartbeat/"

    def _create_user(self):
        user = User.objects.create_user(
            username="agent_test_user",
            password="test-password-123",
        )

        return user

    def test_heartbeat_with_valid_credentials(self):
        response = self.client.post(
            self.url,
            {
                "agent_id": str(self.agent.agent_id),
                "secret": self.secret,
            },
            format="json",
        )

        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(
            data["agent_id"],
            str(self.agent.agent_id),
        )
        self.assertEqual(
            data["device_id"],
            "TEST-AGENT-001",
        )

        self.agent.refresh_from_db()

        self.assertEqual(
            self.agent.status,
            Agent.ONLINE,
        )
        self.assertIsNotNone(self.agent.last_seen)

    def test_heartbeat_rejects_wrong_secret(self):
        response = self.client.post(
            self.url,
            {
                "agent_id": str(self.agent.agent_id),
                "secret": "wrong-secret",
            },
            format="json",
        )

        data = json.loads(response.content)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            data["error"],
            "Authentification échouée.",
        )

    def test_heartbeat_rejects_unknown_agent(self):
        response = self.client.post(
            self.url,
            {
                "agent_id": "00000000-0000-0000-0000-000000000000",
                "secret": self.secret,
            },
            format="json",
        )

        data = json.loads(response.content)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            data["error"],
            "Agent inconnu.",
        )

    def test_heartbeat_rejects_revoked_agent(self):
        self.agent.status = Agent.REVOKED
        self.agent.save(update_fields=["status"])

        response = self.client.post(
            self.url,
            {
                "agent_id": str(self.agent.agent_id),
                "secret": self.secret,
            },
            format="json",
        )

        data = json.loads(response.content)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            data["error"],
            "Agent révoqué.",
        )

    def test_heartbeat_requires_credentials(self):
        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        data = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            data["error"],
            "agent_id et secret sont requis.",
        )

    def test_heartbeat_rejects_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_heartbeat_rejects_invalid_json(self):
        response = self.client.post(
            self.url,
            data="ceci n'est pas du JSON",
            content_type="application/json",
        )

        data = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            data["error"],
            "JSON invalide.",
        )

    def test_heartbeat_rejects_malformed_agent_id(self):
        response = self.client.post(
            self.url,
            {
                "agent_id": "not-a-valid-uuid",
                "secret": self.secret,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)



    def test_heartbeat_rejects_agent_without_secret(self):
        self.agent.secret_hash = None
        self.agent.save(update_fields=["secret_hash"])

        response = self.client.post(
            self.url,
            {
                "agent_id": str(self.agent.agent_id),
                "secret": self.secret,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)
    def test_heartbeat_rejects_inactive_license(self):
        license_obj = self.device.license
        license_obj.is_active = False
        license_obj.save(update_fields=["is_active"])

        response = self.client.post(
            self.url,
            {
                "agent_id": str(self.agent.agent_id),
                "secret": self.secret,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_heartbeat_rejects_expired_license(self):
        from datetime import timedelta
        from django.utils import timezone

        license_obj = self.device.license
        license_obj.expires_at = (
            timezone.now() - timedelta(days=1)
        )
        license_obj.save(update_fields=["expires_at"])

        response = self.client.post(
            self.url,
            {
                "agent_id": str(self.agent.agent_id),
                "secret": self.secret,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

class AgentRegistrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="agent_registration_user",
            password="TestPassword123!",
        )
        self.license = self.user.license
        self.license.max_devices = 2
        self.license.save(update_fields=["max_devices"])

        self.device = LicensedDevice.objects.create(
            license=self.license,
            device_id="REGISTRATION-PC-001",
        )
        self.url = "/api/agent/register/"

    def payload(self):
        return {
            "key": str(self.license.key),
            "device_id": self.device.device_id,
        }

    def test_register_new_agent_successfully(self):
        response = self.client.post(
            self.url, self.payload(), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["registered"])
        self.assertIn("secret", response.data)

        agent = Agent.objects.get(device=self.device)
        secret = response.data["secret"]
        self.assertEqual(str(agent.agent_id), response.data["agent_id"])
        self.assertTrue(agent.check_secret(secret))
        self.assertNotEqual(agent.secret_hash, secret)

    def test_register_rejects_duplicate_agent(self):
        first = self.client.post(
            self.url, self.payload(), format="json"
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            self.url, self.payload(), format="json"
        )
        self.assertEqual(second.status_code, 409)
        self.assertNotIn("secret", second.data)
        self.assertEqual(
            Agent.objects.filter(device=self.device).count(), 1
        )

    def test_register_rejects_inactive_license(self):
        self.license.is_active = False
        self.license.save(update_fields=["is_active"])
        response = self.client.post(
            self.url, self.payload(), format="json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["registered"])

    def test_register_rejects_expired_license(self):
        self.license.expires_at = timezone.now() - timedelta(days=1)
        self.license.save(update_fields=["expires_at"])
        response = self.client.post(
            self.url, self.payload(), format="json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data["registered"])

    def test_register_rejects_unactivated_device(self):
        payload = {
            "key": str(self.license.key),
            "device_id": "UNKNOWN-REGISTRATION-PC",
        }
        response = self.client.post(
            self.url, payload, format="json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["registered"])

    def test_register_requires_license_and_device(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["registered"])

    def test_register_rejects_unknown_license(self):
        payload = self.payload()
        payload["key"] = "00000000-0000-0000-0000-000000000000"
        response = self.client.post(
            self.url, payload, format="json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["registered"])
