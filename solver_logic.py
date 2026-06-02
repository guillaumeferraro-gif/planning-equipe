from ortools.sat.python import cp_model
import datetime
import pandas as pd

def generate_schedule(nurses, year, month, history, holidays):
    model = cp_model.CpModel()
    
    # Nombre de jours dans le mois
    if month == 12:
        num_days = 31
    else:
        num_days = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days
    
    # Identification des jours TIIH (Mar, Jeu, Ven)
    tiih_days = []
    for d in range(1, num_days + 1):
        date_obj = datetime.date(year, month, d)
        if date_obj.weekday() in [1, 3, 4] and date_obj not in holidays:
            tiih_days.append(d)

    # Variables : shifts[(n, d, s)] 
    # s=0: JOUR (12h), s=1: NUIT (12h), s=2: TIIH (7.7h)
    shifts = {}
    for n in nurses:
        for d in range(1, num_days + 1):
            for s in range(3):
                shifts[(n, d, s)] = model.NewBoolVar(f'n{n}_d{d}_s{s}')

    # --- CONTRAINTES DE PRÉSENCE ---
    for d in range(1, num_days + 1):
        model.Add(sum(shifts[(n, d, 0)] for n in nurses) == 1) # 1 Jour
        model.Add(sum(shifts[(n, d, 1)] for n in nurses) == 1) # 1 Nuit
        if d in tiih_days:
            model.Add(sum(shifts[(n, d, 2)] for n in nurses) == 1) # 1 TIIH
        else:
            for n in nurses:
                model.Add(shifts[(n, d, 2)] == 0) # Pas de TIIH les autres jours

    # --- CONTRAINTES INDIVIDUELLES ---
    for n in nurses:
        for d in range(1, num_days + 1):
            # Une personne ne fait qu'UN SEUL poste par jour
            model.Add(sum(shifts[(n, d, s)] for s in range(3)) <= 1)
            
            # Repos : Pas de Nuit puis Jour le lendemain
            if d < num_days:
                model.Add(shifts[(n, d, 1)] + shifts[(n, d+1, 0)] <= 1)
                model.Add(shifts[(n, d, 1)] + shifts[(n, d+1, 2)] <= 1)

    # --- RÈGLE DES 48H GLISSANTES (7 JOURS) ---
    for n in nurses:
        for d in range(1, num_days - 5):
            window = []
            for i in range(7):
                day = d + i
                # Minutes : Jour=720, Nuit=720, TIIH=462
                h = shifts[(n, day, 0)] * 720 + shifts[(n, day, 1)] * 720 + shifts[(n, day, 2)] * 462
                window.append(h)
            model.Add(sum(window) <= 2880) # 2880 min = 48h

    # --- LOGIQUE DE BLOCS (Stabilité des postes) ---
    # On pénalise le fait de changer de type de poste d'un jour à l'autre
    penalties = []
    for n in nurses:
        for d in range(1, num_days):
            for s in range(3):
                # Si l'infirmière change de statut (ex: de Jour à Repos ou de Jour à Nuit)
                change = model.NewBoolVar(f'change_{n}_{d}_{s}')
                model.Add(shifts[(n, d, s)] != shifts[(n, d+1, s)]).OnlyEnforceIf(change)
                penalties.append(change)

    # --- ÉQUITÉ ---
    nurse_minutes = []
    for n in nurses:
        total_m = sum(shifts[(n, d, 0)] * 720 + shifts[(n, d, 1)] * 720 + shifts[(n, d, 2)] * 462 for d in range(1, num_days + 1))
        # Historique récupéré des stats (converti en minutes)
        hist_m = int(history.get(n, 0) * 60)
        nurse_minutes.append(total_m + hist_m)

    min_h = model.NewIntVar(0, 1000000, '')
    max_h = model.NewIntVar(0, 1000000, '')
    model.AddMinEquality(min_h, nurse_minutes)
    model.AddMaxEquality(max_h, nurse_minutes)

    # Objectif : 1. Équité des heures | 2. Moins de changements de postes (blocs)
    model.Minimize((max_h - min_h) + (sum(penalties) // 2))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0 # Évite de ramer trop longtemps
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        data = []
        for d in range(1, num_days + 1):
            row = {"Date": f"{d}/{month}", "Jour": "", "Nuit": "", "TIIH": ""}
            for n in nurses:
                if solver.Value(shifts[(n, d, 0)]): row["Jour"] = n
                if solver.Value(shifts[(n, d, 1)]): row["Nuit"] = n
                if solver.Value(shifts[(n, d, 2)]): row["TIIH"] = n
            data.append(row)
        return pd.DataFrame(data)
    return None
