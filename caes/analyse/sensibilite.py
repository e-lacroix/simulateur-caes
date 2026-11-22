# -*- coding: utf-8 -*-
"""Sensibilité d'une configuration (formules.md#F45).

* **Un paramètre à la fois** : chaque paramètre est mis à sa borne
  basse puis haute, les autres restant à leur valeur nominale ; l'écart
  entre les deux sorties (« balancement ») classe les paramètres
  (graphique en tornade). Simple et lisible, mais aveugle aux
  interactions.
* **Indices de Sobol** (sensibilité globale) : les paramètres sont tirés
  ensemble dans leurs plages (suite de Sobol, estimateur de Saltelli
  via ``scipy.stats.sobol_indices``) ; l'indice de premier ordre S_i
  est la part de la variance de la sortie due au paramètre i seul,
  l'indice total S_Ti inclut ses interactions. Coût : n·(d + 2)
  simulations pour d paramètres et n échantillons de base.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from caes.analyse.evaluation import Evaluateur, ResultatPoint
from caes.analyse.parametres import ParametreAnalyse


@dataclass
class LigneTornade:
    parametre: ParametreAnalyse
    sortie: str
    nominal: float
    bas: float
    """Sortie quand le paramètre est à sa borne basse."""
    haut: float
    """Sortie quand le paramètre est à sa borne haute."""

    @property
    def balancement(self) -> float:
        return abs(self.haut - self.bas)


@dataclass
class ResultatTornade:
    lignes: list[LigneTornade]
    nominal: ResultatPoint
    resultats: list[ResultatPoint]
    """Tous les points évalués (nominal, puis bas et haut par paramètre)."""

    def classement(self, sortie: str) -> list[LigneTornade]:
        """Lignes de la sortie, du plus grand balancement au plus petit
        (les écarts non calculables, nan, à la fin)."""
        lignes = [li for li in self.lignes if li.sortie == sortie]
        return sorted(lignes, key=lambda li: (
            np.isnan(li.balancement), -li.balancement
            if not np.isnan(li.balancement) else 0.0))

    @property
    def echecs(self) -> list[ResultatPoint]:
        return [r for r in self.resultats if not r.valide]


def un_parametre_a_la_fois(
    ev: Evaluateur, parametres: list[ParametreAnalyse],
    sorties: list[str], rappel=None,
) -> ResultatTornade:
    """Nominal, puis chaque paramètre à ses deux bornes (2d + 1 runs)."""
    nominal = ev.point_nominal(parametres)
    points = [dict(nominal)]
    for p in parametres:
        for x in (p.minimum, p.maximum):
            pt = dict(nominal)
            pt[p.nom] = x
            points.append(pt)
    res = ev.evaluer_points(points, rappel)
    lignes = []
    for k, p in enumerate(parametres):
        r_bas, r_haut = res[1 + 2 * k], res[2 + 2 * k]
        for s in sorties:
            lignes.append(LigneTornade(
                p, s, res[0].sorties[s], r_bas.sorties[s],
                r_haut.sorties[s]))
    return ResultatTornade(lignes, res[0], res)


@dataclass
class ResultatSobol:
    parametres: list[ParametreAnalyse]
    sorties: list[str]
    n: int
    graine: int
    premier_ordre: np.ndarray
    """S_i, forme (sorties, paramètres)."""
    total: np.ndarray
    """S_Ti, forme (sorties, paramètres)."""
    premier_ordre_ic: np.ndarray | None = None
    """Intervalle de confiance à 95 % (bootstrap), forme (2, s, d)."""
    total_ic: np.ndarray | None = None
    resultats: list[ResultatPoint] = field(default_factory=list)
    echecs: int = 0
    """Points remplacés par la valeur nominale (simulation échouée)."""

    def classement(self, sortie: str) -> list[tuple[ParametreAnalyse,
                                                    float, float]]:
        i = self.sorties.index(sortie)
        ordre = np.argsort(-self.total[i])
        return [(self.parametres[j], float(self.premier_ordre[i, j]),
                 float(self.total[i, j])) for j in ordre]


def indices_de_sobol(
    ev: Evaluateur, parametres: list[ParametreAnalyse],
    sorties: list[str], n: int = 64, graine: int = 1,
    bootstrap: bool = True, rappel=None,
) -> ResultatSobol:
    """Indices de Sobol de premier ordre et totaux par l'estimateur de
    Saltelli (``scipy.stats.sobol_indices``), paramètres uniformes dans
    leurs plages. ``n`` doit être une puissance de 2."""
    if n & (n - 1):
        raise ValueError("n doit être une puissance de 2")
    noms = [p.nom for p in parametres]
    tous: list[ResultatPoint] = []
    echecs = 0
    nominal = ev.evaluer(ev.point_nominal(parametres))
    if not nominal.valide:
        raise ValueError("la simulation nominale échoue : "
                         f"{nominal.erreur or nominal.arret}")

    def f(x: np.ndarray) -> np.ndarray:
        nonlocal echecs
        points = [dict(zip(noms, col)) for col in x.T]
        res = ev.evaluer_points(points, rappel)
        tous.extend(res)
        out = np.empty((len(sorties), x.shape[1]))
        for j, r in enumerate(res):
            if r.valide:
                out[:, j] = [r.sorties[s] for s in sorties]
            else:
                echecs += 1
                out[:, j] = [nominal.sorties[s] for s in sorties]
        return out

    lois = [stats.uniform(loc=p.minimum, scale=p.maximum - p.minimum)
            for p in parametres]
    res = stats.sobol_indices(func=f, n=n, dists=lois,
                              random_state=graine)
    s1 = np.atleast_2d(res.first_order)
    st = np.atleast_2d(res.total_order)
    ic1 = ict = None
    if bootstrap:
        # le rééchantillonnage de scipy n'accepte pas de graine : on fixe
        # celle du générateur global pour que l'intervalle soit
        # reproductible
        np.random.seed(graine)
        try:
            b = res.bootstrap(confidence_level=0.95, n_resamples=200)
            ic1 = np.stack([np.atleast_2d(b.first_order.confidence_interval
                                          .low),
                            np.atleast_2d(b.first_order.confidence_interval
                                          .high)])
            ict = np.stack([np.atleast_2d(b.total_order.confidence_interval
                                          .low),
                            np.atleast_2d(b.total_order.confidence_interval
                                          .high)])
        except (ValueError, RuntimeWarning):
            ic1 = ict = None
    return ResultatSobol(parametres, sorties, n, graine, s1, st, ic1, ict,
                         tous, echecs)
