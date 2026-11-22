# -*- coding: utf-8 -*-
"""Propagation des incertitudes du registre vers les résultats
(formules.md#F45).

Chaque paramètre retenu est tiré uniformément dans sa plage (plage
publiée du registre, ou ± écart pour une hypothèse) par un hypercube
latin (``scipy.stats.qmc.LatinHypercube``) ; les sorties sont données
avec leur intervalle (minimum, 5e centile, médiane, 95e centile,
maximum) et la corrélation de rang de chaque paramètre avec chaque
sortie (Spearman), qui dit dans quel sens et avec quelle force il agit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from caes.analyse.evaluation import Evaluateur, ResultatPoint
from caes.analyse.parametres import ParametreAnalyse


@dataclass
class IntervalleSortie:
    sortie: str
    nominal: float
    minimum: float
    p05: float
    mediane: float
    p95: float
    maximum: float
    ecart_type: float
    n_valides: int

    @property
    def demi_largeur_90(self) -> float:
        return 0.5 * (self.p95 - self.p05)


@dataclass
class ResultatIncertitudes:
    parametres: list[ParametreAnalyse]
    sorties: list[str]
    n: int
    graine: int
    echantillons: np.ndarray
    """Forme (n, d), valeurs SI (ou facteurs)."""
    valeurs: np.ndarray
    """Forme (n, s), nan pour les simulations échouées."""
    intervalles: list[IntervalleSortie]
    spearman: np.ndarray
    """Forme (s, d) : corrélation de rang paramètre → sortie."""
    resultats: list[ResultatPoint] = field(default_factory=list)

    @property
    def echecs(self) -> int:
        return int(np.isnan(self.valeurs).any(axis=1).sum())

    def intervalle(self, sortie: str) -> IntervalleSortie:
        return self.intervalles[self.sorties.index(sortie)]


def propager(
    ev: Evaluateur, parametres: list[ParametreAnalyse],
    sorties: list[str], n: int = 64, graine: int = 1, rappel=None,
) -> ResultatIncertitudes:
    """Hypercube latin de ``n`` points dans les plages, simulations,
    intervalles et corrélations de rang."""
    d = len(parametres)
    if d == 0:
        raise ValueError("aucun paramètre à propager")
    lhs = stats.qmc.LatinHypercube(d=d, seed=graine)
    u = lhs.random(n)
    bas = np.array([p.minimum for p in parametres])
    haut = np.array([p.maximum for p in parametres])
    x = stats.qmc.scale(u, bas, haut)
    noms = [p.nom for p in parametres]
    nominal = ev.evaluer(ev.point_nominal(parametres))
    points = [dict(zip(noms, ligne)) for ligne in x]
    res = ev.evaluer_points(points, rappel)
    y = np.full((n, len(sorties)), np.nan)
    for i, r in enumerate(res):
        if r.valide:
            y[i] = [r.sorties[s] for s in sorties]
    intervalles = []
    for j, s in enumerate(sorties):
        col = y[:, j]
        v = col[~np.isnan(col)]
        if v.size == 0:
            intervalles.append(IntervalleSortie(
                s, nominal.sorties.get(s, float("nan")), *([float("nan")]
                                                           * 6), 0))
            continue
        intervalles.append(IntervalleSortie(
            s, nominal.sorties.get(s, float("nan")), float(v.min()),
            float(np.percentile(v, 5)), float(np.median(v)),
            float(np.percentile(v, 95)), float(v.max()),
            float(v.std(ddof=1)) if v.size > 1 else 0.0, int(v.size)))
    rho = np.full((len(sorties), d), np.nan)
    for j in range(len(sorties)):
        ok = ~np.isnan(y[:, j])
        if ok.sum() < 3:
            continue
        for k in range(d):
            if np.ptp(x[ok, k]) == 0 or np.ptp(y[ok, j]) == 0:
                rho[j, k] = 0.0
            else:
                rho[j, k] = stats.spearmanr(x[ok, k], y[ok, j]).statistic
    return ResultatIncertitudes(parametres, sorties, n, graine, x, y,
                                intervalles, rho, res)
