"""Matériaux de stockage de chaleur (gravier, roches).

Les propriétés viennent du registre (``materiau.<nom>.*``) pour rester
traçables ; ce module les assemble en un objet :class:`Materiau`.
"""

from __future__ import annotations

from dataclasses import dataclass

from caes.registre import Registre


@dataclass(frozen=True)
class Materiau:
    """Solide granulaire d'un lit de stockage."""

    nom: str
    masse_volumique_kg_m3: float
    cp_j_kgk: float
    conductivite_w_mk: float
    diametre_particule_m: float
    porosite: float

    def __post_init__(self) -> None:
        if not 0.0 < self.porosite < 1.0:
            raise ValueError(f"porosité {self.porosite} hors de ]0, 1[")
        if self.diametre_particule_m <= 0:
            raise ValueError("diamètre de particule <= 0")

    @property
    def capacite_volumique_lit_j_m3k(self) -> float:
        """Capacité thermique du solide par m³ de lit [J/(m³·K)]."""
        return (
            (1.0 - self.porosite) * self.masse_volumique_kg_m3 * self.cp_j_kgk
        )

    @property
    def surface_specifique_m2_m3(self) -> float:
        """Surface des particules par m³ de lit (sphères) [m²/m³]."""
        return 6.0 * (1.0 - self.porosite) / self.diametre_particule_m

    def avec(self, **modifications: float) -> Materiau:
        """Copie avec des propriétés modifiées (expériences numériques)."""
        champs = {
            "nom": self.nom,
            "masse_volumique_kg_m3": self.masse_volumique_kg_m3,
            "cp_j_kgk": self.cp_j_kgk,
            "conductivite_w_mk": self.conductivite_w_mk,
            "diametre_particule_m": self.diametre_particule_m,
            "porosite": self.porosite,
        }
        champs.update(modifications)
        return Materiau(**champs)  # type: ignore[arg-type]


def charger_materiau(nom: str, registre: Registre | None = None) -> Materiau:
    """Construit un matériau à partir des entrées ``materiau.<nom>.*``."""
    reg = registre or Registre.charger()
    pre = f"materiau.{nom}."
    return Materiau(
        nom=nom,
        masse_volumique_kg_m3=reg.si(pre + "masse_volumique"),
        cp_j_kgk=reg.si(pre + "cp"),
        conductivite_w_mk=reg.si(pre + "conductivite"),
        diametre_particule_m=reg.si(pre + "diametre_particule"),
        porosite=reg.si(pre + "porosite"),
    )
