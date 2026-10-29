# SystAudit 🛡️

SystAudit est un outil d'audit de sécurité système développé en Python pour analyser l'état de sécurité d'un poste Windows.

Le projet collecte des informations système, réseau et sécurité, détecte certains éléments suspects, évalue les risques et génère un score de sécurité accompagné de recommandations.

## ✨ Fonctionnalités

### 🖥️ Audit système

- Informations sur le système d'exploitation
- Nom de l'hôte
- Version du système
- Architecture
- Version de Python
- Informations CPU
- Mémoire RAM
- Disques et partitions
- Processus
- Utilisateurs
- Services

### 🌐 Audit réseau

- Informations réseau
- Interfaces réseau
- Adresses IP
- Adresses MAC
- État des interfaces
- Statistiques réseau
- Connexions réseau
- Routes réseau
- Ports en écoute
- Processus utilisant les connexions réseau
- Détection de certains ports suspects

### 🔐 Audit de sécurité

SystAudit analyse notamment :

- Privilèges administrateur
- Administrateurs locaux
- Utilisateurs locaux
- Comptes désactivés
- Pare-feu Windows
- Règles du pare-feu
- Antivirus
- Mises à jour Windows
- Politique de mots de passe
- Utilisateurs connectés
- BitLocker
- Comptes dont le mot de passe n'expire jamais
- UAC
- Services suspects
- Tâches planifiées suspectes
- Processus suspects
- Événements de sécurité suspects

### 📊 Analyse des risques

Les résultats sont classés selon trois niveaux :

- **HIGH** — risque élevé
- **MEDIUM** — risque moyen
- **LOW** — risque faible

SystAudit calcule ensuite un score de sécurité sur 100 et génère des recommandations adaptées aux problèmes détectés.

## 📋 Exemple de rapport

```text
========================================
        SYSAUDIT REPORT
========================================

Security Score : 90/100

Findings
--------
HIGH   : 0
MEDIUM : 1
LOW    : 0

Recommendations
---------------
[MEDIUM] BitLocker protection is disabled on volume(s): C:, D:, E:.
       -> Enable BitLocker protection on unprotected volumes and verify
          that recovery keys are securely stored.

========================================
```

## 🏗️ Architecture

```text
sysaudit/
│
├── src/
│   ├── __init__.py
│   ├── audit.py
│   ├── main.py
│   ├── network.py
│   ├── security.py
│   ├── security_analysis.py
│   ├── security_recommendations.py
│   ├── security_report.py
│   └── system.py
│
├── tests/
│   ├── test_audit.py
│   ├── test_network.py
│   ├── test_security.py
│   ├── test_security_analysis.py
│   ├── test_security_recommendations.py
│   ├── test_security_report.py
│   ├── test_system.py
│   └── test_system_info.py
│
├── docs/
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Prérequis

- Windows 10 ou Windows 11
- Python 3.10+
- Git
- PowerShell recommandé

## 🚀 Installation

Cloner le dépôt :

```powershell
git clone <URL_DU_DEPOT>
cd sysaudit
```

Créer un environnement virtuel :

```powershell
python -m venv .venv
```

Activer l'environnement virtuel :

```powershell
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
pip install -r requirements.txt
```

## ▶️ Utilisation

Lancer l'audit :

```powershell
python -m src.audit
```

Ou directement avec l'environnement virtuel :

```powershell
.\.venv\Scripts\python.exe -m src.audit
```

## 🧪 Tests

SystAudit dispose d'une suite de tests automatisés avec pytest.

Lancer tous les tests :

```powershell
python -m pytest -v
```

Dernière validation :

```text
56 passed (suite pytest du moteur local; certains contrôles Windows nécessitent un accès local)
```

### Tests de l'application SaaS

Dans le dossier `saas`, la suite Django couvre les comptes, les espaces d'équipe,
la facturation et les API :

```powershell
cd saas
..\.venv\Scripts\python.exe manage.py test
```

Dernière validation de l'application SaaS : **96 tests réussis**.

## 🔎 Qualité du projet

Le projet a été vérifié avec :

```powershell
python -m pytest -v
```

Résultat de la dernière validation :

```text
56 passed in 102.11s
```

La vérification Git suivante ne retourne aucune erreur :

```powershell
git diff --check
```

## ⚠️ Limites

SystAudit est actuellement principalement destiné à l'audit de postes Windows.

La détection d'éléments suspects repose sur des règles d'analyse et ne constitue pas une preuve qu'un processus, service ou événement est malveillant.

Les résultats doivent donc être interprétés dans leur contexte.

## 🌐 Application SaaS

Le dépôt contient aussi une application web Django dans `saas/`. Elle prend en
charge les comptes avec confirmation d'adresse e-mail, les licences, les audits,
et un espace partagé pour une PME. Un propriétaire peut ajouter des comptes
SystAudit déjà inscrits et confirmés; les membres voient les appareils et les
rapports de l'équipe, mais pas la clé de licence et ne peuvent pas approuver une
remédiation.

### Lancement local

1. Copier `saas/env.example` vers `.env` à la racine du dépôt et remplacer les
   valeurs de base de données et la clé Django.
2. Démarrer PostgreSQL et créer la base et l'utilisateur indiqués dans `.env`.
3. Depuis `saas/`, installer les dépendances du dépôt, appliquer les migrations,
   puis lancer le serveur de développement :

```powershell
..\.venv\Scripts\python.exe -m pip install -r ..\requirements.txt
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver
```

Ouvrir ensuite `http://127.0.0.1:8000/`. `runserver` sert uniquement aux essais
locaux; le lancement public demande un serveur WSGI/ASGI, HTTPS et une base de
données de production.

### FedaPay

Les paiements Premium sont préparés en XOF pour une période de 30 jours. Le
retour du navigateur n'active jamais l'abonnement : seule la confirmation par
webhook signé l'active. Le renouvellement est manuel; aucun prélèvement
automatique récurrent n'est configuré.

Pour activer les paiements, définir dans `.env` la clé secrète FedaPay, le tarif
Premium entier en XOF, l'environnement (`sandbox` ou `live`) et le secret de
signature du webhook. Dans le tableau FedaPay, configurer l'adresse publique
`https://VOTRE-DOMAINE/billing/webhook/fedapay/` pour les événements de transaction
approuvée et annulée. Garder `FEDAPAY_PREMIUM_PRICE_XOF=0` jusqu'à ce que le prix
soit décidé; le bouton de paiement reste alors indisponible.

### Avant l'ouverture au public

- Configurer un domaine HTTPS, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` et
  `DJANGO_CSRF_TRUSTED_ORIGINS` pour ce domaine.
- Remplacer le courriel console par un fournisseur SMTP pour livrer les
  confirmations de compte et les réinitialisations de mot de passe.
- Créer le compte FedaPay marchand, tester les paiements en sandbox puis
  configurer les secrets du compte live et le webhook HTTPS.
- Les limites d'API sont activées par défaut; configurer un cache partagé pour
  les répartir correctement sur plusieurs processus ou serveurs.
- Planifier les sauvegardes PostgreSQL, la surveillance et la politique de
  conservation/suppression des données.
- Les remédiations demeurent en mode simulation (DRY-RUN); aucune modification
  réelle du poste n'est activée depuis le SaaS.

## 🔒 Sécurité

SystAudit est conçu à des fins d'administration système, d'audit et d'apprentissage de la cybersécurité.

Utilisez cet outil uniquement sur des systèmes que vous êtes autorisé à analyser.

## 🛠️ Technologies

- Python
- psutil
- pytest
- PowerShell
- Windows

## 📈 État du projet

**Version : 1.0.0**

Le moteur d'audit, l'analyse de sécurité, le scoring, les recommandations, le rapport et les tests automatisés sont fonctionnels.

Les prochaines évolutions pourront notamment concerner :

- amélioration de la détection
- export des rapports
- interface graphique ou web
- journalisation
- davantage de contrôles de sécurité
- support d'autres systèmes

## 👨‍💻 Auteur

**Augustin KOYO**

Projet personnel réalisé dans le cadre de mon apprentissage de l'administration système, du développement Python et de la cybersécurité.
