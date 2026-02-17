# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_nsi_2026"

# -------------------------------------------------------------------------
# CLASSES METIER (Votre code d'origine adapté Web)
# -------------------------------------------------------------------------

class Utilisateur:
    def __init__(self, id_u, nom, prenom):
        self.id = id_u
        self.nom = nom
        self.prenom = prenom
        self.db_path = 'pronote.db'

    def _executer(self, sql, params=(), fetch=False, commit=False):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            if commit:
                conn.commit()
            return cur.fetchall() if fetch else None

class Professeur(Utilisateur):
    def lister_eleves_par_classe(self, id_classe):
        """Récupère les élèves d'une classe spécifique (T7, T8, T9)"""
        sql = "SELECT id_eleve, nom, prenom FROM Eleves WHERE id_classe = ? ORDER BY nom"
        return self._executer(sql, (id_classe,), fetch=True)

    def chercher_eleve(self, nom_partiel):
        """Fonctionnalité de recherche par nom"""
        sql = "SELECT id_eleve, nom, prenom, id_classe FROM Eleves WHERE nom LIKE ?"
        return self._executer(sql, (f"%{nom_partiel}%",), fetch=True)

    def ajouter_note(self, id_eleve, id_matiere, note, coeff):
        """Ajoute une note (CREATE)"""
        date_jour = datetime.now().strftime("%d/%m/%Y")
        sql = "INSERT INTO Notes (valeur, coefficient, date_note, id_eleve, id_matiere) VALUES (?,?,?,?,?)"
        self._executer(sql, (note, coeff, date_jour, id_eleve, id_matiere), commit=True)

    def modifier_note(self, id_note, nouvelle_valeur, nouveau_coeff):
        """Modifie une note existante (UPDATE)"""
        sql = "UPDATE Notes SET valeur = ?, coefficient = ? WHERE id_note = ?"
        self._executer(sql, (nouvelle_valeur, nouveau_coeff, id_note), commit=True)

    def supprimer_note(self, id_note):
        """Supprime une note (DELETE)"""
        sql = "DELETE FROM Notes WHERE id_note = ?"
        self._executer(sql, (id_note,), commit=True)

    def voir_notes_eleve(self, id_eleve):
        """Voir le détail pour un élève spécifique"""
        sql = '''SELECT Notes.id_note, Matieres.nom_matiere, Notes.valeur, Notes.coefficient, Notes.date_note, Matieres.id_matiere
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere 
                 WHERE id_eleve = ? ORDER BY date_note DESC'''
        return self._executer(sql, (id_eleve,), fetch=True)

    def stats_matiere_classe(self, id_classe, id_matiere):
        """Calcule Moyenne, Min et Max pour une classe"""
        sql = '''SELECT AVG(valeur), MIN(valeur), MAX(valeur) FROM Notes 
                 JOIN Eleves ON Notes.id_eleve = Eleves.id_eleve 
                 WHERE id_classe = ? AND id_matiere = ?'''
        res = self._executer(sql, (id_classe, id_matiere), fetch=True)
        if res and res[0][0] is not None:
            return res[0] # (Moyenne, Min, Max)
        return None

class Eleve(Utilisateur):
    def voir_mes_notes(self):
        sql = '''SELECT Matieres.nom_matiere, Notes.valeur, Notes.coefficient, Notes.date_note 
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere 
                 WHERE id_eleve = ? ORDER BY date_note DESC'''
        return self._executer(sql, (self.id,), fetch=True)

    def calculer_rang(self):
        """Votre algorithme complexe de classement"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # 1. Trouver sa classe
            cur.execute("SELECT id_classe FROM Eleves WHERE id_eleve = ?", (self.id,))
            res = cur.fetchone()
            if not res: return 0, 0, 0
            id_classe = res[0]
            
            # 2. Récupérer tous les élèves de la classe
            cur.execute("SELECT id_eleve FROM Eleves WHERE id_classe = ?", (id_classe,))
            camarades = cur.fetchall()
            
            # 3. Calculer les moyennes de tout le monde
            classement = []
            for (id_comp,) in camarades:
                cur.execute("SELECT SUM(valeur * coefficient), SUM(coefficient) FROM Notes WHERE id_eleve = ?", (id_comp,))
                row = cur.fetchone()
                somme = row[0] if row[0] is not None else 0
                coeffs = row[1] if row[1] is not None else 0
                moy = (somme / coeffs) if coeffs > 0 else 0
                classement.append((id_comp, moy))
        
        # 4. Trier et trouver son rang
        classement.sort(key=lambda x: x[1], reverse=True)
        for i, (id_c, moy) in enumerate(classement):
            if id_c == self.id:
                return i + 1, len(camarades), round(moy, 2)
        return 0, len(camarades), 0

    def generer_bulletin_txt(self):
        """Génère le fichier TXT comme dans votre version CLI"""
        rang, total, moy_gen = self.calculer_rang()
        notes = self.voir_mes_notes()
        
        # Calcul des moyennes par matière pour le bulletin
        dict_matieres = {}
        for nom_mat, val, coef, date in notes:
            if nom_mat not in dict_matieres: dict_matieres[nom_mat] = []
            dict_matieres[nom_mat].append((val, coef))

        nom_fichier = f"bulletin_{self.nom}_{self.prenom}.txt"
        with open(nom_fichier, "w", encoding="utf-8") as f:
            f.write("╔" + "═"*50 + "╗\n")
            f.write(f"║{'BULLETIN TRIMESTRIEL':^50}║\n")
            f.write("╠" + "═"*50 + "╣\n")
            f.write(f"║ Élève : {self.prenom} {self.nom:<31} ║\n")
            f.write("╟" + "─"*50 + "╢\n")
            
            for mat, liste_notes in dict_matieres.items():
                somme = sum([n[0]*n[1] for n in liste_notes])
                somme_coef = sum([n[1] for n in liste_notes])
                moy_mat = somme/somme_coef if somme_coef > 0 else 0
                f.write(f"║ {mat:<25} | Moy: {moy_mat:>5.2f}/20 ║\n")
            
            f.write("╠" + "═"*50 + "╣\n")
            f.write(f"║ MOYENNE GENERALE : {moy_gen:>23.2f}/20 ║\n")
            f.write(f"║ RANG : {str(rang)+'/'+str(total):>35} ║\n")
            f.write("╚" + "═"*50 + "╝\n")
            
        return nom_fichier

# -------------------------------------------------------------------------
# ROUTES FLASK
# -------------------------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        mdp = request.form['mdp']
        
        with sqlite3.connect('pronote.db') as conn:
            cur = conn.cursor()
            # Vérif Prof
            cur.execute("SELECT nom, prenom FROM Professeurs WHERE id_prof=? AND mot_de_passe=?", (user_id, mdp))
            res = cur.fetchone()
            if res:
                session['user'] = {'id': user_id, 'nom': res[0], 'prenom': res[1], 'role': 'PROF'}
                return redirect(url_for('prof_dashboard'))
            
            # Vérif Élève
            cur.execute("SELECT nom, prenom FROM Eleves WHERE id_eleve=? AND mot_de_passe=?", (user_id, mdp))
            res = cur.fetchone()
            if res:
                session['user'] = {'id': user_id, 'nom': res[0], 'prenom': res[1], 'role': 'ELEVE'}
                return redirect(url_for('eleve_dashboard'))
                
        flash("Identifiant ou mot de passe incorrect.")
    return render_template('login.html')

@app.route('/prof', methods=['GET', 'POST'])
def prof_dashboard():
    if 'user' not in session or session['user']['role'] != 'PROF':
        return redirect(url_for('login'))
    
    p = Professeur(session['user']['id'], session['user']['nom'], session['user']['prenom'])
    
    # Gestion de la recherche
    recherche = request.args.get('search')
    if recherche:
        eleves = p.chercher_eleve(recherche)
        classe_active = None
    else:
        # Par défaut on affiche la classe T7 (id 1), T8 (2) ou T9 (3)
        classe_active = request.args.get('classe', '1')
        eleves = p.lister_eleves_par_classe(classe_active)

    # Gestion des Statistiques (POST)
    stats_result = None
    if request.method == 'POST' and 'calculer_stats' in request.form:
        id_c = request.form.get('stat_classe')
        id_m = request.form.get('stat_matiere')
        stats_result = p.stats_matiere_classe(id_c, id_m)

    return render_template('prof.html', eleves=eleves, current_classe=classe_active, stats=stats_result)

@app.route('/prof/gestion/<id_eleve>', methods=['GET', 'POST'])
def prof_gestion_notes(id_eleve):
    if 'user' not in session or session['user']['role'] != 'PROF': return redirect(url_for('login'))
    
    p = Professeur(session['user']['id'], session['user']['nom'], session['user']['prenom'])
    
    # Ajout d'une note
    if request.method == 'POST' and 'ajouter' in request.form:
        p.ajouter_note(id_eleve, request.form['matiere'], float(request.form['note']), float(request.form['coeff']))
        flash("Note ajoutée.")
    
    # Modification d'une note
    if request.method == 'POST' and 'modifier' in request.form:
        p.modifier_note(request.form['id_note'], float(request.form['valeur']), float(request.form['coeff']))
        flash("Note modifiée.")
        
    # Suppression d'une note
    if request.method == 'POST' and 'supprimer' in request.form:
        p.supprimer_note(request.form['id_note'])
        flash("Note supprimée.")

    notes = p.voir_notes_eleve(id_eleve)
    return render_template('prof_gestion.html', notes=notes, id_eleve=id_eleve)

@app.route('/eleve')
def eleve_dashboard():
    if 'user' not in session or session['user']['role'] != 'ELEVE':
        return redirect(url_for('login'))
    
    e = Eleve(session['user']['id'], session['user']['nom'], session['user']['prenom'])
    notes = e.voir_mes_notes()
    rang, total, moy = e.calculer_rang()
    return render_template('eleve.html', notes=notes, stats={'rang': rang, 'total': total, 'moy': moy})

@app.route('/eleve/download')
def eleve_download():
    if 'user' not in session or session['user']['role'] != 'ELEVE': return redirect(url_for('login'))
    e = Eleve(session['user']['id'], session['user']['nom'], session['user']['prenom'])
    path = e.generer_bulletin_txt()
    return send_file(path, as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)