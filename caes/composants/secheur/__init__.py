"""Composants « sécheur » et « perte de débit ».

* :class:`Secheur` : modèle ``perte_debit`` (phase 1, formules.md#F10) :
  le sécheur par adsorption rejette une fraction du débit pour se
  régénérer ; pression et température ne changent pas. Avec
  ``debit_sortie_impose``, le débit sortant est forcé (par exemple la
  valeur mesurée de 0,032 kg/s chez Dormoy). Modèle ``aucun`` (phase 7) :
  pas de sécheur, l'air passe tel quel (grandes installations de Tola et
  de Shi, qui n'en ont pas). Le bilan d'eau et le point de rosée
  arriveront avec le modèle ``bilan_eau`` (phase 9).
* :class:`PerteDebit`, modèle ``fraction`` : une fraction du débit est
  perdue sans changement d'état. Sert à représenter le rendement
  volumétrique du compresseur selon la convention de Dormoy (tableau 6 :
  le travail s'applique au débit aspiré, 17 % n'est pas refoulé), ou
  une fuite.
"""

from __future__ import annotations

from typing import Any

from caes.composants.base import (
    Composant,
    Contexte,
    ErreurComposant,
    EtatAir,
    Flux,
)
from caes.composants.humidite import w_saturation
from caes.secheur import Secheur as ModelePerteDebit


class Secheur(Composant):
    TYPE = "secheur"
    MODELES = ("perte_debit", "aucun", "separateur")

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        self.modele_phys: ModelePerteDebit | None = None
        self.debit_impose: float | None = None
        self.T_rosee_sortie_K: float | None = None
        self.efficacite_separation = 0.0
        if self.modele == "perte_debit":
            self.modele_phys = ModelePerteDebit(
                efficacite=self.nombre("efficacite"))
            self.debit_impose = self.nombre("debit_sortie_impose", None)
            self.T_rosee_sortie_K = self.nombre("point_de_rosee_sortie",
                                                None)
        elif self.modele == "separateur":
            self.efficacite_separation = self.nombre("efficacite_separation")
            if not 0.0 <= self.efficacite_separation <= 1.0:
                raise ErreurComposant(
                    f"{nom} : efficacite_separation hors de [0, 1]")

    def pas(self, etat: EtatAir, ctx: Contexte) -> tuple[EtatAir, Flux]:
        """Même p et T ; débit réduit (sécheur, F10) et eau retirée
        (point de rosée de sortie, séparateur ; F43)."""
        m = etat.m_dot_kg_s
        if self.modele == "aucun":
            return etat, Flux()
        if self.modele == "separateur":
            retiree = etat.w_liquide_kg_kg * self.efficacite_separation
            flux = Flux(eau_separee_kg_s=retiree * m)
            return etat.remplacer(
                w_liquide_kg_kg=etat.w_liquide_kg_kg - retiree), flux
        assert self.modele_phys is not None
        if self.debit_impose is not None:
            m_out = self.debit_impose
            if m_out > m:
                self.avertir("débit imposé supérieur au débit entrant")
        else:
            m_out = self.modele_phys.debit_sortie(m)
        flux = Flux(m_dot_perdu_kg_s=m - m_out)
        sortie = etat.remplacer(m_dot_kg_s=m_out)
        if self.T_rosee_sortie_K is not None and etat.w_total_kg_kg > 0:
            # sécheur par adsorption : l'eau liquide est drainée, la
            # vapeur est ramenée au point de rosée de sortie (sous
            # pression) ; l'eau retirée part avec l'air de purge
            w_cible = w_saturation(self.T_rosee_sortie_K, etat.p_abs_pa)
            w_vap = min(etat.w_vapeur_kg_kg, w_cible)
            flux.eau_separee_kg_s = m * (
                etat.w_liquide_kg_kg + etat.w_vapeur_kg_kg - w_vap)
            sortie = sortie.remplacer(w_vapeur_kg_kg=w_vap,
                                      w_liquide_kg_kg=0.0)
        return sortie, flux

    def verifier_validite(self) -> list[str]:
        return []


class PerteDebit(Composant):
    TYPE = "perte_debit"
    MODELES = ("fraction",)

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        self.fraction_conservee = self.nombre("fraction_conservee")
        if not 0.0 < self.fraction_conservee <= 1.0:
            raise ErreurComposant(
                f"{nom} : fraction_conservee {self.fraction_conservee} "
                f"hors de ]0, 1]")

    def pas(self, etat: EtatAir, ctx: Contexte) -> tuple[EtatAir, Flux]:
        m_out = etat.m_dot_kg_s * self.fraction_conservee
        flux = Flux(m_dot_perdu_kg_s=etat.m_dot_kg_s - m_out)
        return etat.remplacer(m_dot_kg_s=m_out), flux
