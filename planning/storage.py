"""Persistance locale atomique et reprise non destructive de l'ancien format."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import NAMESPACE_URL, uuid5

from filelock import FileLock, Timeout

from .domain import DomainError, dates, month_bounds, new_state, validate_state


class StorageError(RuntimeError):
    pass


class Store:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "planning-state.json"
        self.backup = self.directory / "planning-state.backup.json"
        self.lock = FileLock(str(self.directory / "planning-state.lock"), timeout=5)

    def _read(self) -> dict:
        if not self.path.exists():
            return new_state()
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            validate_state(state)
            return state
        except (OSError, ValueError, DomainError) as exc:
            raise StorageError(f"Impossible de lire les données ; le fichier est conservé. {exc}") from exc

    def load(self) -> dict:
        try:
            with self.lock:
                return self._read()
        except Timeout as exc:
            raise StorageError("Les données sont en cours d'utilisation. Réessayer.") from exc

    @staticmethod
    def _atomic(path: Path, content: str) -> None:
        handle, name = tempfile.mkstemp(prefix=".planning-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as file:
                file.write(content)
                file.flush()
                os.fsync(file.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def save(self, state: dict, *, expected_revision: int) -> dict:
        candidate = deepcopy(state)
        validate_state(candidate)
        try:
            with self.lock:
                current = self._read()
                if current["revision"] != expected_revision:
                    raise StorageError("Les données ont changé dans une autre session. Recharger avant de réessayer ; aucune modification n'a été écrasée.")
                candidate["revision"] = expected_revision + 1
                encoded = json.dumps(candidate, ensure_ascii=False, indent=2, allow_nan=False)
                if self.path.exists():
                    self._atomic(self.backup, self.path.read_text(encoding="utf-8"))
                self._atomic(self.path, encoded)
                return candidate
        except Timeout as exc:
            raise StorageError("Une autre écriture est en cours. Réessayer.") from exc
        except OSError as exc:
            raise StorageError(f"Enregistrement impossible : {exc}") from exc


def import_legacy(state: dict, directory: str | Path) -> tuple[dict, list[str]]:
    """Construit un candidat ; ne modifie ni les sources ni l'état reçu."""
    candidate = deepcopy(state)
    paths = sorted(Path(directory).glob("planning_*.json"))
    if not paths:
        raise StorageError("Aucun ancien fichier planning_année_mois.json trouvé.")
    records = []
    names = set()
    warnings = []
    try:
        for path in paths:
            match = re.fullmatch(r"planning_(\d{4})_(\d{2})\.json", path.name)
            if not match:
                continue
            year, month = map(int, match.groups())
            first, last = month_bounds(year, month)
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or not raw:
                raise ValueError(f"Fichier vide ou invalide : {path.name}")
            for name, values in raw.items():
                if not str(name).strip() or not isinstance(values, dict):
                    raise ValueError(f"Ligne invalide dans {path.name}")
                names.add(name)
                for day, label in values.items():
                    actual = date(year, month, int(day))
                    if not isinstance(label, str):
                        raise ValueError(f"Poste illisible dans {path.name}, jour {day}")
                    if label.strip() in ("-", "", "Repos"):
                        shift = "-"
                    elif label in ("J", "SMUR J") or "JOUR" in label or "☀" in label:
                        shift = "J"
                    elif label in ("N", "SMUR N") or "NUIT" in label or "🌙" in label:
                        shift = "N"
                    elif label in ("T", "TIIH") or "TIIH" in label or "🛠" in label:
                        shift = "T"
                    else:
                        raise ValueError(f"Valeur non reconnue dans {path.name}, jour {day} : {label}")
                    records.append((str(actual), name, shift))
                if set(values) != {str(d.day) for d in dates(first, last)}:
                    warnings.append(f"{path.name} : historique incomplet pour une IDE.")
        if not records:
            raise ValueError("Aucun planning reconnu.")
        if not candidate["assignments"] and not candidate["absences"] and all(
            n["name"] == f"IDE {chr(65+i)}" for i, n in enumerate(candidate["nurses"])):
            candidate["nurses"] = []
            candidate["phases"] = {}
            candidate["reviewed"] = {}
        mapping = {n["name"]: n["id"] for n in candidate["nurses"]}
        for name in sorted(names):
            if name not in mapping:
                nid = str(uuid5(NAMESPACE_URL, "planning-ide/" + name))
                candidate["nurses"].append({"id": nid, "name": name,
                                            "contracts": [{"from": "1900-01-01", "percent": None}]})
                mapping[name] = nid
        for day, name, shift in records:
            nid = mapping[name]
            current = candidate["assignments"].get(day, {}).get(nid)
            if current and current["shift"] != shift:
                raise ValueError(f"Un planning différent existe déjà le {day} ; import annulé.")
            if not current:
                candidate["assignments"].setdefault(day, {})[nid] = {
                    "shift": shift, "locked": False, "confirmed": False}
            candidate["reviewed"][day] = sorted(set(candidate["reviewed"].get(day, [])) | {nid})
        validate_state(candidate)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        raise StorageError(f"Import annulé sans modifier les sources : {exc}") from exc
    warnings.append("Plannings repris comme brouillons ; quotités, régimes et contraintes à vérifier.")
    return candidate, warnings
