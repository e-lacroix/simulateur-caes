"""Turbine hors de son point nominal : formule de Flügel modifiée
(Zhang S. et al. 2025, éq. 1 à 6), formules.md#F39.

Débit réduit relatif (loi de l'ellipse de Stodola) :
    Ġ = sqrt((p_in² − p_out²) / (p_in0² − p_out0²)) · sqrt(T0 / T_in)
    · (p_in0 / p_in)   avec   G = G0 · Ġ · (p_in / p_in0) · sqrt(T0 / T_in)
soit, pour le débit : G = G0 · sqrt(T0/T_in) · sqrt((p_in² − p_out²) /
(p_in0² − p_out0²)).

Rendement relatif (éq. 2 et 3 de Zhang, t4 = 0,3) :
    η/η0 = [1 − t4·(1 − ṅ)²] · (ṅ/Ġ) · (2 − ṅ/Ġ),
    ṅ = (n/√T_in) / (n/√T_in)_0 = sqrt(T0/T_in) à vitesse constante.

Pour une turbine à plusieurs étages en pression glissante, les
pressions entre étages s'ajustent pour que chaque étage passe le même
débit : on résout le débit G tel que, en remontant la loi de l'ellipse
depuis la sortie du dernier étage (pression fixée), la pression
d'entrée du premier étage égale la pression disponible.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

ETA_RELATIF_MIN = 0.05
"""Plancher du rendement relatif (la formule devient négative loin du
point nominal) ; signalé par un avertissement."""


@dataclass(frozen=True)
class PointNominal:
    p_in0_pa: float
    p_out0_pa: float
    T0_K: float
    G0_kg_s: float


def debit_stodola(pn: PointNominal, p_in_pa: float, p_out_pa: float,
                  T_in_K: float) -> float:
    """Débit [kg/s] admis par l'étage (éq. 1 et 4 de Zhang, #F39)."""
    num = p_in_pa**2 - p_out_pa**2
    if num <= 0:
        return 0.0
    den = pn.p_in0_pa**2 - pn.p_out0_pa**2
    return pn.G0_kg_s * math.sqrt(pn.T0_K / T_in_K) * math.sqrt(num / den)


def p_entree_pour_debit(pn: PointNominal, G_kg_s: float, p_out_pa: float,
                        T_in_K: float) -> float:
    """Inverse de :func:`debit_stodola` : pression d'entrée [Pa]."""
    den = pn.p_in0_pa**2 - pn.p_out0_pa**2
    x = (G_kg_s / pn.G0_kg_s) ** 2 * (T_in_K / pn.T0_K) * den
    return math.sqrt(p_out_pa**2 + x)


def debit_reduit_relatif(pn: PointNominal, G_kg_s: float, p_in_pa: float,
                         T_in_K: float) -> float:
    """Ġ = (G√T/p_in) / (G√T/p_in)_0 (éq. 4 de Zhang)."""
    return (G_kg_s * math.sqrt(T_in_K) / p_in_pa) / (
        pn.G0_kg_s * math.sqrt(pn.T0_K) / pn.p_in0_pa)


def vitesse_reduite_relative(pn: PointNominal, T_in_K: float) -> float:
    """ṅ = sqrt(T0/T_in) à vitesse de rotation constante (éq. 5)."""
    return math.sqrt(pn.T0_K / T_in_K)


def rendement_relatif(G_red: float, n_red: float, t4: float) -> float:
    """η/η0 selon l'éq. 2 de Zhang (formule de Flügel modifiée)."""
    if G_red <= 0:
        return ETA_RELATIF_MIN
    x = n_red / G_red
    eta = (1.0 - t4 * (1.0 - n_red) ** 2) * x * (2.0 - x)
    return max(eta, ETA_RELATIF_MIN)


def resoudre_debit_glissant(
    points: list[PointNominal], T_in_K: list[float], p_disponible_pa: float,
    p_sortie_finale_pa: float, iterations: int = 80,
) -> tuple[float, list[float]]:
    """Débit G et pressions d'entrée de chaque étage tels que la chaîne
    d'étages passe G avec p_in,1 = p_disponible (bissection sur G)."""
    def p_in_1(G: float) -> tuple[float, list[float]]:
        p_out = p_sortie_finale_pa
        p_ins: list[float] = []
        for pn, T in zip(reversed(points), reversed(T_in_K)):
            p_in = p_entree_pour_debit(pn, G, p_out, T)
            p_ins.append(p_in)
            p_out = p_in
        p_ins.reverse()
        return p_ins[0], p_ins

    if p_disponible_pa <= p_sortie_finale_pa:
        return 0.0, [p_disponible_pa] * len(points)
    bas = 0.0
    haut = points[0].G0_kg_s
    while p_in_1(haut)[0] < p_disponible_pa:
        haut *= 2.0
        if haut > 1e6 * points[0].G0_kg_s:
            break
    for _ in range(iterations):
        mil = 0.5 * (bas + haut)
        if p_in_1(mil)[0] < p_disponible_pa:
            bas = mil
        else:
            haut = mil
    G = 0.5 * (bas + haut)
    return G, p_in_1(G)[1]
