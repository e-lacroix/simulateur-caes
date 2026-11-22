"""Composant « stockage de chaleur » : ce qui réchauffe l'air avant une
turbine, et d'où vient cette chaleur.

Cinq modèles (phases 5 et 7, formules.md#F30, #F31, #F40, #F41) :

* ``gravier`` : cuve cylindrique de gravier (modèle de Schumann 1D,
  :mod:`caes.lit_gravier`). En charge, l'air chaud la traverse de haut
  en bas avant le refroidisseur ; en décharge, l'air froid la traverse
  en sens inverse et en ressort chaud, avec un bypass qui vise la
  température cible de la turbine. ``pression: etage`` (air comprimé
  dans la cuve, architecture D) ou ``atmospherique`` (boucle d'air à
  1 bar, architecture E) ; ``pincement`` est l'écart de chaque
  échangeur de la boucle (0 pour le passage direct).
* ``huile_ideale`` : réserve parfaite (hypothèse de Dormoy, § 3.3.5).
  Elle reçoit la chaleur au-dessus du seuil que les refroidisseurs lui
  déposent (``recuperation_vers``) et la rend à la turbine sans perte ;
  si la réserve manque, appoint externe (étiquette ``externe``) quand
  ``appoint_externe`` est vrai.
* ``source_externe`` : chaudière ou réseau de chaleur non modélisé :
  l'air atteint toujours la cible, et toute la chaleur est étiquetée
  ``externe`` (comptée dans le rendement « avec chaleur externe »).
* ``huile_deux_reservoirs`` (Tola 2022 cas B, Wolf et Budt 2014, #F40) :
  réservoirs chaud et froid d'huile thermique, échangeurs à pincement.
* ``eau_sous_pression`` (Shi 2024, #F40) : même modèle avec de l'eau
  liquide à la pression de la cuve, plafonnée par l'ébullition.

Le bloc ``isolation: {materiau, epaisseur}`` (#F41) remplace
``coefficient_perte`` par U = 1/(e/k + 1/h_ext) avec la conductivité
de l'isolant lue au registre (laine minérale d'Ablaoui 2023).

Toute chaleur ajoutée à l'air porte l'étiquette de sa source : le nom
du composant pour un stockage réel, ``externe`` sinon (règle du bilan de
chaleur, formules.md#F19).
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np

from caes.composants.base import (
    Composant,
    Contexte,
    ErreurComposant,
    EtatAir,
    Flux,
)
from caes.composants.humidite import mettre_a_l_equilibre
from caes.composants.isolation import Isolant, isolant_depuis_bloc
from caes.composants.stockage_chaleur.deux_reservoirs import (
    DeuxReservoirs,
    Fluide,
    fluide_eau,
)
from caes.lit_gravier import Correlations, LitGravier
from caes.materiaux import charger_materiau
from caes.registre import Registre

PRESSIONS = ("etage", "atmospherique")
FRACTION_BYPASS_MAX = 0.999
"""Le bypass laisse toujours passer un filet d'air dans la cuve."""


class StockageChaleur(Composant):
    TYPE = "stockage_chaleur"
    MODELES = ("gravier", "huile_ideale", "source_externe",
               "huile_deux_reservoirs", "eau_sous_pression")
    MODELES_PHYSIQUES = ("gravier", "huile_deux_reservoirs",
                         "eau_sous_pression")

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None,
                 registre: Registre | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        self.a_un_etat = self.modele != "source_externe"
        self.physique = self.modele in self.MODELES_PHYSIQUES
        self.lit: LitGravier | None = None
        self.reservoirs: DeuxReservoirs | None = None
        self.isolant: Isolant | None = None
        self.perte_de_charge_pa = self.nombre("perte_de_charge", 0.0)
        self.T_initiale_imposee_K = self.nombre("T_initiale", None)
        bloc_iso = self.param("isolation", None)
        if bloc_iso:
            reg_iso = registre or Registre.charger()
            self.isolant = isolant_depuis_bloc(dict(bloc_iso), reg_iso)
        self.reserve_j = 0.0
        self.externe_j = 0.0
        self.p_derniere_pa: float | None = None
        self.dp_dernier_pa = 0.0
        self.T_initiale_K: float | None = None
        self.T_sortie_min_K = float("inf")
        if self.modele == "gravier":
            reg = registre or Registre.charger()
            self.materiau = charger_materiau(
                str(self.param("materiau")), reg)
            d_part = self.nombre("diametre_particule", None)
            if d_part is not None:
                # granulométrie propre à la cuve (analyses de la phase 10)
                self.materiau = dataclasses.replace(
                    self.materiau, diametre_particule_m=float(d_part))
            self.volume_m3 = self.nombre("volume")
            self.rapport_hd = self.nombre("rapport_hauteur_diametre")
            self.n_cellules = int(self.param("n_cellules"))
            self.pression = str(self.param("pression", "etage"))
            if self.pression not in PRESSIONS:
                raise ErreurComposant(
                    f"{nom} : pression « {self.pression} » inconnue "
                    f"(choix : {PRESSIONS})"
                )
            self.pincement_K = self.nombre("pincement", 0.0)
            self.coefficient_perte = self.nombre("coefficient_perte", 0.0)
            if self.isolant is not None:
                self.coefficient_perte = self.isolant.coefficient_global_w_m2k
            self.bypass = bool(self.param("bypass", True))
            self.correlations = Correlations(
                wakao_a=reg.si("lit.wakao.a"), wakao_b=reg.si("lit.wakao.b"),
                wakao_c=reg.si("lit.wakao.c"),
                wakao_Re_min=reg.si("lit.wakao.Re_min"),
                wakao_Re_max=reg.si("lit.wakao.Re_max"),
                ergun_A=reg.si("lit.ergun.A"), ergun_B=reg.si("lit.ergun.B"),
                jeffreson_facteur=reg.si("lit.jeffreson.facteur"),
            )
            D = (4.0 * self.volume_m3 / (math.pi * self.rapport_hd)) ** (1 / 3)
            self.lit = LitGravier(
                self.materiau, D, self.rapport_hd * D,
                n_cellules=self.n_cellules,
                coefficient_perte_w_m2k=self.coefficient_perte,
                correlations=self.correlations,
            )
        elif self.modele == "huile_ideale":
            self.appoint_externe = bool(self.param("appoint_externe", True))
        elif self.modele in ("huile_deux_reservoirs", "eau_sous_pression"):
            self.pincement_K = self.nombre("pincement")
            self.masse_kg = self.nombre("masse")
            self.coefficient_perte = self.nombre("coefficient_perte", 0.0)
            if self.isolant is not None:
                self.coefficient_perte = self.isolant.coefficient_global_w_m2k
            self.surface_m2 = self.nombre("surface", 0.0)
            if self.modele == "huile_deux_reservoirs":
                self.fluide = Fluide("huile", self.nombre("cp"),
                                     self.nombre("T_max", None))
            else:
                self.p_cuve_pa = self.nombre("pression_cuve")
                self.marge_ebullition_K = self.nombre("marge_ebullition",
                                                      0.0)
                self.fluide = fluide_eau(self.p_cuve_pa,
                                         self.marge_ebullition_K, 293.15)
            self.reservoirs = DeuxReservoirs(
                self.fluide, self.masse_kg, self.pincement_K,
                self.coefficient_perte, self.surface_m2,
                T_froid_maintenue_K=self.nombre("T_froid_maintenue", None))

    # --- état ----------------------------------------------------------
    def initialiser(self, T_K: float) -> None:
        if self.T_initiale_imposee_K is not None:
            T_K = self.T_initiale_imposee_K
        self.T_initiale_K = T_K
        if self.lit is not None:
            self.lit.initialiser(T_K)
        if self.reservoirs is not None:
            if self.modele == "eau_sous_pression":
                # cp de l'eau évalué à mi-chemin entre l'ambiant et le
                # plafond d'ébullition (IAPWS-95 via CoolProp)
                T_max = self.fluide.T_max_K or T_K
                self.fluide = fluide_eau(self.p_cuve_pa,
                                         self.marge_ebullition_K,
                                         0.5 * (T_K + T_max))
                self.reservoirs.fluide = self.fluide
            self.reservoirs.initialiser(T_K)
        self.reserve_j = 0.0
        self.externe_j = 0.0
        self.p_derniere_pa = None

    def reinitialiser(self) -> None:
        if self.T_initiale_K is not None:
            self.initialiser(self.T_initiale_K)

    @property
    def masse_gravier_kg(self) -> float:
        return self.lit.masse_gravier_kg if self.lit is not None else 0.0

    def energie_stockee_j(self, T_ref_K: float) -> float:
        """Chaleur stockée au-dessus de T_ref [J]."""
        if self.lit is not None:
            return self.lit.energie_stockee_j(T_ref_K)
        if self.reservoirs is not None:
            return self.reservoirs.energie_stockee_j(T_ref_K)
        return self.reserve_j

    def exergie_j(self, T0_K: float) -> float:
        """Exergie du stockage [J] (formules.md#F31)."""
        if self.lit is not None:
            T = self.lit.T_s_K
            return float(self.lit.capacite_cellule_j_k * np.sum(
                (T - T0_K) - T0_K * np.log(T / T0_K)))
        if self.reservoirs is not None:
            return self.reservoirs.exergie_j(T0_K)
        return 0.0

    def profil_temperature_K(self) -> np.ndarray | None:
        return None if self.lit is None else self.lit.T_s_K.copy()

    def pression_de_travail(self, p_air_pa: float, ctx: Contexte) -> float:
        if self.modele == "gravier" and self.pression == "atmospherique":
            return ctx.p_amb_pa
        return p_air_pa

    def deposer(self, Q_j: float) -> None:
        """Reçoit de la chaleur d'un refroidisseur (huile idéale)."""
        if self.modele != "huile_ideale":
            raise ErreurComposant(
                f"{self.nom} : seul le modèle « huile_ideale » accepte une "
                f"récupération depuis un refroidisseur"
            )
        self.reserve_j += Q_j

    # --- charge --------------------------------------------------------
    def charger_air(self, etat: EtatAir,
                    ctx: Contexte) -> tuple[EtatAir, Flux]:
        """L'air chaud traverse le stockage (charge, formules.md#F30) ;
        l'eau est remise à l'équilibre à la sortie (F43)."""
        sortie, flux = self._charger_air(etat, ctx)
        sortie = mettre_a_l_equilibre(sortie, flux, self, "en charge, ")
        return sortie, flux

    def _charger_air(self, etat: EtatAir,
                     ctx: Contexte) -> tuple[EtatAir, Flux]:
        if self.modele == "gravier":
            assert self.lit is not None
            pinch = self.pincement_K
            p_cuve = self.pression_de_travail(etat.p_abs_pa, ctx)
            self.p_derniere_pa = p_cuve
            r = self.lit.pas(
                ctx.air, ctx.dt_s, etat.m_dot_kg_s, etat.T_K - pinch, p_cuve,
                ctx.T_amb_K, sens=1,
            )
            self._surveiller_wakao()
            self.dp_dernier_pa = r["dp_pa"]
            T_out = min(etat.T_K, r["T_sortie_K"] + pinch)
            flux = Flux(
                Q_retire_w=r["Q_air_vers_solide_j"] / ctx.dt_s,
                destination=self.nom, dp_pa=r["dp_pa"], resultat=r,
            )
            return etat.remplacer(T_K=T_out), flux
        if self.reservoirs is not None:
            T_out, Q, plafond = self.reservoirs.charger(
                ctx.air, etat.p_abs_pa, etat.T_K, etat.m_dot_kg_s, ctx.dt_s)
            if plafond:
                T_pl = self.reservoirs.T_plafond_K - 273.15
                self.avertir(
                    f"liquide plafonné à {T_pl:.0f} °C (ébullition ou "
                    f"T_max) : l'air sort du compresseur plus chaud que ce "
                    f"que le stockage accepte")
            if Q <= 0:
                self.avertir("réservoir froid vide : stockage saturé")
            return self._avec_perte_de_charge(
                etat.remplacer(T_K=T_out), ctx), Flux(
                Q_retire_w=Q / ctx.dt_s, destination=self.nom,
                dp_pa=self.perte_de_charge_pa,
                resultat={"Q_j": Q, "T_chaud_K": self.reservoirs.T_chaud_K})
        if self.modele == "huile_ideale":
            # Hypothèse comptable : la chaleur au-dessus du seuil est mise
            # de côté, l'air continue tel quel vers le refroidisseur.
            T_seuil = self.nombre("T_seuil", None)
            q = 0.0
            if T_seuil is not None and etat.T_K > T_seuil:
                q = ctx.air.h(etat.p_abs_pa, etat.T_K) - ctx.air.h(
                    etat.p_abs_pa, T_seuil)
                self.reserve_j += etat.m_dot_kg_s * q * ctx.dt_s
            return etat, Flux(resultat={"q_comptee_j_kg": q})
        return etat, Flux()

    # --- décharge ------------------------------------------------------
    def rechauffer(
        self, etat: EtatAir, ctx: Contexte, T_cible_K: float | None
    ) -> tuple[EtatAir, Flux]:
        """Réchauffe l'air avant une turbine, au plus jusqu'à la cible ;
        l'eau entraînée (gouttelettes, givre) s'évapore si l'air
        réchauffé le permet (F43)."""
        sortie, flux = self._rechauffer(etat, ctx, T_cible_K)
        sortie = mettre_a_l_equilibre(sortie, flux, self, "en décharge, ")
        return sortie, flux

    def _rechauffer(
        self, etat: EtatAir, ctx: Contexte, T_cible_K: float | None
    ) -> tuple[EtatAir, Flux]:
        air = ctx.air
        p, T_avant, m = etat.p_abs_pa, etat.T_K, etat.m_dot_kg_s
        if self.modele == "source_externe":
            if T_cible_K is None or T_avant >= T_cible_K:
                return etat, Flux()
            q = air.h(p, T_cible_K) - air.h(p, T_avant)
            self.externe_j += m * q * ctx.dt_s
            return etat.remplacer(T_K=T_cible_K), Flux(
                Q_ajoute_w=m * q, source="externe")
        if self.modele == "huile_ideale":
            if T_cible_K is None or T_avant >= T_cible_K:
                return etat, Flux()
            q = air.h(p, T_cible_K) - air.h(p, T_avant)
            Q = m * q * ctx.dt_s
            if self.reserve_j >= Q:
                self.reserve_j -= Q
                return etat.remplacer(T_K=T_cible_K), Flux(
                    Q_ajoute_w=m * q, source=self.nom)
            if not self.appoint_externe:
                self.avertir("réserve d'huile idéale épuisée, sans appoint")
                return etat, Flux()
            self.externe_j += Q
            self.avertir("réserve d'huile idéale épuisée : appoint externe")
            return etat.remplacer(T_K=T_cible_K), Flux(
                Q_ajoute_w=m * q, source="externe")
        if self.reservoirs is not None:
            T_out, Q = self.reservoirs.rechauffer(
                air, p, T_avant, m, ctx.dt_s, T_cible_K)
            if T_cible_K is not None and T_out < T_cible_K - 0.5:
                self.T_sortie_min_K = min(self.T_sortie_min_K, T_out)
                self.avertir(
                    f"réservoir chaud vide ou trop froid pour la cible de "
                    f"{T_cible_K - 273.15:.0f} °C (pas d'appoint)")
            return self._avec_perte_de_charge(
                etat.remplacer(T_K=T_out), ctx), Flux(
                Q_ajoute_w=Q / ctx.dt_s, source=self.nom if Q > 0 else "",
                dp_pa=self.perte_de_charge_pa,
                resultat={"Q_j": Q, "T_chaud_K": self.reservoirs.T_chaud_K})
        # gravier (formules.md#F30)
        assert self.lit is not None
        pinch = self.pincement_K
        p_cuve = self.pression_de_travail(p, ctx)
        self.p_derniere_pa = p_cuve
        T_in_cuve = T_avant + pinch
        T_plein = self.lit.sortie_instantanee(
            air, m, T_in_cuve, p_cuve, sens=-1) - pinch
        f = 0.0
        if (self.bypass and T_cible_K is not None and T_plein > T_cible_K
                and T_plein > T_avant):
            f = (T_plein - T_cible_K) / (T_plein - T_avant)
            f = min(max(f, 0.0), FRACTION_BYPASS_MAX)
        r = self.lit.pas(air, ctx.dt_s, m * (1.0 - f), T_in_cuve, p_cuve,
                         ctx.T_amb_K, sens=-1)
        self._surveiller_wakao()
        T_out = r["T_sortie_K"] - pinch
        T_mix = f * T_avant + (1.0 - f) * T_out
        if T_cible_K is not None:
            T_mix = min(T_mix, max(T_cible_K, T_avant))
        T_mix = max(T_mix, T_avant)
        q = air.h(p, T_mix) - air.h(p, T_avant)
        if T_cible_K is not None and T_mix < T_cible_K - 0.5:
            self.T_sortie_min_K = min(self.T_sortie_min_K, T_mix)
            self.avertir(
                f"cuve trop froide pour atteindre la cible de "
                f"{T_cible_K - 273.15:.0f} °C (pas d'appoint ; minimum "
                f"suivi dans T_sortie_min_K)"
            )
        flux = Flux(Q_ajoute_w=m * q, source=self.nom, dp_pa=r["dp_pa"],
                    resultat={"fraction_bypass": f,
                              "Q_cuve_j": -r["Q_air_vers_solide_j"]})
        return etat.remplacer(T_K=T_mix), flux

    def _avec_perte_de_charge(self, etat: EtatAir,
                              ctx: Contexte) -> EtatAir:
        """Chute de pression isenthalpique de l'échangeur (Shi : 0,04 MPa)."""
        if self.perte_de_charge_pa <= 0:
            return etat
        p_out = etat.p_abs_pa - self.perte_de_charge_pa
        T_out = ctx.air.T_de_p_h(p_out, ctx.air.h(etat.p_abs_pa, etat.T_K))
        return etat.remplacer(p_abs_pa=p_out, T_K=T_out)

    # --- attente -------------------------------------------------------
    def attendre(self, ctx: Contexte) -> float:
        """Pas sans débit (conduction et pertes) ; retourne Q perdue [J]."""
        if self.reservoirs is not None:
            return self.reservoirs.attendre(ctx.dt_s, ctx.T_amb_K)
        if self.lit is None:
            return 0.0
        p = self.p_derniere_pa if self.p_derniere_pa else ctx.p_amb_pa
        r = self.lit.pas(ctx.air, ctx.dt_s, 0.0, ctx.T_amb_K, p,
                         ctx.T_amb_K)
        return float(r["Q_perte_j"])

    def _surveiller_wakao(self) -> None:
        assert self.lit is not None
        Re = self.lit.Re_dernier
        if Re > 0 and not self.correlations.dans_validite(Re):
            bas = Re < self.correlations.wakao_Re_min
            cote = "sous" if bas else "au-dessus de"
            self.avertir(
                f"nombre de Reynolds {cote} du domaine de Wakao "
                f"({self.correlations.wakao_Re_min:.0f} à "
                f"{self.correlations.wakao_Re_max:.0f}) : coefficient "
                f"d'échange extrapolé"
            )

    def verifier_validite(self) -> list[str]:
        avis: list[str] = []
        if self.modele == "gravier":
            if self.volume_m3 <= 0:
                avis.append("volume de cuve nul")
            if self.n_cellules < 5:
                avis.append(
                    f"{self.n_cellules} cellules : front thermique mal "
                    f"résolu (20 ou plus recommandé)")
            if self.pincement_K < 0:
                avis.append("pincement négatif")
        elif self.modele == "huile_ideale":
            avis.append(
                "modèle « huile_ideale » : hypothèse comptable de Dormoy "
                "(réserve sans perte ni limite de température), pas un "
                "échangeur réel"
            )
        elif self.modele == "huile_deux_reservoirs":
            if self.fluide.T_max_K is None:
                avis.append(
                    "huile sans T_max : la limite d'emploi de l'huile "
                    "(dégradation) n'est pas vérifiée")
            avis.append(
                "cp de l'huile pris constant (valeur de Tola à l'ambiant) ; "
                "concept LTA-CAES de Wolf et Budt 2014 (PDF non récupéré)")
        elif self.modele == "eau_sous_pression":
            avis.append(
                f"eau sous pression : stockage plafonné par l'ébullition à "
                f"{(self.fluide.T_max_K or 0) - 273.15:.0f} °C "
                f"({self.p_cuve_pa / 1e5:.0f} bar)")
        if (self.reservoirs is not None
                and self.reservoirs.T_froid_maintenue_K is not None):
            avis.append(
                "réservoir froid maintenu à température fixe : le "
                "refroidissement du liquide de retour n'est pas modélisé "
                "(hypothèse de Shi 2024)")
        if self.physique and self.coefficient_perte <= 0:
            avis.append("isolation parfaite (aucune perte pendant l'attente)")
        return avis

    def description(self) -> str:
        base = super().description()
        if self.modele == "gravier" and self.lit is not None:
            base += (
                f" : {self.volume_m3:.2f} m³, "
                f"{self.masse_gravier_kg:.0f} kg de {self.materiau.nom}, "
                f"{self.pression}, pincement {self.pincement_K:.0f} K"
            )
        elif self.reservoirs is not None:
            base += (
                f" : {self.masse_kg:.0f} kg de {self.fluide.nom}, pincement "
                f"{self.pincement_K:.0f} K")
        if self.isolant is not None:
            base += f" ; isolant : {self.isolant.description()}"
        return base
