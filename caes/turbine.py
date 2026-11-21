"""Turbine à air à plusieurs étages, avec réchauffage avant chaque étage.

Modèle de Dormoy (2024), §2.2.6 : détente polytropique (éq. 16, même
loi que la compression) puis rendements mécanique et électrique (éq. 17).
Les caractéristiques des trois étages DEPRAG viennent du tableau 9 des
données supplémentaires (voir formules.md#F17 et #F18).

Le réchauffage est un **flux suivi** : chaque étage déclare la chaleur
reçue et sa source (``externe`` ou ``cuve_X``), voir formules.md#F19.
"""

from __future__ import annotations

from dataclasses import dataclass

from caes.proprietes import Air


@dataclass(frozen=True)
class EtageTurbine:
    """Un étage de détente et son réchauffeur amont."""

    p_entree_pa: float
    p_sortie_pa: float
    indice_polytropique: float
    rendement_mecanique: float
    rendement_electrique: float
    T_entree_cible_K: float | None = None
    """Température visée après réchauffage ; ``None`` = pas de réchauffage."""

    def __post_init__(self) -> None:
        if self.p_sortie_pa >= self.p_entree_pa:
            raise ValueError(
                "un étage de turbine doit détendre (p_out < p_in)"
            )
        if self.indice_polytropique <= 1.0:
            raise ValueError("indice polytropique de détente <= 1")
        for r in (self.rendement_mecanique, self.rendement_electrique):
            if not 0.0 < r <= 1.0:
                raise ValueError(f"rendement {r} hors de ]0, 1]")


@dataclass(frozen=True)
class ResultatEtageTurbine:
    """Grandeurs massiques d'un étage (réchauffage + détente)."""

    p_in_pa: float
    T_avant_rechauffage_K: float
    T_in_K: float
    p_out_pa: float
    T_out_K: float
    q_rechauffage: float
    """Chaleur reçue avant l'étage [J/kg], >= 0."""
    source_chaleur: str
    w_pol: float
    """Travail polytropique massique produit [J/kg], > 0."""
    w_mec: float
    """Travail à l'arbre [J/kg] = η_mec · w_pol."""
    w_el: float
    """Travail électrique [J/kg] = η_el · w_mec."""
    dh: float
    """h_out − h_in de la détente [J/kg], < 0."""

    @property
    def q_residuel(self) -> float:
        """Chaleur implicite [J/kg] : −dh − w_mec (> 0 = perdue)."""
        return -self.dh - self.w_mec


def detendre_etage(
    air: Air,
    p_in_pa: float,
    T_in_K: float,
    p_out_pa: float,
    indice_polytropique: float,
) -> tuple[float, float, float]:
    """Détente polytropique (formules.md#F17).

    Retourne (T_out, w_pol, dh) avec
    v_out = v_in · (p_in/p_out)^(1/n)  (éq. 16) et
    w_pol = n/(n−1) · (p_in·v_in − p_out·v_out)  (éq. 17, > 0).
    """
    n = indice_polytropique
    v_in = 1.0 / air.rho(p_in_pa, T_in_K)
    v_out = v_in * (p_in_pa / p_out_pa) ** (1.0 / n)
    T_out = air.T_de_p_rho(p_out_pa, 1.0 / v_out)
    w_pol = n / (n - 1.0) * (p_in_pa * v_in - p_out_pa * v_out)
    dh = air.h(p_out_pa, T_out) - air.h(p_in_pa, T_in_K)
    return T_out, w_pol, dh


@dataclass(frozen=True)
class Turbine:
    """Turbine à ``len(etages)`` étages, débit massique constant."""

    etages: tuple[EtageTurbine, ...]
    debit_massique_kg_s: float
    source_chaleur: str = "externe"

    def __post_init__(self) -> None:
        if not self.etages:
            raise ValueError("turbine sans étage")
        if self.debit_massique_kg_s <= 0:
            raise ValueError("débit massique nul ou négatif")

    @property
    def p_entree_pa(self) -> float:
        return self.etages[0].p_entree_pa

    @property
    def p_sortie_pa(self) -> float:
        return self.etages[-1].p_sortie_pa

    def produire(
        self, air: Air, T_entree_K: float
    ) -> tuple[ResultatEtageTurbine, ...]:
        """Réchauffage et détente de chaque étage, à partir de T_entree.

        L'air arrive à la pression d'entrée du premier étage. Entre deux
        étages, la petite chute de pression (11,5 → 11 bar chez DEPRAG)
        est traitée comme un laminage isenthalpique.
        """
        resultats: list[ResultatEtageTurbine] = []
        T = T_entree_K
        p = self.p_entree_pa
        for etage in self.etages:
            if p > etage.p_entree_pa:
                T = air.T_de_p_h(etage.p_entree_pa, air.h(p, T))
            p = etage.p_entree_pa
            T_avant = T
            q = 0.0
            cible = etage.T_entree_cible_K
            if cible is not None and T < cible:
                q = air.h(p, cible) - air.h(p, T)
                T = cible
            T_out, w_pol, dh = detendre_etage(
                air, p, T, etage.p_sortie_pa, etage.indice_polytropique
            )
            w_mec = etage.rendement_mecanique * w_pol
            resultats.append(
                ResultatEtageTurbine(
                    p_in_pa=p,
                    T_avant_rechauffage_K=T_avant,
                    T_in_K=T,
                    p_out_pa=etage.p_sortie_pa,
                    T_out_K=T_out,
                    q_rechauffage=q,
                    source_chaleur=self.source_chaleur if q > 0 else "",
                    w_pol=w_pol,
                    w_mec=w_mec,
                    w_el=etage.rendement_electrique * w_mec,
                    dh=dh,
                )
            )
            T = T_out
            p = etage.p_sortie_pa
        return tuple(resultats)

    def puissance_electrique(
        self, resultats: tuple[ResultatEtageTurbine, ...]
    ) -> float:
        """Puissance électrique totale [W] (éq. 17, formules.md#F18)."""
        return self.debit_massique_kg_s * sum(r.w_el for r in resultats)
