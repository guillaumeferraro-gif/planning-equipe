from ortools.sat.python import cp_model
import datetime
import pandas as pd

def generate_schedule(nurses, year, month, history, holidays):
    model = cp_model.CpModel()
    
    if month == 12:
        num_days = 31
    else:
        num_days = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days
    
    tiih_days = []
    for d in range(1, num_days + 1):
        date_obj = datetime.date(year, month, d)
        if date_obj.weekday() in [1, 3, 4] and date_obj not in holidays:
            tiih_days.append(d)

    # Variables : s=0: JOUR, s=1: NUIT, s=2: TIIH
    shifts = {}
    for n in nurses:
        for d in range(1, num_days + 1):
            for s in range(3):
                shifts[(n, d, s)] = model.NewBoolVar(f'n{n}_d{d}_s{s}')

    for d in range(1, num_days + 1):
        model.Add(sum(shifts[(n, d, 0)] for n in nurses) == 1) 
        model.Add(sum(shifts[(n, d, 1)] for n in nurses) == 1) 
        if d in tiih_days:
            model.Add(sum(shifts[(n, d, 2)] for n in nurses) == 1) 
        else:
            for n in nurses:
                model.Add(shifts[(n, d, 2)] == 0)

    for n in nurses:
        for d in range(1, num_days + 1):
            model.Add(sum(shifts[(n, d, s)] for s in range(3)) <= 1)
            if d < num_days:
                model.Add(shifts[(n, d, 1)] + shifts[(n, d+1, 0)] <= 1)
                model.Add(shifts[(n, d, 1)] + shifts[(n, d+1, 2)] <= 1)

    # 48h glissantes
    for n in nurses:
        for d in range(1, num_days - 5):
            window = []
            for i in range(7):
                day = d + i
                h = shifts[(n, day, 0)] * 720 + shifts[(n, day, 1)] * 720 + shifts[(n, day, 2)] * 462
                window.append(h)
            model.Add(sum(window) <= 2880)

    # Logique de blocs (Pénalités pour changements)
    penalties = []
    for n in nurses:
        for d in range(1, num_days):
            for s in range(3):
                change = model.NewBoolVar(f'change_{n}_{d}_{s}')
                model.Add(shifts[(n, d, s)] != shifts[(n, d+1, s)]).OnlyEnforceIf(change)
                penalties.append(change)

    # Équité
    nurse_minutes = []
    for n in nurses:
        total_m = sum(shifts[(n, d, 0)] * 720 + shifts[(n, d, 1)] * 720 + shifts[(n, d, 2)] * 462 for d in range(1, num_days + 1))
        hist_m = int(history.get(n, 0) * 60)
        nurse_minutes.append(total_m + hist_m)

    min_h = model.NewIntVar(0, 10000000, 'min_h')
    max_h = model.NewIntVar(0, 10000000, 'max_h')
    model.AddMinEquality(min_h, nurse_minutes)
    model.AddMaxEquality(max_h, nurse_minutes)

    # OBJECTIF : Priorité à l'équité (coeff 10) puis aux blocs (coeff 1)
    model.Minimize(10 * (max_h - min_h) + sum(penalties))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
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
