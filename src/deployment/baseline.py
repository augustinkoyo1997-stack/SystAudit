"""Génère un script PowerShell qui applique les normes de l'entreprise sur un nouveau PC.

Principes de sécurité :
- Le script est généré, relu par le technicien, puis lancé sur le poste.
- Par défaut il fonctionne en SIMULATION : rien n'est modifié sans le paramètre -Apply.
- Toutes les valeurs insérées dans le script sont validées (aucune injection possible).
- Aucun mot de passe, aucune clé de produit, aucun partitionnement ni activation
  automatique de BitLocker (la clé de récupération doit être conservée par un humain).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_COMPUTER_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,14}$")
_WINGET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{1,100}$")
_TIMEZONE_RE = re.compile(r"^[A-Za-z0-9 ().,+-]{1,60}$")


class BaselineError(ValueError):
    """Paramètre de configuration invalide."""


@dataclass
class BaselinePolicy:
    computer_name: str = ""
    # Fuseau Windows du Bénin (UTC+1, sans heure d'été).
    timezone_id: str = "W. Central Africa Standard Time"
    applications: tuple[str, ...] = field(default_factory=tuple)
    enable_firewall: bool = True
    enable_uac: bool = True
    disable_smb1: bool = True
    min_password_length: int = 10
    lockout_threshold: int = 5

    def validate(self) -> None:
        if self.computer_name and not _COMPUTER_NAME_RE.match(self.computer_name):
            raise BaselineError(
                "Nom de poste invalide : 15 caractères maximum, lettres, chiffres et tirets."
            )
        if not _TIMEZONE_RE.match(self.timezone_id):
            raise BaselineError("Fuseau horaire invalide.")
        for app_id in self.applications:
            if not _WINGET_ID_RE.match(app_id):
                raise BaselineError(f"Identifiant d'application winget invalide : {app_id!r}")
        if not 8 <= self.min_password_length <= 128:
            raise BaselineError("La longueur minimale du mot de passe doit être entre 8 et 128.")
        if not 3 <= self.lockout_threshold <= 20:
            raise BaselineError("Le seuil de verrouillage doit être entre 3 et 20.")


_HEADER = r"""#Requires -Version 5.1
<#
 SystAudit - configuration d'un poste selon les normes de l'entreprise.
 Par defaut : SIMULATION (rien n'est modifie). Ajouter -Apply pour appliquer,
 depuis une console PowerShell ouverte en administrateur.
#>
param([switch]$Apply)

$ErrorActionPreference = 'Continue'
$LogDir = Join-Path $env:ProgramData 'SystAudit'
$Log = Join-Path $LogDir ("baseline-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
$script:Failures = 0

if ($Apply) {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error 'Droits administrateur requis pour utiliser -Apply.'
        exit 1
    }
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    if (-not $Apply) {
        Write-Host "[SIMULATION] $Name"
        return
    }
    try {
        & $Action
        Write-Host "[OK]         $Name"
        Add-Content -Path $Log -Value "OK    $Name"
    } catch {
        $script:Failures++
        Write-Host "[ECHEC]      $Name : $($_.Exception.Message)"
        Add-Content -Path $Log -Value "ECHEC $Name : $($_.Exception.Message)"
    }
}
"""


def generate_baseline_script(policy: BaselinePolicy) -> str:
    """Retourne le texte du script PowerShell pour la politique donnée."""
    policy.validate()
    steps: list[str] = []

    if policy.computer_name:
        steps.append(
            f"Invoke-Step 'Renommer le poste en {policy.computer_name}' "
            f"{{ Rename-Computer -NewName '{policy.computer_name}' -Force }}"
        )

    steps.append(
        f"Invoke-Step 'Fuseau horaire : {policy.timezone_id}' "
        f"{{ Set-TimeZone -Id '{policy.timezone_id}' }}"
    )

    if policy.enable_firewall:
        steps.append(
            "Invoke-Step 'Activer le pare-feu Windows (tous les profils)' "
            "{ Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True }"
        )

    if policy.enable_uac:
        steps.append(
            "Invoke-Step 'Activer le controle de compte utilisateur (UAC)' "
            "{ Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' "
            "-Name EnableLUA -Value 1 -Type DWord }"
        )

    if policy.disable_smb1:
        steps.append(
            "Invoke-Step 'Desactiver SMBv1 (protocole obsolete)' "
            "{ Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart | Out-Null }"
        )

    steps.append(
        f"Invoke-Step 'Politique de mots de passe : longueur {policy.min_password_length}, "
        f"verrouillage apres {policy.lockout_threshold} echecs' "
        f"{{ net accounts /minpwlen:{policy.min_password_length} "
        f"/lockoutthreshold:{policy.lockout_threshold} | Out-Null; "
        "if ($LASTEXITCODE -ne 0) { throw 'net accounts a echoue' } }"
    )

    if policy.applications:
        steps.append(
            "Invoke-Step 'Verifier la presence de winget' "
            "{ if (-not (Get-Command winget -ErrorAction SilentlyContinue)) "
            "{ throw 'winget est introuvable : installez App Installer depuis le Microsoft Store' } }"
        )
        for app_id in policy.applications:
            steps.append(
                f"Invoke-Step 'Installer {app_id}' "
                f"{{ winget install --id '{app_id}' -e --silent "
                "--accept-package-agreements --accept-source-agreements; "
                "if ($LASTEXITCODE -ne 0) { throw \"winget a retourne $LASTEXITCODE\" } }"
            )

    footer = r"""
Write-Host ''
if (-not $Apply) {
    Write-Host 'Simulation terminee. Relancez avec -Apply pour appliquer ces etapes.'
} elseif ($script:Failures -gt 0) {
    Write-Host "$($script:Failures) etape(s) en echec. Consultez le journal : $Log"
    exit 2
} else {
    Write-Host "Configuration terminee. Journal : $Log"
    Write-Host 'Redemarrez le poste, puis activez BitLocker et conservez la cle de recuperation.'
}
"""
    return _HEADER + "\n" + "\n".join(steps) + "\n" + footer


def write_baseline_script(output: Path, policy: BaselinePolicy) -> Path:
    output = Path(output)
    content = generate_baseline_script(policy)
    # UTF-8 avec BOM : PowerShell 5.1 lit correctement le fichier.
    output.write_text(content.replace("\n", "\r\n"), encoding="utf-8-sig", newline="")
    return output
