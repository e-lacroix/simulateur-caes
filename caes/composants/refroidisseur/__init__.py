"""Composant « refroidisseur » (échangeur air / air ambiant).

Deux modèles (phase 7, voir ``docs/composants/refroidisseur.md``) :

* ``efficacite`` (phase 1, formules.md#F09) : T_out = T_in − ε·(T_in −
  T_amb), efficacité fixe ou linéaire en pression de refoulement
  (refroidisseur 4 de Dormoy, formules.md#F07) ;
* ``pincement`` (Tola 2022, Shi 2024, formules.md#F37) : l'air ressort à
  T_amb + δ, écart minimal de l'échangeur.

La source froide est **toujours** la température ambiante du bloc
``ambiance`` (F32). ``perte_de_charge`` (Shi : 0,04 MPa) abaisse la
pression de sortie, pour les deux modèles. La chaleur cédée au-dessus de
``T_seuil_chaleur_utile`` est comptée à part (tableau 6 de Dormoy) ;
avec ``recuperation_vers: <stockage>``, elle est déposée dans un stockage
de modèle ``huile_ideale`` sans changer l'état de l'air (hypothèse
comptable de Dormoy, § 3.3.5).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from caes.composants.base import (
    Composant,
    Contexte,
    ErreurComposant,
    EtatAir,
    Flux,
)
from caes.composants.humidite import mettre_a_l_equilibre
from caes.composants.refroidisseur.pincement import refroidir_pincement
from caes.refroidisseur import Refroidisseur as ModeleEfficacite

if TYPE_CHECKING:
    from caes.composants.stockage_chaleur import StockageChaleur


class Refroidisseur(Composant):
    TYPE = "refroidisseur"
    MODELES = ("efficacite", "pincement")

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        self.modele_phys: ModeleEfficacite | None = None
        self.pincement_K = 0.0
        if self.modele == "efficacite":
            eff = self.nombre("efficacite", None)
            eff_min = self.nombre("efficacite_min", None)
            eff_max = self.nombre("efficacite_max", None)
            if eff is None and (eff_min is None or eff_max is None):
                raise ErreurComposant(
                    f"{nom} : donner « efficacite », ou « efficacite_min » "
                    f"et « efficacite_max » avec « p_min » et « p_max »")
            if eff is not None:
                self.modele_phys = ModeleEfficacite(efficacite=eff)
            else:
                self.modele_phys = ModeleEfficacite(
                    efficacite=eff_min,  # type: ignore[arg-type]
                    efficacite_max=eff_max,
                    p_min_pa=self.nombre("p_min"),
                    p_max_pa=self.nombre("p_max"),
                )
        else:
            self.pincement_K = self.nombre("pincement")
        self.perte_de_charge_pa = self.nombre("perte_de_charge", 0.0)
        self.T_seuil_K = self.nombre("T_seuil_chaleur_utile", None)
        self.nom_recuperateur = self.param("recuperation_vers", None)
        self.T_entree_min_K = float("inf")
        self.recuperateur: StockageChaleur | None = None

    def efficacite_a(self, p_refoulement_pa: float) -> float:
        if self.modele_phys is None:
            return float("nan")
        return self.modele_phys.efficacite_a(p_refoulement_pa)

    def pas(self, etat: EtatAir, ctx: Contexte) -> tuple[EtatAir, Flux]:
        """Refroidissement isobare vers l'ambiant (#F09 ou #F37), puis
        perte de charge éventuelle."""
        T_froid = ctx.T_amb_K
        T_seuil = self.T_seuil_K if self.T_seuil_K is not None else 1e9
        if self.modele_phys is not None:
            r = self.modele_phys.refroidir(
                ctx.air, etat.p_abs_pa, etat.T_K, T_froid, T_seuil,
                ctx.p_refoulement_pa,
            )
        else:
            r = refroidir_pincement(ctx.air, etat.p_abs_pa, etat.T_K,
                                    T_froid, self.pincement_K, T_seuil)
        m = etat.m_dot_kg_s
        flux = Flux(Q_retire_w=m * r.q, destination="ambiant", resultat=r,
                    dp_pa=self.perte_de_charge_pa)
        if etat.T_K < T_froid:
            self.T_entree_min_K = min(self.T_entree_min_K, etat.T_K)
            self.avertir(
                "air entrant plus froid que l'ambiant (le gravier amont a "
                "gardé du froid de la décharge) : le modèle à efficacité le "
                "réchauffe ; le modèle à pincement le laisse tel quel"
            )
        if self.recuperateur is not None and r.q_sup_seuil > 0:
            self.recuperateur.deposer(m * r.q_sup_seuil * ctx.dt_s)
            flux.destination = f"ambiant ; > seuil → {self.recuperateur.nom}"
        p_out = etat.p_abs_pa - self.perte_de_charge_pa
        if p_out <= 0:
            raise ErreurComposant(
                f"{self.nom} : perte de charge supérieure à la pression")
        T_out = r.T_out_K
        if self.perte_de_charge_pa > 0:
            # chute de pression isenthalpique après le refroidissement
            T_out = ctx.air.T_de_p_h(p_out, ctx.air.h(etat.p_abs_pa, T_out))
        sortie = etat.remplacer(T_K=T_out, p_abs_pa=p_out)
        # condensation de la vapeur en excès (F43) : la chaleur latente
        # est déclarée à part, l'eau liquide reste entraînée jusqu'à un
        # séparateur
        sortie = mettre_a_l_equilibre(sortie, flux, self,
                                      avertir_condensation=False)
        return sortie, flux

    def verifier_validite(self) -> list[str]:
        avis: list[str] = []
        if self.modele_phys is not None:
            m = self.modele_phys
            for e in (m.efficacite, m.efficacite_max):
                if e is not None and not 0.0 <= e <= 1.0:
                    avis.append(f"efficacité {e} hors de [0, 1]")
            if m.efficacite_max is not None and m.p_min_pa >= m.p_max_pa:
                avis.append("p_min >= p_max pour la loi d'efficacité")
        elif self.pincement_K < 0:
            avis.append("pincement négatif")
        if self.perte_de_charge_pa < 0:
            avis.append("perte de charge négative")
        return avis
