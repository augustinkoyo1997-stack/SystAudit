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
        MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}},
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
        MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}},
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



# ---------------------------------------------------------------------------
# Lot 2 : pièces changées et aide à la décision de remplacement
# ---------------------------------------------------------------------------
from datetime import timedelta as _timedelta

from django.contrib.auth import get_user_model as _get_user_model
from django.test import TestCase as _TestCase
from django.urls import reverse as _reverse
from django.utils import timezone as _timezone

from accounts.models import ManagedComputer as _ManagedComputer
from accounts.models import RepairIntervention as _RepairIntervention
from accounts.models import ReplacedPart as _ReplacedPart


class ReplacementAssessmentTests(_TestCase):
    def setUp(self):
        self.user = _get_user_model().objects.create_user("tech", "tech@example.com", "S3cure-Pass!")
        self.computer = _ManagedComputer.objects.create(
            created_by=self.user,
            name="PC compta",
            purchase_date=_timezone.localdate() - _timedelta(days=int(365.25 * 6)),
            purchase_cost_xof=400000,
            replacement_cost_xof=400000,
            next_repair_estimate_xof=250000,
        )

    def _repair(self, title="Panne", days_ago=10, cost=20000, hours=2):
        return _RepairIntervention.objects.create(
            computer=self.computer,
            title=title,
            cost_xof=cost,
            downtime_hours=hours,
            performed_at=_timezone.localdate() - _timedelta(days=days_ago),
        )

    def test_old_computer_with_expensive_quote_suggests_replacement(self):
        assessment = self.computer.replacement_assessment
        self.assertEqual(assessment["level"], "replace")
        self.assertTrue(assessment["reasons"])

    def test_recent_cheap_repair_is_reasonable(self):
        self.computer.purchase_date = _timezone.localdate() - _timedelta(days=200)
        self.computer.next_repair_estimate_xof = 20000
        self.computer.save()
        self.assertEqual(self.computer.replacement_assessment["level"], "repair")

    def test_recurring_part_is_reported(self):
        for day in (30, 60):
            intervention = self._repair(days_ago=day)
            _ReplacedPart.objects.create(intervention=intervention, part_type=_ReplacedPart.PART_STORAGE)
        self.assertEqual(self.computer.parts_replaced_summary, [("Disque (SSD/HDD)", 2)])
        reasons = " ".join(self.computer.replacement_assessment["reasons"])
        self.assertIn("Disque (SSD/HDD)", reasons)

    def test_missing_replacement_price_is_flagged(self):
        self.computer.replacement_cost_xof = 0
        self.computer.save()
        reasons = " ".join(self.computer.replacement_assessment["reasons"])
        self.assertIn("non renseigné", reasons)


class ReplacedPartViewTests(_TestCase):
    def setUp(self):
        User = _get_user_model()
        self.user = User.objects.create_user("tech", "tech@example.com", "S3cure-Pass!")
        self.other = User.objects.create_user("other", "other@example.com", "S3cure-Pass!")
        self.computer = _ManagedComputer.objects.create(created_by=self.user, name="PC 1")
        self.intervention = _RepairIntervention.objects.create(computer=self.computer, title="Disque HS")
        self.url = _reverse("equipment_detail", kwargs={"asset_tag": self.computer.asset_tag})

    def test_owner_can_add_part(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {
            "action": "part",
            "intervention_id": self.intervention.pk,
            "part_type": "storage",
            "description": "SSD 256 Go",
            "cost_xof": 35000,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.intervention.parts.count(), 1)

    def test_other_user_cannot_add_part(self):
        self.client.force_login(self.other)
        response = self.client.post(self.url, {
            "action": "part",
            "intervention_id": self.intervention.pk,
            "part_type": "ram",
            "cost_xof": 1000,
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.intervention.parts.count(), 0)

    def test_invalid_intervention_id_is_rejected(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"action": "part", "intervention_id": "abc", "part_type": "ram", "cost_xof": 0})
        self.assertEqual(_ReplacedPart.objects.count(), 0)

    def test_label_requires_login_and_renders(self):
        label_url = _reverse("equipment_label", kwargs={"asset_tag": self.computer.asset_tag})
        self.assertEqual(self.client.get(label_url).status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(label_url)
        self.assertContains(response, self.computer.asset_tag)



# ---------------------------------------------------------------------------
# Lot 3 : rapport global de l'entreprise
# ---------------------------------------------------------------------------
from licensing.models import AuditReport as _CRAuditReport
from licensing.models import LicensedDevice as _CRDevice


class CompanyReportTests(_TestCase):
    def setUp(self):
        User = _get_user_model()
        self.user = User.objects.create_user("boss", "boss@example.com", "S3cure-Pass!")
        self.other = User.objects.create_user("stranger", "s@example.com", "S3cure-Pass!")
        self.url = _reverse("company_report")

    def _computer(self, name, score=None, critical=0, owner=None):
        computer = _ManagedComputer.objects.create(created_by=owner or self.user, name=name)
        if score is not None:
            device = _CRDevice.objects.create(license=(owner or self.user).license, device_id=f"dev-{name}")
            computer.licensed_device = device
            computer.save()
            _CRAuditReport.objects.create(device=device, score=score, summary={"critical": critical})
        return computer

    def test_requires_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_worst_scores_come_first_and_average_is_computed(self):
        self._computer("PC-BON", score=90)
        self._computer("PC-MAUVAIS", score=40, critical=2)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["average_score"], 65)
        self.assertEqual(response.context["rows"][0]["computer"].name, "PC-MAUVAIS")
        self.assertEqual(response.context["critical_total"], 2)

    def test_never_audited_computers_are_listed_separately(self):
        self._computer("PC-SANS-AUDIT")
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["not_audited"]), 1)
        self.assertIsNone(response.context["average_score"])

    def test_other_users_computers_are_not_shown(self):
        self._computer("PC-SECRET", score=50, owner=self.other)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_computers"], 0)
