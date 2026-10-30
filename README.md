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
et des espaces d'équipe pour les PME. Un propriétaire peut inviter une personne
par e-mail; elle doit ouvrir le lien, se connecter avec l'adresse invitée et
confirmer son adhésion. Les membres voient les appareils et rapports de l'équipe,
mais pas la clé de licence et ne peuvent pas approuver une remédiation.

En développement local, le backend e-mail affiche les messages dans la fenêtre
PowerShell du serveur. Pour les livrer réellement, configurez dans `.env`
`DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, puis
`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD` et `DEFAULT_FROM_EMAIL` selon le fournisseur choisi.
Gardez le mot de passe SMTP dans `.env` (jamais dans Git) et redémarrez Django
après toute modification. La page après inscription indique aussi où trouver le
lien quand le backend console est actif.

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

## 💿 Préparer Windows et Office localement

Un premier outil local est disponible dans `src/deployment`. Il inspecte un ISO
Windows, peut créer une copie amorçable qui présélectionne la langue du programme
d'installation, et génère puis lance une configuration Microsoft Office via
l'Office Deployment Tool (ODT).

Les opérations s'exécutent sur le poste Windows, pas sur le serveur SaaS. Cette
version crée un ISO de sortie; elle ne formate pas de clé USB. L'installation
Windows conserve le choix de l'édition et du disque à l'utilisateur. Le fichier
de réponse n'ajoute ni partitionnement automatique, ni compte avec mot de passe,
 ni clé produit. Utilise un ISO Microsoft dont tu as vérifié l'origine. Pour créer
 l'ISO modifié, installe les **Deployment Tools** du [Windows ADK officiel](https://learn.microsoft.com/en-us/windows-hardware/get-started/adk-install) (`Oscdimg`); le module WinPE n'est pas nécessaire.

Depuis la racine du dépôt, inspecter les éditions et le hash de l'ISO :

```powershell
.\.venv\Scripts\python.exe -m src.deployment inspect-windows .\media\Windows.iso
```

Créer une copie ISO amorçable en français. Remplace `N` par un index affiché par
`inspect-windows` pour présélectionner une édition; l'installation te demandera
toujours de choisir le disque. L'outil demande de taper `CREER ISO`.
avant de commencer la copie :

```powershell
.\.venv\Scripts\python.exe -m src.deployment build-windows .\media\Windows.iso .\media\Windows-fr.iso --language fr-FR --image-index 6
```

Office n'est pas configuré ici avec un ISO : ODT télécharge les composants
nécessaires et applique le fichier XML. Le Product ID doit correspondre à la
licence Microsoft détenue. Le guide Microsoft décrit le téléchargement avec
`/download` et l'installation avec `/configure` dans son [guide ODT](https://learn.microsoft.com/en-us/microsoft-365-apps/deploy/overview-office-deployment-tool).

Télécharger ODT depuis le Centre de téléchargement Microsoft, extraire `setup.exe`,
puis créer un dossier de travail et le XML. Exemple pour Microsoft 365 Business :

```powershell
New-Item -ItemType Directory -Force .\deployment | Out-Null
.\.venv\Scripts\python.exe -m src.deployment office-config .\deployment\office-fr.xml --product-id O365BusinessRetail --language fr-fr --architecture 64 --channel Current
.\.venv\Scripts\python.exe -m src.deployment office-download .\odt\setup.exe .\deployment\office-fr.xml
.\.venv\Scripts\python.exe -m src.deployment office-install .\odt\setup.exe .\deployment\office-fr.xml
```

Le téléchargement et l'installation demandent une confirmation. L'installation
nécessite une console PowerShell administrateur et une licence Office valide; le
programme vérifie la signature Microsoft du `setup.exe`. La clé de produit ou le
mot de passe Microsoft ne sont jamais demandés ni enregistrés.

## 🖥️ Préparer et suivre le parc informatique

Le tableau de bord SaaS donne accès à **Parc informatique**. Une fiche par poste
permet de suivre son coût d'achat, son attribution et son état, puis de cocher les
étapes de préparation : système, pilotes, mises à jour, logiciels et sécurité.
La page **Préparer un poste** reste dédiée à la création/inspection d'ISO Windows
et à la configuration Office; l'installation effective et la remise du PC sont
validées par le technicien dans la checklist.

La fiche d'un poste conserve aussi chaque panne et intervention, avec coût et
durée d'arrêt. Elle compare le devis à venir au coût d'un poste équivalent et
signale les réparations répétées. Le total historique est un signal à examiner,
pas une règle automatique de remplacement. Les étiquettes QR ouvrent la fiche
du poste et exigent une session sysAudit. Pour générer les QR, installer les
dépendances du projet avec `pip install -r requirements.txt`.

Les postes sont isolés par espace d'équipe. Un compte hors équipe ne voit que
les fiches qu'il a lui-même créées.

### Auditer un poste et remettre le rapport

Dans la fiche du poste, associer l'appareil activé sous la licence de l'équipe.
Sur le PC à contrôler, depuis la racine du projet sysAudit, lancer l'audit avec
envoi au SaaS :

```powershell
$env:SYSAUDIT_API_URL = "https://votre-domaine-sysaudit"
.\.venv\Scripts\python.exe -m src.audit --upload
```

La clé de licence est demandée de façon masquée dans le terminal. Après l'envoi,
le rapport apparaît dans la fiche associée. Le bouton du rapport ouvre une page
imprimable : choisir **Enregistrer au format PDF** dans la fenêtre d'impression
pour transmettre une copie au responsable. L'audit se lance sur le PC lui-même;
le tableau de bord web ne commande pas encore son exécution à distance.

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
