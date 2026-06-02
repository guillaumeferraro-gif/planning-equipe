from ortools.sat.python import cp_model
import datetime
import pandas as pd

def generate_schedule(nurses, year, month, history, holidays):
    model = cp_model.CpModel()
    
    # Calcul des jours du mois
    if month == 12:
        num_days = 31
    else:
        num_days = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days
    
    # Jours TIIH (Mardi=1, Jeudi=3, Vendredi=4)
    tiih_days = []
    for d in range(1, num_days + 1):
        date_obj = datetime.date(year, month, d)
        if date_obj.weekday() in [1, 3, 4] and date_obj not in holidays:
            tiih_days.append(d)

    # Variables : 0 = JOUR, 1 = NUIT
    shifts = {}
    for n in nurses:
        for d in range(1, num_days + 1):
            for s in range(2):
                shifts[(n, d, s)] = model.NewBoolVar(f'n{n}_d{d}_s{s}')

    # --- CONTRAINTES ---
    for d in range(1, num_days + 1):
        model.Add(sum(shifts[(n, d, 0)] for n in nurses) == 1) 
        model.Add(sum(shifts[(n, d, 1)] for n in nurses) == 1) 

        for n in nurses:
            model.Add(shifts[(n, d, 0)] + shifts[(n, d, 1)] <= 1) 
            if d < num_days:
                model.Add(shifts[(n, d, 1)] + shifts[(n, d+1, 0)] <= 1)
                model.Add(shifts[(n, d, 0)] + shifts[(n, d+1, 1)] <= 1)

    # --- RÈGLE DES 48H (EN MINUTES) ---
    for n in nurses:
        for d in range(1, num_days - 5):
            window = []
            for i in range(7):
                day = d + i
                # On utilise les minutes : 720 min = 12h, 462 min = 7h42
                h = shifts[(n, day, 0)] * 720 + shifts[(n, day, 1)] * 720
                if day in tiih_days:
                    h += shifts[(n, day, 0)] * 462
                window.append(h)
            model.Add(sum(window) <= 2880) # 2880 min = 48h

    # --- ÉQUITÉ ---
    nurse_minutes = []
    for n in nurses:
        # On calcule le total en minutes
        total_m = sum(shifts[(n, d, 0)] * (1182 if d in tiih_days else 720) + 
                      shifts[(n, d, 1)] * 720 for d in range(1, num_days + 1))
        # Ajout historique (converti en minutes si stocké en heures)
        hist_m = int(history.get(n, 0) * 60)
        nurse_minutes.append(total_m + hist_m)

    min_h = model.NewIntVar(0, 1000000, 'min_h')
    max_h = model.NewIntVar(0, 1000000, 'max_h')
    model.AddMinEquality(min_h, nurse_minutes)
    model.AddMaxEquality(max_h, nurse_minutes)
    model.Minimize(max_h - min_h)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        data = []
        for d in range(1, num_days + 1):
            row = {"Date": f"{d}/{month}", "Jour": "", "Nuit": ""}
            for n in nurses:
                if solver.Value(shifts[(n, d, 0)]): row["Jour"] = n
                if solver.Value(shifts[(n, d, 1)]): row["Nuit"] = n
            data.append(row)
        return pd.DataFrame(data)
    return None
