"""Propositions CP-SAT ; les données reçues ne sont jamais modifiées."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, timedelta
from functools import reduce
from math import gcd
import time

from ortools.sat.python import cp_model

from .domain import (DomainError, SHIFT_MINUTES, absent_for, credit_minutes, dates,
                     month_bounds, quota_on, shift_interval, tiih_required,
                     validate_schedule, validate_state)


@dataclass
class ScheduleResult:
    status: str
    message: str
    candidate: dict | None = None
    end: date | None = None
    elapsed: float = 0.0
    isolated_nights: int | None = None


def generate_schedule(state: dict, year: int, month: int, *, time_limit: float = 20,
                      lookahead: int = 18, seed: int = 42) -> ScheduleResult:
    started = time.monotonic()
    try:
        validate_state(state)
        start, end = month_bounds(year, month)
        if not 0 < time_limit <= 120 or not 8 <= lookahead <= 45:
            raise DomainError("Délai de 0 à 120 s et anticipation de 8 à 45 jours requis.")
        settings = state["settings"]
        if settings["rest_clock"] is None:
            raise DomainError("Choisir la convention des 12 h de repos dans Équipe et règles.")
        last = end+timedelta(days=lookahead)
        if last.weekday() == 5:
            last += timedelta(days=1)
        nurses = state["nurses"]
        if any(quota_on(n, d) is None for n in nurses for d in dates(start,last)):
            raise DomainError("Renseigner la quotité de chaque IDE pour le mois et son anticipation avant de générer.")
    except (DomainError, ValueError) as exc:
        return ScheduleResult("invalid_input", str(exc))

    model = cp_model.CpModel()
    zone = settings["timezone"]
    cstart, cend = start-timedelta(days=8), last+timedelta(days=8)
    all_days = list(dates(cstart,cend))
    future_days = list(dates(start,cend))
    period = list(dates(start,last))
    ids = [n["id"] for n in nurses]
    x, worked, free = {}, {}, set()

    # Dates hors du mois déjà renseignées et postes verrouillés/confirmés restent fixes.
    for nid in ids:
        for d in all_days:
            old = state["assignments"].get(str(d),{}).get(nid)
            editable = start <= d <= end or (
                end < d <= last and nid not in state["reviewed"].get(str(d),[]) and old is None)
            editable = editable and not (old and (old["locked"] or old["confirmed"]))
            if editable:
                free.add((nid,d))
            for s in ("J","N","T"):
                value = model.new_bool_var(f"x_{nid}_{d}_{s}") if editable else int(bool(old and old["shift"]==s))
                x[nid,d,s] = value
                if editable and (absent_for(state,nid,d,s) or (s=="T" and not tiih_required(state,d))):
                    model.add(value==0)
                if not editable and start <= d <= end and value and absent_for(state,nid,d,s):
                    return ScheduleResult("infeasible", f"Une affectation verrouillée ou confirmée chevauche une absence le {d:%d/%m}.")
            worked[nid,d] = sum(x[nid,d,s] for s in ("J","N","T"))
            if editable:
                model.add(worked[nid,d] <= 1)

    for d in period:
        # Couverture du mois et des dates d'anticipation à construire.
        if d > end and not any((nid,d) in free for nid in ids):
            continue
        for s in ("J","N","T"):
            need = int(s != "T" or tiih_required(state,d))
            available = [n for n in nurses if not absent_for(state,n["id"],d,s)]
            if need and not available:
                return ScheduleResult("infeasible", f"Aucune IDE disponible pour {s} le {d:%d/%m}. La couverture SMUR reste obligatoire.")
            model.add(sum(x[nid,d,s] for nid in ids) == need)

    intervals = {(d,s): shift_interval(d,s,zone) for d in all_days for s in ("J","N","T")}
    rest_intervals = {(d,s): shift_interval(d,s,zone,settings["rest_clock"]) for d in all_days for s in ("J","N","T")}
    minimum, target, maximum = (settings[k] for k in ("phase_min","phase_target","phase_max"))
    night, age, phase_penalties, isolated = {}, {}, [], []

    for pos,nid in enumerate(ids):
        for index,d in enumerate(future_days):
            night[nid,d] = model.new_bool_var(f"night_{nid}_{d}")
            age[nid,d] = model.new_int_var(1,maximum,f"age_{nid}_{d}")
            old = state["phases"].get(str(d),{}).get(nid)
            if old and (d>end or old.get("locked",False)):
                model.add(night[nid,d] == int(old["mode"]=="N"))
                model.add(age[nid,d] == old["age"])
            else:
                model.add_hint(night[nid,d], ((index+pos*4)//target)%2)
                model.add_hint(age[nid,d], (index+pos*4)%target+1)
            previous_day = d-timedelta(days=1)
            if index:
                previous_night, previous_age = night[nid,previous_day], age[nid,previous_day]
            else:
                previous = state["phases"].get(str(previous_day),{}).get(nid)
                if previous is None:
                    continue_link = False
                else:
                    previous_night,previous_age = int(previous["mode"]=="N"),previous["age"]
                    continue_link = True
            if index or continue_link:
                change = model.new_bool_var(f"change_{nid}_{d}")
                model.add(night[nid,d] != previous_night).only_enforce_if(change)
                model.add(night[nid,d] == previous_night).only_enforce_if(change.Not())
                model.add(previous_age >= minimum).only_enforce_if(change)
                model.add(age[nid,d] == 1).only_enforce_if(change)
                model.add(age[nid,d] == previous_age+1).only_enforce_if(change.Not())
                deviation = model.new_int_var(0,maximum+target,f"dev_{nid}_{d}")
                raw = model.new_int_var(0,maximum+target,f"raw_{nid}_{d}")
                model.add_abs_equality(raw, previous_age-target)
                model.add(deviation==raw).only_enforce_if(change)
                model.add(deviation==0).only_enforce_if(change.Not())
                if d <= last:
                    phase_penalties.append(deviation)
            model.add(x[nid,d,"N"] <= night[nid,d])
            model.add(x[nid,d,"J"]+x[nid,d,"T"] <= 1-night[nid,d])

        for d in all_days[:-1]:
            next_day = d+timedelta(days=1)
            if not (start <= d <= last or start <= next_day <= last):
                continue
            for s in ("J","N","T"):
                for t in ("J","N","T"):
                    if rest_intervals[next_day,t][0]-rest_intervals[d,s][1] < 720:
                        model.add(x[nid,d,s]+x[nid,next_day,t] <= 1)
        for d in dates(start-timedelta(days=3),last):
            model.add(sum(worked[nid,d+timedelta(days=i)] for i in range(4)) <= 3)
        for d in all_days:
            if d.weekday()==5 and d+timedelta(days=2) <= cend and d+timedelta(days=2)>=start and d<=last:
                sunday,monday=d+timedelta(days=1),d+timedelta(days=2)
                pair_known = all(start <= day <= last or
                                 nid in state["reviewed"].get(str(day),[]) or
                                 nid in state["assignments"].get(str(day),{})
                                 for day in (d,sunday))
                if pair_known:
                    for s in ("J","N","T"):
                        model.add(x[nid,d,s] == x[nid,sunday,s])
                model.add(worked[nid,sunday]+worked[nid,monday] <= 1)
        for d in period:
            single = model.new_bool_var(f"isolated_{nid}_{d}")
            current = x[nid,d,"N"]
            prev = x[nid,d-timedelta(days=1),"N"]
            nxt = x[nid,d+timedelta(days=1),"N"]
            model.add(single >= current-prev-nxt)
            model.add(single <= current)
            model.add(single+prev <= 1)
            model.add(single+nxt <= 1)
            isolated.append(single)

    # Fenêtres exactes de168h : seuls les points de rupture de l'intégrale sont utiles.
    windows = sorted({p for a,b in intervals.values() for p in (a,b,a-10080,b-10080)})
    for w in windows:
        terms = [(d,s,max(0,min(b,w+10080)-max(a,w))) for (d,s),(a,b) in intervals.items()]
        terms = [(d,s,k) for d,s,k in terms if k]
        if not any(start <= d <= last for d,s,k in terms):
            continue
        for nid in ids:
            model.add(sum(k*x[nid,d,s] for d,s,k in terms) <= 2880)

    feasibility_model = model.clone()
    fairness = []
    objective_scale = 1
    for y in sorted({d.year for d in period}):
        selected = [d for d in period if d.year==y]
        weights = {n["id"]: sum(quota_on(n,d) for d in selected) for n in nurses}
        divisor = reduce(gcd,weights.values())
        weights = {nid:w//divisor for nid,w in weights.items()}
        total_weight = sum(weights.values())
        objective_scale = max(objective_scale,total_weight)
        loads,load_bounds = {},{}
        for n in nurses:
            nid=n["id"]
            prior=sum(SHIFT_MINUTES[a[nid]["shift"]] for d,a in state["assignments"].items()
                      if str(date(y,1,1))<=d<str(selected[0]) and nid in a
                      and (a[nid]["shift"]=="-" or not absent_for(state,nid,date.fromisoformat(d),a[nid]["shift"])))
            credit=credit_minutes(state,nid,date(y,1,1),selected[-1])
            load_bounds[nid] = prior+credit+720*len(selected)
            loads[nid] = model.new_int_var(0,load_bounds[nid],f"load_{nid}_{y}")
            model.add(loads[nid] == prior+credit+sum(SHIFT_MINUTES[s]*x[nid,d,s] for d in selected for s in ("J","N","T")))
        total_bound=sum(load_bounds.values())
        total_load=model.new_int_var(0,total_bound,f"total_load_{y}")
        model.add(total_load == sum(loads.values()))
        for nid in ids:
            bound=max(total_weight*load_bounds[nid],weights[nid]*total_bound)
            dev=model.new_int_var(0,bound,f"fair_{nid}_{y}")
            model.add_abs_equality(dev,total_weight*loads[nid]-weights[nid]*total_load)
            fairness.append(dev)
    model.minimize(sum(fairness)+objective_scale*720*sum(isolated)
                   +objective_scale*30*sum(phase_penalties))
    # Chercher d'abord une solution simple de quatorze jours, alignée sur les lundis.
    # C'est une amorce de recherche, pas une contrainte ajoutée au modèle final.
    seed_solver = None
    if time_limit >= 3:
        warm = feasibility_model
        warm.clear_objective()
        warm.clear_hints()
        if minimum <= 14 <= maximum:
            anchor = date(2000,1,3)
            for nid in ids:
                for d in future_days:
                    warm.add(age[nid,d] == (d-anchor).days % 14+1)
            attempt = cp_model.CpSolver()
            attempt.parameters.max_time_in_seconds = min(4,time_limit/3)
            attempt.parameters.num_search_workers = 4
            attempt.parameters.random_seed = seed
            attempt.parameters.stop_after_first_solution = True
            warm_status = attempt.solve(warm)
            if warm_status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
                seed_solver = attempt
                model.clear_hints()
                for i in range(len(warm.proto.variables)):
                    var = model.get_int_var_from_proto_index(i)
                    model.add_hint(var,attempt.value(var))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=max(0.00001,time_limit-(time.monotonic()-started))
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    status=solver.solve(model)
    if status==cp_model.UNKNOWN and seed_solver is not None:
        solver,status=seed_solver,cp_model.FEASIBLE
    elapsed=time.monotonic()-started
    if status==cp_model.INFEASIBLE:
        return ScheduleResult("infeasible","Aucune solution ne respecte toutes les règles. Vérifier les absences, les verrous, les périodes et les besoins TIIH ; aucune règle n'a été assouplie.",elapsed=elapsed)
    if status==cp_model.MODEL_INVALID:
        return ScheduleResult("invalid_model","Le moteur a détecté une configuration incohérente : "+model.validate(),elapsed=elapsed)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return ScheduleResult("unknown","Le délai est écoulé sans proposition trouvée. Cela ne démontre pas que le planning est impossible.",elapsed=elapsed)
    candidate=deepcopy(state)
    for d in period:
        for nid in ids:
            if (nid,d) in free:
                shift=next((s for s in ("J","N","T") if solver.value(x[nid,d,s])),"-")
                candidate["assignments"].setdefault(str(d),{})[nid]={"shift":shift,"locked":False,"confirmed":False}
                candidate["reviewed"][str(d)]=sorted(set(candidate["reviewed"].get(str(d),[]))|{nid})
            if d<=end or nid not in candidate["phases"].get(str(d),{}):
                old=state["phases"].get(str(d),{}).get(nid,{})
                candidate["phases"].setdefault(str(d),{})[nid]={
                    "mode":"N" if solver.value(night[nid,d]) else "J", "age":solver.value(age[nid,d]),
                    "locked":old.get("locked",False)}
    errors=[i for i in validate_schedule(candidate,start,last) if i.severity=="error"
            and not (i.code=="coverage" and i.day and i.day>str(end)
                     and not any((nid,date.fromisoformat(i.day)) in free for nid in ids))]
    if errors:
        return ScheduleResult("invalid_result","La vérification indépendante a rejeté la proposition : "+errors[0].message,elapsed=elapsed)
    return ScheduleResult("optimal" if status==cp_model.OPTIMAL else "feasible",
                          "Proposition trouvée et contrôlée. Vérifier les alertes de contexte avant validation complète.",
                          candidate,last,elapsed,sum(solver.value(v) for v in isolated))
