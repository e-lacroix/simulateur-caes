"""Bibliothèque de composants interchangeables (phase 6).

Chaque fonction d'une installation d'air comprimé est un composant avec
une interface commune (:mod:`caes.composants.base`) ; un scénario YAML
choisit le composant par ``type`` et le modèle par ``modele``. La table
:data:`FABRIQUES` fait le lien entre le mot-clé ``type`` et la classe.
"""

from __future__ import annotations

from caes.composants.attente import Attente
from caes.composants.base import (
    Avertissement,
    Composant,
    Contexte,
    ElementChaine,
    ErreurComposant,
    EtatAir,
    Flux,
    HorsDomaine,
    Segment,
)
from caes.composants.compresseur import Compresseur, EtageCompresseur
from caes.composants.detente import Detente
from caes.composants.refroidisseur import Refroidisseur
from caes.composants.reservoir_air import ReservoirAir
from caes.composants.secheur import PerteDebit, Secheur
from caes.composants.stockage_chaleur import StockageChaleur
from caes.composants.turbine import EtageTurbineMaillon, Turbine

FABRIQUES: dict[str, type[Composant]] = {
    cls.TYPE: cls
    for cls in (
        Compresseur, Refroidisseur, Secheur, PerteDebit, ReservoirAir,
        StockageChaleur, Detente, Turbine, Attente,
    )
}
"""Mot-clé ``type`` du YAML → classe du composant."""

__all__ = [
    "Attente", "Avertissement", "Composant", "Compresseur", "Contexte",
    "Detente", "ElementChaine", "ErreurComposant", "EtageCompresseur",
    "EtageTurbineMaillon", "EtatAir", "FABRIQUES", "Flux", "HorsDomaine",
    "PerteDebit",
    "Refroidisseur", "ReservoirAir", "Secheur", "Segment",
    "StockageChaleur", "Turbine",
]
