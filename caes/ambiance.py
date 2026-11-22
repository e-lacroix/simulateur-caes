"""Conditions de l'air ambiant d'une installation (bloc ``ambiance``).

Tout scénario porte un bloc ``ambiance`` ; c'est la **seule** source de
température et de pression extérieures pour tous les composants :
source froide des refroidisseurs, pertes des réservoirs et des cuves,
air aspiré par le compresseur, état mort du bilan d'exergie, point de
rosée (phase 9). Changer ``T_amb`` de 20 °C à −20 °C dans le fichier
suffit à simuler l'hiver québécois.

Un profil météo optionnel (CSV temps / température) fait varier la
température extérieure pendant la simulation ; la température de
l'air aspiré suit alors le même écart par rapport à l'ambiant que celui
déclaré (voir formules.md#F32).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

CLES_OBLIGATOIRES = ("T_amb", "p_amb", "humidite_relative")
COLONNES_TEMPS = {"t_s": 1.0, "t_h": 3600.0, "t_j": 86400.0}
COLONNES_TEMPERATURE = {"T_amb_K": 0.0, "T_amb_degC": 273.15}


class ErreurAmbiance(ValueError):
    """Le bloc ``ambiance`` est absent ou incomplet."""


@dataclass
class Ambiance:
    """Conditions ambiantes, constantes ou suivant un profil dans le temps.

    ``T_aspiration_K`` est la température de l'air aspiré par le
    compresseur (par défaut l'ambiant). Avec un profil, l'écart
    ``T_aspiration − T_amb`` déclaré est conservé au cours du temps.
    """

    T_amb_K: float
    p_amb_pa: float
    humidite_relative: float
    T_aspiration_K: float
    profil_t_s: np.ndarray | None = None
    profil_T_K: np.ndarray | None = None
    profil_fichier: str = ""
    provenance: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.humidite_relative <= 1.0:
            raise ErreurAmbiance(
                f"humidité relative {self.humidite_relative} hors de [0, 1]"
            )
        if self.p_amb_pa <= 0 or self.T_amb_K <= 0:
            raise ErreurAmbiance("pression ou température ambiante <= 0")

    @property
    def a_un_profil(self) -> bool:
        return self.profil_t_s is not None

    @property
    def w_kg_kg(self) -> float:
        """Teneur en eau de l'air extérieur [kg/kg] à (T_amb, p_amb, φ)
        (F42) ; constante même avec un profil (l'humidité absolue de
        l'air aspiré est prise au point de référence du bloc)."""
        from caes.composants.humidite import w_de_humidite_relative

        return w_de_humidite_relative(self.T_amb_K, self.p_amb_pa,
                                      self.humidite_relative)

    @property
    def ecart_aspiration_K(self) -> float:
        """Écart déclaré entre l'air aspiré et l'ambiant [K]."""
        return self.T_aspiration_K - self.T_amb_K

    def T_amb_a(self, t_s: float) -> float:
        """Température extérieure [K] à l'instant ``t_s`` (#F32)."""
        if self.profil_t_s is None or self.profil_T_K is None:
            return self.T_amb_K
        return float(np.interp(t_s, self.profil_t_s, self.profil_T_K))

    def T_aspiration_a(self, t_s: float) -> float:
        """Température de l'air aspiré [K] à l'instant ``t_s``."""
        return self.T_amb_a(t_s) + self.ecart_aspiration_K

    def verifier_validite(self) -> list[str]:
        """Avertissements sur des conditions inhabituelles."""
        avis: list[str] = []
        T_min = self.T_amb_K
        T_max = self.T_amb_K
        if self.profil_T_K is not None:
            T_min = min(T_min, float(self.profil_T_K.min()))
            T_max = max(T_max, float(self.profil_T_K.max()))
        if T_min < 223.15 or T_max > 323.15:
            avis.append(
                f"température ambiante de {T_min - 273.15:.0f} à "
                f"{T_max - 273.15:.0f} °C : hors de la plage usuelle "
                f"(−50 à 50 °C) ; vérifier les corrélations"
            )
        if not 0.5e5 <= self.p_amb_pa <= 1.1e5:
            avis.append(
                f"pression ambiante {self.p_amb_pa / 1e5:.3f} bar : hors de "
                f"la plage usuelle (0,5 à 1,1 bar)"
            )
        return avis

    def description(self) -> str:
        texte = (
            f"T_amb {self.T_amb_K - 273.15:.1f} °C, p_amb "
            f"{self.p_amb_pa / 1e5:.4f} bar, humidité relative "
            f"{self.humidite_relative * 100:.0f} %, air aspiré "
            f"{self.T_aspiration_K - 273.15:.1f} °C"
        )
        if self.a_un_profil and self.profil_T_K is not None:
            texte += (
                f" ; profil météo « {self.profil_fichier} » de "
                f"{self.profil_T_K.min() - 273.15:.1f} à "
                f"{self.profil_T_K.max() - 273.15:.1f} °C sur "
                f"{self.profil_t_s[-1] / 86400:.1f} j"  # type: ignore
            )
        return texte


def charger_profil(chemin: Path) -> tuple[np.ndarray, np.ndarray]:
    """Lit un CSV de profil météo : une colonne de temps (``t_s``,
    ``t_h`` ou ``t_j``) et une de température (``T_amb_K`` ou
    ``T_amb_degC``). Retourne (t en s, T en K), temps croissants."""
    import pandas as pd

    tab = pd.read_csv(chemin)
    col_t = next((c for c in COLONNES_TEMPS if c in tab.columns), None)
    col_T = next((c for c in COLONNES_TEMPERATURE if c in tab.columns),
                 None)
    if col_t is None or col_T is None:
        raise ErreurAmbiance(
            f"profil {chemin} : colonnes attendues {list(COLONNES_TEMPS)} "
            f"et {list(COLONNES_TEMPERATURE)}"
        )
    t = tab[col_t].to_numpy(dtype=float) * COLONNES_TEMPS[col_t]
    T = tab[col_T].to_numpy(dtype=float) + COLONNES_TEMPERATURE[col_T]
    if len(t) < 2 or np.any(np.diff(t) <= 0):
        raise ErreurAmbiance(f"profil {chemin} : temps non croissants")
    return t, T


def ambiance_depuis_valeurs(
    bloc: dict[str, Any] | None,
    provenance: dict[str, str],
    dossier: Path | None = None,
) -> Ambiance:
    """Construit l'ambiance à partir du bloc résolu (valeurs SI)."""
    if not bloc:
        raise ErreurAmbiance(
            "bloc « ambiance » obligatoire (T_amb, p_amb, humidite_relative)"
        )
    manquantes = [c for c in CLES_OBLIGATOIRES if bloc.get(c) is None]
    if manquantes:
        raise ErreurAmbiance(
            f"bloc « ambiance » incomplet : il manque {manquantes}"
        )
    T_amb = float(bloc["T_amb"])
    T_asp = bloc.get("T_aspiration")
    prov = {k: v for k, v in provenance.items() if k.startswith("ambiance.")}
    if T_asp is None:
        T_asp = T_amb
        prov["ambiance.T_aspiration"] = "défaut : égale à T_amb"
    t = T = None
    fichier = ""
    if bloc.get("profil"):
        fichier = str(bloc["profil"])
        chemin = Path(fichier)
        if not chemin.is_absolute() and dossier is not None:
            chemin = dossier / chemin
        t, T = charger_profil(chemin)
        prov["ambiance.profil"] = f"fichier {fichier}"
    return Ambiance(
        T_amb_K=T_amb,
        p_amb_pa=float(bloc["p_amb"]),
        humidite_relative=float(bloc["humidite_relative"]),
        T_aspiration_K=float(T_asp),
        profil_t_s=t,
        profil_T_K=T,
        profil_fichier=fichier,
        provenance=prov,
    )
