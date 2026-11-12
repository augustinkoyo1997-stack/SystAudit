# Lot 2 – Normes entreprise, pièces changées, étiquette QR

Après décompression : `python saas/manage.py migrate` (nouvelle migration accounts 0009), puis
`python -m pytest -v` et `python saas/manage.py test`.

- src/deployment/baseline.py + commande `baseline-script` : script PowerShell des normes de l'entreprise
  (simulation par défaut, -Apply requis, valeurs validées, jamais de BitLocker/mot de passe). 13 tests, validés.
- accounts : modèle ReplacedPart (pièce changée par intervention), migration 0009, formulaire, action « part ».
- ManagedComputer : age_years, parts_replaced_summary, replacement_assessment (score expliqué).
- Fiche du poste : aide à la décision détaillée, synthèse des pièces, ajout d'une pièce par intervention.
- Étiquette QR imprimable : /dashboard/equipment/<code>/label/.
- Tests Django ajoutés (accounts/tests.py) : à exécuter chez vous, non lancés ici (Django absent).
