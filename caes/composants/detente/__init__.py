"""Composant « détente » : ce qui se passe entre le réservoir et la
turbine.

Modèles (phases 2 et 7, voir ``docs/composants/detente.md``) :

* ``isenthalpique`` : laminage, h_out = h_in (formules.md#F15) ;
* ``cheayb`` : relation semi-empirique T(P) (#F16, 25 à 150 bar) ;
* ``isotherme`` : diagnostic seulement, pas physique ;
* ``pression_glissante`` (Shi 2024, Zhang S. 2025, #F39) : pas de
  détendeur ; l'air arrive à la turbine à la pression du réservoir, qui
  baisse pendant la décharge. La décharge s'arrête à ``p_min``. La
  turbine aval doit accepter une pression d'entrée variable (modèles
  ``isentropique``, ``polytropique_rendement`` ou ``flugel``) ; une
  turbine à point fixe (``polytropique_deprag``) laminerait l'air à sa
  pression nominale, ce que l'assembleur signale.

Pour les trois premiers modèles, le détendeur s'arrête quand la
pression du réservoir passe sous ``p_consigne + ecart_min``.
"""

from __future__ import annotations

from typing import Any

from caes.composants.base import Composant, Contexte, EtatAir, Flux
from caes.composants.humidite import mettre_a_l_equilibre
from caes.detendeur import CoefficientsCheayb, ResultatDetente
from caes.detendeur import Detendeur as ModeleDetendeur


class Detente(Composant):
    TYPE = "detente"
    MODELES = ("isenthalpique", "cheayb", "isotherme", "pression_glissante")

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        self.modele_phys: ModeleDetendeur | None = None
        if self.modele == "pression_glissante":
            self.p_min_pa = self.nombre("p_min")
            return
        coef = None
        c = self.param("cheayb", None)
        if c:
            coef = CoefficientsCheayb(
                a1=c["a1"], a2=c["a2"], a3=c["a3"], a4=c["a4"],
                b1=c["b1"], b2=c["b2"], b3=c["b3"], b4=c["b4"],
                p_min_validite_pa=float(c.get("p_min_validite", 25e5)),
                p_max_validite_pa=float(c.get("p_max_validite", 150e5)),
            )
        self.modele_phys = ModeleDetendeur(
            p_consigne_pa=self.nombre("p_consigne"),
            ecart_min_pa=self.nombre("ecart_min"),
            modele=self.modele,
            cheayb=coef,
        )

    @property
    def glissante(self) -> bool:
        return self.modele_phys is None

    @property
    def p_consigne_pa(self) -> float | None:
        return None if self.modele_phys is None else (
            self.modele_phys.p_consigne_pa)

    @property
    def p_arret_pa(self) -> float:
        if self.modele_phys is None:
            return self.p_min_pa
        return self.modele_phys.p_arret_pa

    def peut_fonctionner(self, p_reservoir_pa: float) -> bool:
        return p_reservoir_pa >= self.p_arret_pa

    def p_sortie_pour(self, p_reservoir_pa: float) -> float:
        """Pression livrée à la turbine pour une pression de réservoir."""
        if self.modele_phys is None:
            return p_reservoir_pa
        return self.modele_phys.p_consigne_pa

    def pas(self, etat: EtatAir, ctx: Contexte) -> tuple[EtatAir, Flux]:
        if self.modele_phys is None:
            h = ctx.air.h(etat.p_abs_pa, etat.T_K)
            r = ResultatDetente(
                p_in_pa=etat.p_abs_pa, T_in_K=etat.T_K,
                p_out_pa=etat.p_abs_pa, T_out_K=etat.T_K, h_in=h, h_out=h,
                modele="pression_glissante",
            )
            return etat, Flux(resultat=r)
        r = self.modele_phys.detendre(ctx.air, etat.p_abs_pa, etat.T_K)
        if r.hors_validite:
            self.avertir(
                "pression d'entrée hors du domaine de Cheayb (25 à 150 bar)"
            )
        flux = Flux(resultat=r)
        if r.dh > 0:
            flux.Q_ajoute_w = etat.m_dot_kg_s * r.dh
            flux.source = "modele_detendeur"
        sortie = EtatAir(r.p_out_pa, r.T_out_K, etat.m_dot_kg_s,
                         etat.w_vapeur_kg_kg, etat.w_liquide_kg_kg)
        sortie = mettre_a_l_equilibre(sortie, flux, self, "à la sortie, ")
        return sortie, flux

    def verifier_validite(self) -> list[str]:
        avis: list[str] = []
        if self.modele == "isotherme":
            avis.append(
                "modèle « isotherme » : diagnostic seulement, pas physique"
            )
        if self.modele_phys is not None and self.modele_phys.ecart_min_pa < 0:
            avis.append("ecart_min négatif")
        if self.modele == "pression_glissante" and self.p_min_pa <= 0:
            avis.append("p_min <= 0")
        return avis
