# 📝 Projet NSI NOOB-NOTE : mini-PRONOTE en Flask + SQLite

## Présentation du projet
**NOOB-NOTE** est un projet NSI qui reproduit les bases de PRONOTE avec une architecture simple :
- **Backend** en Python/Flask,
- **base de données** en SQLite,
- **interface** en HTML/CSS.

L’objectif est d’avoir un code clair, compréhensible par un niveau **Terminale NSI**, tout en proposant une vraie logique métier (professeur / élève, notes, moyennes, rang, emploi du temps).

---    

## Fonctionnalités actuelles

### Espace Professeur
- Connexion professeur (mots de passe **hachés**).
- Liste des élèves par classe (onglets générés depuis la base).
- Recherche d’élève par nom.
- Gestion des notes en **CRUD** (ajouter / modifier / supprimer).
- Statistiques par matière et par classe (moyenne / min / max).
- **Emploi du temps** personnel (grille hebdomadaire, jour du jour surligné).
- **Cahier de textes** : donner un devoir à une classe.
- **Vie scolaire** : signaler une absence, un retard ou une observation.

### Espace Élève
- Connexion élève (mots de passe **hachés**).
- Page **Notes** avec :
  - filtre par **trimestre** (périodes réelles) et par matière,
  - tri par matière ou chronologique,
  - panneau de détail d’une note (moyenne / min / max de la classe),
  - moyenne générale + rang, couleur par matière.
- Export d’un bulletin `.txt` (généré en mémoire).
- Pages dédiées :
  - **Mes données**,
  - **Cahier de textes** (devoirs à faire de la classe),
  - **Résultats** (moyennes par matière et par trimestre),
  - **Vie scolaire** (absences / retards / observations),
  - **Emploi du temps** en grille hebdomadaire colorée.

---

## Stack technique
- **Python 3**
- **Flask**
- **SQLite3**
- **HTML5 / CSS3**

---

## Structure du projet
```text
noob-note/
├── app.py                # Backend Flask (routes + classes métier)
├── generer_db.py         # Génération de la base de démonstration
├── pronote.db            # Base SQLite (données de démonstration)
├── requirements.txt
├── README.md
├── static/
│   └── css/
│       └── style.css     # Feuille de style unique (look PRONOTE)
└── templates/
    ├── base_eleve.html   # Gabarit espace élève
    ├── base_prof.html    # Gabarit espace professeur
    ├── login.html
    ├── prof.html, prof_gestion.html, prof_emploi.html, prof_cahier.html, prof_vie.html
    ├── eleve.html, mes_donnees.html, cahier_texte.html
    ├── resultats.html, vie_scolaire.html, emploi_du_temps.html
```

---

## Base de données
Le projet utilise `pronote.db`.

Le script `generer_db.py` génère une base riche : classes, périodes (trimestres),
élèves, professeurs, matières, notes, emploi du temps, cahier de textes (devoirs)
et vie scolaire (absences / retards / observations). Les mots de passe sont hachés.

Exemple d’exécution (écrase `pronote.db` par défaut) :
```bash
python generer_db.py                 # 20 classes, 30 élèves, 60 notes chacun
python generer_db.py --classes 5     # version plus légère
```

---

## Identifiants de test
```text
Élève
  Identifiant : 1
  Mot de passe : pass1

Professeur
  Identifiant : p1_1
  Mot de passe : mdp_p1_1
```

---

## Lancer le projet en local
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

## Version en ligne
 https://noob-note.onrender.com

---

## Auteur
Projet réalisé dans un objectif d’apprentissage en spécialité NSI, avec une priorité sur la lisibilité du code.
