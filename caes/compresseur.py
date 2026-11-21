"""Compresseur volumétrique à plusieurs étages, modèle polytropique.

Reproduit les équations 1 à 5 de Dormoy (2024) : chaque étage suit
p·vⁿ = constante (voir formules.md#F04 et #F05). Le rapport de pression
des étages 1 et 2 est fixe ; celui de l'étage 3 varie linéairement avec
la pression de refoulement (hypothèse, formules.md#F07) et l'étage 4
prend le reste.

L'assemblage avec les refroidisseurs se fait dans :mod:`caes.systeme`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from caes.proprietes import Air


def interpoler_lineaire(
    x: float, x0: float, x1: float, y0: float, y1: float
) -> float:
    """Interpolation linéaire bornée : y(x0) = y0, y(x1) = y1.

    En dehors de [x0, x1], la valeur est bloquée à la borne la plus
    proche. Sert aux lois « varie avec la pression » de Dormoy dont la
    forme exacte n'est pas publiée (formules.md#F07).
    """
    if x1 == x0:
        return y0
    if x <= x0:
        return y0
    if x >= x1:
        return y1
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


@dataclass(frozen=True)
class ResultatEtage:
    """Résultat de la compression d'un étage (grandeurs massiques)."""

    p_in_pa: float
    T_in_K: float
    p_out_pa: float
    T_out_K: float
    rho_in: float
    rho_out: float
    rapport_pression: float
    indice_polytropique: float
    w_pol: float
    """Travail polytropique massique fourni à l'air [J/kg], > 0."""
    dh: float
    """Variation d'enthalpie massique de l'air [J/kg]."""
    q_poly: float
    """Chaleur échangée pendant la compression [J/kg] ; < 0 si rejetée."""


def comprimer_etage(
    air: Air,
    p_in_pa: float,
    T_in_K: float,
    rapport_pression: float,
    indice_polytropique: float,
) -> ResultatEtage:
    """Compression polytropique d'un étage (formules.md#F04, #F05).

    * volume massique de sortie : v_out = v_in · β^(−1/n)  (éq. 2) ;
    * température de sortie : état (p_out, v_out) par l'équation d'état ;
    * travail massique : w = n/(n−1) · (p_out·v_out − p_in·v_in)  (éq. 4).
    """
    if rapport_pression < 1.0:
        raise ValueError(
            f"rapport de pression {rapport_pression} < 1 : pas une compression"
        )
    n = indice_polytropique
    if n < 1.0:
        raise ValueError("indice polytropique n < 1 : pas physique")
    rho_in = air.rho(p_in_pa, T_in_K)
    v_in = 1.0 / rho_in
    p_out = p_in_pa * rapport_pression
    if n - 1.0 < 1e-9:
        # Cas limite isotherme (n = 1) : T constante, w = p·v·ln(β)
        # pour un gaz parfait (formules.md#F05).
        T_out = T_in_K
        rho_out = air.rho(p_out, T_out)
        v_out = 1.0 / rho_out
        w_pol = p_in_pa * v_in * math.log(rapport_pression)
    else:
        v_out = v_in * rapport_pression ** (-1.0 / n)  # formules.md#F04
        rho_out = 1.0 / v_out
        T_out = air.T_de_p_rho(p_out, rho_out)
        w_pol = n / (n - 1.0) * (p_out * v_out - p_in_pa * v_in)  # #F05
    dh = air.h(p_out, T_out) - air.h(p_in_pa, T_in_K)
    return ResultatEtage(
        p_in_pa=p_in_pa,
        T_in_K=T_in_K,
        p_out_pa=p_out,
        T_out_K=T_out,
        rho_in=rho_in,
        rho_out=rho_out,
        rapport_pression=rapport_pression,
        indice_polytropique=n,
        w_pol=w_pol,
        dh=dh,
        q_poly=dh - w_pol,
    )


@dataclass(frozen=True)
class Compresseur:
    """Compresseur à ``len(indices_polytropiques)`` étages.

    Attributs
    ---------
    indices_polytropiques :
        n de chaque étage (tableau 2 de Dormoy).
    rapports_fixes :
        Rapports de pression des premiers étages, constants pendant la
        charge (3,25 et 3,75 chez Dormoy). Les étages restants se
        partagent le rapport total.
    rapport_avant_dernier_min, rapport_avant_dernier_max :
        Bornes du rapport de l'avant-dernier étage (étage 3 chez
        Dormoy), atteintes à ``p_refoulement_min`` et ``p_refoulement_max``.
    p_refoulement_min_pa :
        Pression de refoulement minimale (soupape de pression minimale
        avant le sécheur). Sous cette pression de réservoir, l'air est
        laminé du refoulement vers le réservoir.
    rendement_mecanique_min, rendement_mecanique_max :
        Bornes du rendement mécanique calibré de Dormoy (69-74 %),
        interpolées linéairement entre p_refoulement_min et max.
    rendement_electrique :
        Rendement du moteur électrique (94-95 %, tableau 7).
    debit_volumique_aspire_m3_s :
        Cylindrée × vitesse : débit volumique à l'aspiration.
    rendement_volumetrique :
        Fraction du débit aspiré réellement refoulée (83 %).
    debit_massique_aspire_impose_kg_s :
        Si donné, remplace rho × débit volumique (par exemple la valeur
        mesurée de 0,052 kg/s).
    """

    indices_polytropiques: tuple[float, ...]
    rapports_fixes: tuple[float, ...]
    rapport_avant_dernier_min: float
    rapport_avant_dernier_max: float
    p_refoulement_min_pa: float
    p_refoulement_max_pa: float
    rendement_mecanique_min: float
    rendement_mecanique_max: float
    rendement_electrique: float
    debit_volumique_aspire_m3_s: float
    rendement_volumetrique: float
    debit_massique_aspire_impose_kg_s: float | None = None

    def __post_init__(self) -> None:
        if len(self.rapports_fixes) != len(self.indices_polytropiques) - 2:
            raise ValueError(
                "il faut un rapport fixe pour chaque étage sauf les deux "
                "derniers"
            )

    @property
    def nb_etages(self) -> int:
        return len(self.indices_polytropiques)

    def p_refoulement(self, p_reservoir_pa: float) -> float:
        """Pression de refoulement : au moins la pression minimale."""
        return max(p_reservoir_pa, self.p_refoulement_min_pa)

    def debit_massique_aspire(
        self, air: Air, p_aspiration_pa: float, T_aspiration_K: float
    ) -> float:
        """Débit massique aspiré [kg/s] (formules.md#F06)."""
        if self.debit_massique_aspire_impose_kg_s is not None:
            return self.debit_massique_aspire_impose_kg_s
        rho = air.rho(p_aspiration_pa, T_aspiration_K)
        return rho * self.debit_volumique_aspire_m3_s

    def rapports_pression(
        self, p_aspiration_pa: float, p_refoulement_pa: float
    ) -> tuple[float, ...]:
        """Rapport de pression de chaque étage (formules.md#F07)."""
        total = p_refoulement_pa / p_aspiration_pa
        produit_fixes = 1.0
        for beta in self.rapports_fixes:
            produit_fixes *= beta
        reste = total / produit_fixes
        beta_avant_dernier = interpoler_lineaire(
            p_refoulement_pa,
            self.p_refoulement_min_pa,
            self.p_refoulement_max_pa,
            self.rapport_avant_dernier_min,
            self.rapport_avant_dernier_max,
        )
        beta_dernier = reste / beta_avant_dernier
        if beta_dernier < 1.0:
            raise ValueError(
                f"rapport du dernier étage {beta_dernier:.3f} < 1 à "
                f"p_refoulement = {p_refoulement_pa / 1e5:.1f} bar"
            )
        return (*self.rapports_fixes, beta_avant_dernier, beta_dernier)

    def rendement_mecanique(self, p_refoulement_pa: float) -> float:
        """Rendement mécanique selon la pression (formules.md#F07)."""
        return interpoler_lineaire(
            p_refoulement_pa,
            self.p_refoulement_min_pa,
            self.p_refoulement_max_pa,
            self.rendement_mecanique_min,
            self.rendement_mecanique_max,
        )

    def puissance_electrique(
        self,
        debit_massique_kg_s: float,
        travail_massique_total_j_kg: float,
        p_refoulement_pa: float,
    ) -> float:
        """Puissance électrique absorbée [W] (éq. 5, formules.md#F08)."""
        eta = self.rendement_mecanique(p_refoulement_pa)
        return (
            debit_massique_kg_s
            * travail_massique_total_j_kg
            / (eta * self.rendement_electrique)
        )
