"""Refroidisseurs intermédiaires, méthode de l'efficacité (NTU).

Équations 6 à 9 de Dormoy (2024), voir formules.md#F09. La géométrie des
échangeurs est inconnue : on utilise directement les efficacités
calibrées du tableau 2, et la chaleur retirée est calculée avec
l'enthalpie réelle de l'air (éq. 7).
"""

from __future__ import annotations

from dataclasses import dataclass

from caes.compresseur import interpoler_lineaire
from caes.proprietes import Air


@dataclass(frozen=True)
class ResultatRefroidisseur:
    """Grandeurs massiques d'un passage dans un refroidisseur."""

    p_pa: float
    T_in_K: float
    T_out_K: float
    efficacite: float
    q: float
    """Chaleur retirée à l'air [J/kg], >= 0."""
    q_sup_seuil: float
    """Part de ``q`` cédée au-dessus de la température seuil [J/kg]."""


def refroidir(
    air: Air,
    p_pa: float,
    T_in_K: float,
    T_froid_K: float,
    efficacite: float,
    T_seuil_K: float,
) -> ResultatRefroidisseur:
    """Refroidissement à pression constante (formules.md#F09).

    T_out = T_in − ε·(T_in − T_froid)   (éq. 8)
    q = h(p, T_in) − h(p, T_out)        (éq. 7, avec cp(T) réel)

    ``q_sup_seuil`` est la chaleur cédée pendant que l'air est encore
    au-dessus de ``T_seuil_K`` (130 °C chez Dormoy) : c'est la part
    récupérable pour réchauffer la turbine (tableau 6).
    """
    if not 0.0 <= efficacite <= 1.0:
        raise ValueError(f"efficacité {efficacite} hors de [0, 1]")
    T_out = T_in_K - efficacite * (T_in_K - T_froid_K)
    h_in = air.h(p_pa, T_in_K)
    h_out = air.h(p_pa, T_out)
    q = h_in - h_out
    if T_in_K > T_seuil_K:
        T_bas = max(T_out, T_seuil_K)
        q_sup = h_in - air.h(p_pa, T_bas)
    else:
        q_sup = 0.0
    return ResultatRefroidisseur(
        p_pa=p_pa,
        T_in_K=T_in_K,
        T_out_K=T_out,
        efficacite=efficacite,
        q=q,
        q_sup_seuil=q_sup,
    )


@dataclass(frozen=True)
class Refroidisseur:
    """Un refroidisseur d'efficacité fixe ou variable avec la pression.

    Si ``efficacite_max`` est donné, l'efficacité varie linéairement de
    ``efficacite`` (à ``p_min_pa``) à ``efficacite_max`` (à ``p_max_pa``),
    comme le refroidisseur 4 de Dormoy (74 → 85 %, formules.md#F07).
    """

    efficacite: float
    efficacite_max: float | None = None
    p_min_pa: float = 0.0
    p_max_pa: float = 0.0

    def efficacite_a(self, p_refoulement_pa: float) -> float:
        if self.efficacite_max is None:
            return self.efficacite
        return interpoler_lineaire(
            p_refoulement_pa,
            self.p_min_pa,
            self.p_max_pa,
            self.efficacite,
            self.efficacite_max,
        )

    def refroidir(
        self,
        air: Air,
        p_pa: float,
        T_in_K: float,
        T_froid_K: float,
        T_seuil_K: float,
        p_refoulement_pa: float,
    ) -> ResultatRefroidisseur:
        return refroidir(
            air,
            p_pa,
            T_in_K,
            T_froid_K,
            self.efficacite_a(p_refoulement_pa),
            T_seuil_K,
        )
