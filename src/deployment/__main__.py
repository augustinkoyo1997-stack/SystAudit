from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .office import generate_office_configuration, run_office_deployment
from .windows_media import (
    DeploymentError,
    build_configured_windows_iso,
    inspect_windows_iso,
)


def _confirm(phrase: str) -> bool:
    try:
        response = input(f"Pour continuer, tape exactement « {phrase} » : ")
    except EOFError:
        return False
    return response == phrase


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m src.deployment",
        description="Préparer un ISO Windows et une configuration Microsoft Office localement.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect-windows", help="Lire les éditions et le SHA-256 d'un ISO Windows.")
    inspect.add_argument("iso", type=Path)

    build = commands.add_parser("build-windows", help="Créer une copie ISO avec langue de setup prédéfinie.")
    build.add_argument("iso", type=Path)
    build.add_argument("output", type=Path)
    build.add_argument("--language", default="fr-FR")
    build.add_argument("--architecture", choices=("amd64",), default="amd64")
    build.add_argument("--image-index", type=int, help="Préselectionner l'édition affichée par inspect-windows.")

    office_config = commands.add_parser("office-config", help="Générer un XML pour l'Office Deployment Tool.")
    office_config.add_argument("output", type=Path)
    office_config.add_argument("--product-id", required=True)
    office_config.add_argument("--language", default="fr-fr")
    office_config.add_argument("--architecture", choices=("32", "64"), default="64")
    office_config.add_argument(
        "--channel",
        choices=("Current", "MonthlyEnterprise", "SemiAnnual", "PerpetualVL2024", "PerpetualVL2021", "PerpetualVL2019"),
        default="Current",
    )
    office_config.add_argument("--exclude-app", action="append", default=[])
    office_config.add_argument("--source-path")

    office_download = commands.add_parser("office-download", help="Télécharger les fichiers Office avec ODT.")
    office_download.add_argument("setup_exe", type=Path)
    office_download.add_argument("configuration", type=Path)

    office_install = commands.add_parser("office-install", help="Installer Office avec ODT (administrateur requis).")
    office_install.add_argument("setup_exe", type=Path)
    office_install.add_argument("configuration", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "inspect-windows":
            details, digest = inspect_windows_iso(args.iso)
            print(details)
            print(f"\nSHA-256 : {digest}")
            return 0

        if args.command == "build-windows":
            print("Cette opération copie tout l'ISO et crée un nouvel ISO amorçable. Elle ne formate aucune clé USB.")
            print("L'Autounattend.xml ne choisit ni disque, ni partition, ni mot de passe, ni clé produit.")
            if not _confirm("CREER ISO"):
                print("Opération annulée.")
                return 1
            output, digest = build_configured_windows_iso(
                args.iso,
                args.output,
                language=args.language,
                architecture=args.architecture,
                image_index=args.image_index,
            )
            print(f"ISO créé : {output}\nSHA-256 : {digest}")
            return 0

        if args.command == "office-config":
            path = generate_office_configuration(
                args.output,
                product_id=args.product_id,
                language=args.language,
                architecture=args.architecture,
                channel=args.channel,
                exclude_apps=tuple(args.exclude_app),
                source_path=args.source_path,
            )
            print(f"Configuration Office créée : {path}")
            print("Elle ne contient aucune clé produit ou donnée de compte.")
            return 0

        if args.command == "office-download":
            if not _confirm("TELECHARGER OFFICE"):
                print("Opération annulée.")
                return 1
            result = run_office_deployment(args.setup_exe, args.configuration, mode="download")
            return result

        if args.command == "office-install":
            print("Cette opération installe ou modifie Office sur cet ordinateur.")
            if not _confirm("INSTALLER OFFICE"):
                print("Opération annulée.")
                return 1
            return run_office_deployment(args.setup_exe, args.configuration, mode="configure")

    except DeploymentError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
