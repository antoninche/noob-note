import sqlite3
import random
from datetime import datetime, timedelta

def initialiser_systeme():
    conn = sqlite3.connect('pronote.db')
    cur = conn.cursor()

    # --- RECREATION DES TABLES ---
    cur.executescript('''
        DROP TABLE IF EXISTS Notes; DROP TABLE IF EXISTS Eleves; 
        DROP TABLE IF EXISTS Classes; DROP TABLE IF EXISTS Matieres;
        DROP TABLE IF EXISTS Professeurs;
        
        CREATE TABLE Classes (id_classe INTEGER PRIMARY KEY, nom_classe TEXT);
        CREATE TABLE Matieres (id_matiere INTEGER PRIMARY KEY, nom_matiere TEXT);
        CREATE TABLE Professeurs (id_prof TEXT PRIMARY KEY, nom TEXT, prenom TEXT, mot_de_passe TEXT);
        CREATE TABLE Eleves (
            id_eleve TEXT PRIMARY KEY, nom TEXT, prenom TEXT, date_naissance TEXT, 
            mot_de_passe TEXT, id_classe INTEGER,
            FOREIGN KEY(id_classe) REFERENCES Classes(id_classe)
        );
        CREATE TABLE Notes (
            id_note INTEGER PRIMARY KEY AUTOINCREMENT,
            valeur REAL, coefficient REAL, date_note TEXT,
            id_eleve TEXT, id_matiere INTEGER,
            FOREIGN KEY(id_eleve) REFERENCES Eleves(id_eleve),
            FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere)
        );
    ''')

    # --- DONNÉES DE BASE ---
    classes = [(1, 'T7'), (2, 'T8'), (3, 'T9')]
    matieres = [(1, 'Maths'), (2, 'NSI'), (3, 'EPS')]
    cur.executemany("INSERT INTO Classes VALUES (?,?)", classes)
    cur.executemany("INSERT INTO Matieres VALUES (?,?)", matieres)

    # --- GENERATION DES 9 PROFESSEURS ---
    # Un prof par matière (3) et par classe (3) = 9 profs
    profs = []
    noms_profs = ["Einstein", "Curie", "Turing", "Lovelace", "Pascal", "Newton", "Leibniz", "Hopper", "Hamilton"]
    i = 1
    for nom in noms_profs:
        profs.append((f"p{i}", nom, "Prof", f"mdp_prof{i}"))
        i += 1
    cur.executemany("INSERT INTO Professeurs VALUES (?,?,?,?)", profs)

    # --- GENERATION DES 90 ELEVES ---
    noms = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau", 
            "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier"]
    prenoms = ["Lucas", "Enzo", "Nathan", "Hugo", "Louis", "Jules", "Adam", "Liam", "Noah", "Arthur", 
               "Emma", "Alice", "Jade", "Lola", "Lea", "Mila", "Chloé", "Ines", "Sarah", "Camille"]
    
    eleves_ids = []
    for i in range(1, 91):
        nom = random.choice(noms)
        prenom = random.choice(prenoms)
        # On répartit dans les 3 classes (1 à 30 -> T7, 31 à 60 -> T8, 61 à 90 -> T9)
        id_classe = 1 if i <= 30 else (2 if i <= 60 else 3)
        date_naiss = f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/2008"
        mdp = f"pass{i}"
        cur.execute("INSERT INTO Eleves VALUES (?,?,?,?,?,?)", (str(i), nom, prenom, date_naiss, mdp, id_classe))
        eleves_ids.append(str(i))

    # --- GENERATION DES NOTES (6 par élève) ---
    for id_e in eleves_ids:
        for _ in range(6):
            valeur = round(random.uniform(6, 20), 1) # Note entre 6 et 20
            coeff = random.choice([1, 2, 4])
            id_m = random.randint(1, 3) # Matière aléatoire
            # Date aléatoire dans les 3 derniers mois
            jours_ecoules = random.randint(1, 90)
            date_note = (datetime.now() - timedelta(days=jours_ecoules)).strftime("%d/%m/%Y")
            
            cur.execute("INSERT INTO Notes (valeur, coefficient, date_note, id_eleve, id_matiere) VALUES (?,?,?,?,?)",
                        (valeur, coeff, date_note, id_e, id_m))

    conn.commit()
    conn.close()
    print("Base de données 'pronote.db' générée avec 90 élèves, 540 notes et 9 profs.")

if __name__ == "__main__":
    initialiser_systeme()
