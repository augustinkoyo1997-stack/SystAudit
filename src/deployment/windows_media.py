from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class DeploymentError(RuntimeError):
    """A deployment prerequisite or command failed safely."""


def _require_windows() -> None:
    if os.name != "nt":
        raise DeploymentError("La préparation des médias Windows doit être lancée sous Windows.")


def _powershell(script: str, iso_path: Path) -> dict:
    environment = os.environ.copy()
    environment["SYSAUDIT_DEPLOY_ISO"] = str(iso_path)
    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded_script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise DeploymentError(detail or "PowerShell n'a pas pu monter le fichier ISO.")
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise DeploymentError("PowerShell n'a pas retourné d'informations de montage valides.") from exc


def _mount_iso(iso_path: Path) -> tuple[Path, bool]:
    state = _powershell(
        """
$path = $env:SYSAUDIT_DEPLOY_ISO
$image = Get-DiskImage -ImagePath $path -ErrorAction SilentlyContinue
$mountedByTool = $false
try {
    if (-not $image -or -not $image.Attached) {
        $image = Mount-DiskImage -ImagePath $path -PassThru -ErrorAction Stop
        $mountedByTool = $true
    }
    $volume = $image | Get-Volume | Where-Object { $_.DriveLetter } | Select-Object -First 1
    if (-not $volume) { throw 'No volume drive letter was found for this ISO.' }
    [pscustomobject]@{ driveLetter = $volume.DriveLetter; mountedByTool = $mountedByTool } | ConvertTo-Json -Compress
} catch {
    if ($mountedByTool) { Dismount-DiskImage -ImagePath $path -ErrorAction SilentlyContinue | Out-Null }
    throw
}
""",
        iso_path,
    )
    drive_letter = state.get("driveLetter")
    if not isinstance(drive_letter, str) or len(drive_letter) != 1:
        raise DeploymentError("Windows n'a pas attribué de lettre de lecteur à l'ISO.")
    return Path(f"{drive_letter.upper()}:\\"), bool(state.get("mountedByTool"))


def _unmount_iso(iso_path: Path) -> None:
    _powershell(
        "Dismount-DiskImage -ImagePath $env:SYSAUDIT_DEPLOY_ISO -ErrorAction Stop | Out-Null; "
        "[pscustomobject]@{ unmounted = $true } | ConvertTo-Json -Compress",
        iso_path,
    )


def _find_dism() -> str:
    candidate = shutil.which("dism.exe") or shutil.which("dism")
    if candidate:
        return candidate
    candidate = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "dism.exe"
    if candidate.is_file():
        return str(candidate)
    raise DeploymentError("DISM est introuvable. Il est fourni avec Windows et le Windows ADK.")


def inspect_windows_iso(iso_file: str | Path) -> tuple[str, str]:
    """Mount an ISO temporarily, list its Windows image editions, and return its SHA-256."""
    _require_windows()
    iso_path = Path(iso_file).expanduser().resolve()
    if not iso_path.is_file() or iso_path.suffix.lower() != ".iso":
        raise DeploymentError("Choisis un fichier .iso Windows existant.")

    mount_point, mounted_by_tool = _mount_iso(iso_path)
    try:
        sources = mount_point / "sources"
        image_file = next(
            (candidate for candidate in (sources / "install.wim", sources / "install.esd") if candidate.is_file()),
            None,
        )
        if image_file is None:
            raise DeploymentError("Cet ISO ne contient ni sources/install.wim ni sources/install.esd.")
        result = subprocess.run(
            [_find_dism(), "/English", "/Get-WimInfo", f"/WimFile:{image_file}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode:
            raise DeploymentError(result.stderr.strip() or result.stdout.strip() or "DISM n'a pas pu lire l'image.")
        image_info = result.stdout.strip()
    finally:
        if mounted_by_tool:
            _unmount_iso(iso_path)

    digest = hashlib.sha256()
    with iso_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return image_info, digest.hexdigest()


def _find_oscdimg() -> str:
    candidate = shutil.which("oscdimg.exe") or shutil.which("oscdimg")
    if candidate:
        return candidate
    program_files = os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles")
    if program_files:
        candidate_path = (
            Path(program_files)
            / "Windows Kits"
            / "10"
            / "Assessment and Deployment Kit"
            / "Deployment Tools"
            / "amd64"
            / "Oscdimg"
            / "oscdimg.exe"
        )
        if candidate_path.is_file():
            return str(candidate_path)
    raise DeploymentError(
        "Oscdimg est introuvable. Installe Windows ADK avec les outils de déploiement, puis réessaie."
    )


def _answer_file(language: str, architecture: str, image_index: int | None) -> str:
    """Create a locale-only answer file: no partition, account, password, or product-key commands."""
    escaped_language = language.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    image_selection = ""
    namespaces = ""
    if image_index is not None:
        namespaces = ' xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State"'
        image_selection = f'''\n    <component name="Microsoft-Windows-Setup" processorArchitecture="{architecture}" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <ImageInstall><OSImage><InstallFrom><MetaData wcm:action="add"><Key>/IMAGE/INDEX</Key><Value>{image_index}</Value></MetaData></InstallFrom></OSImage></ImageInstall>
    </component>'''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend"{namespaces}>
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="{architecture}" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <SetupUILanguage><UILanguage>{escaped_language}</UILanguage></SetupUILanguage>
      <InputLocale>{escaped_language}</InputLocale>
      <SystemLocale>{escaped_language}</SystemLocale>
      <UILanguage>{escaped_language}</UILanguage>
      <UserLocale>{escaped_language}</UserLocale>
    </component>
    {image_selection}
  </settings>
</unattend>
'''


def build_configured_windows_iso(
    iso_file: str | Path,
    output_iso: str | Path,
    *,
    language: str = "fr-FR",
    architecture: str = "amd64",
    image_index: int | None = None,
) -> tuple[Path, str]:
    """Copy a Windows ISO, add a non-destructive locale answer file, and rebuild it as a bootable ISO."""
    _require_windows()
    iso_path = Path(iso_file).expanduser().resolve()
    output_path = Path(output_iso).expanduser().resolve()
    if not iso_path.is_file() or iso_path.suffix.lower() != ".iso":
        raise DeploymentError("Choisis un fichier .iso Windows existant.")
    if output_path.exists():
        raise DeploymentError(f"Le fichier de sortie existe déjà : {output_path}")
    if output_path.suffix.lower() != ".iso" or not output_path.parent.is_dir():
        raise DeploymentError("Le fichier de sortie doit être un .iso dans un dossier existant.")
    if output_path == iso_path:
        raise DeploymentError("Le fichier source ne peut pas servir de fichier de sortie.")
    if architecture != "amd64":
        raise DeploymentError("Cette première version prépare les images Windows x64 (amd64).")
    if not re.fullmatch(r"[A-Za-z]{2,3}-[A-Za-z]{2,4}", language):
        raise DeploymentError("Le code de langue est invalide, par exemple fr-FR ou en-US.")
    if image_index is not None and image_index < 1:
        raise DeploymentError("L'index d'édition doit être un entier positif.")

    oscdimg = _find_oscdimg()
    required_space = iso_path.stat().st_size * 2 + 1024**3
    if shutil.disk_usage(output_path.parent).free < required_space:
        raise DeploymentError("Espace disque insuffisant : prévois au moins deux fois la taille de l'ISO plus 1 Go.")

    mount_point, mounted_by_tool = _mount_iso(iso_path)
    try:
        bios_boot = mount_point / "boot" / "etfsboot.com"
        uefi_boot = mount_point / "efi" / "microsoft" / "boot" / "efisys.bin"
        boot_wim = mount_point / "sources" / "boot.wim"
        if not bios_boot.is_file() or not uefi_boot.is_file() or not boot_wim.is_file():
            raise DeploymentError("Les fichiers de démarrage BIOS/UEFI requis sont absents de cet ISO.")

        if image_index is not None:
            image_file = next(
                (
                    candidate
                    for candidate in (
                        mount_point / "sources" / "install.wim",
                        mount_point / "sources" / "install.esd",
                    )
                    if candidate.is_file()
                ),
                None,
            )
            if image_file is None:
                raise DeploymentError("Cet ISO ne contient ni sources/install.wim ni sources/install.esd.")
            image_info = subprocess.run(
                [_find_dism(), "/English", "/Get-WimInfo", f"/WimFile:{image_file}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if image_info.returncode:
                raise DeploymentError(image_info.stderr.strip() or "DISM n'a pas pu lire les éditions de l'ISO.")
            available_indexes = {
                int(value)
                for value in re.findall(r"(?m)^\s*Index\s*:\s*(\d+)\s*$", image_info.stdout)
            }
            if image_index not in available_indexes:
                raise DeploymentError(
                    f"L'édition {image_index} n'est pas dans cet ISO. Choisis un index affiché par inspect-windows."
                )

        with tempfile.TemporaryDirectory(prefix="sysaudit-media-", dir=output_path.parent) as temporary:
            staging = Path(temporary) / "media"
            staging.mkdir()
            for item in mount_point.iterdir():
                destination = staging / item.name
                if item.is_dir():
                    shutil.copytree(item, destination)
                else:
                    shutil.copy2(item, destination)
            answer_path = staging / "Autounattend.xml"
            if answer_path.exists():
                raise DeploymentError("L'ISO contient déjà Autounattend.xml; le fichier original ne sera pas écrasé.")
            answer_path.write_text(
                _answer_file(language, architecture, image_index),
                encoding="utf-8",
            )

            boot_order_candidates = (
                "boot\\bcd",
                "boot\\boot.sdi",
                "boot\\bootfix.bin",
                "boot\\bootsect.exe",
                "boot\\etfsboot.com",
                "boot\\memtest.efi",
                "boot\\memtest.exe",
                "boot\\en-us\\bootsect.exe.mui",
                "boot\\fonts\\chs_boot.ttf",
                "boot\\fonts\\cht_boot.ttf",
                "boot\\fonts\\jpn_boot.ttf",
                "boot\\fonts\\kor_boot.ttf",
                "boot\\fonts\\wgl4_boot.ttf",
                "efi\\microsoft\\boot\\efisys.bin",
                "sources\\boot.wim",
            )
            boot_order = Path(temporary) / "boot-order.txt"
            boot_order.write_text(
                "".join(
                    f"{relative_path}\n"
                    for relative_path in boot_order_candidates
                    if (staging / Path(relative_path)).is_file()
                ),
                encoding="ascii",
            )

            temporary_iso = Path(temporary) / "configured.iso"
            boot_data = f"-bootdata:2#p0,e,b{bios_boot}#pEF,e,b{uefi_boot}"
            result = subprocess.run(
                [
                    oscdimg,
                    "-m",
                    "-o",
                    "-u2",
                    "-udfver102",
                    f"-yo{boot_order}",
                    boot_data,
                    str(staging),
                    str(temporary_iso),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode or not temporary_iso.is_file():
                detail = result.stderr.strip() or result.stdout.strip()
                raise DeploymentError(detail or "Oscdimg n'a pas créé le fichier ISO.")
            temporary_iso.rename(output_path)
    finally:
        if mounted_by_tool:
            _unmount_iso(iso_path)

    digest = hashlib.sha256()
    with output_path.open("rb") as output:
        for chunk in iter(lambda: output.read(1024 * 1024), b""):
            digest.update(chunk)
    return output_path, digest.hexdigest()
