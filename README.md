# 📝 Projet NSI NOOB-NOTE : mini-PRONOTE en Flask + SQLite

## 📌 Présentation du projet
**NOOB-NOTE** est un projet NSI qui reproduit les bases de PRONOTE avec une architecture simple :
- **Backend** en Python/Flask,
- **base de données** en SQLite,
- **interface** en HTML/CSS.

L’objectif est d’avoir un code clair, compréhensible par un niveau **Terminale NSI**, tout en proposant une vraie logique métier (professeur / élève, notes, moyennes, rang, emploi du temps).

---

## ✅ Fonctionnalités actuelles

### 👨‍🏫 Espace Professeur
- Connexion professeur.
- Liste des élèves par classe.
- Recherche d’élève par nom.
- Gestion des notes en **CRUD** :
  - ajouter une note,
  - modifier une note,
  - supprimer une note.
- Statistiques par matière et par classe (moyenne / min / max).

### 🎓 Espace Élève
- Connexion élève.
- Page **Notes** avec :
  - filtre par période,
  - filtre par matière,
  - tri par matière ou chronologique,
  - panneau de détail d’une note,
  - moyenne générale + rang.
- Export d’un bulletin `.txt`.
- Pages dédiées :
  - **Mes données**,
  - **Cahier de textes**,
  - **Résultats**,
  - **Vie scolaire**,
  - **Emploi du temps** (affiche les cours si présents en base, sinon message vide).

---

## 🧱 Stack technique
- **Python 3**
- **Flask**
- **SQLite3**
- **HTML5 / CSS3**

---

## 📂 Structure du projet (version actuelle)
```text
noob-note/
├── app.py
├── generer_pronote_db.py
├── pronote.db
├── requirements.txt
├── README.md
├── static/
│   └── css/
│       └── style.css
└── templates/
    ├── base_eleve.html
    ├── login.html
    ├── prof.html
    ├── prof_gestion.html
    ├── eleve.html
    ├── mes_donnees.html
    ├── cahier_texte.html
    ├── resultats.html
    ├── vie_scolaire.html
    ├── emploi_du_temps.html
    └── page_eleve_construction.html
```

---

## 🗃️ Base de données
Le projet utilise `pronote.db`.

Le script `generer_pronote_db.py` permet de générer une base de test plus riche (classes, élèves, professeurs, matières, notes, emplois du temps).

Exemple d’exécution :
```bash
python generer_pronote_db.py
```

---

## 🔐 Identifiants de test
```text
Élève
  Identifiant : 1
  Mot de passe : pass1

Professeur
  Identifiant : p1
  Mot de passe : mdp_prof1
```

---

## 🚀 Lancer le projet en local
```bash
git clone https://github.com/antoninche/noob-note.git
cd noob-note
pip install -r requirements.txt
python app.py
```

Puis ouvrir :
```text
http://127.0.0.1:5000
```

---

## 🌐 Version en ligne
👉 https://noob-note.onrender.com

---

## 👤 Auteur
Projet réalisé dans un objectif d’apprentissage en spécialité NSI, avec une priorité sur la lisibilité du code.
