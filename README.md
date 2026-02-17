# 📝 Projet NSI NOOB-NOTE: Système de Gestion Scolaire (PRONOTE 2026)

## 📌 Présentation du Projet
Ce projet est une plateforme de gestion scolaire complète développée pour la spécialité NSI. Il permet de gérer de manière centralisée les notes, les moyennes et les rangs de **90 élèves** répartis sur trois classes (**T7, T8 et T9**). 

L'application est passée d'une version console à une architecture **Web dynamique** utilisant le framework **Flask**, tout en conservant une logique métier rigoureuse basée sur la **Programmation Orientée Objet (POO)** et une base de données **SQLite3**.

---

## 🚀 Fonctionnalités Détaillées

### 👨‍🏫 Espace Professeur (Dashboard Enseignant)
* **Navigation Multi-classes** : Système d'onglets permettant de basculer instantanément entre les listes d'élèves des classes T7, T8 et T9.
* **Moteur de Recherche** : Recherche par nom pour filtrer les élèves parmi les 90 profils enregistrés.
* **Gestion CRUD (Notes)** :
    * **Ajout** : Interface de saisie rapide (Note, Coefficient, Matière).
    * **Modification** : Correction directe des valeurs et coefficients dans le tableau de l'élève.
    * **Suppression** : Retrait sécurisé d'une évaluation par un bouton dédié.
* **Statistiques de Classe** : Calcul automatique de la moyenne, du minimum et du maximum pour une matière donnée au sein d'une classe sélectionnée.

### 🎓 Espace Élève
* **Tableau de Bord Personnel** : Consultation sécurisée des notes et des coefficients.
* **Indicateurs de Performance** : 
    * Calcul de la moyenne générale pondérée.
    * Positionnement au sein de la classe (Rang).
* **Exportation Officielle** : Génération d'un fichier `bulletin_NOM_PRENOM.txt` avec un rendu ASCII structuré.

---

## 🛠️ Stack Technique
* **Backend** : Python 3.12+ / Flask (Serveur Web).
* **Base de données** : SQLite3 (Gestion relationnelle des tables Eleves, Professeurs, Matieres, Notes).
* **Modélisation** : Programmation Orientée Objet (Classes héritées `Utilisateur` -> `Professeur` / `Eleve`).
* **Frontend** : HTML5 / CSS3 (Design "Modern Clean" sans frameworks lourds pour optimiser la performance).

---

## 📊 Configuration des Matières
Le projet supporte officiellement les 6 matières suivantes (IDs utilisés dans la base) :
1.  **Maths**
2.  **NSI**
3.  **EPS**
4.  **Français**
5.  **Physique**
6.  **Histoire**

---

## 📂 Structure du Projet
```text
PROJET_PRONOTE/
│
├── main.py               # Serveur Flask & Logique métier (POO)
├── pronote.db            # Base de données relationnelle
├── static/
│   └── css/
│       └── style.css     # Mise en page et design
└── templates/
    ├── login.html        # Page de connexion
    ├── prof.html         # Dashboard Enseignant (Navigation/Stats)
    ├── prof_gestion.html # Interface CRUD (Modif/Suppr des notes)
    └── eleve.html        # Dashboard Élève (Notes & Rang)

## 💾 Gestion de la Base de Données

Deux options s'offrent à vous selon que vous souhaitiez tester mes données ou repartir à zéro.

### Option A : Utiliser les données de test incluses
Si vous voulez tester le programme avec mes 90 élèves (classes T7, T8, T9) et les professeurs déjà configurés :
* **Action** : Aucune commande de base de données. Passez directement au lancement.

### Option B : Initialiser une nouvelle base vierge
Si vous souhaitez vider la base actuelle pour l'utiliser avec vos propres données, utilisez le script d'initialisation aux normes du projet :
```bash
python init_db.py
