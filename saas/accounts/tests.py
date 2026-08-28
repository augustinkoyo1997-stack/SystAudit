from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import License


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