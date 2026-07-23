\# Cookbook - Application de Gestion Culinaire



Application de bureau native permettant de gérer des recettes de cuisine, d'ajuster dynamiquement les portions, et de calculer automatiquement le bilan nutritionnel complet (calories, macronutriments, micronutriments) à partir des données de l'Anses (CIQUAL) et d'Open Food Facts.



\---



\## 1. Prérequis



Avant de configurer le projet sur une nouvelle machine, assurez-vous d'avoir installé ou téléchargé les éléments suivants :



\* Python : Version 3.10 ou supérieure (incluant pip) - \[Télécharger Python](https://www.python.org/downloads/)

\* Git : Pour le versionnage et la récupération du dépôt - \[Télécharger Git](https://git-scm.com/downloads)

\* Fichier CIQUAL : Le fichier source `ciqual.csv` à placer dans le dossier `data/` - \[Télécharger sur data.gouv.fr](https://www.data.gouv.fr/fr/datasets/table-de-composition-nutritionnelle-des-aliments-ciqual-2020/)



\---



\## 2. Structure du Projet



```text

livre\_recettes/

├── database/            # Connexion et modèles de la base de données SQLite

├── core/                # Moteur de parsing, calculs et chargement des données

├── ui/                  # Interfaces graphiques Flet (Accueil, Édition, Consultation)

├── data/                # Fichiers de données (ciqual.csv, mon\_livre.db)

├── main.py              # Point d'entrée principal de l'application

├── requirements.txt     # Dépendances Python

└── README.md            # Documentation de configuration

```



\---



\## 3. Procédure d'installation



\### Étape 1 : Récupérer le projet

Ouvrez un terminal et clonez le dépôt :

```bash

git clone https://github.com/EEEmryc/CookBook

cd livre\_recettes

```



\### Étape 2 : Créer et activer l'environnement virtuel Python

\* Sur Windows (PowerShell) :

```powershell

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

```



\* Sur Windows (Invite de commandes CMD) :

```cmd

python -m venv venv

.\\venv\\Scripts\\activate.bat

```



\### Étape 3 : Installer les dépendances

Une fois l'environnement virtuel activé, lancez l'installation des paquets nécessaires :

```bash

pip install -r requirements.txt

```



\---



\## 4. Lancement de l'application



Pour démarrer l'application en mode développement :

```bash

python main.py

```



Lors du premier lancement, le script initialisera automatiquement le fichier de base de données data/mon\_livre.db et importera la table CIQUAL si elle n'est pas présente.



\---



\## 5. Compilation en exécutable (.exe)



Pour générer un fichier .exe autonome utilisable sans Python :

```bash

pyinstaller --onefile --noconsole --add-data "data;data" main.py

```

L'exécutable généré se trouvera dans le dossier dist/main.exe.



