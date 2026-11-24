"""Règles métier pures, indépendantes de l'interface et du solveur."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from typing import Iterator
from uuid import uuid4
from zoneinfo import ZoneInfo
import calendar
import re

import holidays

SHIFT_MINUTES = {"J": 720, "N": 720, "T": 462, "-": 0}
SHIFT_LABELS = {"J": "SMUR J", "N": "SMUR N", "T": "TIIH", "-": "Repos"}
ABSENCE_KINDS = ["Maladie", "Congés annuels", "RTT", "Grossesse / maternité",
                 "Formation", "Congés exceptionnels", "Temps partiel thérapeutique", "Autre"]
UTC = timezone.utc


class DomainError(ValueError):
    pass


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    severity: str = "error"
    nurse_id: str | None = None
    day: str | None = None


def dates(start: date, end: date) -> Iterator[date]:
    for n in range((end - start).days + 1):
        yield start + timedelta(days=n)


def month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def format_minutes(value: int | None) -> str:
    if value is None:
        return "À renseigner"
    sign = "−" if value < 0 else ""
    h, m = divmod(abs(int(value)), 60)
    return f"{sign}{h} h {m:02d}"


def parse_duration(text: str, *, allow_blank: bool = False) -> int | None:
    text = str(text).strip().replace("h", ":").replace(" ", "")
    if not text and allow_blank:
        return None
    if not re.fullmatch(r"\d{1,5}:\d{2}", text):
        raise DomainError("Saisir une durée au format heures:minutes, par exemple 7:42.")
    h, m = map(int, text.split(":"))
    if m >= 60:
        raise DomainError("Les minutes doivent être comprises entre 00 et 59.")
    return h * 60 + m


def new_state(year: int | None = None) -> dict:
    year = year or datetime.now(ZoneInfo("Europe/Paris")).year
    return {
        "schema_version": 2, "revision": 0,
        "nurses": [{"id": f"ide-{chr(97+i)}", "name": f"IDE {chr(65+i)}",
                    "contracts": [{"from": f"{year}-01-01", "percent": q}]}
                   for i, q in enumerate([80, 80, 100, None, None, None, None])],
        "assignments": {}, "phases": {}, "reviewed": {}, "absences": [],
        "tiih_changes": {}, "oat": {},
        "settings": {"timezone": "Europe/Paris", "rest_clock": "wall",
                     "phase_min": 14, "phase_target": 15, "phase_max": 16,
                     "extra_holidays": []},
    }


def quota_on(nurse: dict, day: date) -> int | None:
    applicable = [c for c in nurse["contracts"] if date.fromisoformat(c["from"]) <= day]
    return max(applicable, key=lambda c: c["from"])["percent"] if applicable else None


def set_contract(nurse: dict, effective: date, percent: int | None) -> None:
    if percent is not None and (type(percent) is not int or not 1 <= percent <= 100):
        raise DomainError("Une quotité doit être un entier entre 1 et 100 %, ou rester vide.")
    nurse["contracts"] = sorted(
        [c for c in nurse["contracts"] if c["from"] != str(effective)]
        + [{"from": str(effective), "percent": percent}], key=lambda c: c["from"])


@lru_cache(maxsize=40)
def _holidays(year: int) -> frozenset[date]:
    return frozenset(holidays.France(years=year))


def is_holiday(state: dict, day: date) -> bool:
    return day in _holidays(day.year) or str(day) in state["settings"]["extra_holidays"]


def default_tiih(state: dict, day: date) -> bool:
    return day.weekday() in (1, 3, 4) and not is_holiday(state, day)


def tiih_required(state: dict, day: date) -> bool:
    key = str(day)
    if any(target == key for target in state["tiih_changes"].values()):
        return True
    if key in state["tiih_changes"]:
        return False
    return default_tiih(state, day)


def change_tiih(state: dict, origin: date, target: date | None = None,
                *, restore: bool = False) -> None:
    if not default_tiih(state, origin):
        raise DomainError("Choisir un poste TIIH d'origine prévu un mardi, jeudi ou vendredi non férié.")
    key = str(origin)
    previous = state["tiih_changes"].get(key, key)
    destination = str(origin) if restore else (str(target) if target else None)
    if destination is not None:
        dest = date.fromisoformat(destination)
        if is_holiday(state, dest):
            raise DomainError("Un TIIH ne peut pas être déplacé sur un jour férié.")
        others = {k: v for k, v in state["tiih_changes"].items() if k != key}
        occupied = destination in others.values() or (
            destination != key and destination not in others and default_tiih(state, dest))
        if occupied:
            raise DomainError("Cette destination possède déjà un poste TIIH.")
    if previous != destination and previous:
        for assignment in state["assignments"].get(previous, {}).values():
            if assignment["shift"] == "T" and assignment["confirmed"]:
                raise DomainError("Ce TIIH est confirmé réalisé ; corriger d'abord son état si nécessaire.")
    if restore or destination == key:
        state["tiih_changes"].pop(key, None)
    else:
        state["tiih_changes"][key] = destination
    if previous and previous != destination:
        values = state["assignments"].get(previous, {})
        state["assignments"][previous] = {n: a for n, a in values.items() if a["shift"] != "T"}


def local_datetime(day: date, at: time, zone: str = "Europe/Paris") -> datetime:
    naive = datetime.combine(day, at)
    result = naive.replace(tzinfo=ZoneInfo(zone))
    if result.astimezone(UTC).astimezone(ZoneInfo(zone)).replace(tzinfo=None) != naive:
        raise DomainError("Cet horaire local n'existe pas lors du changement d'heure.")
    return result


def time_minute(value: datetime, clock: str = "elapsed") -> int:
    if clock == "wall":
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() // 60)


def shift_interval(day: date, shift: str, zone: str = "Europe/Paris",
                   clock: str = "elapsed") -> tuple[int, int]:
    if shift == "J":
        start, end = local_datetime(day, time(8), zone), local_datetime(day, time(20), zone)
    elif shift == "N":
        start = local_datetime(day, time(20), zone)
        end = local_datetime(day + timedelta(days=1), time(8), zone)
    elif shift == "T":
        start, end = local_datetime(day, time(9), zone), local_datetime(day, time(16, 42), zone)
    else:
        raise DomainError("Type de poste inconnu.")
    return time_minute(start, clock), time_minute(end, clock)


def overlaps(a: int, b: int, c: int, d: int) -> bool:
    return max(a, c) < min(b, d)


def absence_intervals(state: dict, nurse_id: str) -> list[tuple[int, int]]:
    return [(time_minute(datetime.fromisoformat(x["start"])),
             time_minute(datetime.fromisoformat(x["end"])))
            for x in state["absences"] if x["nurse_id"] == nurse_id]


def absent_for(state: dict, nurse_id: str, day: date, shift: str) -> bool:
    a, b = shift_interval(day, shift, state["settings"]["timezone"])
    return any(overlaps(a, b, c, d) for c, d in absence_intervals(state, nurse_id))


def absence_on(state: dict, nurse_id: str, day: date) -> bool:
    zone = state["settings"]["timezone"]
    a = time_minute(local_datetime(day, time(), zone))
    b = time_minute(local_datetime(day + timedelta(days=1), time(), zone))
    return any(overlaps(a, b, c, d) for c, d in absence_intervals(state, nurse_id))


def set_absence(state: dict, nurse_id: str, start: datetime, end: datetime, kind: str,
                daily_minutes: int = 462, *, credits: dict | None = None,
                absence_id: str | None = None) -> str:
    if nurse_id not in {n["id"] for n in state["nurses"]}:
        raise DomainError("IDE inconnue.")
    if start.tzinfo is None or end.tzinfo is None or start.second or end.second:
        raise DomainError("Les horaires doivent être datés, localisés et précis à la minute.")
    a, b = time_minute(start), time_minute(end)
    if a >= b:
        raise DomainError("La fin de l'absence doit être après son début.")
    if (end.date() - start.date()).days > 1100:
        raise DomainError("Saisir les absences par périodes de trois ans maximum.")
    if type(daily_minutes) is not int or not 0 <= daily_minutes <= 1440:
        raise DomainError("Le crédit quotidien doit être entre 0 et 24 heures.")
    for item in state["absences"]:
        if item["id"] != absence_id and item["nurse_id"] == nurse_id:
            if overlaps(a, b, time_minute(datetime.fromisoformat(item["start"])),
                        time_minute(datetime.fromisoformat(item["end"]))):
                raise DomainError("Cette absence chevauche une absence déjà saisie pour cette IDE.")
    zone = ZoneInfo(state["settings"]["timezone"])
    first = start.astimezone(zone).date()
    last = (end.astimezone(UTC) - timedelta(microseconds=1)).astimezone(zone).date()
    allowed = {str(d) for d in dates(first, last)}
    if credits is None:
        credits = {str(d): daily_minutes for d in dates(first, last) if d.weekday() < 5}
    if not set(credits) <= allowed or any(type(v) is not int or not 0 <= v <= 1440
                                        for v in credits.values()):
        raise DomainError("Crédits invalides : dates dans l'absence et durées de 0 à 24 h.")
    key = absence_id or str(uuid4())
    entry = {"id": key, "nurse_id": nurse_id, "kind": str(kind),
             "start": start.isoformat(), "end": end.isoformat(), "credits": dict(credits)}
    state["absences"] = [x for x in state["absences"] if x["id"] != key] + [entry]
    return key


def credit_minutes(state: dict, nurse_id: str, start: date, end: date) -> int:
    return sum(v for x in state["absences"] if x["nurse_id"] == nurse_id
               for d, v in x["credits"].items() if str(start) <= d <= str(end))


def validate_state(state: dict) -> None:
    try:
        if state["schema_version"] != 2 or type(state["revision"]) is not int or state["revision"] < 0:
            raise DomainError("Version ou révision de données invalide.")
        identifiers = [n["id"] for n in state["nurses"]]
        if not identifiers or len(identifiers) != len(set(identifiers)):
            raise DomainError("L'équipe doit avoir des identifiants uniques.")
        for nurse in state["nurses"]:
            if not str(nurse["name"]).strip() or not nurse["contracts"]:
                raise DomainError("Chaque IDE doit avoir un nom et un contrat, même non renseigné.")
            seen = set()
            for c in nurse["contracts"]:
                date.fromisoformat(c["from"])
                if c["from"] in seen or (c["percent"] is not None and
                    (type(c["percent"]) is not int or not 1 <= c["percent"] <= 100)):
                    raise DomainError("Date de contrat dupliquée ou quotité invalide (1 à 100 %).")
                seen.add(c["from"])
        settings = state["settings"]
        ZoneInfo(settings["timezone"])
        if settings["rest_clock"] not in (None, "elapsed", "wall"):
            raise DomainError("Convention de repos invalide.")
        bounds = [settings[k] for k in ("phase_min", "phase_target", "phase_max")]
        if any(type(v) is not int for v in bounds) or not 2 <= bounds[0] <= bounds[1] <= bounds[2] <= 60:
            raise DomainError("Respecter 2 ≤ minimum ≤ cible ≤ maximum ≤ 60 jours.")
        for d in settings["extra_holidays"]:
            date.fromisoformat(d)
        for y, value in state["oat"].items():
            if not 1900 <= int(y) <= 2200 or type(value) is not int or not 0 < value <= 366*1440:
                raise DomainError("OAT invalide.")
        for day, values in state["assignments"].items():
            date.fromisoformat(day)
            for nurse_id, item in values.items():
                if nurse_id not in identifiers or item["shift"] not in SHIFT_MINUTES:
                    raise DomainError("Affectation liée à une IDE ou un poste inconnu.")
                if type(item["locked"]) is not bool or type(item["confirmed"]) is not bool:
                    raise DomainError("État d'affectation invalide.")
        for day, values in state["phases"].items():
            date.fromisoformat(day)
            for nurse_id, p in values.items():
                if nurse_id not in identifiers or p["mode"] not in ("J", "N") or type(p["age"]) is not int or not 1 <= p["age"] <= 60:
                    raise DomainError("Période de régime invalide.")
        for day, ids in state["reviewed"].items():
            date.fromisoformat(day)
            if not set(ids) <= set(identifiers):
                raise DomainError("Historique associé à une IDE inconnue.")
        for source, dest in state["tiih_changes"].items():
            date.fromisoformat(source)
            if dest is not None:
                date.fromisoformat(dest)
        targets = [x for x in state["tiih_changes"].values() if x is not None]
        if len(targets) != len(set(targets)):
            raise DomainError("Plusieurs TIIH sont déplacés vers la même date.")
        scratch = {**state, "absences": []}
        seen_ids = set()
        for item in state["absences"]:
            if item["id"] in seen_ids:
                raise DomainError("Absence dupliquée.")
            seen_ids.add(item["id"])
            set_absence(scratch, item["nurse_id"], datetime.fromisoformat(item["start"]),
                        datetime.fromisoformat(item["end"]), item["kind"],
                        credits=item["credits"], absence_id=item["id"])
    except DomainError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise DomainError(f"Structure des données invalide : {exc}") from exc


def annual_totals(state: dict, year: int) -> list[dict]:
    start, end = date(year, 1, 1), date(year, 12, 31)
    days = list(dates(start, end))
    result = []
    for nurse in state["nurses"]:
        nid = nurse["id"]
        planned = confirmed = conflicts = 0
        for day, assignments in state["assignments"].items():
            if str(start) <= day <= str(end) and nid in assignments:
                item = assignments[nid]
                if item["shift"] == "-":
                    continue
                if absent_for(state, nid, date.fromisoformat(day), item["shift"]):
                    conflicts += 1
                    continue
                if item["confirmed"]:
                    confirmed += SHIFT_MINUTES[item["shift"]]
                else:
                    planned += SHIFT_MINUTES[item["shift"]]
        credit = credit_minutes(state, nid, start, end)
        quotas = [quota_on(nurse, d) for d in days]
        oat = state["oat"].get(str(year))
        target = round(oat * sum(quotas) / (100 * len(days))) if oat and all(q is not None for q in quotas) else None
        total = None if conflicts else planned + confirmed + credit
        result.append({"nurse_id": nid, "name": nurse["name"], "planned_minutes": planned,
                       "confirmed_minutes": confirmed, "absence_minutes": credit,
                       "total_minutes": total, "target_minutes": target,
                       "remaining_minutes": target-total if target is not None and total is not None else None,
                       "conflicts": conflicts,
                       "reviewed_days": sum(nid in state["reviewed"].get(str(d), []) for d in days)})
    return result


def validate_schedule(state: dict, start: date, end: date, *, coverage: bool = True) -> list[Issue]:
    validate_state(state)
    issues: list[Issue] = []
    zone = state["settings"]["timezone"]
    clock = state["settings"]["rest_clock"]
    names = {n["id"]: n["name"] for n in state["nurses"]}
    if clock is None:
        issues.append(Issue("rest_convention", "Choisir la convention de calcul des 12 h de repos.", "warning"))
    if any(quota_on(n, d) is None for n in state["nurses"] for d in dates(start, end)):
        issues.append(Issue("quota", "Certaines quotités restent à renseigner pour cette période.", "warning"))
    before = list(dates(start-timedelta(days=8), start-timedelta(days=1)))
    after = list(dates(end+timedelta(days=1), end+timedelta(days=8)))
    for code, label, context in [("history", "Historique antérieur", before), ("future", "Contexte suivant", after)]:
        missing = sum(n not in state["reviewed"].get(str(d), []) for d in context for n in names)
        if missing:
            issues.append(Issue(code, f"{label} incomplet : {missing} journées-IDE à renseigner ; validation provisoire.", "warning"))
    if coverage:
        for day in dates(start, end):
            counts = {s: sum(a["shift"] == s for a in state["assignments"].get(str(day), {}).values()) for s in ("J", "N", "T")}
            needs = {"J": 1, "N": 1, "T": int(tiih_required(state, day))}
            for shift, need in needs.items():
                if counts[shift] != need:
                    issues.append(Issue("coverage", f"{day:%d/%m} · {SHIFT_LABELS[shift]} : {counts[shift]} affectation(s), {need} attendue(s).", day=str(day)))
    for source, target in state["tiih_changes"].items():
        if target and start <= date.fromisoformat(target) <= end and is_holiday(state, date.fromisoformat(target)):
            issues.append(Issue("holiday", "Un TIIH déplacé se trouve sur un jour férié.", day=target))
    cstart, cend = start-timedelta(days=8), end+timedelta(days=8)
    scope_a = time_minute(local_datetime(start, time(), zone))
    scope_b = time_minute(local_datetime(end+timedelta(days=1), time(), zone))
    for nid, name in names.items():
        work = []
        by_day = {}
        for day in dates(cstart, cend):
            entry = state["assignments"].get(str(day), {}).get(nid)
            if entry and entry["shift"] != "-":
                code = entry["shift"]
                a, b = shift_interval(day, code, zone)
                work.append((a, b, day, code))
                by_day[day] = code
                if start <= day <= end and absent_for(state, nid, day, code):
                    issues.append(Issue("absence", f"{name} · {day:%d/%m} : poste pendant une absence.", nurse_id=nid, day=str(day)))
        work.sort()
        if clock:
            for first, second in zip(work, work[1:]):
                if not (start <= first[2] <= end or start <= second[2] <= end):
                    continue
                _, b = shift_interval(first[2], first[3], zone, clock)
                a, _ = shift_interval(second[2], second[3], zone, clock)
                if a-b < 720:
                    issues.append(Issue("rest", f"{name} · {first[2]:%d/%m} → {second[2]:%d/%m} : repos {format_minutes(a-b)}, minimum 12 h.", nurse_id=nid, day=str(second[2])))
        for day in dates(start-timedelta(days=3), end):
            block = [day+timedelta(days=i) for i in range(4)]
            if all(d in by_day for d in block):
                issues.append(Issue("consecutive", f"{name} : quatre prises de poste consécutives du {block[0]:%d/%m} au {block[-1]:%d/%m}.", nurse_id=nid, day=str(day)))
        windows = {x for a, b, _, _ in work for x in (a, b, a-10080, b-10080)}
        worst, worst_start = 0, 0
        for w in windows:
            if not overlaps(w, w+10080, scope_a, scope_b):
                continue
            total = sum(max(0, min(b, w+10080)-max(a, w)) for a, b, _, _ in work)
            if total > worst:
                worst, worst_start = total, w
        if worst > 2880:
            when = datetime.fromtimestamp(worst_start*60, UTC).astimezone(ZoneInfo(zone))
            issues.append(Issue("weekly", f"{name} : {format_minutes(worst)} travaillées sur 168 h à partir du {when:%d/%m à %H:%M}, maximum 48 h.", nurse_id=nid, day=str(when.date())))
        for saturday in dates(start-timedelta(days=2), end):
            if saturday.weekday() != 5:
                continue
            sunday, monday = saturday+timedelta(days=1), saturday+timedelta(days=2)
            if not any(start <= d <= end for d in (saturday, sunday, monday)):
                continue
            known = all(start <= d <= end or nid in state["reviewed"].get(str(d), []) or d in by_day for d in (saturday, sunday))
            if known and by_day.get(saturday) != by_day.get(sunday):
                issues.append(Issue("weekend", f"{name} : samedi {saturday:%d/%m} et dimanche doivent être travaillés ensemble au même poste.", nurse_id=nid, day=str(saturday)))
            if sunday in by_day and monday in by_day:
                issues.append(Issue("monday", f"{name} : nouvelle prise de poste le lundi {monday:%d/%m} après un dimanche travaillé.", nurse_id=nid, day=str(monday)))
        missing_phases = 0
        for day in dates(start, end):
            current = state["phases"].get(str(day), {}).get(nid)
            previous = state["phases"].get(str(day-timedelta(days=1)), {}).get(nid)
            if not current or not previous:
                missing_phases += 1
            if current:
                if current["age"] > state["settings"]["phase_max"]:
                    issues.append(Issue("regime", f"{name} : période au-delà de la durée maximale le {day:%d/%m}.", nurse_id=nid, day=str(day)))
                shift = by_day.get(day)
                if shift and (shift == "N") != (current["mode"] == "N"):
                    issues.append(Issue("regime", f"{name} : poste incompatible avec le régime du {day:%d/%m}.", nurse_id=nid, day=str(day)))
                if previous:
                    changed = current["mode"] != previous["mode"]
                    valid = (current["age"] == 1 and previous["age"] >= state["settings"]["phase_min"]) if changed else current["age"] == previous["age"]+1
                    if not valid:
                        issues.append(Issue("regime", f"{name} : transition ou âge du régime incohérent le {day:%d/%m}.", nurse_id=nid, day=str(day)))
        if missing_phases:
            issues.append(Issue("phase_history", f"{name} : contexte des périodes jour/nuit incomplet ({missing_phases} date(s)).", "warning", nid))
    return issues
