from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import DeploymentProfile, ManagedComputer, RepairIntervention, ReplacedPart


class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        error_messages={
            "required": "Veuillez saisir un nom d'utilisateur.",
            "unique": "Ce nom d'utilisateur est déjà utilisé.",
            "max_length": "Le nom d'utilisateur ne peut pas dépasser 150 caractères.",
        },
        widget=forms.TextInput(
            attrs={
                "placeholder": "Choisissez votre nom d'utilisateur",
                "autocomplete": "username",
            }
        ),
    )

    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "vous@exemple.com",
                "autocomplete": "email",
            }
        ),
        error_messages={
            "required": "Veuillez saisir votre adresse e-mail.",
            "invalid": "Veuillez saisir une adresse e-mail valide.",
        },
    )

    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Créez un mot de passe sécurisé",
                "autocomplete": "new-password",
            }
        ),
        error_messages={
            "required": "Veuillez saisir un mot de passe.",
        },
    )

    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirmez votre mot de passe",
                "autocomplete": "new-password",
            }
        ),
        error_messages={
            "required": "Veuillez confirmer votre mot de passe.",
        },
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "Ce nom d'utilisateur est déjà utilisé."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà utilisée."
            )

        return email


class ManagedComputerForm(forms.ModelForm):
    class Meta:
        model = ManagedComputer
        fields = (
            "name", "brand", "model_name", "serial_number", "assigned_to",
            "purchase_date", "purchase_cost_xof", "replacement_cost_xof",
            "next_repair_estimate_xof", "deployment_profile",
        )
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
        }


class RepairInterventionForm(forms.ModelForm):
    class Meta:
        model = RepairIntervention
        fields = ("performed_at", "title", "details", "cost_xof", "downtime_hours", "technician")
        widgets = {
            "performed_at": forms.DateInput(attrs={"type": "date"}),
            "details": forms.Textarea(attrs={"rows": 3}),
            "downtime_hours": forms.NumberInput(attrs={"min": "0", "step": "0.25"}),
        }


class DeploymentProfileForm(forms.ModelForm):
    APPLICATION_CHOICES = [
        ("7zip", "7-Zip — archives"),
        ("chrome", "Google Chrome — navigateur"),
        ("firefox", "Mozilla Firefox — navigateur"),
        ("vlc", "VLC — audio et vidéo"),
        ("libreoffice", "LibreOffice — documents et tableurs"),
        ("sumatrapdf", "SumatraPDF — fichiers PDF"),
    ]

    applications = forms.MultipleChoiceField(
        choices=APPLICATION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Logiciels à préparer",
    )

    class Meta:
        model = DeploymentProfile
        fields = ("name", "windows_iso", "image_index", "language", "applications", "office_product_id")
        labels = {
            "name": "Nom du profil",
            "windows_iso": "Image Windows",
            "image_index": "Index d’édition (facultatif)",
            "language": "Langue",
            "office_product_id": "Produit Office (facultatif)",
        }
        widgets = {"image_index": forms.NumberInput(attrs={"min": "1", "placeholder": "Ex. 6"})}

    def __init__(self, *args, iso_names=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["windows_iso"] = forms.ChoiceField(
            label="Image Windows",
            choices=[("", "Choisir un ISO")] + [(name, name) for name in iso_names],
            help_text="L’ISO doit être présent dans le dossier media du PC central.",
        )
        self.fields["office_product_id"].help_text = "Le déploiement respectera la licence Microsoft de l’entreprise."
        if self.instance and self.instance.pk:
            self.initial["applications"] = self.instance.applications

    def clean_applications(self):
        selected = self.cleaned_data["applications"]
        allowed = {value for value, _label in self.APPLICATION_CHOICES}
        if any(value not in allowed for value in selected):
            raise forms.ValidationError("Un logiciel sélectionné n’est pas dans le catalogue autorisé.")
        return selected

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.applications = self.cleaned_data["applications"]
        if commit:
            profile.save()
        return profile


class ReplacedPartForm(forms.ModelForm):
    class Meta:
        model = ReplacedPart
        fields = ("part_type", "description", "cost_xof", "warranty_until")
        widgets = {
            "warranty_until": forms.DateInput(attrs={"type": "date"}),
        }
