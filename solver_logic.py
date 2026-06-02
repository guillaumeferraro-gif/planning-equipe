from ortools.sat.python import cp_model
import datetime
import pandas as pd

def generate_schedule(nurses, year, month, history, holidays):
    model = cp_model.CpModel()
    # Calcul du nombre de jours dans le mois
    if month == 12:
        num_days = 31
    else:
        num_days = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days
    
    # Jours TIIH (Mardi=1, Jeudi=3, Vendredi=4)
    tiih_days = []
    for d in range(1, num_days + 1):
        date_obj = datetime.date(year, month, d)
        if date_obj.weekday() in [1, 3, 4]:
            tiih_days.append(d)

    # Variables :shifts[(infirmière, jour, poste)]
    # postes : 0 = JOUR, 1 = NUIT
    shifts = {}
    for n in nurses:
        for d in range(1, num_days + 1):
            for s in range(2):
                shifts[(n, d, s)] = model.NewBoolVar(f'n{n}_d{d}_s{s}')

    # --- CONTRAINTES ---
    for d in range(1, num_days + 1):
        model.Add(sum(shifts[(n, d, 0)] for n in nurses) == 1) # 1 Jour par jour
        model.Add(sum(shifts[(n, d, 1)] for n in nurses) == 1) # 1 Nuit par jour

        for n in nurses:
            model.Add(shifts[(n, d, 0)] + shifts[(n, d, 1)] <= 1) # Pas J et N le même jour
            if d < num_days:
                model.Add(shifts[(n, d, 1)] + shifts[(n, d+1, 0)] <= 1) # Pas Nuit puis Jour

    # 48h glissantes (7 jours)
    for n in nurses:
        for d in range(1, num_days - 5):
            window = []
            for i in range(7):
                day = d + i
                h = shifts[(n, day, 0)] * 12 + shifts[(n, day, 1)] * 12
                if day in tiih_days:
                    h += shifts[(n, day, 0)] * 7.7
                window.append(h)
            model.Add(sum(window) <= 48)

    # Équité (Heures totales)
    nurse_hours = []
    for n in nurses:
        total = sum(shifts[(n, d, 0)] * (19.7 if d in tiih_days else 12) + shifts[(n, d, 1)] * 12 for d in range(1, num_days + 1))
        # On ajoute l'historique du mois précédent
        nurse_hours.append(total + history.get(n, 0))

    min_h = model.NewIntVar(0, 5000, 'min_h')
    max_h = model.NewIntVar(0, 5000, 'max_h')
    model.AddMinEquality(min_h, nurse_hours)
    model.AddMaxEquality(max_h, nurse_hours)
    model.Minimize(max_h - min_h)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        data = []
        for d in range(1, num_days + 1):
            row = {"Jour": f"{d}/{month}/{year}"}
            for n in nurses:
                if solver.Value(shifts[(n, d, 0)]): row["Jour"] = n
                if solver.Value(shifts[(n, d, 1)]): row["Nuit"] = n
            data.append(row)
        return pd.DataFrame(data, columns=["Jour", "Nuit"])
    return None
