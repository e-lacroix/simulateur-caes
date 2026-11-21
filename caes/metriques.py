"""Indicateurs d'écart entre simulation et référence.

Équations 18 et 19 de Dormoy (2024), voir formules.md#F14 : RMSE et
MAPE. Sert aux scripts de ``validation/``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def rmse(simule: np.ndarray, mesure: np.ndarray) -> float:
    """Racine de l'erreur quadratique moyenne (mêmes unités que y)."""
    simule = np.asarray(simule, dtype=float)
    mesure = np.asarray(mesure, dtype=float)
    return float(np.sqrt(np.mean((simule - mesure) ** 2)))


def mape(simule: np.ndarray, mesure: np.ndarray) -> float:
    """Erreur absolue moyenne en pourcentage de la mesure."""
    simule = np.asarray(simule, dtype=float)
    mesure = np.asarray(mesure, dtype=float)
    if np.any(mesure == 0):
        raise ValueError("MAPE indéfini : une mesure vaut zéro")
    return float(np.mean(np.abs((simule - mesure) / mesure)) * 100.0)


def ecart_relatif_pct(simule: float, reference: float) -> float:
    """(simulé − référence) / référence, en pourcent."""
    return (simule - reference) / reference * 100.0


def lire_courbe_numerisee(chemin: Path | str) -> pd.DataFrame:
    """Lit un CSV de ``data/validation/`` (lignes ``#`` ignorées)."""
    return pd.read_csv(chemin, comment="#")


def comparer_sur_grille(
    t_sim: np.ndarray,
    y_sim: np.ndarray,
    t_ref: np.ndarray,
    y_ref: np.ndarray,
) -> dict[str, float]:
    """Interpole la simulation aux instants de la référence, puis RMSE/MAPE."""
    y_interp = np.interp(t_ref, t_sim, y_sim)
    return {"rmse": rmse(y_interp, y_ref), "mape_pct": mape(y_interp, y_ref)}
