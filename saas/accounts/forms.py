from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
        fields = ("username", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "Ce nom d'utilisateur est déjà utilisé."
            )

        return username