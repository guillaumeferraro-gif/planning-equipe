"""Point d’entrée du moteur : generate_schedule(state, year, month).

Les fichiers historiques sont repris depuis l’interface Données.
"""
from planning.solver import ScheduleResult, generate_schedule

__all__ = ["ScheduleResult", "generate_schedule"]
