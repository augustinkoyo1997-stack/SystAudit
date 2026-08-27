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

🏗️ Architecture

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

⚙️ Prérequis
Windows 10 ou Windows 11
Python 3.10+
Git
PowerShell recommandé

🚀 Installation

Cloner le dépôt :
git clone <URL_DU_DEPOT>
cd sysaudit

Créer un environnement virtuel :

python -m venv .venv

Activer l'environnement virtuel :

.\.venv\Scripts\Activate.ps1

Installer les dépendances :

pip install -r requirements.txt
▶️ Utilisation

Lancer l'audit :

python -m src.audit

Ou directement avec l'environnement virtuel :

.\.venv\Scripts\python.exe -m src.audit
🧪 Tests

SystAudit dispose d'une suite de tests automatisés avec pytest.

Lancer tous les tests :

python -m pytest -v

Dernière validation :

56 passed
🔎 Qualité du projet

Le projet a été vérifié avec :

python -m pytest -v

Résultat de la dernière validation :

56 passed in 102.11s

La vérification Git suivante ne retourne aucune erreur :

git diff --check
⚠️ Limites

SystAudit est actuellement principalement destiné à l'audit de postes Windows.

La détection d'éléments suspects repose sur des règles d'analyse et ne constitue pas une preuve qu'un processus, service ou événement est malveillant.

Les résultats doivent donc être interprétés dans leur contexte.

🔒 Sécurité

SystAudit est conçu à des fins d'administration système, d'audit et d'apprentissage de la cybersécurité.

Utilisez cet outil uniquement sur des systèmes que vous êtes autorisé à analyser.

🛠️ Technologies
Python
psutil
pytest
PowerShell
Windows
📈 État du projet

Version : 1.0.0

Le moteur d'audit, l'analyse de sécurité, le scoring, les recommandations, le rapport et les tests automatisés sont fonctionnels.

Les prochaines évolutions pourront notamment concerner :

amélioration de la détection
export des rapports
interface graphique ou web
journalisation
davantage de contrôles de sécurité
support d'autres systèmes
👨‍💻 Auteur

Augustin KOYO

Projet personnel réalisé dans le cadre de mon apprentissage de l'administration système, du développement Python et de la cybersécurité.