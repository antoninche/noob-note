# -*- coding: utf-8 -*-
"""
PRONOTE CLI v3.0 - Spécialité NSI
Système de gestion de notes avec SQL, POO et Moyennes pondérées.
"""
import sqlite3
from datetime import datetime

# ----------------------------- LOGIQUE SQL ------------------------

def connexion_globale(user_id, mdp):
    """Vérifie les identifiants dans les tables Professeurs ou Eleves."""
    conn = sqlite3.connect('pronote.db')
    cur = conn.cursor()
    
    # Test chez les Professeurs
    cur.execute("SELECT nom, prenom FROM Professeurs WHERE id_prof = ? AND mot_de_passe = ?", (user_id, mdp))
    res = cur.fetchone()
    if res:
        conn.close()
        return ("PROF", res[0], res[1])
    
    # Test chez les Elèves
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
    def ajouter_note(self, id_eleve, id_matiere, note, coeff):
        """Ajoute une note avec coefficient et date automatique."""
        date_du_jour = datetime.now().strftime("%d/%m/%Y")
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute('''INSERT INTO Notes (valeur, coefficient, date_note, id_eleve, id_matiere) 
                       VALUES (?, ?, ?, ?, ?)''', (note, coeff, date_du_jour, id_eleve, id_matiere))
        conn.commit()
        conn.close()
        print(f"\n✅ Note de {note} (coeff {coeff}) enregistrée pour l'élève {id_eleve}.")

    def moyenne_classe(self, id_classe, id_matiere):
        """Calcule la moyenne pondérée de toute une classe pour une matière."""
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute('''SELECT SUM(valeur * coefficient) / SUM(coefficient) 
                       FROM Notes JOIN Eleves ON Notes.id_eleve = Eleves.id_eleve 
                       WHERE Eleves.id_classe = ? AND Notes.id_matiere = ?''', (id_classe, id_matiere))
        moy = cur.fetchone()[0]
        conn.close()
        if moy:
            print(f"\n📈 Moyenne pondérée de la classe : {moy:.2f}/20")
        else:
            print("\n⚠️ Aucune donnée disponible pour ce calcul.")

    def chercher_eleve(self, nom_recherche):
        """Recherche un élève par son nom ou une partie de son nom."""
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute("SELECT id_eleve, nom, prenom FROM Eleves WHERE nom LIKE ?", (f"%{nom_recherche}%",))
        resultats = cur.fetchall()
        conn.close()
        print("\n--- Résultats de la recherche ---")
        for e in resultats:
            print(f"ID: {e[0]} | Nom: {e[1]} | Prénom: {e[2]}")

class Eleve(Utilisateur):
    def voir_mes_notes(self):
        """Affiche l'historique des notes par date décroissante."""
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute('''SELECT Matieres.nom_matiere, Notes.valeur, Notes.coefficient, Notes.date_note 
                       FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere 
                       WHERE id_eleve = ? ORDER BY date_note DESC''', (self.id,))
        notes = cur.fetchall()
        conn.close()
        print("\n--- Vos Notes ---")
        for n in notes:
            print(f"[{n[3]}] {n[0]:<12} : {n[1]:>5}/20 (Coeff {n[2]})")

    def moyenne_generale(self):
        """Calcule la moyenne pondérée de l'élève sur toutes ses matières."""
        conn = sqlite3.connect('pronote.db')
        cur = conn.cursor()
        cur.execute("SELECT SUM(valeur * coefficient) / SUM(coefficient) FROM Notes WHERE id_eleve = ?", (self.id,))
        moy = cur.fetchone()[0]
        conn.close()
        if moy:
            print(f"\n⭐ Votre Moyenne Générale Pondérée : {moy:.2f}/20")
        else:
            print("\nVous n'avez pas encore de notes.")

# ----------------------------- MENUS CLI ------------------------

def menu_prof(prof):
    while True:
        print(f"\n=== ESPACE PROF : {prof.prenom} {prof.nom} ===")
        print("1. Rechercher un élève")
        print("2. Ajouter une note")
        print("3. Statistiques de classe")
        print("4. Déconnexion")
        choix = input("Commande > ")

        if choix == "1":
            nom = input("Nom de l'élève à chercher : ")
            prof.chercher_eleve(nom)
        elif choix == "2":
            ide = input("ID de l'élève : ")
            mat = int(input("ID Matière (1:Maths, 2:NSI, 3:EPS) : "))
            val = float(input("Note obtenue : "))
            cof = float(input("Coefficient : "))
            prof.ajouter_note(ide, mat, val, cof)
        elif choix == "3":
            cls = int(input("ID Classe (1:T7, 2:T8, 3:T9) : "))
            mat = int(input("ID Matière (1:Maths, 2:NSI, 3:EPS) : "))
            prof.moyenne_classe(cls, mat)
        elif choix == "4": break

def menu_eleve(eleve):
    while True:
        print(f"\n=== ESPACE ÉLÈVE : {eleve.prenom} {eleve.nom} ===")
        print("1. Voir mes notes")
        print("2. Voir ma moyenne générale")
        print("3. Déconnexion")
        choix = input("Commande > ")

        if choix == "1":
            eleve.voir_mes_notes()
        elif choix == "2":
            eleve.moyenne_generale()
        elif choix == "3": break

# ----------------------------- BOOT ------------------------

if __name__ == "__main__":
    print("---------------------------------")
    print("  BIENVENUE SUR PRONOTE CLI  ")
    print("---------------------------------")
    
    uid = input("Identifiant : ")
    pwd = input("Mot de passe : ")
    
    auth = connexion_globale(uid, pwd)
    
    if auth:
        role, nom, prenom = auth
        if role == "PROF":
            menu_prof(Professeur(uid, nom, prenom))
        else:
            menu_eleve(Eleve(uid, nom, prenom))
    else:
        print("\n❌ Accès refusé : Identifiants incorrects.")
