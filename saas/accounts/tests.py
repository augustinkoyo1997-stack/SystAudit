from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from urllib.parse import urlsplit

from accounts.models import License, Workspace, WorkspaceMembership
from licensing.models import AuditReport, LicensedDevice
from remediation.models import RemediationRequest


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
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_register_requires_email_confirmation(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vérifiez votre boîte e-mail")

        user = User.objects.get(username="newuser")

        license_obj = License.objects.get(user=user)

        self.assertEqual(license_obj.plan, License.PLAN_FREE)
        self.assertTrue(license_obj.is_active)
        self.assertEqual(license_obj.max_devices, 1)
        self.assertEqual(user.email, "newuser@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(license_obj.is_valid)
        self.assertEqual(len(mail.outbox), 1)

        verification_url = next(
            part for part in mail.outbox[0].body.split()
            if "/accounts/verify-email/" in part
        )
        verification_path = urlsplit(verification_url).path
        verification_segments = verification_path.strip("/").split("/")
        uidb64, token = verification_segments[-2:]

        response = self.client.get(
            reverse(
                "verify_email",
                kwargs={"uidb64": uidb64, "token": token},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Adresse e-mail confirmée")

        user.refresh_from_db()
        license_obj.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(license_obj.is_valid)

    def test_unverified_user_cannot_log_in(self):
        User.objects.create_user(
            username="unverified",
            email="unverified@example.com",
            password="StrongPassword123!",
            is_active=False,
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "unverified",
                "password": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_requires_a_valid_unique_email(self):
        User.objects.create_user(
            username="existinguser",
            email="taken@example.com",
            password="StrongPassword123!",
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "anotheruser",
                "email": "TAKEN@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cette adresse e-mail est déjà utilisée.")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_password_reset_email_can_reset_the_password(self):
        User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OldStrongPassword123!",
        )

        response = self.client.post(
            reverse("password_reset"),
            {"email": "reset@example.com"},
        )

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

        reset_url = next(
            part for part in mail.outbox[0].body.split()
            if "/accounts/password-reset/" in part
        )
        reset_path = urlsplit(reset_url).path
        reset_segments = reset_path.strip("/").split("/")
        uidb64, token = reset_segments[-2:]

        response = self.client.get(
            reverse(
                "password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": token},
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        confirm_path = response.request["PATH_INFO"]
        response = self.client.post(
            confirm_path,
            {
                "new_password1": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("password_reset_complete"),
        )
        self.assertTrue(
            User.objects.get(username="resetuser").check_password(
                "NewStrongPassword123!"
            )
        )

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


class WorkspaceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="company_owner", email="owner@example.com", password="StrongPassword123!"
        )
        self.member = User.objects.create_user(
            username="company_member", email="member@example.com", password="StrongPassword123!"
        )

    def test_owner_can_create_workspace_and_add_existing_confirmed_account(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("create_workspace"), {"name": "Acme PME"})
        self.assertRedirects(response, reverse("dashboard"))
        workspace = Workspace.objects.get(owner=self.owner)
        self.assertEqual(workspace.license, self.owner.license)
        owner_membership = WorkspaceMembership.objects.get(user=self.owner)
        self.assertEqual(owner_membership.role, WorkspaceMembership.OWNER)

        response = self.client.post(
            reverse("add_workspace_member"), {"email": "MEMBER@example.com"}
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(
            WorkspaceMembership.objects.get(user=self.member).workspace,
            workspace,
        )

    def test_member_dashboard_uses_only_the_shared_workspace_license(self):
        workspace = Workspace.objects.create(
            name="Acme PME", owner=self.owner, license=self.owner.license
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.owner, role=WorkspaceMembership.OWNER
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.member, role=WorkspaceMembership.MEMBER
        )
        team_device = LicensedDevice.objects.create(
            license=self.owner.license, device_id="team-device"
        )
        team_report = AuditReport.objects.create(device=team_device, score=80)
        personal_device = LicensedDevice.objects.create(
            license=self.member.license, device_id="private-device"
        )
        AuditReport.objects.create(device=personal_device, score=30)

        self.client.force_login(self.member)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["license"], self.owner.license)
        self.assertEqual(list(response.context["audit_history"]), [team_report])
        self.assertEqual(list(response.context["devices"]), [team_device])
        self.assertNotContains(response, "private-device")
        self.assertNotContains(response, str(self.owner.license.key))

    def test_non_admin_cannot_add_a_member(self):
        workspace = Workspace.objects.create(
            name="Acme PME", owner=self.owner, license=self.owner.license
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.owner, role=WorkspaceMembership.OWNER
        )
        another = User.objects.create_user(
            username="another", email="another@example.com", password="StrongPassword123!"
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.member, role=WorkspaceMembership.MEMBER
        )
        self.client.force_login(self.member)
        self.client.post(reverse("add_workspace_member"), {"email": another.email})
        self.assertFalse(WorkspaceMembership.objects.filter(user=another).exists())

    def test_member_cannot_open_owner_remediation_using_private_audit_id(self):
        workspace = Workspace.objects.create(
            name="Acme PME", owner=self.owner, license=self.owner.license
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.owner, role=WorkspaceMembership.OWNER
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.member, role=WorkspaceMembership.MEMBER
        )
        private_device = LicensedDevice.objects.create(
            license=self.member.license, device_id="private-device"
        )
        private_report = AuditReport.objects.create(
            device=private_device,
            score=30,
            findings=[{"category": "firewall", "risk": "high", "message": "test"}],
        )
        self.client.force_login(self.member)
        response = self.client.post(
            reverse(
                "create_remediation_request",
                kwargs={"audit_id": private_report.pk, "category": "firewall"},
            )
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(private_report.remediation_requests.exists())

    def test_team_member_cannot_approve_company_remediation(self):
        workspace = Workspace.objects.create(
            name="Acme PME", owner=self.owner, license=self.owner.license
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.owner, role=WorkspaceMembership.OWNER
        )
        WorkspaceMembership.objects.create(
            workspace=workspace, user=self.member, role=WorkspaceMembership.MEMBER
        )
        device = LicensedDevice.objects.create(
            license=self.owner.license, device_id="team-device"
        )
        report = AuditReport.objects.create(device=device, score=30)
        remediation = RemediationRequest.objects.create(
            audit_report=report,
            remediation_id="REM-FIREWALL",
            title="Firewall",
            description="Check firewall",
            severity="HIGH",
        )
        self.client.force_login(self.member)
        response = self.client.post(
            reverse("approve_remediation_request", kwargs={"request_id": remediation.pk})
        )
        self.assertEqual(response.status_code, 404)
        remediation.refresh_from_db()
        self.assertEqual(remediation.status, RemediationRequest.PROPOSED)
