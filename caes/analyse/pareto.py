# -*- coding: utf-8 -*-
"""Front de Pareto à deux objectifs par NSGA-II (formules.md#F46).

Implémentation compacte de Deb et al. 2002 : tri par rangs de
non-dominance, distance d'encombrement, sélection par tournoi binaire,
croisement SBX et mutation polynomiale, élitisme (parents + enfants).
Les variables sont normalisées dans [0, 1] ; les objectifs sont tous
ramenés à une **minimisation** (un objectif à maximiser est pris avec
le signe moins). Tous les réglages sont dans :class:`ReglagesNSGA2` et
sont imprimés dans le rapport, pour que le front soit reproductible
(graine fixe), ce que Wang 2020 ne documente pas.

Une évaluation échouée (nan) reçoit une pénalité : elle est dominée par
tout point valide.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class ReglagesNSGA2:
    population: int = 24
    generations: int = 15
    p_croisement: float = 0.9
    eta_croisement: float = 15.0
    p_mutation: float | None = None
    """Probabilité de mutation par variable (défaut : 1 / nombre de
    variables)."""
    eta_mutation: float = 20.0
    graine: int = 1

    def __post_init__(self) -> None:
        if self.population < 4 or self.population % 2:
            raise ValueError("population : au moins 4, paire")
        if self.generations < 1:
            raise ValueError("generations : au moins 1")


def tri_non_domine(F: np.ndarray) -> list[list[int]]:
    """Rangs de non-dominance (minimisation) : liste de fronts, chacun
    une liste d'indices. Front 0 = points non dominés."""
    n = F.shape[0]
    domine_par = [0] * n
    domines: list[list[int]] = [[] for _ in range(n)]
    fronts: list[list[int]] = [[]]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if _domine(F[i], F[j]):
                domines[i].append(j)
            elif _domine(F[j], F[i]):
                domine_par[i] += 1
        if domine_par[i] == 0:
            fronts[0].append(i)
    k = 0
    while fronts[k]:
        suivant = []
        for i in fronts[k]:
            for j in domines[i]:
                domine_par[j] -= 1
                if domine_par[j] == 0:
                    suivant.append(j)
        k += 1
        fronts.append(suivant)
    fronts.pop()
    return fronts


def _domine(a: np.ndarray, b: np.ndarray) -> bool:
    return bool(np.all(a <= b) and np.any(a < b))


def distance_encombrement(F: np.ndarray, front: list[int]) -> np.ndarray:
    """Distance d'encombrement de chaque point du front (∞ aux bouts)."""
    m = len(front)
    dist = np.zeros(m)
    if m <= 2:
        dist[:] = np.inf
        return dist
    sub = F[front]
    for k in range(F.shape[1]):
        ordre = np.argsort(sub[:, k])
        etendue = sub[ordre[-1], k] - sub[ordre[0], k]
        dist[ordre[0]] = dist[ordre[-1]] = np.inf
        if etendue <= 0:
            continue
        for i in range(1, m - 1):
            dist[ordre[i]] += (sub[ordre[i + 1], k]
                               - sub[ordre[i - 1], k]) / etendue
    return dist


def _rangs_et_distances(F: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rang = np.empty(F.shape[0], dtype=int)
    dist = np.empty(F.shape[0])
    for k, front in enumerate(tri_non_domine(F)):
        rang[front] = k
        dist[front] = distance_encombrement(F, front)
    return rang, dist


def _tournoi(rang: np.ndarray, dist: np.ndarray,
             rng: np.random.Generator, n: int) -> np.ndarray:
    a = rng.integers(0, rang.size, n)
    b = rng.integers(0, rang.size, n)
    meilleur_a = (rang[a] < rang[b]) | ((rang[a] == rang[b])
                                        & (dist[a] > dist[b]))
    return np.where(meilleur_a, a, b)


def _sbx(p1: np.ndarray, p2: np.ndarray, eta: float, prob: float,
         rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Croisement binaire simulé (Deb et Agrawal 1995), variables dans
    [0, 1]."""
    c1, c2 = p1.copy(), p2.copy()
    if rng.random() > prob:
        return c1, c2
    for k in range(p1.size):
        if rng.random() > 0.5 or abs(p1[k] - p2[k]) < 1e-12:
            continue
        u = rng.random()
        if u <= 0.5:
            beta = (2.0 * u) ** (1.0 / (eta + 1.0))
        else:
            beta = (1.0 / (2.0 * (1.0 - u))) ** (1.0 / (eta + 1.0))
        c1[k] = 0.5 * ((1 + beta) * p1[k] + (1 - beta) * p2[k])
        c2[k] = 0.5 * ((1 - beta) * p1[k] + (1 + beta) * p2[k])
    return np.clip(c1, 0.0, 1.0), np.clip(c2, 0.0, 1.0)


def _mutation_polynomiale(x: np.ndarray, eta: float, prob: float,
                          rng: np.random.Generator) -> np.ndarray:
    y = x.copy()
    for k in range(x.size):
        if rng.random() > prob:
            continue
        u = rng.random()
        if u < 0.5:
            delta = (2.0 * u) ** (1.0 / (eta + 1.0)) - 1.0
        else:
            delta = 1.0 - (2.0 * (1.0 - u)) ** (1.0 / (eta + 1.0))
        y[k] = x[k] + delta
    return np.clip(y, 0.0, 1.0)


@dataclass
class ResultatPareto:
    reglages: ReglagesNSGA2
    X: np.ndarray
    """Toutes les variables évaluées (normalisées), forme (N, d)."""
    F: np.ndarray
    """Objectifs correspondants (minimisation, nan si échec), (N, m)."""
    front: np.ndarray
    """Indices (dans X, F) des points non dominés valides."""
    generations: list[np.ndarray] = field(default_factory=list)
    """Indices de la population à la fin de chaque génération."""

    @property
    def evaluations(self) -> int:
        return int(self.X.shape[0])

    @property
    def echecs(self) -> int:
        return int(np.isnan(self.F).any(axis=1).sum())


def _penaliser(F: np.ndarray) -> np.ndarray:
    """Remplace les nan par une valeur pire que tout point valide."""
    G = F.copy()
    mauvais = np.isnan(G).any(axis=1)
    if not mauvais.any():
        return G
    for k in range(G.shape[1]):
        col = G[~mauvais, k]
        pire = col.max() if col.size else 0.0
        etendue = np.ptp(col) if col.size > 1 else 1.0
        G[mauvais, k] = pire + etendue + 1.0
    return G


def nsga2(
    evaluer: Callable[[np.ndarray], np.ndarray], d: int,
    reglages: ReglagesNSGA2 = ReglagesNSGA2(),
    rappel: Callable[[int, np.ndarray, np.ndarray], None] | None = None,
) -> ResultatPareto:
    """``evaluer(U)`` reçoit une matrice (k, d) de variables dans [0, 1]
    et rend (k, m) objectifs à minimiser (nan si échec)."""
    r = reglages
    rng = np.random.default_rng(r.graine)
    p_mut = r.p_mutation if r.p_mutation is not None else 1.0 / d
    X = rng.random((r.population, d))
    F = np.asarray(evaluer(X), dtype=float)
    X_tous, F_tous = [X], [F]
    pop = np.arange(r.population)
    generations = []
    decalage = r.population
    for g in range(r.generations):
        G = _penaliser(F)
        rang, dist = _rangs_et_distances(G)
        parents = _tournoi(rang, dist, rng, r.population)
        enfants = []
        for i in range(0, r.population, 2):
            c1, c2 = _sbx(X[parents[i]], X[parents[i + 1]],
                          r.eta_croisement, r.p_croisement, rng)
            enfants.append(_mutation_polynomiale(c1, r.eta_mutation,
                                                 p_mut, rng))
            enfants.append(_mutation_polynomiale(c2, r.eta_mutation,
                                                 p_mut, rng))
        Xe = np.array(enfants)
        Fe = np.asarray(evaluer(Xe), dtype=float)
        X_tous.append(Xe)
        F_tous.append(Fe)
        indices_e = np.arange(decalage, decalage + r.population)
        decalage += r.population
        # élitisme : parents + enfants, on garde la meilleure moitié
        Xc = np.vstack([X, Xe])
        Fc = np.vstack([F, Fe])
        idc = np.concatenate([pop, indices_e])
        Gc = _penaliser(Fc)
        garde: list[int] = []
        for front in tri_non_domine(Gc):
            if len(garde) + len(front) <= r.population:
                garde.extend(front)
            else:
                dist_f = distance_encombrement(Gc, front)
                ordre = np.argsort(-dist_f)
                garde.extend(front[i] for i in ordre[
                    :r.population - len(garde)])
                break
        X, F, pop = Xc[garde], Fc[garde], idc[garde]
        generations.append(pop.copy())
        if rappel is not None:
            rappel(g + 1, X, F)
    X_all = np.vstack(X_tous)
    F_all = np.vstack(F_tous)
    valides = np.where(~np.isnan(F_all).any(axis=1))[0]
    front_idx = np.array([], dtype=int)
    if valides.size:
        f0 = tri_non_domine(F_all[valides])[0]
        front_idx = valides[np.array(f0)]
        # un seul représentant par point du front (la population finale
        # contient souvent des copies d'un même individu)
        uniques: dict[tuple[float, ...], int] = {}
        for i in front_idx:
            uniques.setdefault(tuple(np.round(F_all[i], 9)), int(i))
        front_idx = np.array(sorted(uniques.values(),
                                    key=lambda i: F_all[i, 0]), dtype=int)
    return ResultatPareto(r, X_all, F_all, front_idx, generations)
