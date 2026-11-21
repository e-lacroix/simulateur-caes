"""Sécheur d'air par adsorption.

Modèle de Dormoy (2024), éq. 10 : le sécheur rejette une fraction du
débit pour régénérer l'adsorbant ; pression et température ne changent
pas (voir formules.md#F10). L'interface :meth:`Secheur.traiter` est
prévue pour accueillir plus tard un modèle d'humidité (phase 8) qui
calculerait l'eau retirée et la perte de débit réelle.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EtatDebit:
    """Un débit d'air avec son état (humidité à venir en phase 8)."""

    p_abs_pa: float
    T_K: float
    debit_massique_kg_s: float


@dataclass(frozen=True)
class Secheur:
    """Sécheur à perte de débit constante (éq. 10 de Dormoy)."""

    efficacite: float
    """Fraction du débit entrant qui ressort (0,81 chez Dormoy)."""

    def __post_init__(self) -> None:
        if not 0.0 < self.efficacite <= 1.0:
            raise ValueError(f"efficacité {self.efficacite} hors de ]0, 1]")

    def debit_sortie(self, debit_entree_kg_s: float) -> float:
        """Débit massique sortant [kg/s] (formules.md#F10)."""
        return debit_entree_kg_s * self.efficacite

    def debit_rejete(self, debit_entree_kg_s: float) -> float:
        """Débit perdu à la régénération [kg/s]."""
        return debit_entree_kg_s * (1.0 - self.efficacite)

    def traiter(self, entree: EtatDebit) -> EtatDebit:
        """Passage dans le sécheur : même p et T, débit réduit."""
        return EtatDebit(
            p_abs_pa=entree.p_abs_pa,
            T_K=entree.T_K,
            debit_massique_kg_s=self.debit_sortie(entree.debit_massique_kg_s),
        )
