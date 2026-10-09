from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import License


class LicenseValidityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="license_test_user",
            password="StrongPassword123!",
        )
        self.license = License.objects.get(
            user=self.user,
        )

    def test_active_license_without_expiration_is_valid(self):
        self.assertTrue(self.license.is_valid)

    def test_inactive_license_is_invalid(self):
        self.license.is_active = False

        self.assertFalse(self.license.is_valid)

    def test_expired_license_is_invalid(self):
        self.license.expires_at = (
            timezone.now() - timedelta(days=1)
        )

        self.assertFalse(self.license.is_valid)

    def test_active_license_with_future_expiration_is_valid(self):
        self.license.expires_at = (
            timezone.now() + timedelta(days=30)
        )

        self.assertTrue(self.license.is_valid)


class AuthenticationTests(TestCase):
    def test_register_creates_user_and_free_license(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))

        user = User.objects.get(username="newuser")

        license_obj = License.objects.get(user=user)

        self.assertEqual(license_obj.plan, License.PLAN_FREE)
        self.assertTrue(license_obj.is_active)
        self.assertEqual(license_obj.max_devices, 1)

    def test_login_success(self):
        User.objects.create_user(
            username="loginuser",
            password="StrongPassword123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "loginuser",
                "password": "StrongPassword123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))

    def test_login_invalid_credentials(self):
        User.objects.create_user(
            username="loginuser",
            password="StrongPassword123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "loginuser",
                "password": "WrongPassword!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Please enter a correct username and password.",
        )

    def test_logout(self):
        User.objects.create_user(
            username="logoutuser",
            password="StrongPassword123!",
        )

        self.client.login(
            username="logoutuser",
            password="StrongPassword123!",
        )

        response = self.client.get(reverse("logout"))

        self.assertRedirects(response, reverse("login"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}",
        )