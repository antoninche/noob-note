import sqlite3

def initialiser_systeme():
    conn = sqlite3.connect('pronote.db')
    cur = conn.cursor()

    cur.executescript('''
        DROP TABLE IF EXISTS Notes; DROP TABLE IF EXISTS Eleves; 
        DROP TABLE IF EXISTS Classes; DROP TABLE IF EXISTS Matieres;
        DROP TABLE IF EXISTS Professeurs;
        
        CREATE TABLE Classes (id_classe INTEGER PRIMARY KEY, nom_classe TEXT);
        CREATE TABLE Matieres (id_matiere INTEGER PRIMARY KEY, nom_matiere TEXT);
        
        CREATE TABLE Professeurs (
            id_prof TEXT PRIMARY KEY,
            nom TEXT,
            prenom TEXT,
            mot_de_passe TEXT
        );

        CREATE TABLE Eleves (
            id_eleve TEXT PRIMARY KEY,
            nom TEXT, prenom TEXT, date_naissance TEXT, 
            mot_de_passe TEXT, id_classe INTEGER,
            FOREIGN KEY(id_classe) REFERENCES Classes(id_classe)
        );

        CREATE TABLE Notes (
            id_note INTEGER PRIMARY KEY AUTOINCREMENT,
            valeur REAL, id_eleve TEXT, id_matiere INTEGER,
            FOREIGN KEY(id_eleve) REFERENCES Eleves(id_eleve),
            FOREIGN KEY(id_matiere) REFERENCES Matieres(id_matiere)
        );
    ''')

    # Données de base
    cur.execute("INSERT INTO Classes VALUES (1,'T7'), (2,'T8'), (3,'T9')")
    cur.execute("INSERT INTO Matieres VALUES (1,'Maths'), (2,'NSI'), (3,'EPS')")
    
    # Création d'un prof test
    cur.execute("INSERT INTO Professeurs VALUES ('p1', 'Curie', 'Marie', 'science123')")
    
    # Création d'un élève test (Lucas Martin de ton exemple)
    cur.execute("INSERT INTO Eleves VALUES ('1', 'Martin', 'Lucas', '14/03/2009', 'alpha1', 1)")

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès !")

if __name__ == "__main__":
    initialiser_systeme()