#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de génération d'une base PRONOTE de démonstration (version enrichie).

Objectif :
- beaucoup de classes et d'élèves,
- 3 périodes (trimestres),
- beaucoup de notes réparties sur l'année,
- un cahier de textes réel (table Devoirs),
- de la vie scolaire (absences / retards / observations),
- un emploi du temps du lundi au vendredi de 08h à 18h,
- des mots de passe hachés (sécurité).

Par défaut, la base est écrite directement dans pronote.db.
"""

import argparse
import os
import random
import sqlite3
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau",
    "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier",
    "Morel", "Girard", "Andre", "Lefevre", "Mercier", "Dupont", "Lambert", "Bonnet", "Francois", "Martinez",
    "Legrand", "Garnier", "Faure", "Rousseau", "Blanc", "Guerin", "Muller", "Henry", "Roussel", "Nicolas",
    "Perrin", "Morin", "Mathieu", "Clement", "Gauthier", "Dumont", "Lopez", "Fontaine", "Chevalier", "Robin",
    "Masson", "Sanchez", "Gerard", "Nguyen", "Boyer", "Denis", "Lemaire", "Duval", "Joly", "Gautier",
    "Roger", "Roche", "Roy", "Noel", "Meyer", "Lucas", "Meunier", "Jean", "Perez", "Marchand",
    "Dufour", "Blanchard", "Marie", "Barbier", "Brun", "Dumas", "Brunet", "Schmitt", "Leroux", "Colin",
    "Fernandez", "Caron", "Renard", "Arnaud", "Aubert", "Leclerc", "Marty", "Guillot", "Philippe", "Bourgeois",
    "Pierre", "Benoit", "Rey", "Rolland", "Levy", "Guillaume", "Pons", "Fischer", "Mallet", "Lecomte",
]

PRENOMS = [
    "Lucas", "Louis", "Gabriel", "Jules", "Adam", "Arthur", "Léo", "Hugo", "Raphael", "Mael",
    "Ethan", "Noah", "Nathan", "Tom", "Sacha", "Paul", "Mathis", "Axel", "Evan", "Ilyes",
    "Malo", "Theo", "Nolan", "Timeo", "Yanis", "Enzo", "Nino", "Baptiste", "Rayan", "Julien",
    "Antoine", "Alexandre", "Maxime", "Florian", "Valentin", "Damien", "Quentin", "Kevin", "Tristan", "Emma",
    "Jade", "Louise", "Alice", "Chloe", "Lina", "Mia", "Rose", "Ambre", "Lea", "Anna",
    "Manon", "Ines", "Sarah", "Jeanne", "Nina", "Eva", "Clara", "Iris", "Lola", "Camille",
    "Zoé", "Juliette", "Agathe", "Lucie", "Elena", "Margaux", "Adele", "Noemie", "Elsa", "Marion",
    "Anais", "Pauline", "Mathilde", "Sophie", "Carla", "Meline", "Romane", "Alicia", "Salome", "Youssef",
    "Imran", "Ibrahim", "Ismael", "Samir", "Karim", "Bilal", "Nassim", "Sofiane", "Aya", "Nour",
    "Yasmine", "Imane", "Luna", "Maya", "Elisa", "Celia", "Aurore", "Helene", "Morgane", "Celine",
]

MATIERES = [
    (1, "Maths"),
    (2, "NSI"),
    (3, "EPS"),
    (4, "Français"),
    (5, "Physique"),
    (6, "Histoire"),
]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

# Les 3 trimestres de l'année scolaire (dates au format JJ/MM/AAAA).
PERIODES = [
    (1, "Trimestre 1", "01/09/2025", "30/11/2025"),
    (2, "Trimestre 2", "01/12/2025", "28/02/2026"),
    (3, "Trimestre 3", "01/03/2026", "30/06/2026"),
]

DESCRIPTIONS_DEVOIRS = [
    "Faire les exercices 1 à 5 page 42.",
    "Apprendre la leçon pour l'évaluation.",
    "Terminer le TP commencé en classe.",
    "Rédiger une synthèse d'une page.",
    "Réviser le chapitre en cours.",
    "Lire le document distribué et répondre aux questions.",
    "Préparer la présentation orale.",
    "Faire la fiche de révision du chapitre.",
]

MOTIFS_ABSENCE = ["Maladie", "Rendez-vous médical", "Raison familiale", "Non justifiée"]
MOTIFS_RETARD = ["Transport en retard", "Réveil tardif", "Rendez-vous", "Non justifié"]
MOTIFS_OBSERVATION = ["Bavardages en cours", "Travail non rendu", "Très bonne participation", "Oubli de matériel"]


# ---------------------------------------------------------------------
# OUTILS SIMPLES
# ---------------------------------------------------------------------

def date_aleatoire(date_min, date_max):
    """Retourne une date aléatoire entre date_min et date_max."""
    delta = date_max - date_min
    nb_jours = random.randint(0, delta.days)
    return date_min + timedelta(days=nb_jours)


def format_date_fr(date_obj):
    """Convertit une date Python en format JJ/MM/AAAA."""
    return date_obj.strftime("%d/%m/%Y")


# ---------------------------------------------------------------------
# CREATION DE LA BASE
# ---------------------------------------------------------------------

def creer_tables(cur):
    """Crée toutes les tables nécessaires."""
    for table in ["VieScolaire", "Devoirs", "EmploiDuTemps", "Notes",
                  "Eleves", "Professeurs", "Matieres", "Periodes", "Classes"]:
        cur.execute(f"DROP TABLE IF EXISTS {table}")

    cur.execute("CREATE TABLE Classes (id_classe INTEGER PRIMARY KEY, nom_classe TEXT)")

    cur.execute(
        """
        CREATE TABLE Periodes (
            id_periode INTEGER PRIMARY KEY,
            nom TEXT,
            date_debut TEXT,
            date_fin TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE Eleves (
            id_eleve TEXT PRIMARY KEY,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            mot_de_passe TEXT,
            id_classe INTEGER,
            FOREIGN KEY(id_classe) REFERENCES Classes(id_classe)
        )
        """
    )

    cur.execute("CREATE TABLE Matieres (id_matiere INTEGER PRIMARY KEY, nom_matiere TEXT)")

    cur.execute(
        """
        CREATE TABLE Professeurs (
            id_prof TEXT PRIMARY KEY,
            nom TEXT,
            prenom TEXT,
            mot_de_passe TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE Notes (
            id_note INTEGER PRIMARY KEY AUTOINCREMENT,
            valeur REAL,
            coefficient REAL,
            date_note TEXT,
            id_eleve TEXT,
            id_matiere INTEGER,
            FOREIGN KEY(id_eleve) REFERENCES Eleves(id_eleve),
            FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE EmploiDuTemps (
            id_cours INTEGER PRIMARY KEY AUTOINCREMENT,
            id_classe INTEGER,
            jour_semaine TEXT,
            heure_debut TEXT,
            heure_fin TEXT,
            id_matiere INTEGER,
            id_prof TEXT,
            salle TEXT,
            FOREIGN KEY(id_classe) REFERENCES Classes(id_classe),
            FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere),
            FOREIGN KEY(id_prof) REFERENCES Professeurs(id_prof)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE Devoirs (
            id_devoir INTEGER PRIMARY KEY AUTOINCREMENT,
            id_classe INTEGER,
            id_matiere INTEGER,
            id_prof TEXT,
            date_donne TEXT,
            date_pour TEXT,
            description TEXT,
            FOREIGN KEY(id_classe) REFERENCES Classes(id_classe),
            FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere),
            FOREIGN KEY(id_prof) REFERENCES Professeurs(id_prof)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE VieScolaire (
            id_evenement INTEGER PRIMARY KEY AUTOINCREMENT,
            id_eleve TEXT,
            type_evenement TEXT,
            date_evenement TEXT,
            motif TEXT,
            justifie INTEGER,
            FOREIGN KEY(id_eleve) REFERENCES Eleves(id_eleve)
        )
        """
    )


def inserer_classes(cur, nb_classes):
    """Insère les classes (nom lisible type Terminale)."""
    for id_classe in range(1, nb_classes + 1):
        cur.execute(
            "INSERT INTO Classes (id_classe, nom_classe) VALUES (?, ?)",
            (id_classe, f"Terminale {id_classe}")
        )


def inserer_periodes(cur):
    """Insère les 3 trimestres."""
    for id_periode, nom, debut, fin in PERIODES:
        cur.execute(
            "INSERT INTO Periodes (id_periode, nom, date_debut, date_fin) VALUES (?, ?, ?, ?)",
            (id_periode, nom, debut, fin)
        )


def inserer_matieres(cur):
    """Insère les matières de base."""
    for id_matiere, nom in MATIERES:
        cur.execute(
            "INSERT INTO Matieres (id_matiere, nom_matiere) VALUES (?, ?)",
            (id_matiere, nom)
        )


def creer_profs_par_matiere_et_classes(cur, nb_classes):
    """
    Crée les profs et la correspondance (classe, matière) -> professeur.

    Règle : 1 prof pour 2 classes par matière.
    """
    mapping = {}

    for id_matiere, nom_matiere in MATIERES:
        groupe = 1
        for classe_a in range(1, nb_classes + 1, 2):
            classe_b = classe_a + 1
            id_prof = f"p{id_matiere}_{groupe}"
            nom_prof = random.choice(NOMS)
            prenom_prof = random.choice(PRENOMS)
            mot_de_passe = generate_password_hash(f"mdp_{id_prof}", method="pbkdf2")

            cur.execute(
                "INSERT INTO Professeurs (id_prof, nom, prenom, mot_de_passe) VALUES (?, ?, ?, ?)",
                (id_prof, nom_prof, prenom_prof, mot_de_passe)
            )

            mapping[(classe_a, id_matiere)] = id_prof
            if classe_b <= nb_classes:
                mapping[(classe_b, id_matiere)] = id_prof

            groupe += 1

    return mapping


def inserer_eleves(cur, nb_classes, eleves_par_classe):
    """Insère les élèves avec identifiant unique et mot de passe haché."""
    date_min = datetime(2007, 1, 1)
    date_max = datetime(2010, 12, 31)

    compteur = 1
    ids_eleves = []

    for id_classe in range(1, nb_classes + 1):
        for _ in range(eleves_par_classe):
            id_eleve = str(compteur)
            nom = random.choice(NOMS)
            prenom = random.choice(PRENOMS)
            naissance = format_date_fr(date_aleatoire(date_min, date_max))
            mot_de_passe = generate_password_hash(f"pass{id_eleve}", method="pbkdf2")

            cur.execute(
                """
                INSERT INTO Eleves (id_eleve, nom, prenom, date_naissance, mot_de_passe, id_classe)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (id_eleve, nom, prenom, naissance, mot_de_passe, id_classe)
            )

            ids_eleves.append((id_eleve, id_classe))
            compteur += 1

    return ids_eleves


def inserer_notes(cur, ids_eleves, nb_notes_par_eleve):
    """Insère des notes aléatoires sur l'année scolaire."""
    debut_annee = datetime(2025, 9, 1)
    fin_annee = datetime(2026, 6, 30)

    for id_eleve, _ in ids_eleves:
        # Un petit niveau propre à l'élève rend les moyennes plus réalistes.
        niveau = random.uniform(8, 15)
        for _ in range(nb_notes_par_eleve):
            valeur = round(min(20, max(2, random.gauss(niveau, 3))), 2)
            coefficient = random.choice([0.5, 1, 1, 1, 2, 2, 3])
            date_note = format_date_fr(date_aleatoire(debut_annee, fin_annee))
            id_matiere = random.randint(1, len(MATIERES))

            cur.execute(
                """
                INSERT INTO Notes (valeur, coefficient, date_note, id_eleve, id_matiere)
                VALUES (?, ?, ?, ?, ?)
                """,
                (valeur, coefficient, date_note, id_eleve, id_matiere)
            )


def inserer_emploi_du_temps(cur, nb_classes, mapping_profs):
    """Insère un EDT complet du lundi au vendredi, de 08h à 18h (créneaux d'1h)."""
    salles = [f"B{numero:02d}" for numero in range(1, 31)]

    for id_classe in range(1, nb_classes + 1):
        for jour in JOURS_SEMAINE:
            for heure in range(8, 18):
                id_matiere = random.randint(1, len(MATIERES))
                id_prof = mapping_profs[(id_classe, id_matiere)]
                heure_debut = f"{heure:02d}:00"
                heure_fin = f"{heure + 1:02d}:00"
                salle = random.choice(salles)

                cur.execute(
                    """
                    INSERT INTO EmploiDuTemps (
                        id_classe, jour_semaine, heure_debut, heure_fin, id_matiere, id_prof, salle
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (id_classe, jour, heure_debut, heure_fin, id_matiere, id_prof, salle)
                )


def inserer_devoirs(cur, nb_classes, mapping_profs, devoirs_par_matiere):
    """Insère un cahier de textes : plusieurs devoirs par classe et par matière."""
    debut_annee = datetime(2025, 9, 1)
    fin_annee = datetime(2026, 6, 20)

    for id_classe in range(1, nb_classes + 1):
        for id_matiere, _ in MATIERES:
            id_prof = mapping_profs[(id_classe, id_matiere)]
            for _ in range(devoirs_par_matiere):
                date_donne_obj = date_aleatoire(debut_annee, fin_annee)
                date_pour_obj = date_donne_obj + timedelta(days=random.randint(2, 10))
                description = random.choice(DESCRIPTIONS_DEVOIRS)

                cur.execute(
                    """
                    INSERT INTO Devoirs (id_classe, id_matiere, id_prof, date_donne, date_pour, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (id_classe, id_matiere, id_prof,
                     format_date_fr(date_donne_obj), format_date_fr(date_pour_obj), description)
                )


def inserer_vie_scolaire(cur, ids_eleves):
    """Insère des événements de vie scolaire (absences, retards, observations)."""
    debut_annee = datetime(2025, 9, 1)
    fin_annee = datetime(2026, 6, 30)

    for id_eleve, _ in ids_eleves:
        for _ in range(random.randint(0, 5)):
            type_evenement = random.choice(["Absence", "Absence", "Retard", "Observation"])

            if type_evenement == "Absence":
                motif = random.choice(MOTIFS_ABSENCE)
            elif type_evenement == "Retard":
                motif = random.choice(MOTIFS_RETARD)
            else:
                motif = random.choice(MOTIFS_OBSERVATION)

            justifie = 0 if "Non justifi" in motif else random.choice([0, 1, 1])
            date_evt = format_date_fr(date_aleatoire(debut_annee, fin_annee))

            cur.execute(
                """
                INSERT INTO VieScolaire (id_eleve, type_evenement, date_evenement, motif, justifie)
                VALUES (?, ?, ?, ?, ?)
                """,
                (id_eleve, type_evenement, date_evt, motif, justifie)
            )


def afficher_resume(cur):
    """Affiche le nombre de lignes dans chaque table pour vérification."""
    tables = ["Classes", "Periodes", "Eleves", "Professeurs", "Matieres",
              "Notes", "EmploiDuTemps", "Devoirs", "VieScolaire"]
    print("\nRésumé de la base générée :")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total = cur.fetchone()[0]
        print(f"- {table}: {total}")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def generer_base(chemin_db, seed, nb_classes, eleves_par_classe, nb_notes_par_eleve):
    """Génère une base complète en écrasant le fichier si besoin."""
    random.seed(seed)

    if os.path.exists(chemin_db):
        os.remove(chemin_db)

    conn = sqlite3.connect(chemin_db)
    cur = conn.cursor()

    creer_tables(cur)
    inserer_classes(cur, nb_classes)
    inserer_periodes(cur)
    inserer_matieres(cur)

    mapping_profs = creer_profs_par_matiere_et_classes(cur, nb_classes)
    ids_eleves = inserer_eleves(cur, nb_classes, eleves_par_classe)
    inserer_notes(cur, ids_eleves, nb_notes_par_eleve)
    inserer_emploi_du_temps(cur, nb_classes, mapping_profs)
    inserer_devoirs(cur, nb_classes, mapping_profs, devoirs_par_matiere=6)
    inserer_vie_scolaire(cur, ids_eleves)

    conn.commit()
    afficher_resume(cur)
    conn.close()


def construire_arguments():
    """Lit les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="Générer une base PRONOTE de démonstration.")
    parser.add_argument("--sortie", default="pronote.db",
                        help="Chemin du fichier .db généré (défaut: pronote.db)")
    parser.add_argument("--seed", type=int, default=2026,
                        help="Graine aléatoire pour retrouver le même jeu de données")
    parser.add_argument("--classes", type=int, default=20, help="Nombre de classes")
    parser.add_argument("--eleves", type=int, default=30, help="Nombre d'élèves par classe")
    parser.add_argument("--notes", type=int, default=60, help="Nombre de notes par élève")
    return parser.parse_args()


def main():
    args = construire_arguments()
    generer_base(args.sortie, args.seed, args.classes, args.eleves, args.notes)
    print(f"\nBase créée : {args.sortie}")


if __name__ == "__main__":
    main()
