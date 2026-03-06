# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_nsi_2026"

JOURS_SEMAINE = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']

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
        """Récupère les élèves d'une classe spécifique (T7, T8, T9)."""
        sql = "SELECT id_eleve, nom, prenom FROM Eleves WHERE id_classe = ? ORDER BY nom"
        return self._executer(sql, (id_classe,), fetch=True)

    def chercher_eleve(self, nom_partiel):
        """Recherche d'élèves par nom."""
        sql = "SELECT id_eleve, nom, prenom, id_classe FROM Eleves WHERE nom LIKE ?"
        return self._executer(sql, (f"%{nom_partiel}%",), fetch=True)

    def ajouter_note(self, id_eleve, id_matiere, note, coeff):
        """Ajoute une note (CREATE)."""
        date_jour = datetime.now().strftime("%d/%m/%Y")
        sql = "INSERT INTO Notes (valeur, coefficient, date_note, id_eleve, id_matiere) VALUES (?,?,?,?,?)"
        self._executer(sql, (note, coeff, date_jour, id_eleve, id_matiere), commit=True)

    def modifier_note(self, id_note, nouvelle_valeur, nouveau_coeff):
        """Modifie une note existante (UPDATE)."""
        sql = "UPDATE Notes SET valeur = ?, coefficient = ? WHERE id_note = ?"
        self._executer(sql, (nouvelle_valeur, nouveau_coeff, id_note), commit=True)

    def supprimer_note(self, id_note):
        """Supprime une note (DELETE)."""
        sql = "DELETE FROM Notes WHERE id_note = ?"
        self._executer(sql, (id_note,), commit=True)

    def voir_notes_eleve(self, id_eleve):
        """Voir le détail des notes pour un élève spécifique."""
        sql = '''SELECT Notes.id_note, Matieres.nom_matiere, Notes.valeur, Notes.coefficient, Notes.date_note, Matieres.id_matiere
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE id_eleve = ? ORDER BY date_note DESC'''
        return self._executer(sql, (id_eleve,), fetch=True)

    def stats_matiere_classe(self, id_classe, id_matiere):
        """Calcule Moyenne, Min et Max pour une classe."""
        sql = '''SELECT AVG(valeur), MIN(valeur), MAX(valeur) FROM Notes
                 JOIN Eleves ON Notes.id_eleve = Eleves.id_eleve
                 WHERE id_classe = ? AND id_matiere = ?'''
        res = self._executer(sql, (id_classe, id_matiere), fetch=True)
        if res and res[0][0] is not None:
            return res[0]
        return None


class Eleve(Utilisateur):
    def voir_mes_notes(self):
        """Version simple des notes pour les fonctions existantes (bulletin txt)."""
        sql = '''SELECT Matieres.nom_matiere, Notes.valeur, Notes.coefficient, Notes.date_note
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE id_eleve = ? ORDER BY date_note DESC'''
        return self._executer(sql, (self.id,), fetch=True)

    def voir_mes_notes_detaillees(self):
        """Version détaillée des notes pour l'interface web élève."""
        sql = '''SELECT Notes.id_note, Notes.id_matiere, Matieres.nom_matiere,
                        Notes.valeur, Notes.coefficient, Notes.date_note
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE Notes.id_eleve = ?'''
        lignes = self._executer(sql, (self.id,), fetch=True)

        notes_detaillees = []
        for id_note, id_matiere, nom_matiere, valeur, coefficient, date_note in lignes:
            notes_detaillees.append({
                'id_note': id_note,
                'id_matiere': id_matiere,
                'nom_matiere': nom_matiere,
                'valeur': valeur,
                'coefficient': coefficient,
                'date_note': date_note
            })

        notes_detaillees.sort(
            key=lambda note: self.convertir_date_fr_vers_tuple(note['date_note']),
            reverse=True
        )
        return notes_detaillees

    def convertir_date_fr_vers_tuple(self, date_fr):
        """Convertit JJ/MM/AAAA en tuple (AAAA, MM, JJ) pour trier simplement."""
        try:
            jour, mois, annee = date_fr.split('/')
            return (int(annee), int(mois), int(jour))
        except ValueError:
            return (0, 0, 0)

    def calculer_moyenne_ponderee(self, liste_notes):
        """Calcule une moyenne pondérée à partir d'une liste [(note, coeff), ...]."""
        somme_notes = 0
        somme_coefficients = 0

        for valeur, coefficient in liste_notes:
            somme_notes += valeur * coefficient
            somme_coefficients += coefficient

        if somme_coefficients == 0:
            return 0
        return round(somme_notes / somme_coefficients, 2)

    def recuperer_id_classe(self):
        """Retourne l'id de classe de l'élève connecté."""
        sql = "SELECT id_classe FROM Eleves WHERE id_eleve = ?"
        res = self._executer(sql, (self.id,), fetch=True)
        if not res:
            return None
        return res[0][0]

    def note_dans_periode(self, note, periode):
        """Filtre les notes selon le semestre demandé."""
        if periode == 'tout':
            return True

        _, mois, _ = self.convertir_date_fr_vers_tuple(note['date_note'])

        if periode == 's1':
            return mois in [9, 10, 11, 12, 1]
        if periode == 's2':
            return mois in [2, 3, 4, 5, 6, 7]
        return True

    def filtrer_notes(self, notes_detaillees, id_matiere, periode):
        """Applique les filtres matière + période."""
        notes_filtrees = []

        for note in notes_detaillees:
            if id_matiere != 'toutes' and str(note['id_matiere']) != str(id_matiere):
                continue
            if not self.note_dans_periode(note, periode):
                continue
            notes_filtrees.append(note)

        return notes_filtrees

    def construire_notes_par_matiere(self, notes_detaillees):
        """Regroupe les notes par matière (affichage type PRONOTE)."""
        dictionnaire = {}

        for note in notes_detaillees:
            id_matiere = note['id_matiere']
            if id_matiere not in dictionnaire:
                dictionnaire[id_matiere] = {
                    'id_matiere': id_matiere,
                    'nom_matiere': note['nom_matiere'],
                    'notes': [],
                    'moyenne_matiere': 0
                }
            dictionnaire[id_matiere]['notes'].append(note)

        matieres = []
        for matiere in dictionnaire.values():
            notes_pour_moyenne = []
            for note in matiere['notes']:
                notes_pour_moyenne.append((note['valeur'], note['coefficient']))
            matiere['moyenne_matiere'] = self.calculer_moyenne_ponderee(notes_pour_moyenne)
            matieres.append(matiere)

        matieres.sort(key=lambda matiere: matiere['nom_matiere'])
        return matieres

    def lister_matieres_disponibles(self, notes_detaillees):
        """Retourne la liste unique des matières présentes dans les notes."""
        matieres = {}
        for note in notes_detaillees:
            matieres[note['id_matiere']] = note['nom_matiere']

        lignes = []
        for id_matiere, nom_matiere in matieres.items():
            lignes.append({'id_matiere': id_matiere, 'nom_matiere': nom_matiere})

        lignes.sort(key=lambda ligne: ligne['nom_matiere'])
        return lignes

    def construire_infos_detail_note(self, note_selectionnee, id_classe):
        """Prépare le panneau de droite (stats de classe pour la matière choisie)."""
        if note_selectionnee is None or id_classe is None:
            return None

        sql = '''SELECT AVG(Notes.valeur), MIN(Notes.valeur), MAX(Notes.valeur)
                 FROM Notes JOIN Eleves ON Notes.id_eleve = Eleves.id_eleve
                 WHERE Eleves.id_classe = ? AND Notes.id_matiere = ?'''
        res = self._executer(sql, (id_classe, note_selectionnee['id_matiere']), fetch=True)

        moyenne_classe = 0
        note_min = 0
        note_max = 0
        if res and res[0][0] is not None:
            moyenne_classe = round(res[0][0], 2)
            note_min = round(res[0][1], 2)
            note_max = round(res[0][2], 2)

        return {
            'matiere': note_selectionnee['nom_matiere'],
            'date_note': note_selectionnee['date_note'],
            'note_eleve': note_selectionnee['valeur'],
            'coefficient': note_selectionnee['coefficient'],
            'moyenne_classe': moyenne_classe,
            'note_min': note_min,
            'note_max': note_max,
            'mention': self.generer_mention_note(note_selectionnee['valeur'])
        }



    def recuperer_infos_personnelles(self):
        """Récupère les informations de base de l'élève et de sa classe."""
        sql = '''SELECT Eleves.id_eleve, Eleves.nom, Eleves.prenom, Eleves.date_naissance,
                        Classes.id_classe, Classes.nom_classe
                 FROM Eleves JOIN Classes ON Eleves.id_classe = Classes.id_classe
                 WHERE Eleves.id_eleve = ?'''
        res = self._executer(sql, (self.id,), fetch=True)
        if not res:
            return None

        ligne = res[0]
        return {
            'id_eleve': ligne[0],
            'nom': ligne[1],
            'prenom': ligne[2],
            'date_naissance': ligne[3],
            'id_classe': ligne[4],
            'nom_classe': ligne[5]
        }

    def calculer_resultats_par_matiere(self):
        """Calcule la moyenne de l'élève matière par matière."""
        sql = '''SELECT Matieres.id_matiere, Matieres.nom_matiere,
                        SUM(Notes.valeur * Notes.coefficient), SUM(Notes.coefficient), COUNT(Notes.id_note)
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE Notes.id_eleve = ?
                 GROUP BY Matieres.id_matiere, Matieres.nom_matiere
                 ORDER BY Matieres.nom_matiere'''
        lignes = self._executer(sql, (self.id,), fetch=True)

        resultats = []
        for id_matiere, nom_matiere, somme_notes, somme_coef, nb_notes in lignes:
            moyenne = round(somme_notes / somme_coef, 2) if somme_coef else 0
            resultats.append({
                'id_matiere': id_matiere,
                'nom_matiere': nom_matiere,
                'moyenne': moyenne,
                'nb_notes': nb_notes
            })
        return resultats

    def construire_cahier_de_texte(self):
        """Construit un cahier de texte simple à partir des dernières évaluations."""
        sql = '''SELECT Notes.date_note, Matieres.nom_matiere, Notes.valeur, Notes.coefficient
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE Notes.id_eleve = ?
                 ORDER BY Notes.id_note DESC LIMIT 20'''
        lignes = self._executer(sql, (self.id,), fetch=True)

        entries = []
        for date_note, nom_matiere, valeur, coefficient in lignes:
            entries.append({
                'date_note': date_note,
                'nom_matiere': nom_matiere,
                'description': f"Réviser le chapitre lié à la note {valeur}/20 (coef {coefficient})."
            })
        return entries

    def table_emploi_du_temps_disponible(self):
        """Vérifie si la table EmploiDuTemps existe dans la base."""
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='EmploiDuTemps'"
        res = self._executer(sql, fetch=True)
        return bool(res)

    def recuperer_emploi_du_temps(self):
        """Retourne l'emploi du temps de la classe de l'élève."""
        id_classe = self.recuperer_id_classe()
        if id_classe is None:
            return []

        sql = '''SELECT EmploiDuTemps.jour_semaine, EmploiDuTemps.heure_debut, EmploiDuTemps.heure_fin,
                        Matieres.nom_matiere, Professeurs.prenom, Professeurs.nom, EmploiDuTemps.salle
                 FROM EmploiDuTemps
                 JOIN Matieres ON EmploiDuTemps.id_matiere = Matieres.id_matiere
                 JOIN Professeurs ON EmploiDuTemps.id_prof = Professeurs.id_prof
                 WHERE EmploiDuTemps.id_classe = ?
                 ORDER BY CASE EmploiDuTemps.jour_semaine
                    WHEN 'Lundi' THEN 1
                    WHEN 'Mardi' THEN 2
                    WHEN 'Mercredi' THEN 3
                    WHEN 'Jeudi' THEN 4
                    WHEN 'Vendredi' THEN 5
                    ELSE 6 END,
                    EmploiDuTemps.heure_debut'''

        try:
            lignes = self._executer(sql, (id_classe,), fetch=True)
        except sqlite3.OperationalError:
            return []

        edt = []
        for jour, h_debut, h_fin, matiere, prenom_prof, nom_prof, salle in lignes:
            edt.append({
                'jour': jour,
                'heure_debut': h_debut,
                'heure_fin': h_fin,
                'matiere': matiere,
                'prof': f"{prenom_prof} {nom_prof}",
                'salle': salle
            })
        return edt

    def generer_mention_note(self, note_sur_20):
        """Donne une mention courte pour aider l'élève à se situer."""
        if note_sur_20 >= 16:
            return 'Excellent travail, continue !'
        if note_sur_20 >= 14:
            return 'Très bon niveau.'
        if note_sur_20 >= 12:
            return 'Bon travail, encore un petit effort.'
        if note_sur_20 >= 10:
            return 'Niveau correct, tu peux viser plus haut.'
        return 'Ne lâche pas, une révision régulière va aider.'

    def construire_emploi_par_jour(self, emploi):
        """Regroupe les cours par jour pour simplifier l'affichage HTML."""
        emploi_par_jour = {jour: [] for jour in JOURS_SEMAINE}
        for cours in emploi:
            if cours['jour'] in emploi_par_jour:
                emploi_par_jour[cours['jour']].append(cours)
        return emploi_par_jour

    def calculer_rang(self):
        """Algorithme simple de classement dans la classe."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute("SELECT id_classe FROM Eleves WHERE id_eleve = ?", (self.id,))
            res = cur.fetchone()
            if not res:
                return 0, 0, 0
            id_classe = res[0]

            cur.execute("SELECT id_eleve FROM Eleves WHERE id_classe = ?", (id_classe,))
            camarades = cur.fetchall()

            classement = []
            for (id_comp,) in camarades:
                cur.execute(
                    "SELECT SUM(valeur * coefficient), SUM(coefficient) FROM Notes WHERE id_eleve = ?",
                    (id_comp,)
                )
                row = cur.fetchone()
                somme = row[0] if row[0] is not None else 0
                coeffs = row[1] if row[1] is not None else 0
                moyenne = (somme / coeffs) if coeffs > 0 else 0
                classement.append((id_comp, moyenne))

        classement.sort(key=lambda ligne: ligne[1], reverse=True)
        for i, (id_c, moyenne) in enumerate(classement):
            if id_c == self.id:
                return i + 1, len(camarades), round(moyenne, 2)

        return 0, len(camarades), 0

    def generer_bulletin_txt(self):
        """Génère un bulletin texte simple à télécharger."""
        rang, total, moyenne_generale = self.calculer_rang()
        notes = self.voir_mes_notes()

        notes_par_matiere = {}
        for nom_mat, val, coef, _ in notes:
            if nom_mat not in notes_par_matiere:
                notes_par_matiere[nom_mat] = []
            notes_par_matiere[nom_mat].append((val, coef))

        nom_fichier = f"bulletin_{self.nom}_{self.prenom}.txt"
        with open(nom_fichier, "w", encoding="utf-8") as fichier:
            fichier.write("╔" + "═" * 50 + "╗\n")
            fichier.write(f"║{'BULLETIN TRIMESTRIEL':^50}║\n")
            fichier.write("╠" + "═" * 50 + "╣\n")
            fichier.write(f"║ Élève : {self.prenom} {self.nom:<31} ║\n")
            fichier.write("╟" + "─" * 50 + "╢\n")

            for matiere, liste_notes in notes_par_matiere.items():
                somme = sum([note[0] * note[1] for note in liste_notes])
                somme_coef = sum([note[1] for note in liste_notes])
                moyenne_matiere = somme / somme_coef if somme_coef > 0 else 0
                fichier.write(f"║ {matiere:<25} | Moy: {moyenne_matiere:>5.2f}/20 ║\n")

            fichier.write("╠" + "═" * 50 + "╣\n")
            fichier.write(f"║ MOYENNE GENERALE : {moyenne_generale:>23.2f}/20 ║\n")
            fichier.write(f"║ RANG : {str(rang) + '/' + str(total):>35} ║\n")
            fichier.write("╚" + "═" * 50 + "╝\n")

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

            cur.execute("SELECT nom, prenom FROM Professeurs WHERE id_prof=? AND mot_de_passe=?", (user_id, mdp))
            res_prof = cur.fetchone()
            if res_prof:
                session['user'] = {'id': user_id, 'nom': res_prof[0], 'prenom': res_prof[1], 'role': 'PROF'}
                return redirect(url_for('prof_dashboard'))

            cur.execute("SELECT nom, prenom FROM Eleves WHERE id_eleve=? AND mot_de_passe=?", (user_id, mdp))
            res_eleve = cur.fetchone()
            if res_eleve:
                session['user'] = {'id': user_id, 'nom': res_eleve[0], 'prenom': res_eleve[1], 'role': 'ELEVE'}
                return redirect(url_for('eleve_dashboard'))

        flash("Identifiant ou mot de passe incorrect.")
    return render_template('login.html')


@app.route('/prof', methods=['GET', 'POST'])
def prof_dashboard():
    if 'user' not in session or session['user']['role'] != 'PROF':
        return redirect(url_for('login'))

    p = Professeur(session['user']['id'], session['user']['nom'], session['user']['prenom'])

    recherche = request.args.get('search')
    if recherche:
        eleves = p.chercher_eleve(recherche)
        classe_active = None
    else:
        classe_active = request.args.get('classe', '1')
        eleves = p.lister_eleves_par_classe(classe_active)

    stats_result = None
    if request.method == 'POST' and 'calculer_stats' in request.form:
        id_c = request.form.get('stat_classe')
        id_m = request.form.get('stat_matiere')
        stats_result = p.stats_matiere_classe(id_c, id_m)

    return render_template('prof.html', eleves=eleves, current_classe=classe_active, stats=stats_result)


@app.route('/prof/gestion/<id_eleve>', methods=['GET', 'POST'])
def prof_gestion_notes(id_eleve):
    if 'user' not in session or session['user']['role'] != 'PROF':
        return redirect(url_for('login'))

    p = Professeur(session['user']['id'], session['user']['nom'], session['user']['prenom'])

    if request.method == 'POST' and 'ajouter' in request.form:
        p.ajouter_note(id_eleve, request.form['matiere'], float(request.form['note']), float(request.form['coeff']))
        flash("Note ajoutée.")

    if request.method == 'POST' and 'modifier' in request.form:
        p.modifier_note(request.form['id_note'], float(request.form['valeur']), float(request.form['coeff']))
        flash("Note modifiée.")

    if request.method == 'POST' and 'supprimer' in request.form:
        p.supprimer_note(request.form['id_note'])
        flash("Note supprimée.")

    notes = p.voir_notes_eleve(id_eleve)
    return render_template('prof_gestion.html', notes=notes, id_eleve=id_eleve)


@app.route('/eleve')
def eleve_dashboard():
    if 'user' not in session or session['user']['role'] != 'ELEVE':
        return redirect(url_for('login'))

    eleve = Eleve(session['user']['id'], session['user']['nom'], session['user']['prenom'])

    tri_actif = request.args.get('tri', 'matiere')
    periode_active = request.args.get('periode', 'tout')
    id_matiere_active = request.args.get('matiere', 'toutes')

    notes_detaillees = eleve.voir_mes_notes_detaillees()
    notes_filtrees = eleve.filtrer_notes(notes_detaillees, id_matiere_active, periode_active)

    if tri_actif == 'matiere':
        notes_affichage = eleve.construire_notes_par_matiere(notes_filtrees)
    else:
        notes_affichage = notes_filtrees

    note_selectionnee = None
    id_note_selectionnee = request.args.get('note')
    if id_note_selectionnee:
        for note in notes_filtrees:
            if str(note['id_note']) == id_note_selectionnee:
                note_selectionnee = note
                break

    if note_selectionnee is None and notes_filtrees:
        note_selectionnee = notes_filtrees[0]

    id_classe = eleve.recuperer_id_classe()
    detail_note = eleve.construire_infos_detail_note(note_selectionnee, id_classe)

    matieres_disponibles = eleve.lister_matieres_disponibles(notes_detaillees)

    rang, total, moyenne_generale = eleve.calculer_rang()

    return rendre_page_eleve(
        'eleve.html',
        'notes',
        tri_actif=tri_actif,
        periode_active=periode_active,
        id_matiere_active=id_matiere_active,
        matieres_disponibles=matieres_disponibles,
        notes_affichage=notes_affichage,
        notes_filtrees=notes_filtrees,
        note_selectionnee=note_selectionnee,
        detail_note=detail_note,
        stats={'rang': rang, 'total': total, 'moy': moyenne_generale}
    )


@app.route('/eleve/download')
def eleve_download():
    if 'user' not in session or session['user']['role'] != 'ELEVE':
        return redirect(url_for('login'))

    eleve = Eleve(session['user']['id'], session['user']['nom'], session['user']['prenom'])
    path = eleve.generer_bulletin_txt()
    return send_file(path, as_attachment=True)


def verifier_session_eleve():
    """Vérifie qu'un élève est connecté avant d'ouvrir ses pages."""
    if 'user' not in session:
        return False
    return session['user'].get('role') == 'ELEVE'


def recuperer_eleve_connecte():
    """Crée l'objet Eleve à partir de la session."""
    return Eleve(session['user']['id'], session['user']['nom'], session['user']['prenom'])


def rendre_page_eleve(template, onglet_actif, **contexte):
    """Ajoute les infos de navigation communes à toutes les pages élève."""
    return render_template(template, onglet_actif=onglet_actif, **contexte)


@app.route('/eleve/mes-donnees')
def eleve_mes_donnees():
    if not verifier_session_eleve():
        return redirect(url_for('login'))

    eleve = recuperer_eleve_connecte()
    infos = eleve.recuperer_infos_personnelles()
    return rendre_page_eleve('mes_donnees.html', 'mes_donnees', infos=infos)


@app.route('/eleve/cahier-de-texte')
def eleve_cahier_de_texte():
    if not verifier_session_eleve():
        return redirect(url_for('login'))

    eleve = recuperer_eleve_connecte()
    cahier = eleve.construire_cahier_de_texte()
    return rendre_page_eleve('cahier_texte.html', 'cahier_texte', cahier=cahier)


@app.route('/eleve/resultats')
def eleve_resultats():
    if not verifier_session_eleve():
        return redirect(url_for('login'))

    eleve = recuperer_eleve_connecte()
    resultats = eleve.calculer_resultats_par_matiere()
    rang, total, moyenne = eleve.calculer_rang()
    return rendre_page_eleve('resultats.html', 'resultats', resultats=resultats, stats={'rang': rang, 'total': total, 'moy': moyenne})


@app.route('/eleve/vie-scolaire')
def eleve_vie_scolaire():
    if not verifier_session_eleve():
        return redirect(url_for('login'))

    eleve = recuperer_eleve_connecte()
    infos = eleve.recuperer_infos_personnelles()
    table_emploi_disponible = eleve.table_emploi_du_temps_disponible()
    emploi = eleve.recuperer_emploi_du_temps()

    nb_cours_semaine = len(emploi)
    matieres_differentes = len(set(c['matiere'] for c in emploi)) if emploi else 0

    return rendre_page_eleve(
        'vie_scolaire.html',
        'vie_scolaire',
        infos=infos,
        nb_cours_semaine=nb_cours_semaine,
        matieres_differentes=matieres_differentes,
        table_emploi_disponible=table_emploi_disponible
    )


@app.route('/eleve/emploi-du-temps')
def eleve_emploi_du_temps():
    if not verifier_session_eleve():
        return redirect(url_for('login'))

    eleve = recuperer_eleve_connecte()
    table_emploi_disponible = eleve.table_emploi_du_temps_disponible()
    emploi = eleve.recuperer_emploi_du_temps()

    emploi_par_jour = eleve.construire_emploi_par_jour(emploi)

    return rendre_page_eleve(
        'emploi_du_temps.html',
        'emploi_du_temps',
        emploi_par_jour=emploi_par_jour,
        table_emploi_disponible=table_emploi_disponible,
        jours_semaine=JOURS_SEMAINE
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)