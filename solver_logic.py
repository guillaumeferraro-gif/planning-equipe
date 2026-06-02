from ortools.sat.python import cp_model
import datetime
import pandas as pd

def generate_schedule(nurses, year, month, history, public_holidays):
    model = cp_model.CpModel()
    
    if month == 12:
        num_days = 31
    else:
        num_days = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days
    
    tiih_days = []
    for d in range(1, num_days + 1):
        date_obj = datetime.date(year, month, d)
        # Mardi(1), Jeudi(3), Vendredi(4). Pas de TIIH si férié.
        if date_obj.weekday() in [1, 3, 4] and date_obj not in public_holidays:
            tiih_days.append(d)

    # Variables : s0=JOUR, s1=NUIT, s2=TIIH
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
            for n in nurses: model.Add(shifts[(n, d, 2)] == 0)

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

    # Blocs et équité
    penalties = []
    for n in nurses:
        for d in range(1, num_days):
            for s in range(3):
                change = model.NewBoolVar(f'c_{n}_{d}_{s}')
                model.Add(shifts[(n, d, s)] != shifts[(n, d+1, s)]).OnlyEnforceIf(change)
                penalties.append(change)

    nurse_min = []
    for n in nurses:
        total = sum(shifts[(n, d, 0)] * 720 + shifts[(n, d, 1)] * 720 + shifts[(n, d, 2)] * 462 for d in range(1, num_days + 1))
        nurse_min.append(total + int(history.get(n, 0) * 60))

    min_h = model.NewIntVar(0, 10000000, '')
    max_h = model.NewIntVar(0, 10000000, '')
    model.AddMinEquality(min_h, nurse_min)
    model.AddMaxEquality(max_h, nurse_min)

    model.Minimize(10 * (max_h - min_h) + sum(penalties))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 8.0
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # On retourne un dictionnaire {infirmière: {jour: poste}}
        res = {n: {} for n in nurses}
        for d in range(1, num_days + 1):
            for n in nurses:
                if solver.Value(shifts[(n, d, 0)]): res[n][d] = "☀️ JOUR"
                elif solver.Value(shifts[(n, d, 1)]): res[n][d] = "🌙 NUIT"
                elif solver.Value(shifts[(n, d, 2)]): res[n][d] = "🛠️ TIIH"
                else: res[n][d] = "-"
        return res
    return None
