# Brief-3-YKAS
Mise en place d'une solution de gestion de données et d'une interface analytique polyvalente - Sabine Ali Yohan Khalid

# 🌊 Projet Data Engineering : Opérations CROSS

Ce projet vise à consolider, nettoyer et analyser les données des opérations de surveillance et de sauvetage en mer (CROSS).

## 🛠️ Installation (Windows / PowerShell)

À faire une seule fois pour configurer le projet sur votre machine.

```powershell
# 1. Cloner le projet (si ce n'est pas déjà fait)
git clone https://github.com/Simplon-DE-P1-2025/Brief-3-YKAS.git
cd Brief-3-YKAS

# 2. Créer l'environnement virtuel Python
python -m venv .venv

# 3. Activer l'environnement (Vous verrez (.venv) apparaître)
.\.venv\Scripts\Activate

# 4. Installer les outils nécessaires
pip install -r requirements.txt

# 5. Recuperer les CSV
python src/download_data.py

# 📜 Règles et Convention Git

### 1. Les Branches
* 🔴 **`main`** : Production stable. **INTERDIT** de pousser dessus directement.
* 🟡 **`dev`** : Branche commune. Tout le monde part de `dev` et fusionne vers `dev`.
* 🟢 **`feat/xxx`** : Votre branche de travail personnel.

### 2. Le Workflow (La boucle de travail)
1.  **Se mettre à jour** :
    ```bash
    git checkout dev
    git pull origin dev
    ```
2.  **Créer sa branche** :
    ```bash
    git checkout -b type/initiales-description
    ```
3.  **Travailler, commiter et pousser** :
    ```bash
    git add .
    git commit -m "mon message clair"
    git push
    ```
4.  **Fusionner** :
    * Aller sur GitHub.
    * Créer une **Pull Request (PR)** vers `dev`.
    * **Attendre la validation** d'un collègue avant de merger.

### 3. Convention de Nommage
Structure : `type/INITIALES-description-courte`

* **Types autorisés :**
    * `feat` : Nouvelle fonctionnalité
    * `fix` : Correction de bug
    * `docs` : Mise à jour documentation
* **Exemples :**
    * `feat/NM-connexion-bdd`
    * `fix/NM-colonne-date`
