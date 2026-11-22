"""Pertes à travers un isolant : coefficient global U (formules.md#F41).

Une cuve entourée d'une épaisseur e d'isolant de conductivité k, avec
un échange convectif h_ext sur sa face extérieure, perd
Q = U·A·(T − T_amb) avec 1/U = e/k + 1/h_ext (résistances en série,
paroi plane : l'épaisseur est petite devant le diamètre). La
conductivité et la chaleur massique de l'isolant viennent du registre
(``materiau.<nom>.conductivite``, par exemple la laine minérale
d'Ablaoui 2023, tableau 1).
"""

from __future__ import annotations

from dataclasses import dataclass

from caes.registre import Registre


@dataclass(frozen=True)
class Isolant:
    nom: str
    epaisseur_m: float
    conductivite_w_mk: float
    h_ext_w_m2k: float

    @property
    def coefficient_global_w_m2k(self) -> float:
        """U = 1 / (e/k + 1/h_ext) (#F41)."""
        return 1.0 / (self.epaisseur_m / self.conductivite_w_mk
                      + 1.0 / self.h_ext_w_m2k)

    def description(self) -> str:
        return (f"{self.epaisseur_m * 100:.0f} cm de {self.nom} "
                f"(k = {self.conductivite_w_mk:.3f} W/m·K), "
                f"U = {self.coefficient_global_w_m2k:.3f} W/m²K")


def isolant_depuis_bloc(bloc: dict, registre: Registre) -> Isolant:
    """Construit l'isolant d'un bloc ``isolation: {materiau, epaisseur}``.

    ``materiau`` est un identifiant du registre (``materiau.<nom>``) ;
    ``conductivite`` peut remplacer la valeur du registre (valeur sourcée
    dans le scénario) ; ``h_ext`` par défaut ``isolation.h_ext``.
    """
    nom = str(bloc.get("materiau", "laine_minerale"))
    e = bloc.get("epaisseur")
    if e is None or float(e) <= 0:
        raise ValueError("isolation : épaisseur manquante ou nulle")
    k = bloc.get("conductivite")
    if k is None:
        k = registre.si(f"materiau.{nom}.conductivite")
    h = bloc.get("h_ext")
    if h is None:
        h = registre.si("isolation.h_ext")
    return Isolant(nom, float(e), float(k), float(h))
