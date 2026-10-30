from __future__ import annotations

import ctypes
import os
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree

from .windows_media import DeploymentError


OFFICE_CHANNELS = {
    "Current",
    "MonthlyEnterprise",
    "SemiAnnual",
    "SemiAnnualPreview",
    "CurrentPreview",
    "PerpetualVL2024",
    "PerpetualVL2021",
    "PerpetualVL2019",
}
OFFICE_APPS = {
    "Access",
    "Excel",
    "Groove",
    "Lync",
    "OneDrive",
    "OneNote",
    "Outlook",
    "OutlookForWindows",
    "PowerPoint",
    "Publisher",
    "Teams",
    "Word",
}


def generate_office_configuration(
    output_file: str | Path,
    *,
    product_id: str,
    language: str = "fr-fr",
    architecture: str = "64",
    channel: str = "Current",
    exclude_apps: tuple[str, ...] = (),
    source_path: str | None = None,
) -> Path:
    """Write an Office Deployment Tool configuration without embedding credentials or license keys."""
    output_path = Path(output_file).expanduser().resolve()
    if output_path.exists():
        raise DeploymentError(f"Le fichier existe déjà : {output_path}")
    if not output_path.parent.is_dir():
        raise DeploymentError("Le dossier de sortie n'existe pas.")
    if architecture not in {"32", "64"}:
        raise DeploymentError("L'architecture Office doit être 32 ou 64.")
    if channel not in OFFICE_CHANNELS:
        raise DeploymentError(f"Canal Office non reconnu : {channel}")
    if not re.fullmatch(r"[A-Za-z0-9_-]{2,80}", product_id):
        raise DeploymentError("Product ID invalide.")
    if not re.fullmatch(r"[A-Za-z]{2,3}-[A-Za-z]{2,4}", language):
        raise DeploymentError("Code de langue invalide, par exemple fr-fr ou en-us.")
    unknown_apps = set(exclude_apps) - OFFICE_APPS
    if unknown_apps:
        raise DeploymentError("Applications Office inconnues : " + ", ".join(sorted(unknown_apps)))

    configuration = ElementTree.Element("Configuration")
    attributes = {"OfficeClientEdition": architecture, "Channel": channel}
    if source_path:
        attributes["SourcePath"] = source_path
    add = ElementTree.SubElement(configuration, "Add", attributes)
    product = ElementTree.SubElement(add, "Product", {"ID": product_id})
    ElementTree.SubElement(product, "Language", {"ID": language})
    for app in sorted(set(exclude_apps)):
        ElementTree.SubElement(product, "ExcludeApp", {"ID": app})
    ElementTree.SubElement(configuration, "Updates", {"Enabled": "TRUE"})
    ElementTree.SubElement(configuration, "Display", {"Level": "Full", "AcceptEULA": "FALSE"})
    ElementTree.indent(configuration, space="  ")
    ElementTree.ElementTree(configuration).write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
    )
    return output_path


def _require_admin() -> None:
    if os.name != "nt":
        raise DeploymentError("L'installation Office doit être lancée sous Windows.")
    try:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError) as exc:
        raise DeploymentError("Impossible de vérifier les droits administrateur Windows.") from exc
    if not is_admin:
        raise DeploymentError("Relance PowerShell en tant qu'administrateur pour installer Office.")


def _verify_official_odt(executable: Path) -> None:
    environment = os.environ.copy()
    environment["SYSAUDIT_DEPLOY_ODT"] = str(executable)
    script = r'''
$signature = Get-AuthenticodeSignature -FilePath $env:SYSAUDIT_DEPLOY_ODT
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'CN=Microsoft Corporation') {
    throw 'La signature Microsoft de setup.exe est absente ou invalide.'
}
[pscustomobject]@{ verified = $true } | ConvertTo-Json -Compress
'''
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise DeploymentError(detail or "Impossible de vérifier la signature Microsoft de setup.exe.")


def run_office_deployment(
    setup_exe: str | Path,
    configuration_file: str | Path,
    *,
    mode: str,
) -> int:
    """Run the user-supplied official ODT executable in download or configure mode."""
    if os.name != "nt":
        raise DeploymentError("ODT doit être lancé sous Windows.")
    executable = Path(setup_exe).expanduser().resolve()
    config = Path(configuration_file).expanduser().resolve()
    if not executable.is_file() or executable.name.lower() != "setup.exe":
        raise DeploymentError("Sélectionne setup.exe provenant de l'Office Deployment Tool officiel.")
    _verify_official_odt(executable)
    if not config.is_file() or config.suffix.lower() != ".xml":
        raise DeploymentError("Sélectionne un fichier XML de configuration ODT existant.")
    if mode not in {"download", "configure"}:
        raise DeploymentError("Le mode ODT doit être download ou configure.")
    if mode == "configure":
        _require_admin()
    result = subprocess.run(
        [str(executable), f"/{mode}", str(config)],
        cwd=str(executable.parent),
        check=False,
    )
    return result.returncode
