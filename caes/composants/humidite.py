"""Air humide : teneur en eau, saturation, point de rosée, givre
(phase 9, formules.md#F42 et #F43).

Propriétés par CoolProp (``HAPropsSI``, formulation ASHRAE RP-1485 de
Herrmann, Kretzschmar et Gatley 2009, qui inclut le facteur
d'augmentation de la solubilité de l'eau à haute pression). Domaine de
validité : 10 Pa à 10 MPa, −143 à 350 °C. Au-dessus de 10 MPa (le
réservoir de Dormoy va à 19 MPa), la teneur à saturation est
extrapolée à pression partielle de vapeur constante,
w(p) = w(10 MPa) · 10 MPa / p (le facteur d'augmentation continue de
croître avec la pression : l'extrapolation sous-estime un peu la teneur
à saturation, donc surestime la condensation ; signalé).

Convention : ``w`` est la masse d'eau par kg d'air (le débit ``m_dot``
des composants est traité comme de l'air, l'eau étant au plus
quelques pour cent) ; ``w_vapeur`` est en phase gazeuse,
``w_liquide`` est entraîné sous forme de gouttelettes ou de givre.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

import CoolProp.CoolProp as CP
from CoolProp.CoolProp import HAPropsSI

if TYPE_CHECKING:
    from caes.composants.base import Composant, EtatAir, Flux

P_MAX_VALIDITE_PA = 1.0e7
"""Borne haute de la formulation RP-1485 (CoolProp HumidAir)."""
T_MIN_VALIDITE_K = 130.0
T_TRIPLE_EAU_K = 273.16
T_GIVRE_K = 273.15
"""Sous 0 °C, l'eau qui se dépose est du givre (point de congélation)."""
ENTHALPIE_FUSION_GLACE_J_KG = 333.4e3
"""Enthalpie de fusion de la glace Ih au point triple (Feistel et Wagner
2006, IAPWS ; registre ``eau.enthalpie_fusion``)."""


class HorsDomaineHumidite(ValueError):
    """État hors du domaine de la formulation d'air humide."""


def _borner(p_abs_pa: float, T_K: float) -> tuple[float, float]:
    if T_K < T_MIN_VALIDITE_K:
        raise HorsDomaineHumidite(
            f"température {T_K:.0f} K sous le domaine de l'air humide")
    return min(p_abs_pa, P_MAX_VALIDITE_PA), T_K


def sous_domaine_froid(T_K: float) -> bool:
    """Vrai sous 130 K : la formulation RP-1485 ne s'applique plus ; la
    pression de vapeur de la glace y est négligeable (< 1e-6 Pa), toute
    l'eau est considérée gelée (teneur à saturation nulle)."""
    return T_K < T_MIN_VALIDITE_K


def hors_validite(p_abs_pa: float) -> bool:
    return p_abs_pa > P_MAX_VALIDITE_PA


T_CRITIQUE_EAU_K = 647.096
FRACTION_PWS_MAX = 0.9
"""Quand la pression de vapeur saturante approche la pression totale,
l'air peut contenir une quantité d'eau sans borne (il n'y a plus de
condensation possible à cette pression) : teneur à saturation infinie."""


def w_saturation(T_K: float, p_abs_pa: float) -> float:
    """Teneur en eau à saturation [kg/kg] (sur la glace sous 0 °C) ;
    infinie si l'eau ne peut pas condenser à cette pression. Mise en
    cache au 0,01 K et au 0,1 % de pression près (CoolProp est lent)."""
    return _w_saturation_cache(round(T_K, 2), round(p_abs_pa, -2))


@lru_cache(maxsize=200000)
def _w_saturation_cache(T_K: float, p_abs_pa: float) -> float:
    if T_K >= T_CRITIQUE_EAU_K:
        return float("inf")
    if sous_domaine_froid(T_K):
        return 0.0
    if T_K >= T_TRIPLE_EAU_K:
        pws = CP.PropsSI("P", "T", T_K, "Q", 0, "Water")
        if pws >= FRACTION_PWS_MAX * p_abs_pa:
            return float("inf")
    p, T = _borner(p_abs_pa, T_K)
    w = HAPropsSI("W", "T", T, "P", p, "R", 1.0)
    if p_abs_pa > P_MAX_VALIDITE_PA:
        w *= P_MAX_VALIDITE_PA / p_abs_pa
    return float(w)


def w_de_humidite_relative(T_K: float, p_abs_pa: float,
                           humidite_relative: float) -> float:
    """Teneur en eau [kg/kg] d'un air à (T, p, φ)."""
    if not 0.0 <= humidite_relative <= 1.0:
        raise ValueError(f"humidité relative {humidite_relative} hors de "
                         f"[0, 1]")
    if humidite_relative <= 0:
        return 0.0
    p, T = _borner(p_abs_pa, T_K)
    w = HAPropsSI("W", "T", T, "P", p, "R", humidite_relative)
    if p_abs_pa > P_MAX_VALIDITE_PA:
        w *= P_MAX_VALIDITE_PA / p_abs_pa
    return float(w)


def point_de_rosee(p_abs_pa: float, w_kg_kg: float) -> float:
    """Température de rosée (ou de givre sous 0 °C) [K] à la pression p
    pour une teneur w en vapeur ; −inf pour un air sec."""
    if w_kg_kg <= 0:
        return float("-inf")
    return _point_de_rosee_cache(round(p_abs_pa, -2),
                                 float(f"{w_kg_kg:.5g}"))


@lru_cache(maxsize=200000)
def _point_de_rosee_cache(p_abs_pa: float, w_kg_kg: float) -> float:
    p = p_abs_pa
    w = w_kg_kg
    if p > P_MAX_VALIDITE_PA:
        # même pression partielle de vapeur, ramenée à 10 MPa
        w = w * p / P_MAX_VALIDITE_PA
        p = P_MAX_VALIDITE_PA
    try:
        return float(HAPropsSI("Tdp", "T", 293.15, "P", p, "W", w))
    except ValueError:
        pass
    # w au-dessus de la saturation à 20 °C : bissection sur T
    bas, haut = T_MIN_VALIDITE_K, 450.0
    for _ in range(60):
        mil = 0.5 * (bas + haut)
        if w_saturation(min(mil, 449.0), p) < w:
            bas = mil
        else:
            haut = mil
    return 0.5 * (bas + haut)


def enthalpie_condensation(T_K: float) -> float:
    """Chaleur libérée par kg d'eau qui se condense à T [J/kg] :
    enthalpie de vaporisation (IAPWS-95 via CoolProp), plus l'enthalpie
    de fusion de la glace quand il se forme du givre (T < 0 °C)."""
    T = max(T_K, T_TRIPLE_EAU_K)
    h = (CP.PropsSI("H", "T", T, "Q", 1, "Water")
         - CP.PropsSI("H", "T", T, "Q", 0, "Water"))
    if T_K < T_GIVRE_K:
        h += ENTHALPIE_FUSION_GLACE_J_KG
    return float(h)


@dataclass(frozen=True)
class Equilibre:
    """Résultat d'une mise à l'équilibre vapeur / liquide."""

    w_vapeur: float
    w_liquide: float
    condense: float
    """Eau passée de la vapeur au liquide [kg/kg] (< 0 : évaporation)."""
    givre: bool
    T_rosee_K: float
    """Point de rosée de toute l'eau présente (vapeur + liquide)."""
    w_saturation: float


def equilibrer(T_K: float, p_abs_pa: float, w_vapeur: float,
               w_liquide: float) -> Equilibre:
    """Répartit l'eau entre vapeur et liquide à (T, p) : la vapeur ne
    peut pas dépasser la saturation, le liquide s'évapore si l'air est
    sous-saturé (#F43)."""
    total = w_vapeur + w_liquide
    if total <= 0:
        return Equilibre(0.0, 0.0, 0.0, False, float("-inf"), 0.0)
    w_sat = w_saturation(T_K, p_abs_pa)
    vap = min(total, w_sat)
    liq = total - vap
    return Equilibre(
        w_vapeur=vap, w_liquide=liq, condense=w_vapeur - vap,
        givre=liq > 1e-12 and T_K < T_GIVRE_K,
        T_rosee_K=point_de_rosee(p_abs_pa, total), w_saturation=w_sat,
    )


def mettre_a_l_equilibre(
    etat: EtatAir, flux: Flux, composant: Composant | None = None,
    etiquette: str = "", avertir_condensation: bool = True,
) -> EtatAir:
    """Met l'eau de ``etat`` à l'équilibre à son (T, p), remplit les
    champs d'eau du flux et avertit (givre, condensation)."""
    if etat.w_vapeur_kg_kg <= 0 and etat.w_liquide_kg_kg <= 0:
        return etat
    eq = equilibrer(etat.T_K, etat.p_abs_pa, etat.w_vapeur_kg_kg,
                    etat.w_liquide_kg_kg)
    m = etat.m_dot_kg_s
    flux.eau_condensee_kg_s = eq.condense * m
    flux.Q_latente_w = max(eq.condense, 0.0) * m * (
        enthalpie_condensation(etat.T_K) if eq.condense > 0 else 0.0)
    flux.givre = eq.givre
    flux.T_rosee_K = eq.T_rosee_K
    if composant is not None:
        if hors_validite(etat.p_abs_pa):
            composant.avertir(
                "air humide au-delà de 10 MPa : teneur à saturation "
                "extrapolée (formulation RP-1485 valable jusqu'à 10 MPa)")
        if sous_domaine_froid(etat.T_K):
            composant.avertir(
                "air humide sous 130 K : hors de la formulation RP-1485, "
                "toute l'eau est supposée gelée")
        if eq.givre:
            composant.avertir(
                f"{etiquette}givre : de l'eau se dépose en glace (air sous "
                f"0 °C et sous son point de givre)")
        elif eq.condense > 1e-12 and avertir_condensation:
            composant.avertir(
                f"{etiquette}condensation d'eau (air refroidi sous son "
                f"point de rosée)")
    return etat.remplacer(w_vapeur_kg_kg=eq.w_vapeur,
                          w_liquide_kg_kg=eq.w_liquide)
