# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime

# -------------------------------------------------------------------------
# UTILS : Fonctions d'aide pour simplifier le reste du code
# -------------------------------------------------------------------------

def saisie_nombre(message, est_entier=False):
    """
    Demande un nombre à l'utilisateur et sécurise la saisie.
    Paramètres :
        message (str) : La question à poser.
        est_entier (bool) : Si True, transforme en int, sinon en float.
    Retour :
        int ou float : Le nombre saisi proprement.
    """
    while True:
        saisie = input(message)
        try:
            return int(saisie) if est_entier else float(saisie)
        except ValueError:
            print("⚠️ Erreur : Tu dois entrer un chiffre (ex: 15 ou 15.5).")

def connexion_globale(user_id, mdp):
    """
    Vérifie dans la base de données si l'utilisateur existe.
    Retour : Un tuple (Rôle, Nom, Prénom) ou None si échec.
    """
    with sqlite3.connect('pronote.db') as conn:
        cur = conn.cursor()
        
        # On teste d'abord si c'est un prof
        cur.execute("SELECT nom, prenom FROM Professeurs WHERE id_prof = ? AND mot_de_passe = ?", (user_id, mdp))
        res = cur.fetchone()
        if res:
            return ("PROF", res[0], res[1])
            
        # Sinon on teste si c'est un élève
        cur.execute("SELECT nom, prenom FROM Eleves WHERE id_eleve = ? AND mot_de_passe = ?", (user_id, mdp))
        res = cur.fetchone()
        if res:
            return ("ELEVE", res[0], res[1])
            
    return None

# -------------------------------------------------------------------------
# CLASSES : Programmation Orientée Objet (POO)
# -------------------------------------------------------------------------

class Utilisateur:
    """Classe mère regroupant les points communs (Nom, Prénom, ID)."""
    def __init__(self, id_u, nom, prenom):
        self.id = id_u
        self.nom = nom
        self.prenom = prenom
        self.db_path = 'pronote.db'

    def _executer_requete(self, requete, params=(), fetch=False, commit=False):
        """Méthode interne pour centraliser les appels SQL et gérer la connexion."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(requete, params)
            if commit:
                conn.commit()
            return cur.fetchall() if fetch else None

class Professeur(Utilisateur):
    """Classe représentant un professeur, hérite de Utilisateur."""
    
    def ajouter_note(self, id_eleve, id_matiere, note, coeff):
        """Ajoute une nouvelle ligne dans la table Notes."""
        date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
        sql = "INSERT INTO Notes (valeur, coefficient, date_note, id_eleve, id_matiere) VALUES (?,?,?,?,?)"
        self._executer_requete(sql, (note, coeff, date_aujourdhui, id_eleve, id_matiere), commit=True)
        print(f"✅ Note de {note}/20 enregistrée.")

    def modifier_note(self, id_note, nouvelle_valeur):
        """Modifie une note existante via son identifiant unique."""
        sql = "UPDATE Notes SET valeur = ? WHERE id_note = ?"
        self._executer_requete(sql, (nouvelle_valeur, id_note), commit=True)
        print("✅ Note modifiée.")

    def supprimer_note(self, id_note):
        """Supprime une note de la base de données."""
        sql = "DELETE FROM Notes WHERE id_note = ?"
        self._executer_requete(sql, (id_note,), commit=True)
        print("🗑️ Note supprimée.")

    def chercher_eleve(self, nom_recherche):
        """Affiche les élèves dont le nom ressemble à la recherche."""
        sql = "SELECT id_eleve, nom, prenom FROM Eleves WHERE nom LIKE ?"
        resultats = self._executer_requete(sql, (f"%{nom_recherche}%",), fetch=True)
        for e in resultats:
            print(f"ID: {e[0]} | Nom: {e[1]} {e[2]}")

    def voir_notes_eleve(self, id_eleve):
        """Affiche toutes les notes d'un élève précis."""
        sql = '''SELECT Notes.id_note, Matieres.nom_matiere, Notes.valeur, Notes.date_note 
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere 
                 WHERE id_eleve = ?'''
        resultats = self._executer_requete(sql, (id_eleve,), fetch=True)
        for n in resultats:
            print(f"ID: {n[0]} | {n[1]:<12} : {n[2]}/20 ({n[3]})")

    def stats_matiere_classe(self, id_classe, id_matiere):
        """Calcule les statistiques (moyenne, min, max) d'une classe dans une matière."""
        sql = '''SELECT AVG(valeur), MIN(valeur), MAX(valeur) FROM Notes 
                 JOIN Eleves ON Notes.id_eleve = Eleves.id_eleve 
                 WHERE id_classe = ? AND id_matiere = ?'''
        res = self._executer_requete(sql, (id_classe, id_matiere), fetch=True)
        if res and res[0][0] is not None:
            stats = res[0]
            print(f"\n📊 Stats : Moyenne {stats[0]:.2f} | Min {stats[1]} | Max {stats[2]}")
        else:
            print("⚠️ Aucune note trouvée pour ce groupe.")

class Eleve(Utilisateur):
    """Classe représentant un élève, hérite de Utilisateur."""

    def voir_mes_notes(self):
        """Récupère et affiche les notes de l'élève connecté."""
        sql = '''SELECT Matieres.nom_matiere, Notes.valeur, Notes.coefficient, Notes.date_note 
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere 
                 WHERE id_eleve = ? ORDER BY date_note DESC'''
        for n in self._executer_requete(sql, (self.id,), fetch=True):
            print(f"[{n[3]}] {n[0]:<12} : {n[1]}/20 (Coeff {n[2]})")

    def calculer_rang(self):
        """Algorithme de classement : Compare la moyenne de l'élève à ses camarades."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id_classe FROM Eleves WHERE id_eleve = ?", (self.id,))
            id_classe = cur.fetchone()[0]
            
            cur.execute("SELECT id_eleve FROM Eleves WHERE id_classe = ?", (id_classe,))
            camarades = cur.fetchall()

            classement = []
            for (id_comp,) in camarades:
                cur.execute("SELECT SUM(valeur * coefficient), SUM(coefficient) FROM Notes WHERE id_eleve = ?", (id_comp,))
                somme, coeffs = cur.fetchone()
                moy = (somme / coeffs) if coeffs and coeffs > 0 else 0
                classement.append((id_comp, moy))

        # Tri décroissant selon la moyenne
        classement.sort(key=lambda x: x[1], reverse=True)

        for i, (id_c, moy) in enumerate(classement):
            if id_c == self.id:
                return i + 1, len(camarades), moy
        return 0, len(camarades), 0

    def generer_bulletin(self):
        """Crée un fichier texte structuré avec les moyennes par matière."""
        rang, total, moy_gen = self.calculer_rang()
        
        sql = '''SELECT Matieres.nom_matiere, Notes.valeur, Notes.coefficient 
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere 
                 WHERE id_eleve = ?'''
        notes = self._executer_requete(sql, (self.id,), fetch=True)

        if not notes:
            print("❌ Pas de notes pour le bulletin.")
            return

        dict_stats = {}
        for mat, val, coef in notes:
            if mat not in dict_stats:
                dict_stats[mat] = [0, 0]
            dict_stats[mat][0] += val * coef
            dict_stats[mat][1] += coef

        nom_fichier = f"bulletin_{self.nom}.txt"
        with open(nom_fichier, "w", encoding="utf-8") as f:
            f.write("╔" + "═"*50 + "╗\n")
            f.write(f"║{'BULLETIN TRIMESTRIEL':^50}║\n")
            f.write("╠" + "═"*50 + "╣\n")
            f.write(f"║ Nom : {self.nom:<41} ║\n")
            f.write(f"║ Prénom : {self.prenom:<38} ║\n")
            f.write("╟" + "─"*50 + "╢\n")
            
            for mat, data in dict_stats.items():
                moy_mat = data[0] / data[1]
                f.write(f"║ {mat:<25} | Moyenne: {moy_mat:>5.2f}/20 ║\n")
            
            f.write("╠" + "═"*50 + "╣\n")
            f.write(f"║ MOYENNE GÉNÉRALE : {moy_gen:>23.2f}/20 ║\n")
            f.write(f"║ RANG : {str(rang)+'/'+str(total):>35} ║\n")
            f.write("╚" + "═"*50 + "╝\n")
        
        print(f"✅ Bulletin généré : {nom_fichier}")

# -------------------------------------------------------------------------
# INTERFACES : Menus de navigation
# -------------------------------------------------------------------------

def menu_professeur(prof):
    while True:
        print(f"\n--- SESSION PROF : {prof.prenom} {prof.nom} ---")
        print("1. Chercher un élève")
        print("2. Ajouter une note")
        print("3. Gérer les notes (Modifier/Supprimer)")
        print("4. Statistiques de classe")
        print("5. Se déconnecter")
        
        choix = input("Choix : ")
        
        if choix == "1":
            prof.chercher_eleve(input("Nom recherché : "))
        elif choix == "2":
            ide = input("ID Élève : ")
            idm = saisie_nombre("ID Matière (1:Maths, 2:NSI, 3:EPS) : ", True)
            note = saisie_nombre("Note : ")
            coef = saisie_nombre("Coefficient : ")
            prof.ajouter_note(ide, idm, note, coef)
        elif choix == "3":
            ide = input("ID Élève : ")
            prof.voir_notes_eleve(ide)
            action = input("(M)odifier, (S)upprimer ou (R)etour ? ").upper()
            if action == "M":
                idn = saisie_nombre("ID de la note : ", True)
                prof.modifier_note(idn, saisie_nombre("Nouvelle note : "))
            elif action == "S":
                prof.supprimer_note(saisie_nombre("ID de la note : ", True))
        elif choix == "4":
            idc = saisie_nombre("ID Classe (1, 2 ou 3) : ", True)
            idm = saisie_nombre("ID Matière : ", True)
            prof.stats_matiere_classe(idc, idm)
        elif choix == "5":
            break

def menu_eleve(eleve):
    while True:
        print(f"\n--- SESSION ÉLÈVE : {eleve.prenom} ---")
        print("1. Voir mes notes")
        print("2. Voir mon rang")
        print("3. Télécharger mon bulletin (.txt)")
        print("4. Se déconnecter")
        
        choix = input("Choix : ")
        
        if choix == "1":
            eleve.voir_mes_notes()
        elif choix == "2":
            rang, total, moy = eleve.calculer_rang()
            print(f"⭐ Ta moyenne : {moy:.2f}/20 | Ton rang : {rang}/{total}")
        elif choix == "3":
            eleve.generer_bulletin()
        elif choix == "4":
            break

# -------------------------------------------------------------------------
# LANCEMENT DU PROGRAMME
# -------------------------------------------------------------------------

if __name__ == "__main__":
    print("PROJET NSI : GESTIONNAIRE PRONOTE")
    id_saisie = input("Identifiant : ")
    mdp_saisie = input("Mot de passe : ")
    
    verif = connexion_globale(id_saisie, mdp_saisie)
    
    if verif:
        role, nom, prenom = verif
        if role == "PROF":
            mon_prof = Professeur(id_saisie, nom, prenom)
            menu_professeur(mon_prof)
        else:
            mon_eleve = Eleve(id_saisie, nom, prenom)
            menu_eleve(mon_eleve)
    else:
        print("❌ Identifiants incorrects.")
