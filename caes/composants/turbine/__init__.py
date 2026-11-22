"""Composant « turbine » : une machine à plusieurs étages de détente.

Quatre modèles (phase 7, voir ``docs/composants/turbine.md``) :

* ``polytropique_deprag`` (phase 2, formules.md#F17, #F18) : détente
  polytropique entre les pressions nominales de chaque étage,
  rendements mécanique et électrique par étage (tableau 9 de Dormoy) ;
  modèle à point fixe ;
* ``isentropique`` (Shi 2024, Zhang S. 2025, #F34) : rendement
  isentropique constant ; accepte une pression d'entrée variable ;
* ``polytropique_rendement`` (Tola 2022, #F35) : rendement polytropique
  constant ; accepte une pression d'entrée variable ;
* ``flugel`` (Zhang S. 2025, #F39) : rendement isentropique nominal
  corrigé hors du point nominal, débit imposé par la loi de l'ellipse
  (pression glissante réelle : le débit varie avec la pression du
  réservoir).

Dans une chaîne, chaque étage est un maillon (``turbine.1``, ...)
précédé des stockages de chaleur qui le réchauffent. La température
nominale d'entrée ``T_entree_cible`` est la **cible** des réchauffeurs
placés avant l'étage ; sans réchauffeur, l'étage reçoit l'air tel quel
(pas d'appoint implicite).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from caes.composants.base import (
    Composant,
    Contexte,
    ErreurComposant,
    EtatAir,
    Flux,
    HorsDomaine,
)
from caes.composants.humidite import mettre_a_l_equilibre
from caes.composants.turbine.flugel import (
    PointNominal,
    debit_reduit_relatif,
    rendement_relatif,
    resoudre_debit_glissant,
    vitesse_reduite_relative,
)
from caes.composants.turbine.rendement import (
    detendre_isentropique,
    detendre_polytropique_rendement,
)
from caes.turbine import EtageTurbine as ModeleEtage
from caes.turbine import detendre_etage

TOLERANCE_PRESSION_PA = 1.0
T_MIN_GAZ_K = 100.0
"""Sous cette température, l'air se condense (ébullition ≈ 79 K à 1 bar,
≈ 100 K vers 10 bar) : le modèle gazeux n'a plus de sens et l'équation
d'état de CoolProp ne converge plus."""
MODELES_PRESSION_VARIABLE = ("isentropique", "polytropique_rendement",
                             "flugel")


@dataclass(frozen=True)
class ResultatDetenteEtage:
    """Grandeurs massiques d'un étage (sans le réchauffage amont)."""

    p_in_pa: float
    T_in_K: float
    p_out_pa: float
    T_out_K: float
    w_pol: float
    w_mec: float
    w_el: float
    dh: float
    rendement_relatif: float = 1.0

    @property
    def q_residuel(self) -> float:
        """Chaleur implicite [J/kg] : −dh − w_mec (> 0 = perdue)."""
        return -self.dh - self.w_mec


class EtageTurbineMaillon:
    """Vue « maillon » de l'étage ``numero`` d'une turbine."""

    def __init__(self, machine: Turbine, numero: int,
                 spec: dict[str, Any]) -> None:
        self.machine = machine
        self.numero = numero
        self.spec = spec
        if spec.get("p_sortie") is None:
            if machine.p_sortie_finale_pa is None:
                raise ErreurComposant(
                    f"{machine.nom} : p_sortie manquant à l'étage {numero} "
                    f"(ou donner pression_sortie_finale à la machine pour "
                    f"une répartition égale glissante)")
            self.p_sortie_pa = machine.p_sortie_finale_pa
            self.sortie_glissante = True
        else:
            self.p_sortie_pa = float(spec["p_sortie"])
            self.sortie_glissante = False
        self.p_entree_pa: float | None = (
            None if spec.get("p_entree") is None else float(spec["p_entree"]))
        self.T_entree_cible_K: float | None = (
            None if spec.get("T_entree_cible") is None
            else float(spec["T_entree_cible"]))
        self.p_sortie_liaison_pa = self.p_sortie_pa
        self.modele: ModeleEtage | None = None
        if machine.modele == "polytropique_deprag":
            if self.p_entree_pa is None:
                raise ErreurComposant(
                    f"{machine.nom} : p_entree requis pour chaque étage du "
                    f"modèle polytropique_deprag")
            self.modele = ModeleEtage(
                p_entree_pa=self.p_entree_pa, p_sortie_pa=self.p_sortie_pa,
                indice_polytropique=float(spec["indice_polytropique"]),
                rendement_mecanique=float(spec["rendement_mecanique"]),
                rendement_electrique=float(spec["rendement_electrique"]),
                T_entree_cible_K=self.T_entree_cible_K,
            )
        # état courant (pression glissante, Flügel)
        self.p_in_courant_pa: float | None = None
        self.p_out_courant_pa: float | None = None
        self.eta_relatif = 1.0
        self.T_in_derniere_K: float | None = None
        self.point_nominal: PointNominal | None = None
        if machine.modele == "flugel":
            if self.p_entree_pa is None:
                raise ErreurComposant(
                    f"{machine.nom} : p_entree (point nominal) requis pour "
                    f"chaque étage du modèle flugel")
            T0 = spec.get("T_entree_nominale", self.T_entree_cible_K)
            if T0 is None:
                raise ErreurComposant(
                    f"{machine.nom} : T_entree_nominale (ou T_entree_cible) "
                    f"requis pour le modèle flugel")
            self.point_nominal = PointNominal(
                self.p_entree_pa, self.p_sortie_pa, float(T0),
                machine.debit_massique_kg_s)

    @property
    def nom(self) -> str:
        return f"{self.machine.nom}.{self.numero}"

    def _detendre(self, ctx: Contexte, p_in: float, T_in: float,
                  p_out: float) -> tuple[float, float, float, float]:
        """(T_out, w, dh, η_relatif) selon le modèle de la machine."""
        m = self.machine
        if m.modele == "polytropique_deprag":
            assert self.modele is not None
            T_out, w, dh = detendre_etage(ctx.air, p_in, T_in, p_out,
                                          self.modele.indice_polytropique)
            return T_out, w, dh, 1.0
        if m.modele == "polytropique_rendement":
            T_out, w, dh = detendre_polytropique_rendement(
                ctx.air, p_in, T_in, p_out, m.rendement_etage(self.numero))
            return T_out, w, dh, 1.0
        eta = m.rendement_etage(self.numero)
        if m.modele == "flugel":
            eta *= self.eta_relatif
        T_out, w, dh = detendre_isentropique(ctx.air, p_in, T_in, p_out, eta)
        return T_out, w, dh, self.eta_relatif

    def pas(self, etat: EtatAir, ctx: Contexte) -> tuple[EtatAir, Flux]:
        """Détente de l'étage puis laminage vers l'étage suivant."""
        air = ctx.air
        m = self.machine
        p, T = etat.p_abs_pa, etat.T_K
        self.T_in_derniere_K = T
        if self.p_in_courant_pa is not None:
            p_in = self.p_in_courant_pa
            p_out = self.p_out_courant_pa or self.p_sortie_pa
            if abs(p - p_in) > 0.01 * p_in:
                m.avertir(
                    f"étage {self.numero} : pression reçue différente de "
                    f"celle prévue par la répartition des étages (loi de "
                    f"l'ellipse ou répartition égale)")
        else:
            p_in = p
            p_out = self.p_sortie_pa
            if self.p_entree_pa is not None:
                if p > self.p_entree_pa + TOLERANCE_PRESSION_PA:
                    T = air.T_de_p_h(self.p_entree_pa, air.h(p, T))
                    p_in = self.p_entree_pa
                    m.avertir(
                        f"étage {self.numero} : air reçu au-dessus de la "
                        f"pression nominale d'entrée "
                        f"({self.p_entree_pa / 1e5:.2f} bar), laminé")
                elif (p < self.p_entree_pa - TOLERANCE_PRESSION_PA
                      and m.modele == "polytropique_deprag"):
                    p_in = self.p_entree_pa
                    m.avertir(
                        f"étage {self.numero} : air reçu sous la pression "
                        f"nominale d'entrée ({self.p_entree_pa / 1e5:.2f} "
                        f"bar) ; calcul fait à la pression nominale (modèle "
                        f"à point fixe, voir le modèle « flugel »)")
        m_dot = etat.m_dot_kg_s
        if p_in <= p_out * (1.0 + 1e-9):
            m.avertir(
                f"étage {self.numero} : pression d'entrée au niveau de la "
                f"sortie, aucune détente (étage inactif)")
            r = ResultatDetenteEtage(p_in, T, p_out, T, 0.0, 0.0, 0.0, 0.0,
                                     self.eta_relatif)
            return EtatAir(p_out, T, m_dot, etat.w_vapeur_kg_kg,
                           etat.w_liquide_kg_kg), Flux(resultat=r)
        try:
            T_out, w, dh, eta_rel = self._detendre(ctx, p_in, T, p_out)
        except ValueError as err:
            raise HorsDomaine(
                f"{self.nom} : détente de {p_in / 1e5:.1f} à "
                f"{p_out / 1e5:.1f} bar depuis {T - 273.15:.0f} °C hors du "
                f"domaine de l'équation d'état ({err})") from err
        if T_out < T_MIN_GAZ_K:
            raise HorsDomaine(
                f"{self.nom} : l'air sortirait à {T_out - 273.15:.0f} °C, "
                f"dans la zone de condensation de l'air : détente sans "
                f"réchauffage hors du modèle")
        w_mec = m.rendement_mecanique_etage(self.numero) * w
        w_el = m.rendement_electrique_etage(self.numero) * w_mec
        r = ResultatDetenteEtage(
            p_in_pa=p_in, T_in_K=T, p_out_pa=p_out, T_out_K=T_out,
            w_pol=w, w_mec=w_mec, w_el=w_el, dh=dh, rendement_relatif=eta_rel,
        )
        flux = Flux(W_el_produit_w=m_dot * w_el, W_pol_w=-m_dot * w,
                    resultat=r)
        T_liaison = T_out
        p_liaison = p_out
        if (self.p_in_courant_pa is None
                and self.p_sortie_liaison_pa < p_out - TOLERANCE_PRESSION_PA):
            p_liaison = self.p_sortie_liaison_pa
            T_liaison = air.T_de_p_h(p_liaison, air.h(p_out, T_out))
        if T_out < m.T_sortie_min_K:
            m.T_sortie_min_observee_K = min(m.T_sortie_min_observee_K, T_out)
            m.avertir(
                f"étage {self.numero} : air rejeté sous "
                f"{m.T_sortie_min_K - 273.15:.0f} °C : risque de givrage "
                f"(humidité, phase 9)")
        sortie = EtatAir(p_liaison, T_liaison, m_dot, etat.w_vapeur_kg_kg,
                         etat.w_liquide_kg_kg)
        sortie = mettre_a_l_equilibre(sortie, flux, m,
                                      f"étage {self.numero} : ")
        return sortie, flux


class Turbine(Composant):
    TYPE = "turbine"
    MODELES = ("polytropique_deprag", "isentropique",
               "polytropique_rendement", "flugel")

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        etages = self.param("etages")
        if not isinstance(etages, list) or not etages:
            raise ErreurComposant(f"{nom} : il faut au moins un étage")
        self.debit_massique_kg_s = self.nombre("debit_massique")
        if self.debit_massique_kg_s <= 0:
            raise ErreurComposant(f"{nom} : débit massique <= 0")
        # Seuil d'avertissement de givrage : point de congélation de l'eau
        # (définition de l'échelle Celsius, pas un paramètre physique).
        self.T_sortie_min_K = self.nombre("T_sortie_min", 273.15)
        self.T_sortie_min_observee_K = float("inf")
        self.p_sortie_finale_pa = self.nombre("pression_sortie_finale", None)
        self.rendements_etages: list[float] = []
        self.rendements_mec: list[float] = []
        self.rendements_el: list[float] = []
        if self.modele == "polytropique_deprag":
            for e in etages:
                self.rendements_mec.append(float(e["rendement_mecanique"]))
                self.rendements_el.append(float(e["rendement_electrique"]))
                self.rendements_etages.append(1.0)
        else:
            cle = ("rendement_polytropique"
                   if self.modele == "polytropique_rendement"
                   else "rendement_isentropique")
            eta = self.nombre(cle)
            eta_mec = self.nombre("rendement_mecanique")
            eta_el = self.nombre("rendement_electrique")
            for e in etages:
                self.rendements_etages.append(
                    float(e[cle]) if e.get(cle) is not None else eta)
                self.rendements_mec.append(
                    float(e["rendement_mecanique"])
                    if e.get("rendement_mecanique") is not None else eta_mec)
                self.rendements_el.append(
                    float(e["rendement_electrique"])
                    if e.get("rendement_electrique") is not None else eta_el)
        self.t4 = self.nombre("t4", None) if self.modele == "flugel" else None
        if self.modele == "flugel" and self.t4 is None:
            raise ErreurComposant(f"{nom} : t4 requis pour le modèle flugel")
        self.etages = [EtageTurbineMaillon(self, i + 1, e)
                       for i, e in enumerate(etages)]

    # --- accès ---------------------------------------------------------
    @property
    def nb_etages(self) -> int:
        return len(self.etages)

    @property
    def debit_variable(self) -> bool:
        return self.modele == "flugel"

    @property
    def repartition_egale(self) -> bool:
        """Tous les étages glissent avec un rapport commun (Tola)."""
        return any(e.sortie_glissante for e in self.etages)

    @property
    def pression_entree_variable(self) -> bool:
        return self.modele in MODELES_PRESSION_VARIABLE

    def etage(self, numero: int) -> EtageTurbineMaillon:
        if not 1 <= numero <= self.nb_etages:
            raise ErreurComposant(
                f"{self.nom} : pas d'étage {numero} (1 à {self.nb_etages})")
        return self.etages[numero - 1]

    def rendement_etage(self, numero: int) -> float:
        return self.rendements_etages[numero - 1]

    def rendement_mecanique_etage(self, numero: int) -> float:
        return self.rendements_mec[numero - 1]

    def rendement_electrique_etage(self, numero: int) -> float:
        return self.rendements_el[numero - 1]

    # --- préparation du pas ----------------------------------------------
    def preparer(self, p_disponible_pa: float) -> float:
        """Fixe les pressions des étages pour ce pas et rend le débit
        [kg/s] : nominal, loi de l'ellipse (``flugel``, F39) ou
        répartition égale glissante (``pression_sortie_finale``)."""
        if self.repartition_egale and self.modele != "flugel":
            n = self.nb_etages
            p_fin = float(self.p_sortie_finale_pa)
            r = max(p_disponible_pa / p_fin, 1.0) ** (1.0 / n)
            p = p_disponible_pa
            for e in self.etages:
                if e.sortie_glissante:
                    e.p_in_courant_pa = p
                    e.p_out_courant_pa = p / r
                    p = p / r
                else:
                    e.p_in_courant_pa = None
                    p = e.p_sortie_pa
            return self.debit_massique_kg_s
        return self.debit(p_disponible_pa)

    def debit(self, p_disponible_pa: float) -> float:
        """Débit massique du pas [kg/s]. Nominal, sauf pour ``flugel`` où
        la loi de l'ellipse l'impose (formules.md#F39)."""
        if self.modele != "flugel":
            return self.debit_massique_kg_s
        points = [e.point_nominal for e in self.etages]
        assert all(pn is not None for pn in points)
        T_in = [
            e.T_in_derniere_K if e.T_in_derniere_K is not None
            else e.point_nominal.T0_K  # type: ignore[union-attr]
            for e in self.etages
        ]
        G, p_ins = resoudre_debit_glissant(
            points, T_in, p_disponible_pa,  # type: ignore[arg-type]
            self.etages[-1].p_sortie_pa)
        for k, e in enumerate(self.etages):
            e.p_in_courant_pa = p_ins[k]
            e.p_out_courant_pa = (p_ins[k + 1] if k + 1 < len(p_ins)
                                  else e.p_sortie_pa)
            pn = e.point_nominal
            assert pn is not None
            G_red = debit_reduit_relatif(pn, G, p_ins[k], T_in[k])
            n_red = vitesse_reduite_relative(pn, T_in[k])
            e.eta_relatif = rendement_relatif(G_red, n_red, float(self.t4))
            if e.eta_relatif < 0.5:
                self.avertir(
                    f"étage {e.numero} : loin du point nominal (rendement "
                    f"relatif de Flügel sous 50 %) ; coefficients ajustés "
                    f"sur de grosses turbines")
        if G <= 0:
            self.avertir("pression disponible insuffisante : débit nul")
        return G

    def verifier_validite(self) -> list[str]:
        avis: list[str] = []
        for et in self.etages:
            if et.p_sortie_pa < 0.9e5:
                avis.append(
                    f"étage {et.numero} : pression de sortie "
                    f"{et.p_sortie_pa / 1e5:.2f} bar sous la pression "
                    f"atmosphérique (donnée fabricant, artefact signalé en "
                    f"phase 3)")
        for i, r in enumerate(self.rendements_etages, 1):
            if not 0.0 < r <= 1.0:
                avis.append(f"rendement de l'étage {i} hors de ]0, 1]")
        if self.modele == "flugel":
            avis.append(
                "modèle « flugel » : coefficients (t4 = 0,3) ajustés sur de "
                "grandes turbines (Zhang S. 2025) ; à vérifier pour une "
                "petite turbine")
        return avis
