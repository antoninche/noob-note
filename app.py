# -*- coding: utf-8 -*-
"""NOOB-NOTE : mini-PRONOTE en Flask + SQLite
Organisation du fichier :
1. Configuration + outils communs (couleurs, dates, accès base, décorateur)
2. Classes métier : Utilisateur -> Professeur / Eleve
3. Routes Flask (connexion, espace prof, espace élève)
"""

import iov
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_file)
from werkzeug.security import check_password_hash

app = Flask(__name__)
# La clé secrète vient d'une variable d'environnement en production (sinon valeur de dev).
app.secret_key = os.environ.get("SECRET_KEY", "cle_dev_nsi_2026")

DB_PATH = "pronote.db"
JOURS_SEMAINE = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']

# Couleur associée à chaque matière (comme dans PRONOTE).
# 'bord' = couleur forte (trait / pastille), 'fond' = version claire pour le fond.
COULEURS_MATIERES = {
    'Maths':    {'bord': '#3b7ddd', 'fond': '#e8f0fd'},
    'NSI':      {'bord': '#7c4dff', 'fond': '#efe9ff'},
    'EPS':      {'bord': '#2fa86a', 'fond': '#e4f6ec'},
    'Français': {'bord': '#e0567a', 'fond': '#fce8ee'},
    'Physique': {'bord': '#e8843c', 'fond': '#fdefe2'},
    'Histoire': {'bord': '#b07d3b', 'fond': '#f6efe0'},
}
COULEUR_MATIERE_DEFAUT = {'bord': '#0b8d83', 'fond': '#e2f4f2'}


def couleur_matiere(nom_matiere):
    """Retourne la couleur PRONOTE d'une matière (ou une couleur par défaut)."""
    return COULEURS_MATIERES.get(nom_matiere, COULEUR_MATIERE_DEFAUT)


@app.context_processor
def injecter_outils():
    """Rend couleur_matiere() et le jour du jour utilisables dans tous les templates."""
    return {
        'couleur_matiere': couleur_matiere,
        'jour_aujourdhui': JOURS_SEMAINE[datetime.now().weekday()] if datetime.now().weekday() < 5 else None,
    }


# -------------------------------------------------------------------------
# OUTILS COMMUNS (accès base + dates)
# -------------------------------------------------------------------------

def executer_sql(sql, params=(), fetch=False, commit=False):
    """Point d'entrée unique vers la base : ouvre, exécute, renvoie ou valide."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        if commit:
            conn.commit()
        return cur.fetchall() if fetch else None


def date_fr_vers_tuple(date_fr):
    """Convertit JJ/MM/AAAA en tuple (AAAA, MM, JJ) pour comparer/trier facilement."""
    try:
        jour, mois, annee = date_fr.split('/')
        return (int(annee), int(mois), int(jour))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def date_dans_periode(date_note, date_debut, date_fin):
    """Vrai si date_note (JJ/MM/AAAA) est comprise dans [date_debut, date_fin]."""
    jour = date_fr_vers_tuple(date_note)
    return date_fr_vers_tuple(date_debut) <= jour <= date_fr_vers_tuple(date_fin)


def construire_grille_edt(emploi):
    """Construit une grille hebdomadaire (heures en lignes, jours en colonnes).

    Chaque ligne contient l'heure et une case par jour : le cours du créneau
    (un dictionnaire) ou None s'il n'y a pas cours à cette heure-là.
    """
    cours_par_creneau = {}
    for cours in emploi:
        cours_par_creneau[(cours['jour'], cours['heure_debut'])] = cours

    grille = []
    for heure in range(8, 18):
        heure_debut = f"{heure:02d}:00"
        heure_fin = f"{heure + 1:02d}:00"
        cellules = [cours_par_creneau.get((jour, heure_debut)) for jour in JOURS_SEMAINE]
        grille.append({'heure_debut': heure_debut, 'heure_fin': heure_fin, 'cellules': cellules})
    return grille


def login_requis(role=None):
    """Décorateur : exige une connexion, et éventuellement un rôle précis ('PROF' ou 'ELEVE')."""
    def decorateur(fonction):
        @wraps(fonction)
        def enveloppe(*args, **kwargs):
            utilisateur = session.get('user')
            if not utilisateur or (role and utilisateur['role'] != role):
                return redirect(url_for('login'))
            return fonction(*args, **kwargs)
        return enveloppe
    return decorateur


# -------------------------------------------------------------------------
# CLASSES METIER
# -------------------------------------------------------------------------

class Utilisateur:
    def __init__(self, id_u, nom, prenom):
        self.id = id_u
        self.nom = nom
        self.prenom = prenom

    def _executer(self, sql, params=(), fetch=False, commit=False):
        return executer_sql(sql, params, fetch=fetch, commit=commit)


class Professeur(Utilisateur):
    def lister_classes(self):
        """Toutes les classes (pour construire les onglets et les menus déroulants)."""
        sql = "SELECT id_classe, nom_classe FROM Classes ORDER BY id_classe"
        return self._executer(sql, fetch=True)

    def lister_matieres(self):
        """Toutes les matières (pour les menus déroulants)."""
        sql = "SELECT id_matiere, nom_matiere FROM Matieres ORDER BY nom_matiere"
        return self._executer(sql, fetch=True)

    def lister_eleves_par_classe(self, id_classe):
        sql = "SELECT id_eleve, nom, prenom FROM Eleves WHERE id_classe = ? ORDER BY nom"
        return self._executer(sql, (id_classe,), fetch=True)

    def chercher_eleve(self, nom_partiel):
        sql = "SELECT id_eleve, nom, prenom, id_classe FROM Eleves WHERE nom LIKE ? ORDER BY nom"
        return self._executer(sql, (f"%{nom_partiel}%",), fetch=True)

    def ajouter_note(self, id_eleve, id_matiere, note, coeff):
        date_jour = datetime.now().strftime("%d/%m/%Y")
        sql = "INSERT INTO Notes (valeur, coefficient, date_note, id_eleve, id_matiere) VALUES (?,?,?,?,?)"
        self._executer(sql, (note, coeff, date_jour, id_eleve, id_matiere), commit=True)

    def modifier_note(self, id_note, nouvelle_valeur, nouveau_coeff):
        sql = "UPDATE Notes SET valeur = ?, coefficient = ? WHERE id_note = ?"
        self._executer(sql, (nouvelle_valeur, nouveau_coeff, id_note), commit=True)

    def supprimer_note(self, id_note):
        sql = "DELETE FROM Notes WHERE id_note = ?"
        self._executer(sql, (id_note,), commit=True)

    def voir_notes_eleve(self, id_eleve):
        sql = '''SELECT Notes.id_note, Matieres.nom_matiere, Notes.valeur, Notes.coefficient,
                        Notes.date_note, Matieres.id_matiere
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE id_eleve = ? ORDER BY date_note DESC'''
        return self._executer(sql, (id_eleve,), fetch=True)

    def stats_matiere_classe(self, id_classe, id_matiere):
        sql = '''SELECT AVG(valeur), MIN(valeur), MAX(valeur) FROM Notes
                 JOIN Eleves ON Notes.id_eleve = Eleves.id_eleve
                 WHERE id_classe = ? AND id_matiere = ?'''
        res = self._executer(sql, (id_classe, id_matiere), fetch=True)
        if res and res[0][0] is not None:
            return res[0]
        return None

    # --- Cahier de textes (devoirs) ---

    def ajouter_devoir(self, id_classe, id_matiere, date_pour, description):
        date_donne = datetime.now().strftime("%d/%m/%Y")
        sql = '''INSERT INTO Devoirs (id_classe, id_matiere, id_prof, date_donne, date_pour, description)
                 VALUES (?, ?, ?, ?, ?, ?)'''
        self._executer(sql, (id_classe, id_matiere, self.id, date_donne, date_pour, description), commit=True)

    def lister_mes_devoirs(self):
        sql = '''SELECT Classes.nom_classe, Matieres.nom_matiere,
                        Devoirs.date_pour, Devoirs.description
                 FROM Devoirs
                 JOIN Classes ON Devoirs.id_classe = Classes.id_classe
                 JOIN Matieres ON Devoirs.id_matiere = Matieres.id_matiere
                 WHERE Devoirs.id_prof = ?
                 ORDER BY Devoirs.id_devoir DESC LIMIT 40'''
        lignes = self._executer(sql, (self.id,), fetch=True)
        return [{'classe': c, 'matiere': m, 'date_pour': d, 'description': desc}
                for c, m, d, desc in lignes]

    # --- Vie scolaire ---

    def ajouter_evenement(self, id_eleve, type_evenement, date_evenement, motif, justifie):
        sql = '''INSERT INTO VieScolaire (id_eleve, type_evenement, date_evenement, motif, justifie)
                 VALUES (?, ?, ?, ?, ?)'''
        self._executer(sql, (id_eleve, type_evenement, date_evenement, motif, justifie), commit=True)

    def lister_evenements_recents(self):
        sql = '''SELECT Eleves.id_eleve, Eleves.nom, Eleves.prenom,
                        VieScolaire.type_evenement, VieScolaire.date_evenement,
                        VieScolaire.motif, VieScolaire.justifie
                 FROM VieScolaire JOIN Eleves ON VieScolaire.id_eleve = Eleves.id_eleve
                 ORDER BY VieScolaire.id_evenement DESC LIMIT 30'''
        lignes = self._executer(sql, fetch=True)
        return [{'id_eleve': i, 'nom': n, 'prenom': p, 'type': t,
                 'date': d, 'motif': mo, 'justifie': ju}
                for i, n, p, t, d, mo, ju in lignes]

    # --- Emploi du temps du prof ---

    def recuperer_mon_emploi(self):
        sql = '''SELECT EmploiDuTemps.jour_semaine, EmploiDuTemps.heure_debut, EmploiDuTemps.heure_fin,
                        Matieres.nom_matiere, Classes.nom_classe, EmploiDuTemps.salle
                 FROM EmploiDuTemps
                 JOIN Matieres ON EmploiDuTemps.id_matiere = Matieres.id_matiere
                 JOIN Classes ON EmploiDuTemps.id_classe = Classes.id_classe
                 WHERE EmploiDuTemps.id_prof = ?'''
        lignes = self._executer(sql, (self.id,), fetch=True)
        return [{'jour': j, 'heure_debut': hd, 'heure_fin': hf,
                 'matiere': m, 'classe': c, 'salle': s}
                for j, hd, hf, m, c, s in lignes]


class Eleve(Utilisateur):
    def voir_mes_notes(self):
        """Notes simples (utilisé pour le bulletin .txt)."""
        sql = '''SELECT Matieres.nom_matiere, Notes.valeur, Notes.coefficient, Notes.date_note
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE id_eleve = ? ORDER BY date_note DESC'''
        return self._executer(sql, (self.id,), fetch=True)

    def voir_mes_notes_detaillees(self):
        """Notes détaillées (dictionnaires) pour l'interface web, triées par date décroissante."""
        sql = '''SELECT Notes.id_note, Notes.id_matiere, Matieres.nom_matiere,
                        Notes.valeur, Notes.coefficient, Notes.date_note
                 FROM Notes JOIN Matieres ON Notes.id_matiere = Matieres.id_matiere
                 WHERE Notes.id_eleve = ?'''
        lignes = self._executer(sql, (self.id,), fetch=True)

        notes = [{'id_note': i, 'id_matiere': im, 'nom_matiere': nm,
                  'valeur': v, 'coefficient': c, 'date_note': d}
                 for i, im, nm, v, c, d in lignes]
        notes.sort(key=lambda note: date_fr_vers_tuple(note['date_note']), reverse=True)
        return notes

    def calculer_moyenne_ponderee(self, liste_notes):
        """Moyenne pondérée à partir d'une liste [(valeur, coefficient), ...]."""
        somme_notes = 0
        somme_coefficients = 0
        for valeur, coefficient in liste_notes:
            somme_notes += valeur * coefficient
            somme_coefficients += coefficient
        if somme_coefficients == 0:
            return 0
        return round(somme_notes / somme_coefficients, 2)

    def recuperer_id_classe(self):
        sql = "SELECT id_classe FROM Eleves WHERE id_eleve = ?"
        res = self._executer(sql, (self.id,), fetch=True)
        return res[0][0] if res else None

    # --- Périodes ---

    def lister_periodes(self):
        sql = "SELECT id_periode, nom, date_debut, date_fin FROM Periodes ORDER BY id_periode"
        lignes = self._executer(sql, fetch=True)
        return [{'id_periode': i, 'nom': n, 'date_debut': dd, 'date_fin': df}
                for i, n, dd, df in lignes]

    def trouver_periode(self, periodes, id_periode):
        """Retrouve le dictionnaire d'une période à partir de son identifiant (str)."""
        for periode in periodes:
            if str(periode['id_periode']) == str(id_periode):
                return periode
        return None

    def note_dans_periode(self, note, periode):
        """Vrai si la note appartient à la période choisie (None = toute l'année)."""
        if periode is None:
            return True
        return date_dans_periode(note['date_note'], periode['date_debut'], periode['date_fin'])

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
                dictionnaire[id_matiere] = {'id_matiere': id_matiere,
                                            'nom_matiere': note['nom_matiere'],
                                            'notes': [], 'moyenne_matiere': 0}
            dictionnaire[id_matiere]['notes'].append(note)

        matieres = []
        for matiere in dictionnaire.values():
            couples = [(n['valeur'], n['coefficient']) for n in matiere['notes']]
            matiere['moyenne_matiere'] = self.calculer_moyenne_ponderee(couples)
            matieres.append(matiere)

        matieres.sort(key=lambda m: m['nom_matiere'])
        return matieres

    def lister_matieres_disponibles(self, notes_detaillees):
        """Liste unique des matières présentes dans les notes."""
        matieres = {}
        for note in notes_detaillees:
            matieres[note['id_matiere']] = note['nom_matiere']
        lignes = [{'id_matiere': i, 'nom_matiere': n} for i, n in matieres.items()]
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

        moyenne_classe = note_min = note_max = 0
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
        sql = '''SELECT Eleves.id_eleve, Eleves.nom, Eleves.prenom, Eleves.date_naissance,
                        Classes.id_classe, Classes.nom_classe
                 FROM Eleves JOIN Classes ON Eleves.id_classe = Classes.id_classe
                 WHERE Eleves.id_eleve = ?'''
        res = self._executer(sql, (self.id,), fetch=True)
        if not res:
            return None
        ligne = res[0]
        return {'id_eleve': ligne[0], 'nom': ligne[1], 'prenom': ligne[2],
                'date_naissance': ligne[3], 'id_classe': ligne[4], 'nom_classe': ligne[5]}

    def calculer_resultats_par_matiere(self):
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
            resultats.append({'id_matiere': id_matiere, 'nom_matiere': nom_matiere,
                              'moyenne': moyenne, 'nb_notes': nb_notes})
        return resultats

    def calculer_moyennes_par_periode(self, periodes):
        """Moyenne générale de l'élève pour chaque trimestre."""
        notes = self.voir_mes_notes_detaillees()
        resultats = []
        for periode in periodes:
            couples = [(n['valeur'], n['coefficient']) for n in notes
                       if self.note_dans_periode(n, periode)]
            resultats.append({'nom': periode['nom'],
                              'moyenne': self.calculer_moyenne_ponderee(couples),
                              'nb_notes': len(couples)})
        return resultats

    # --- Cahier de textes (devoirs de la classe) ---

    def recuperer_devoirs(self):
        id_classe = self.recuperer_id_classe()
        if id_classe is None:
            return []

        sql = '''SELECT Devoirs.date_donne, Devoirs.date_pour, Matieres.nom_matiere, Devoirs.description
                 FROM Devoirs JOIN Matieres ON Devoirs.id_matiere = Matieres.id_matiere
                 WHERE Devoirs.id_classe = ?'''
        lignes = self._executer(sql, (id_classe,), fetch=True)

        aujourdhui = date_fr_vers_tuple(datetime.now().strftime("%d/%m/%Y"))
        devoirs = []
        for date_donne, date_pour, nom_matiere, description in lignes:
            devoirs.append({'date_donne': date_donne, 'date_pour': date_pour,
                            'nom_matiere': nom_matiere, 'description': description,
                            'a_venir': date_fr_vers_tuple(date_pour) >= aujourdhui})
        devoirs.sort(key=lambda d: date_fr_vers_tuple(d['date_pour']))
        return devoirs

    # --- Vie scolaire ---

    def recuperer_vie_scolaire(self):
        sql = '''SELECT type_evenement, date_evenement, motif, justifie
                 FROM VieScolaire WHERE id_eleve = ?'''
        lignes = self._executer(sql, (self.id,), fetch=True)
        evenements = [{'type': t, 'date': d, 'motif': m, 'justifie': j}
                      for t, d, m, j in lignes]
        evenements.sort(key=lambda e: date_fr_vers_tuple(e['date']), reverse=True)
        return evenements

    def resume_vie_scolaire(self, evenements):
        """Compte les absences, retards et observations."""
        return {
            'absences': sum(1 for e in evenements if e['type'] == 'Absence'),
            'retards': sum(1 for e in evenements if e['type'] == 'Retard'),
            'observations': sum(1 for e in evenements if e['type'] == 'Observation'),
            'non_justifies': sum(1 for e in evenements if not e['justifie']),
        }

    # --- Emploi du temps ---

    def recuperer_emploi_du_temps(self):
        id_classe = self.recuperer_id_classe()
        if id_classe is None:
            return []

        sql = '''SELECT EmploiDuTemps.jour_semaine, EmploiDuTemps.heure_debut, EmploiDuTemps.heure_fin,
                        Matieres.nom_matiere, Professeurs.prenom, Professeurs.nom, EmploiDuTemps.salle
                 FROM EmploiDuTemps
                 JOIN Matieres ON EmploiDuTemps.id_matiere = Matieres.id_matiere
                 JOIN Professeurs ON EmploiDuTemps.id_prof = Professeurs.id_prof
                 WHERE EmploiDuTemps.id_classe = ?'''
        lignes = self._executer(sql, (id_classe,), fetch=True)
        return [{'jour': j, 'heure_debut': hd, 'heure_fin': hf,
                 'matiere': m, 'prof': f"{pp} {pn}", 'salle': s}
                for j, hd, hf, m, pp, pn, s in lignes]

    def generer_mention_note(self, note_sur_20):
        if note_sur_20 >= 16:
            return 'Excellent travail, continue !'
        if note_sur_20 >= 14:
            return 'Très bon niveau.'
        if note_sur_20 >= 12:
            return 'Bon travail, encore un petit effort.'
        if note_sur_20 >= 10:
            return 'Niveau correct, tu peux viser plus haut.'
        return 'Ne lâche pas, une révision régulière va aider.'

    def calculer_rang(self):
        """Classement simple de l'élève dans sa classe (par moyenne générale)."""
        id_classe = self.recuperer_id_classe()
        if id_classe is None:
            return 0, 0, 0

        sql = '''SELECT Eleves.id_eleve, SUM(Notes.valeur * Notes.coefficient), SUM(Notes.coefficient)
                 FROM Eleves LEFT JOIN Notes ON Eleves.id_eleve = Notes.id_eleve
                 WHERE Eleves.id_classe = ?
                 GROUP BY Eleves.id_eleve'''
        lignes = self._executer(sql, (id_classe,), fetch=True)

        classement = []
        for id_comp, somme, coeffs in lignes:
            moyenne = (somme / coeffs) if coeffs else 0
            classement.append((id_comp, moyenne))

        classement.sort(key=lambda ligne: ligne[1], reverse=True)
        for position, (id_comp, moyenne) in enumerate(classement):
            if id_comp == self.id:
                return position + 1, len(classement), round(moyenne, 2)
        return 0, len(classement), 0

    def generer_bulletin_txt(self):
        """Génère le bulletin en mémoire et renvoie (fichier, nom_fichier)."""
        rang, total, moyenne_generale = self.calculer_rang()
        notes = self.voir_mes_notes()

        notes_par_matiere = {}
        for nom_mat, val, coef, _ in notes:
            notes_par_matiere.setdefault(nom_mat, []).append((val, coef))

        texte = io.StringIO()
        texte.write("╔" + "═" * 50 + "╗\n")
        texte.write(f"║{'BULLETIN TRIMESTRIEL':^50}║\n")
        texte.write("╠" + "═" * 50 + "╣\n")
        texte.write(f"║ Élève : {self.prenom} {self.nom:<31} ║\n")
        texte.write("╟" + "─" * 50 + "╢\n")
        for matiere, liste_notes in notes_par_matiere.items():
            somme = sum(note[0] * note[1] for note in liste_notes)
            somme_coef = sum(note[1] for note in liste_notes)
            moyenne_matiere = somme / somme_coef if somme_coef > 0 else 0
            texte.write(f"║ {matiere:<25} | Moy: {moyenne_matiere:>5.2f}/20 ║\n")
        texte.write("╠" + "═" * 50 + "╣\n")
        texte.write(f"║ MOYENNE GENERALE : {moyenne_generale:>23.2f}/20 ║\n")
        texte.write(f"║ RANG : {str(rang) + '/' + str(total):>35} ║\n")
        texte.write("╚" + "═" * 50 + "╝\n")

        fichier = io.BytesIO(texte.getvalue().encode('utf-8'))
        return fichier, f"bulletin_{self.nom}_{self.prenom}.txt"


# -------------------------------------------------------------------------
# AIDES DE SESSION
# -------------------------------------------------------------------------

def prof_connecte():
    u = session['user']
    return Professeur(u['id'], u['nom'], u['prenom'])


def eleve_connecte():
    u = session['user']
    return Eleve(u['id'], u['nom'], u['prenom'])


# -------------------------------------------------------------------------
# ROUTES : CONNEXION
# -------------------------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        mdp = request.form['mdp']

        prof = executer_sql("SELECT nom, prenom, mot_de_passe FROM Professeurs WHERE id_prof=?",
                            (user_id,), fetch=True)
        if prof and check_password_hash(prof[0][2], mdp):
            session['user'] = {'id': user_id, 'nom': prof[0][0], 'prenom': prof[0][1], 'role': 'PROF'}
            return redirect(url_for('prof_dashboard'))

        eleve = executer_sql("SELECT nom, prenom, mot_de_passe FROM Eleves WHERE id_eleve=?",
                             (user_id,), fetch=True)
        if eleve and check_password_hash(eleve[0][2], mdp):
            session['user'] = {'id': user_id, 'nom': eleve[0][0], 'prenom': eleve[0][1], 'role': 'ELEVE'}
            return redirect(url_for('eleve_dashboard'))

        flash("Identifiant ou mot de passe incorrect.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# -------------------------------------------------------------------------
# ROUTES : ESPACE PROFESSEUR
# -------------------------------------------------------------------------

@app.route('/prof', methods=['GET', 'POST'])
@login_requis('PROF')
def prof_dashboard():
    prof = prof_connecte()
    classes = prof.lister_classes()
    matieres = prof.lister_matieres()

    recherche = request.args.get('search')
    if recherche:
        eleves = prof.chercher_eleve(recherche)
        classe_active = None
    else:
        classe_active = request.args.get('classe', str(classes[0][0]) if classes else '1')
        eleves = prof.lister_eleves_par_classe(classe_active)

    stats_result = None
    if request.method == 'POST' and 'calculer_stats' in request.form:
        stats_result = prof.stats_matiere_classe(request.form.get('stat_classe'),
                                                 request.form.get('stat_matiere'))

    return render_template('prof.html', onglet_actif='dashboard',
                           eleves=eleves, classes=classes, matieres=matieres,
                           current_classe=classe_active, stats=stats_result)


@app.route('/prof/gestion/<id_eleve>', methods=['GET', 'POST'])
@login_requis('PROF')
def prof_gestion_notes(id_eleve):
    prof = prof_connecte()

    if request.method == 'POST' and 'ajouter' in request.form:
        prof.ajouter_note(id_eleve, request.form['matiere'],
                          float(request.form['note']), float(request.form['coeff']))
        flash("Note ajoutée.")
    if request.method == 'POST' and 'modifier' in request.form:
        prof.modifier_note(request.form['id_note'],
                           float(request.form['valeur']), float(request.form['coeff']))
        flash("Note modifiée.")
    if request.method == 'POST' and 'supprimer' in request.form:
        prof.supprimer_note(request.form['id_note'])
        flash("Note supprimée.")

    notes = prof.voir_notes_eleve(id_eleve)
    return render_template('prof_gestion.html', onglet_actif='',
                           notes=notes, id_eleve=id_eleve, matieres=prof.lister_matieres())


@app.route('/prof/emploi')
@login_requis('PROF')
def prof_emploi():
    prof = prof_connecte()
    grille_edt = construire_grille_edt(prof.recuperer_mon_emploi())
    return render_template('prof_emploi.html', onglet_actif='emploi',
                           grille_edt=grille_edt, jours_semaine=JOURS_SEMAINE)


@app.route('/prof/cahier', methods=['GET', 'POST'])
@login_requis('PROF')
def prof_cahier():
    prof = prof_connecte()

    if request.method == 'POST':
        prof.ajouter_devoir(request.form['classe'], request.form['matiere'],
                            request.form['date_pour'], request.form['description'])
        flash("Devoir ajouté au cahier de textes.")
        return redirect(url_for('prof_cahier'))

    return render_template('prof_cahier.html', onglet_actif='cahier',
                           classes=prof.lister_classes(), matieres=prof.lister_matieres(),
                           devoirs=prof.lister_mes_devoirs())


@app.route('/prof/vie-scolaire', methods=['GET', 'POST'])
@login_requis('PROF')
def prof_vie_scolaire():
    prof = prof_connecte()

    if request.method == 'POST':
        justifie = 1 if request.form.get('justifie') else 0
        prof.ajouter_evenement(request.form['id_eleve'], request.form['type_evenement'],
                               request.form['date_evenement'], request.form['motif'], justifie)
        flash("Événement enregistré.")
        return redirect(url_for('prof_vie_scolaire'))

    return render_template('prof_vie.html', onglet_actif='vie',
                           evenements=prof.lister_evenements_recents())


# -------------------------------------------------------------------------
# ROUTES : ESPACE ELEVE
# -------------------------------------------------------------------------

@app.route('/eleve')
@login_requis('ELEVE')
def eleve_dashboard():
    eleve = eleve_connecte()

    tri_actif = request.args.get('tri', 'matiere')
    periode_active = request.args.get('periode', 'tout')
    id_matiere_active = request.args.get('matiere', 'toutes')

    periodes = eleve.lister_periodes()
    periode_choisie = eleve.trouver_periode(periodes, periode_active)

    notes_detaillees = eleve.voir_mes_notes_detaillees()
    notes_filtrees = eleve.filtrer_notes(notes_detaillees, id_matiere_active, periode_choisie)

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

    return render_template('eleve.html', onglet_actif='notes',
                           tri_actif=tri_actif, periode_active=periode_active, periodes=periodes,
                           id_matiere_active=id_matiere_active, matieres_disponibles=matieres_disponibles,
                           notes_affichage=notes_affichage, notes_filtrees=notes_filtrees,
                           note_selectionnee=note_selectionnee, detail_note=detail_note,
                           stats={'rang': rang, 'total': total, 'moy': moyenne_generale})


@app.route('/eleve/download')
@login_requis('ELEVE')
def eleve_download():
    fichier, nom = eleve_connecte().generer_bulletin_txt()
    return send_file(fichier, as_attachment=True, download_name=nom, mimetype='text/plain')


@app.route('/eleve/mes-donnees')
@login_requis('ELEVE')
def eleve_mes_donnees():
    infos = eleve_connecte().recuperer_infos_personnelles()
    return render_template('mes_donnees.html', onglet_actif='mes_donnees', infos=infos)


@app.route('/eleve/cahier-de-texte')
@login_requis('ELEVE')
def eleve_cahier_de_texte():
    devoirs = eleve_connecte().recuperer_devoirs()
    return render_template('cahier_texte.html', onglet_actif='cahier_texte', devoirs=devoirs)


@app.route('/eleve/resultats')
@login_requis('ELEVE')
def eleve_resultats():
    eleve = eleve_connecte()
    resultats = eleve.calculer_resultats_par_matiere()
    moyennes_periodes = eleve.calculer_moyennes_par_periode(eleve.lister_periodes())
    rang, total, moyenne = eleve.calculer_rang()
    return render_template('resultats.html', onglet_actif='resultats', resultats=resultats,
                           moyennes_periodes=moyennes_periodes,
                           stats={'rang': rang, 'total': total, 'moy': moyenne})


@app.route('/eleve/vie-scolaire')
@login_requis('ELEVE')
def eleve_vie_scolaire():
    eleve = eleve_connecte()
    infos = eleve.recuperer_infos_personnelles()
    evenements = eleve.recuperer_vie_scolaire()
    resume = eleve.resume_vie_scolaire(evenements)
    return render_template('vie_scolaire.html', onglet_actif='vie_scolaire',
                           infos=infos, evenements=evenements, resume=resume)


@app.route('/eleve/emploi-du-temps')
@login_requis('ELEVE')
def eleve_emploi_du_temps():
    eleve = eleve_connecte()
    grille_edt = construire_grille_edt(eleve.recuperer_emploi_du_temps())
    return render_template('emploi_du_temps.html', onglet_actif='emploi_du_temps',
                           grille_edt=grille_edt, jours_semaine=JOURS_SEMAINE)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug)
