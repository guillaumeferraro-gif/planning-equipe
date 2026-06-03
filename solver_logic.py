from ortools.sat.python import cp_model
import datetime
import pandas as pd

def generate_schedule(nurses, year, month, history, public_holidays):
    model = cp_model.CpModel()
    
    # Calcul du nombre de jours
    last_day = (datetime.date(year, month, 28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
    num_days = last_day.day
    
    tiih_days = [d for d in range(1, num_days + 1) 
                 if datetime.date(year, month, d).weekday() in [1, 3, 4] 
                 and datetime.date(year, month, d) not in public_holidays]

    # Variables : s0=JOUR, s1=NUIT, s2=TIIH
    shifts = {}
    phase_nuit = {} 

    for n in nurses:
        for w in range(6): phase_nuit[(n, w)] = model.NewBoolVar(f'phaseN_n{n}_w{w}')
        for d in range(1, num_days + 1):
            for s in range(3): shifts[(n, d, s)] = model.NewBoolVar(f'n{n}_d{d}_s{s}')

    for d in range(1, num_days + 1):
        model.Add(sum(shifts[(n, d, 0)] for n in nurses) == 1) 
        model.Add(sum(shifts[(n, d, 1)] for n in nurses) == 1) 
        if d in tiih_days:
            model.Add(sum(shifts[(n, d, 2)] for n in nurses) == 1) 
        else:
            for n in nurses: model.Add(shifts[(n, d, 2)] == 0)

    for n in nurses:
        for d in range(1, num_days + 1):
            week = (d - 1) // 7
            model.Add(shifts[(n, d, 0)] == 0).OnlyEnforceIf(phase_nuit[(n, week)])
            model.Add(shifts[(n, d, 2)] == 0).OnlyEnforceIf(phase_nuit[(n, week)])
            model.Add(shifts[(n, d, 1)] == 0).OnlyEnforceIf(phase_nuit[(n, week)].Not())
            model.Add(sum(shifts[(n, d, s)] for s in range(3)) <= 1)
            if d < num_days:
                model.Add(shifts[(n, d, 1)] + shifts[(n, d+1, 0)] <= 1)

        for d in range(1, num_days - 2):
            model.Add(sum(sum(shifts[(n, di, s)] for s in range(3)) for di in range(d, d + 4)) <= 3)

        for d in range(1, num_days):
            if datetime.date(year, month, d).weekday() == 5:
                model.Add(shifts[(n, d, 0)] == shifts[(n, d+1, 0)])
                model.Add(shifts[(n, d, 1)] == shifts[(n, d+1, 1)])

    for n in nurses:
        for d in range(1, num_days - 5):
            window = [shifts[(n, d+i, 0)] * 720 + shifts[(n, d+i, 1)] * 720 + shifts[(n, d+i, 2)] * 462 for i in range(7)]
            model.Add(sum(window) <= 2880)

    nurse_totals = []
    for n in nurses:
        total = sum(shifts[(n, d, 0)] * 720 + shifts[(n, d, 1)] * 720 + shifts[(n, d, 2)] * 462 for d in range(1, num_days + 1))
        nurse_totals.append(total + int(history.get(n, 0) * 60))

    min_h, max_h = model.NewIntVar(0, 10**7, ''), model.NewIntVar(0, 10**7, '')
    model.AddMinEquality(min_h, nurse_totals)
    model.AddMaxEquality(max_h, nurse_totals)
    model.Minimize(max_h - min_h)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    if solver.Solve(model) in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Structure : {Nom: {Jour1: Poste, Jour2: Poste...}}
        return {n: {str(d): ("☀️ JOUR" if solver.Value(shifts[(n, d, 0)]) else "🌙 NUIT" if solver.Value(shifts[(n, d, 1)]) else "🛠️ TIIH" if solver.Value(shifts[(n, d, 2)]) else "-") for d in range(1, num_days + 1)} for n in nurses}
    return None
