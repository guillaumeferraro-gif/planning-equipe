from ortools.sat.python import cp_model
import datetime
import pandas as pd

def generate_schedule(nurses, year, month, history, public_holidays):
    model = cp_model.CpModel()
    
    if month == 12:
        num_days = 31
    else:
        num_days = (datetime.date(year, month + 1, 1) - datetime.date(year, month, 1)).days
    
    tiih_days = [d for d in range(1, num_days + 1) 
                 if datetime.date(year, month, d).weekday() in [1, 3, 4] 
                 and datetime.date(year, month, d) not in public_holidays]

    # Variables : s0=JOUR, s1=NUIT, s2=TIIH
    shifts = {}
    # Variable de Phase : 1 si l'infirmière est en "Phase Nuit" pour la semaine W
    # On divise le mois en 4 semaines pour plus de souplesse
    phase_nuit = {} 

    for n in nurses:
        for w in range(5): # Jusqu'à 5 semaines par mois
            phase_nuit[(n, w)] = model.NewBoolVar(f'phaseNuit_n{n}_w{w}')
        
        for d in range(1, num_days + 1):
            for s in range(3):
                shifts[(n, d, s)] = model.NewBoolVar(f'n{n}_d{d}_s{s}')

    # --- CONTRAINTES DE PRÉSENCE ---
    for d in range(1, num_days + 1):
        model.Add(sum(shifts[(n, d, 0)] for n in nurses) == 1) 
        model.Add(sum(shifts[(n, d, 1)] for n in nurses) == 1) 
        if d in tiih_days:
            model.Add(sum(shifts[(n, d, 2)] for n in nurses) == 1) 
        else:
            for n in nurses: model.Add(shifts[(n, d, 2)] == 0)

    # --- LOGIQUE DE PHASE ET BLOCS ---
    for n in nurses:
        for d in range(1, num_days + 1):
            week = (d - 1) // 7
            # Si on est en phase nuit cette semaine :
            # 1. Interdiction de faire JOUR (s0)
            model.Add(shifts[(n, d, 0)] == 0).OnlyEnforceIf(phase_nuit[(n, week)])
            # 2. Interdiction de faire TIIH (s2)
            model.Add(shifts[(n, d, 2)] == 0).OnlyEnforceIf(phase_nuit[(n, week)])
            
            # Si on est en phase JOUR (non phase nuit) :
            # 1. Interdiction de faire NUIT (s1)
            model.Add(shifts[(n, d, 1)] == 0).OnlyEnforceIf(phase_nuit[(n, week)].Not())

            # Sécurité standard
            model.Add(sum(shifts[(n, d, s)] for s in range(3)) <= 1)

        # --- MAX 3 SHIFTS D'AFFILÉE ---
        for d in range(1, num_days - 2):
            model.Add(sum(sum(shifts[(n, di, s)] for s in range(3)) for di in range(d, d + 4)) <= 3)

        # --- WEEK-ENDS GROUPÉS ---
        for d in range(1, num_days):
            if datetime.date(year, month, d).weekday() == 5: # Samedi
                model.Add(shifts[(n, d, 0)] == shifts[(n, d+1, 0)])
                model.Add(shifts[(n, d, 1)] == shifts[(n, d+1, 1)])

    # --- 48H GLISSANTES ---
    for n in nurses:
        for d in range(1, num_days - 5):
            window = [shifts[(n, d+i, 0)] * 720 + shifts[(n, d+i, 1)] * 720 + shifts[(n, d+i, 2)] * 462 for i in range(7)]
            model.Add(sum(window) <= 2880)

    # --- ÉQUITÉ ---
    nurse_min = []
    for n in nurses:
        total = sum(shifts[(n, d, 0)] * 720 + shifts[(n, d, 1)] * 720 + shifts[(n, d, 2)] * 462 for d in range(1, num_days + 1))
        nurse_min.append(total + int(history.get(n, 0) * 60))

    min_h, max_h = model.NewIntVar(0, 10000000, ''), model.NewIntVar(0, 10000000, '')
    model.AddMinEquality(min_h, nurse_min)
    model.AddMaxEquality(max_h, nurse_min)
    model.Minimize(max_h - min_h)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        res = {n: {} for n in nurses}
        for d in range(1, num_days + 1):
            for n in nurses:
                if solver.Value(shifts[(n, d, 0)]): res[n][d] = "☀️ JOUR"
                elif solver.Value(shifts[(n, d, 1)]): res[n][d] = "🌙 NUIT"
                elif solver.Value(shifts[(n, d, 2)]): res[n][d] = "🛠️ TIIH"
                else: res[n][d] = "-"
        return res
    return None
