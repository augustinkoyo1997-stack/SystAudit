import hashlib
import hmac
import json
import time
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import License
from .models import Payment
from .views import _verify_fedapay_signature


class FedaPaySignatureTests(TestCase):
    def test_accepts_valid_recent_signature(self):
        body = b'{"name":"transaction.approved"}'
        secret = "webhook-secret"
        timestamp = int(time.time())
        digest = hmac.new(secret.encode(), str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
        self.assertTrue(_verify_fedapay_signature(body, f"t={timestamp},s={digest}", secret))

    def test_rejects_bad_or_stale_signature(self):
        body = b'{"name":"transaction.approved"}'
        self.assertFalse(_verify_fedapay_signature(body, "t=1,s=bad", "secret"))
        self.assertFalse(_verify_fedapay_signature(body, "t=1,s=bad", ""))


class FedaPayCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="premium_user",
            email="premium@example.com",
            password="StrongPassword123!",
        )
        self.license = License.objects.get(user=self.user)
        self.client.force_login(self.user)

    @override_settings(FEDAPAY_PREMIUM_PRICE_XOF=0)
    def test_checkout_disabled_until_price_is_configured(self):
        response = self.client.post(reverse("start_premium_checkout"))
        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(Payment.objects.exists())

    @override_settings(FEDAPAY_PREMIUM_PRICE_XOF=10000)
    @patch("billing.views.create_payment_link", return_value=("fp-123", "https://checkout.fedapay.com/pay/123"))
    def test_checkout_creates_local_payment_and_redirects_to_provider(self, create_link):
        response = self.client.post(reverse("start_premium_checkout"))
        self.assertRedirects(response, "https://checkout.fedapay.com/pay/123", fetch_redirect_response=False)
        payment = Payment.objects.get(provider_transaction_id="fp-123")
        self.assertEqual(payment.amount_xof, 10000)
        self.assertEqual(payment.status, Payment.PENDING)
        create_link.assert_called_once()

    def _post_webhook(self, event):
        body = json.dumps(event, separators=(",", ":")).encode()
        secret = "webhook-secret"
        timestamp = int(time.time())
        digest = hmac.new(secret.encode(), str(timestamp).encode() + b"." + body, hashlib.sha256).hexdigest()
        return self.client.post(
            reverse("fedapay_webhook"),
            data=body,
            content_type="application/json",
            HTTP_X_FEDAPAY_SIGNATURE=f"t={timestamp},s={digest}",
        )

    @override_settings(FEDAPAY_WEBHOOK_SECRET="webhook-secret", FEDAPAY_PREMIUM_MAX_DEVICES=5)
    def test_only_signed_approved_payment_activates_premium_once(self):
        payment = Payment.objects.create(
            user=self.user,
            license=self.license,
            provider_transaction_id="fp-approved",
            amount_xof=10000,
        )
        event = {
            "name": "transaction.approved",
            "data": {"transaction": {"id": "fp-approved", "amount": 10000, "status": "approved"}},
        }
        response = self._post_webhook(event)
        self.assertEqual(response.status_code, 200)
        self.license.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(self.license.plan, License.PLAN_PREMIUM)
        self.assertEqual(self.license.max_devices, 5)
        self.assertEqual(payment.status, Payment.APPROVED)
        expiry = self.license.expires_at

        self._post_webhook(event)
        self.license.refresh_from_db()
        self.assertEqual(self.license.expires_at, expiry)

    @override_settings(FEDAPAY_WEBHOOK_SECRET="webhook-secret")
    def test_amount_mismatch_does_not_activate_plan(self):
        Payment.objects.create(
            user=self.user,
            license=self.license,
            provider_transaction_id="fp-wrong-amount",
            amount_xof=10000,
        )
        response = self._post_webhook({
            "name": "transaction.approved",
            "data": {"transaction": {"id": "fp-wrong-amount", "amount": 1, "status": "approved"}},
        })
        self.assertEqual(response.status_code, 400)
        self.license.refresh_from_db()
        self.assertEqual(self.license.plan, License.PLAN_FREE)

    def test_browser_return_never_activates_a_subscription(self):
        self.client.get(reverse("fedapay_return"), {"status": "approved", "id": "forged"})
        self.license.refresh_from_db()
        self.assertEqual(self.license.plan, License.PLAN_FREE)
        self.assertIsNone(self.license.expires_at)\n