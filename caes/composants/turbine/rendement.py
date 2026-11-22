"""Détente adiabatique à rendement : isentropique (Shi 2024, Zhang S.
2025) ou polytropique (Tola 2022), formules.md#F34 et #F35.

* ``detendre_isentropique`` : h_out = h_in − η_s·(h_in − h_out,s), avec
  h_out,s l'enthalpie à (p_out, s_in) ;
* ``detendre_polytropique_rendement`` : T_out = T_in·(p_out/p_in)^(η_p·
  (γ−1)/γ), γ = cp/cv à l'entrée.

Dans les deux cas la détente est adiabatique : le travail produit par
kg vaut h_in − h_out. Les fonctions rendent (T_out, w, dh) comme
:func:`caes.turbine.detendre_etage`.
"""

from __future__ import annotations

from caes.proprietes import Air


def detendre_isentropique(
    air: Air, p_in_pa: float, T_in_K: float, p_out_pa: float, eta_s: float,
) -> tuple[float, float, float]:
    """Détente à rendement isentropique (#F34). Retourne (T_out, w, dh)."""
    if p_out_pa >= p_in_pa:
        raise ValueError("une détente exige p_out < p_in")
    if not 0.0 < eta_s <= 1.0:
        raise ValueError(f"rendement isentropique {eta_s} hors de ]0, 1]")
    h_in = air.h(p_in_pa, T_in_K)
    s_in = air.s(p_in_pa, T_in_K)
    T_out_s = air.T_de_p_s(p_out_pa, s_in)
    h_out_s = air.h(p_out_pa, T_out_s)
    h_out = h_in - eta_s * (h_in - h_out_s)
    T_out = air.T_de_p_h(p_out_pa, h_out)
    return T_out, h_in - h_out, h_out - h_in


def detendre_polytropique_rendement(
    air: Air, p_in_pa: float, T_in_K: float, p_out_pa: float, eta_p: float,
) -> tuple[float, float, float]:
    """Détente à rendement polytropique (#F35). Retourne (T_out, w, dh)."""
    if p_out_pa >= p_in_pa:
        raise ValueError("une détente exige p_out < p_in")
    if not 0.0 < eta_p <= 1.0:
        raise ValueError(f"rendement polytropique {eta_p} hors de ]0, 1]")
    gamma = air.gamma(p_in_pa, T_in_K)
    T_out = T_in_K * (p_out_pa / p_in_pa) ** (eta_p * (gamma - 1.0) / gamma)
    h_in = air.h(p_in_pa, T_in_K)
    h_out = air.h(p_out_pa, T_out)
    return T_out, h_in - h_out, h_out - h_in
