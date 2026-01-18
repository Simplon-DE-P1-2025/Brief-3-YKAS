# 🌊 Solution de Gestion de Données & Interface Analytique — SECMAR

Ce projet propose une **solution Data Engineering complète** dédiée à la gestion et à l’analyse des opérations de **surveillance et de sauvetage en mer (CROSS)**.

Il s’appuie sur une **architecture modulaire et robuste**, couvrant l’ensemble du cycle de vie de la donnée :  
**ingestion → normalisation → validation → stockage → visualisation & édition**.

L’infrastructure repose sur :
- une **base de données PostgreSQL conteneurisée (Docker)**  
- une **interface interactive Streamlit** permettant à la fois l’analyse (KPIs) et la gestion des données (CRUD)

---

## 🏗 Architecture Technique

Le pipeline suit une logique **ETL (Extract – Transform – Load)** séquentielle et contrôlée :

1. **Ingestion** (`ingest.py`)  
   Récupération automatisée des jeux de données CSV depuis l’API **data.gouv.fr**

2. **Normalisation** (`normalize.py`)  
   Nettoyage technique des données :
   - encodage
   - formatage des chaînes
   - suppression des accents
   - homogénéisation des valeurs

3. **Validation** (`validate.py`)  
   Contrôle qualité strict via **Pandera** :
   - séparation des données conformes (**processed**)
   - isolation des données non conformes (**rejects**)

4. **Chargement** (`load_local.py`)  
   Injection optimisée des données validées dans **PostgreSQL** via **SQLAlchemy**

5. **Interface Utilisateur** (`streamlit_app.py`)  
   Dashboard interactif connecté en temps réel à la base SQL

---

## 📂 Structure du Projet

```text
Brief-3-YKAS/
├── data/                  # Entrepôt local (ignoré par Git)
│   ├── raw/               # Données brutes téléchargées
│   ├── normalize/         # Données nettoyées (intermédiaire)
│   ├── processed/         # Données validées prêtes pour la BDD
│   └── rejects/           # Données rejetées (logs qualité)
├── src/
│   ├── ingest.py          # Extraction via API Open Data
│   ├── normalize.py       # Nettoyage et normalisation
│   ├── schemas.py         # Règles de validation Pandera
│   ├── validate.py        # Validation et routage Valid / Reject
│   ├── models.py          # Modèles relationnels SQLAlchemy
│   ├── load_local.py      # Chargement PostgreSQL (Docker)
│   └── streamlit_app.py   # Dashboard & CRUD
├── docker-compose.yml     # PostgreSQL + Adminer
└── requirements.txt       # Dépendances Python
```

### ⚙️ Prérequis

Avant de commencer, assurez-vous d’avoir installé :

- Docker Desktop (doit être lancé)
- Python 3.9+
- Git

### 🚀 Installation

1️⃣ **Clonage du dépôt & environnement virtuel**

```bash
# Cloner le dépôt
git clone https://github.com/Simplon-DE-P1-2025/Brief-3-YKAS.git
cd Brief-3-YKAS

# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement
# Windows :
.\.venv\Scripts\Activate
# macOS / Linux :
source .venv/bin/activate
```

2️⃣ **Installation des dépendances**

```bash
pip install -r requirements.txt
```

3️⃣ **Configuration de l'environnement**

Créez un fichier `.env` à la racine du projet et ajoutez-y la ligne suivante :

```ini
DATABASE_URL=postgresql://admin:admin@localhost:5432/maritime
```

4️⃣ **Démarrage de l’infrastructure Docker**

Cette commande lance la base de données PostgreSQL ainsi que l’interface d’administration Adminer.

```bash
docker-compose up -d
```

### 🐳 Accès Adminer

- **URL :** `http://localhost:8081`
- **Système :** `PostgreSQL`
- **Serveur :** `db`
- **Utilisateur :** `admin`
- **Mot de passe :** `admin`
- **Base de données :** `maritime`

### ▶️ Exécution du Pipeline ETL

⚠️ **Important :** L’ordre d’exécution est primordial pour garantir l’intégrité référentielle des données.

**Étape 1 — Ingestion**

Téléchargement des dernières données Open Data.

```bash
python -m src.ingest
```

**Étape 2 — Normalisation**

Nettoyage des formats hétérogènes.

```bash
python -m src.normalize
```

**Étape 3 — Validation Qualité**

Contrôle du typage et des règles métier (Pandera).

```bash
python -m src.validate
```

**Étape 4 — Chargement en Base**

Alimentation de la base PostgreSQL locale.

```bash
python -m src.load_local
```

### 📊 Utilisation de l’Application

Une fois la base de données alimentée, lancez le dashboard Streamlit :

```bash
streamlit run src/streamlit_app.py
```

### Pytest

### workflow git

### Fonctionnalités clés

📈 **Dashboard Live**

Visualisation des opérations avec filtres dynamiques :
- Par Année
- Par CROSS

✏️ **CRUD Réel**

Formulaires permettant d'interagir directement avec la BDD :
- Ajout d’opérations (INSERT)
- Suppression d’opérations (DELETE)

🧩 **Audit & Modélisation**

Visualisation du modèle relationnel des données (Graphviz).

### 🛠 Stack Technique

- **Langage :** Python
- **Base de données :** PostgreSQL
- **Infrastructure :** Docker
- **ORM :** SQLAlchemy
- **Qualité de données :** Pandera
- **Frontend :** Streamlit, Plotly, Graphviz

### 👥 Auteurs

Simplon - Data Engineer :

- Sabine
- Ali
- Yohan
- Khalid (chef de projet)

---