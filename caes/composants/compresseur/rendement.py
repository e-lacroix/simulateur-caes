"""Compression adiabatique à rendement : isentropique (Shi 2024) ou
polytropique (Tola 2022).

* ``comprimer_isentropique`` (formules.md#F34) : l'état de sortie idéal
  est à entropie constante ; le travail réel vaut le travail idéal
  divisé par le rendement isentropique η_s ; pas d'échange de chaleur
  pendant la compression (q = 0, tout le travail devient enthalpie).
* ``comprimer_polytropique_rendement`` (formules.md#F35) : le rendement
  polytropique η_p définit l'exposant (n−1)/n = (γ−1)/(γ·η_p) ; la
  compression est adiabatique irréversible, w = Δh.

Les deux fonctions rendent un :class:`caes.compresseur.ResultatEtage`
pour que la chaîne, les séries et le bilan d'exergie restent les mêmes
quel que soit le modèle.
"""

from __future__ import annotations

import math

from caes.compresseur import ResultatEtage
from caes.proprietes import Air


def _indice_equivalent(T_in_K: float, T_out_K: float, beta: float) -> float:
    """Exposant polytropique équivalent n tel que T_out/T_in = β^((n−1)/n)."""
    if beta <= 1.0 or T_out_K <= T_in_K:
        return 1.0
    e = math.log(T_out_K / T_in_K) / math.log(beta)
    return 1.0 / (1.0 - e) if e < 1.0 else float("inf")


def comprimer_isentropique(
    air: Air, p_in_pa: float, T_in_K: float, beta: float, eta_s: float,
) -> ResultatEtage:
    """Compression adiabatique à rendement isentropique (#F34).

    h_out = h_in + (h_out,s − h_in) / η_s, avec h_out,s l'enthalpie à
    (p_out, s_in).
    """
    if beta < 1.0:
        raise ValueError(f"rapport de pression {beta} < 1")
    if not 0.0 < eta_s <= 1.0:
        raise ValueError(f"rendement isentropique {eta_s} hors de ]0, 1]")
    p_out = p_in_pa * beta
    h_in = air.h(p_in_pa, T_in_K)
    s_in = air.s(p_in_pa, T_in_K)
    T_out_s = air.T_de_p_s(p_out, s_in)
    h_out_s = air.h(p_out, T_out_s)
    h_out = h_in + (h_out_s - h_in) / eta_s
    T_out = air.T_de_p_h(p_out, h_out)
    rho_in = air.rho(p_in_pa, T_in_K)
    rho_out = air.rho(p_out, T_out)
    return ResultatEtage(
        p_in_pa=p_in_pa, T_in_K=T_in_K, p_out_pa=p_out, T_out_K=T_out,
        rho_in=rho_in, rho_out=rho_out, rapport_pression=beta,
        indice_polytropique=_indice_equivalent(T_in_K, T_out, beta),
        w_pol=h_out - h_in, dh=h_out - h_in, q_poly=0.0,
    )


def comprimer_polytropique_rendement(
    air: Air, p_in_pa: float, T_in_K: float, beta: float, eta_p: float,
) -> ResultatEtage:
    """Compression adiabatique à rendement polytropique (#F35).

    T_out = T_in · β^((γ−1)/(γ·η_p)), γ = cp/cv à l'entrée ; w = Δh.
    """
    if beta < 1.0:
        raise ValueError(f"rapport de pression {beta} < 1")
    if not 0.0 < eta_p <= 1.0:
        raise ValueError(f"rendement polytropique {eta_p} hors de ]0, 1]")
    p_out = p_in_pa * beta
    gamma = air.gamma(p_in_pa, T_in_K)
    expo = (gamma - 1.0) / (gamma * eta_p)
    T_out = T_in_K * beta ** expo
    h_in = air.h(p_in_pa, T_in_K)
    h_out = air.h(p_out, T_out)
    rho_in = air.rho(p_in_pa, T_in_K)
    rho_out = air.rho(p_out, T_out)
    return ResultatEtage(
        p_in_pa=p_in_pa, T_in_K=T_in_K, p_out_pa=p_out, T_out_K=T_out,
        rho_in=rho_in, rho_out=rho_out, rapport_pression=beta,
        indice_polytropique=1.0 / (1.0 - expo),
        w_pol=h_out - h_in, dh=h_out - h_in, q_poly=0.0,
    )
