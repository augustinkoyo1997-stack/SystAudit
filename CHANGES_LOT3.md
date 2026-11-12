# Lot 3 – Rapport entreprise, tarifs, alertes

- accounts : vue `company_report` + template imprimable (score moyen, postes à risque, jamais audités).
- licensing/alerts.py : e-mail d'alerte (baisse de score >= 10 points ou nouveaux problèmes critiques),
  appelé depuis `submit_audit_report` sans jamais bloquer l'enregistrement du rapport.
- commande `send_monthly_reminders` (--days, --dry-run).
- billing : page publique /billing/pricing/ ; la racine redirige les visiteurs anonymes vers les tarifs.
- CORRECTION D'UN BUG EXISTANT : saas/billing/tests.py contenait un `\n` littéral en ligne 115
  (SyntaxError) : les tests de facturation ne pouvaient pas s'exécuter.
- Tests ajoutés pour toutes ces fonctions (non exécutés ici : Django absent de mon environnement).
