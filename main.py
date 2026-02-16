# -*- coding: utf-8 -*-
import sqlite3

# ----------------------------- LOGIQUE SQL ------------------------

def connexion_globale(user_id, mdp):
    conn = sqlite3.connect('pronote.db')
    cur = conn.cursor()
    
    # On cherche d'abord dans les profs
    cur.execute("SELECT nom, prenom FROM Professeurs WHERE id_prof = ? AND mot_de_passe = ?", (user_id, mdp))
    res = cur.fetchone()
    if res:
        conn.close()
        return ("PROF", res[0], res[1])
    
    # Sinon on cherche dans les élèves
    cur.execute("SELECT nom, prenom FROM Eleves WHERE id_eleve = ? AND mot_de_passe = ?", (user_id, mdp))
    res = cur.fetchone()
    conn.close()
    if res:
        return ("ELEVE", res[0], res[1])
    
    return None

# ----------------------------- CLASSES ------------------------

class Utilisateur:
    def __init__(self, id_u, nom, prenom):
        self.id = id_u
        self.nom = nom
        self.prenom = prenom

class Professeur(Utilisateur):
    def ajouter_note(self, id_eleve, id_matiere, note):
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO Notes (valeur, id_eleve, id_matiere) VALUES (?, ?, ?)", (note, id_eleve, id_matiere))
        conn.commit()
        conn.close()
        print(f"✅ Note de {note} ajoutée pour l'élève {id_eleve}")

    def voir_tous_eleves(self):
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute("SELECT id_eleve, nom, prenom FROM Eleves")
        for e in cur.fetchall():
            print(f"ID: {e[0]} | {e[2]} {e[1]}")
        conn.close()

class Eleve(Utilisateur):
    def voir_mes_notes(self):
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute('''SELECT Matieres.nom_matiere, Notes.valeur 
                       FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere 
                       WHERE id_eleve = ?''', (self.id,))
        notes = cur.fetchall()
        conn.close()
        if not notes:
            print("Aucune note enregistrée.")
        else:
            for n in notes:
                print(f"{n[0]} : {n[1]}/20")

# ----------------------------- INTERFACE CLI ------------------------

def interface_prof(prof):
    while True:
        print(f"\n--- ESPACE PROFESSEUR ({prof.prenom} {prof.nom}) ---")
        print("1. Liste des élèves")
        print("2. Ajouter une note")
        print("3. Déconnexion")
        choix = input("Action > ")

        if choix == "1":
            prof.voir_tous_eleves()
        elif choix == "2":
            id_e = input("ID de l'élève : ")
            id_m = int(input("Matière (1:Maths, 2:NSI, 3:EPS) : "))
            note = float(input("Note : "))
            prof.ajouter_note(id_e, id_m, note)
        elif choix == "3": break

def interface_eleve(eleve):
    while True:
        print(f"\n--- ESPACE ÉLÈVE ({eleve.prenom} {eleve.nom}) ---")
        print("1. Voir mes notes")
        print("2. Déconnexion")
        choix = input("Action > ")

        if choix == "1":
            eleve.voir_mes_notes()
        elif choix == "2": break

# ----------------------------- MAIN ------------------------

print("=== BIENVENUE SUR PRONOTE CLI ===")
identifiant = input("ID : ")
mdp = input("Mot de passe : ")

auth = connexion_globale(identifiant, mdp)

if auth:
    role, nom, prenom = auth
    if role == "PROF":
        prof_objet = Professeur(identifiant, nom, prenom)
        interface_prof(prof_objet)
    else:
        eleve_objet = Eleve(identifiant, nom, prenom)
        interface_eleve(eleve_objet)
else:
    print("Identifiants incorrects.")