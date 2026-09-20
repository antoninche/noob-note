# NOOB-NOTE

Un mini-PRONOTE : carnet de notes en ligne avec un espace professeur et un espace
élève. Projet de spécialité NSI, en Flask et SQLite.

Démo en ligne : https://noob-note.onrender.com

Comptes de test — professeur `p1_1` / `mdp_p1_1`, élève `1` / `pass1`.

## Espace professeur

- Liste des élèves par classe et recherche par nom
- Ajout, modification et suppression de notes
- Statistiques par matière et par classe (moyenne, min, max)
- Emploi du temps, cahier de textes, saisie des absences et retards

## Espace élève

- Notes filtrables par trimestre et par matière
- Détail d'une note : moyenne, min et max de la classe
- Moyenne générale et rang
- Export du bulletin en `.txt`
- Emploi du temps, devoirs à faire, absences et observations

Les mots de passe sont hachés (pbkdf2, via Werkzeug). La base de démonstration
est régénérée par `generer_db.py`.

## Lancer en local

```bash
git clone https://github.com/antoninche/noob-note.git
cd noob-note
pip install -r requirements.txt
python app.py
```

Puis http://127.0.0.1:5000

## Limites connues

- Pas de gestion des trimestres côté professeur : la période est déduite de la date de la note.
- Les identifiants élèves sont des entiers séquentiels, ce qui rend les comptes devinables.
- `pronote.db` est versionné dans le dépôt pour que la démo fonctionne sans setup.
