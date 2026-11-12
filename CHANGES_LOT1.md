# Lot 1 – Corrections (à vérifier avec `python -m pytest` puis `python saas/manage.py test`)

## Moteur d'audit
- security.py : tous les appels système passent par `_run()` avec timeout de 60 s (plus de blocage possible).
- security.py : `get_antivirus_status()` décode `productState` (champs `enabled`, `up_to_date`).
- audit_engine.py : l'antivirus n'est plus toujours « inactif » ; le message BitLocker liste les volumes ;
  `summary["score_reliable"]` = False si la couverture est < 70 %.
- audit.py : séparateur du rapport corrigé ; avertissement si score non fiable.
- security_analysis.py et son test supprimés (module ancien et cassé).

## Client
- license_client.py : refuse une URL d'API en HTTP (sauf localhost).

## SaaS
- agent_heartbeat : limite 30 requêtes/min/IP avant tout hash, corps limité à 4 Ko.
- submit_audit_report : plafonds (500 findings, 200 recommandations, 512 Ko).
- settings.py : HSTS, STATIC_ROOT, LOGGING, option DJANGO_BEHIND_PROXY, suppression du réglage obsolète.
- CI : lance désormais les tests de toutes les apps Django.
