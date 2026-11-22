"""Assembleur : du fichier YAML à la simulation (phase 6).

Un scénario décrit une installation par ses **composants** (section
``composants``, chacun avec un ``type`` et un ``modele``) et par deux
**chaînes** qui disent dans quel ordre l'air les traverse :

* ``charge.chaine`` : du compresseur (étage par étage) au réservoir,
  avec les stockages de chaleur et les refroidisseurs intercalés ;
* ``decharge.chaine`` : du réservoir aux étages de turbine, avec le
  détendeur et les réchauffeurs.

L'assembleur instancie les composants, vérifie les liaisons (ordre des
étages, pressions compatibles, un seul réservoir) et construit une
:class:`Installation` qui sait simuler une charge, une décharge, une
attente ou des cycles jusqu'au régime stable. Les séries temporelles
et les totaux gardent les noms des phases 1 à 5, pour que les bilans
d'exergie (:mod:`caes.exergie`) et le tableau « 1000 unités »
(:mod:`caes.tableau_1000`) s'appliquent tels quels.

Règles d'assemblage : formules.md#F33.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from caes.ambiance import Ambiance, ambiance_depuis_valeurs
from caes.composants.humidite import point_de_rosee
from caes.composants import (
    FABRIQUES,
    Attente,
    Avertissement,
    Composant,
    Compresseur,
    Contexte,
    Detente,
    ElementChaine,
    EtatAir,
    Flux,
    HorsDomaine,
    Refroidisseur,
    ReservoirAir,
    Segment,
    StockageChaleur,
    Turbine,
)
from caes.proprietes import Air, air_par_defaut
from caes.registre import UNITES, Registre
from caes.scenario import Scenario, charger_scenario
from caes.systeme import (
    ResultatCharge,
    ResultatDecharge,
    rendements_aller_retour,
)

MODES = ("charge", "decharge", "cycles")
CLES_SCENARIO = {"ambiance", "composants", "charge", "decharge",
                 "simulation"}
NOM_VALIDE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TYPES_ENTRE_ETAGES_CHARGE = {"refroidisseur", "stockage_chaleur",
                             "secheur", "perte_debit"}
WH_PAR_J = 1.0 / 3.6e6


class ErreurAssemblage(ValueError):
    """Le scénario ne décrit pas une installation cohérente."""


# ----------------------------------------------------------------------
# Chaînes
# ----------------------------------------------------------------------


@dataclass
class ChaineCharge:
    elements: list[ElementChaine]
    compresseur: Compresseur
    reservoir: ReservoirAir
    segments: list[Segment]
    """Pour chaque étage i (index i−1) : les maillons jusqu'à l'étage
    suivant (réservoir exclu)."""
    stockage_par_etage: dict[int, StockageChaleur]
    p_cible_pa: float
    dt_s: float
    duree_max_s: float
    etat_initial: dict[str, float] | None
    surpression_aval_pa: float = 0.0
    """Pertes de charge des maillons placés après le dernier étage de
    compression : le dernier étage doit les compenser."""


@dataclass
class ChaineDecharge:
    elements: list[ElementChaine]
    reservoir: ReservoirAir
    detente: Detente | None
    turbine: Turbine | None
    segments: list[Segment]
    """Pour chaque étage de turbine : les réchauffeurs qui le précèdent."""
    cibles: dict[int, float | None]
    """Index du maillon (dans ``elements``) → cible du prochain étage."""
    debit_impose_kg_s: float | None
    dt_s: float
    duree_max_s: float
    etat_initial: dict[str, float] | None


@dataclass
class Cycle:
    numero: int
    charge: ResultatCharge
    decharge: ResultatDecharge
    attente_h: float
    chaleur_cuves_debut_kwh: float
    chaleur_cuves_fin_kwh: float
    pertes_attente_kwh: float


@dataclass
class ResultatSimulation:
    """Ce que rend :meth:`Installation.simuler`, selon le mode."""

    installation: Installation
    mode: str
    charge: ResultatCharge | None = None
    decharge: ResultatDecharge | None = None
    cycles: list[Cycle] = field(default_factory=list)
    converge: bool | None = None

    @property
    def dernier_cycle(self) -> Cycle | None:
        return self.cycles[-1] if self.cycles else None

    @property
    def charge_finale(self) -> ResultatCharge | None:
        c = self.dernier_cycle
        return c.charge if c else self.charge

    @property
    def decharge_finale(self) -> ResultatDecharge | None:
        c = self.dernier_cycle
        return c.decharge if c else self.decharge

    def rendements(self) -> dict[str, float] | None:
        ch, d = self.charge_finale, self.decharge_finale
        if ch is None or d is None:
            return None
        return rendements_aller_retour(ch, d)

    @property
    def avertissements(self) -> list[Avertissement]:
        return self.installation.avertissements()

    def resume(self) -> str:
        parts = [f"{self.installation.nom} ({self.mode})"]
        ch, d = self.charge_finale, self.decharge_finale
        if self.cycles:
            parts.append(f"cycle {self.cycles[-1].numero}"
                         + ("" if self.converge else " (non stabilisé)"))
        if ch is not None:
            parts.append(
                f"charge {ch.totaux['energie_electrique_kwh']:.1f} kWh en "
                f"{ch.totaux['duree_h']:.2f} h")
        if d is not None:
            parts.append(
                f"produit {d.totaux['energie_electrique_kwh']:.2f} kWh en "
                f"{d.totaux['duree_min']:.1f} min, chaleur "
                + ", ".join(f"{k} {v:.1f}" for k, v in
                            d.chaleur_par_source.items()))
        r = self.rendements()
        if r:
            parts.append(
                f"RTE {r['rte_sans_chaleur'] * 100:.1f} % "
                f"({r['rte_avec_chaleur_externe'] * 100:.1f} % avec la "
                f"chaleur externe)")
        n = len(self.avertissements)
        if n:
            parts.append(f"{n} avertissement(s)")
        return " ; ".join(parts)


# ----------------------------------------------------------------------
# Installation
# ----------------------------------------------------------------------


@dataclass
class Installation:
    nom: str
    description: str
    scenario: Scenario
    ambiance: Ambiance
    air: Air
    registre: Registre
    composants: dict[str, Composant]
    mode: str
    charge: ChaineCharge | None
    decharge: ChaineDecharge | None
    attente: Attente | None
    options: dict[str, Any]
    avis_statiques: list[Avertissement] = field(default_factory=list)
    avis_assemblage: list[Avertissement] = field(default_factory=list)
    """Avis émis à l'assemblage (liaisons), conservés par ``verifier``."""

    # --- accès ---------------------------------------------------------
    @property
    def stockages(self) -> list[StockageChaleur]:
        return [c for c in self.composants.values()
                if isinstance(c, StockageChaleur)]

    @property
    def reservoir(self) -> ReservoirAir | None:
        if self.charge is not None:
            return self.charge.reservoir
        if self.decharge is not None:
            return self.decharge.reservoir
        return None

    def avertissements(self) -> list[Avertissement]:
        """Avis statiques (vérification) puis dynamiques (simulation)."""
        tous = list(self.avis_statiques)
        for c in self.composants.values():
            tous.extend(c.avertissements)
        return tous

    def verifier(self) -> list[Avertissement]:
        """Vérifications statiques de l'ambiance et des composants."""
        avis = [Avertissement("ambiance", m)
                for m in self.ambiance.verifier_validite()]
        for c in self.composants.values():
            avis.extend(Avertissement(c.nom, m)
                        for m in c.verifier_validite())
        self.avis_statiques = list(self.avis_assemblage) + avis
        return self.avis_statiques

    def description_composants(self) -> list[str]:
        return [c.description() for c in self.composants.values()]

    # --- simulation ----------------------------------------------------
    def simuler(self) -> ResultatSimulation:
        """Lance la simulation selon ``simulation.mode``."""
        self.verifier()
        if self.mode == "charge":
            return ResultatSimulation(self, self.mode,
                                      charge=self.simuler_charge())
        if self.mode == "decharge":
            return ResultatSimulation(self, self.mode,
                                      decharge=self.simuler_decharge())
        return self.simuler_cycles()

    def _initialiser_stockages(self, t_s: float) -> None:
        T = self.ambiance.T_amb_a(t_s)
        for st in self.stockages:
            if st.T_initiale_K is None:
                st.initialiser(T)

    def simuler_charge(self, reprise: bool = False,
                       t0_s: float = 0.0) -> ResultatCharge:
        """Charge jusqu'à la pression cible (formules.md#F13).

        ``reprise`` : repart de l'état courant du réservoir (cycles).
        """
        if self.charge is None:
            raise ErreurAssemblage(f"{self.nom} : pas de chaîne de charge")
        ch = self.charge
        air, amb = self.air, self.ambiance
        comp, res = ch.compresseur, ch.reservoir
        dt, t_max = ch.dt_s, ch.duree_max_s
        if not reprise or not res.initialise:
            ei = ch.etat_initial
            if ei is None:
                raise ErreurAssemblage(
                    f"{self.nom} : charge.reservoir_initial manquant")
            res.initialiser(air, ei["p"], ei["T"], ei.get("T_paroi"),
                            w_kg_kg=amb.w_kg_kg)
        self._initialiser_stockages(t0_s)
        p_init, T_init = res.p_abs_pa, res.T_K
        w_amb = amb.w_kg_kg
        maillons = ch.elements[:-1]
        sans_etat = (not any(e.composant.a_un_etat for e in maillons)
                     and not amb.a_un_profil)
        cache: dict[int, tuple[EtatAir, list]] = {}
        nb = comp.nb_etages
        cumul = {k: 0.0 for k in (
            "E_el", "E_pol", "Q_poly", "Q_ref", "Q_sup", "E_air_perdu",
            "Q_paroi", "Q_ext", "m_in", "Q_cuves", "H_amb_in",
            "eau_entree", "eau_condensee", "eau_separee", "eau_reservoir",
            "Q_latente")}
        Q_ref_etage = np.zeros(nb)
        Q_sup_etage = np.zeros(nb)
        Q_cuve_etage = np.zeros(nb)
        a_des_cuves = bool(ch.stockage_par_etage)
        U0, m0 = res.energie_interne_j, res.masse_kg
        lignes: list[dict[str, float]] = []
        t = t0_s
        arret = "pression cible atteinte"
        while res.p_abs_pa < ch.p_cible_pa:
            if t - t0_s >= t_max:
                arret = "durée maximale atteinte"
                break
            ctx = Contexte(air, amb, t, dt)
            m_asp = comp.debit_aspire(ctx)
            comp.preparer(res.p_abs_pa, ctx.p_amb_pa,
                          res.surpression_entree_pa + ch.surpression_aval_pa)
            ctx.p_refoulement_pa = comp.p_chaine_pa
            cle = comp.cle_cache
            if sans_etat and cle in cache:
                etat_fin, parcours = cache[cle]
            else:
                etat = EtatAir(ctx.p_amb_pa, ctx.T_aspiration_K, m_asp,
                               w_vapeur_kg_kg=w_amb)
                parcours = []
                for el in maillons:
                    etat_in = etat
                    etat, flux = _traverser_charge(el, etat, ctx)
                    parcours.append((el, etat_in, etat, flux))
                etat_fin = etat
                if sans_etat:
                    cache[cle] = (etat_fin, parcours)
            if res.eau_initiale_a_plafonner:
                # L'air déjà dans le réservoir vient d'une charge
                # précédente par la même chaîne : il n'est pas plus
                # humide que ce qu'elle refoule (hypothèse, F43).
                res.plafonner_eau(etat_fin.w_vapeur_kg_kg)
            h_amb = air.h(ctx.p_amb_pa, ctx.T_aspiration_K)
            P_pol = sum(f.W_pol_w for _, _, _, f in parcours
                        if f.W_pol_w > 0)
            P_el = comp.puissance_electrique_depuis_travail(P_pol)
            h_sortie = air.h(etat_fin.p_abs_pa, etat_fin.T_K)
            m_res = etat_fin.m_dot_kg_s
            flux_res = res.remplir(ctx, etat_fin)
            t += dt
            # --- comptes du pas ---------------------------------------
            cumul["E_el"] += P_el * dt
            cumul["E_pol"] += P_pol * dt
            Q_poly_w = Q_ref_w = Q_sup_w = Q_cuves_w = E_perdu_w = 0.0
            eau_cond_s = eau_sep_s = Q_lat_w = 0.0
            ligne: dict[str, float] = {}
            etage_courant = 0
            T_in_ref: dict[int, float] = {}
            T_out_seg: dict[int, float] = {}
            eps: dict[int, float] = {}
            for el, etat_in, etat_out, flux in parcours:
                if el.type_ == "compresseur":
                    etage_courant = el.etage or 0
                    r = flux.resultat
                    i = etage_courant
                    Q_poly_w += -etat_in.m_dot_kg_s * r.q_poly
                    ligne[f"beta_{i}"] = r.rapport_pression
                    ligne[f"p_in_comp_{i}_pa"] = r.p_in_pa
                    ligne[f"T_in_comp_{i}_K"] = r.T_in_K
                    ligne[f"T_out_comp_{i}_K"] = r.T_out_K
                    ligne[f"w_pol_{i}_j_kg"] = r.w_pol
                    ligne[f"q_poly_{i}_j_kg"] = r.q_poly
                    T_out_seg[i] = etat_out.T_K
                    continue
                i = etage_courant
                T_out_seg[i] = etat_out.T_K
                if el.type_ == "refroidisseur":
                    r = flux.resultat
                    m = etat_in.m_dot_kg_s
                    T_in_ref.setdefault(i, etat_in.T_K)
                    eps.setdefault(i, r.efficacite)
                    Q_ref_w += m * r.q
                    Q_sup_w += m * r.q_sup_seuil
                    Q_ref_etage[i - 1] += m * r.q * dt
                    Q_sup_etage[i - 1] += m * r.q_sup_seuil * dt
                    ligne[f"Q_ref_{i}_w"] = ligne.get(f"Q_ref_{i}_w", 0.0) + (
                        m * r.q)
                    ligne[f"Q_sup_seuil_{i}_w"] = ligne.get(
                        f"Q_sup_seuil_{i}_w", 0.0) + m * r.q_sup_seuil
                elif el.type_ == "stockage_chaleur":
                    Q_cuves_w += flux.Q_retire_w
                    Q_cuve_etage[i - 1] += flux.Q_retire_w * dt
                    ligne[f"Q_cuve_{i}_w"] = ligne.get(
                        f"Q_cuve_{i}_w", 0.0) + flux.Q_retire_w
                if flux.m_dot_perdu_kg_s > 0:
                    E_perdu_w += flux.m_dot_perdu_kg_s * (
                        air.h(etat_in.p_abs_pa, etat_in.T_K) - h_amb)
                eau_cond_s += max(flux.eau_condensee_kg_s, 0.0)
                eau_sep_s += flux.eau_separee_kg_s
                Q_lat_w += flux.Q_latente_w
            for i in range(1, nb + 1):
                ligne.setdefault(f"T_in_ref_{i}_K", T_in_ref.get(
                    i, T_out_seg.get(i, ligne[f"T_out_comp_{i}_K"])))
                ligne.setdefault(f"T_out_ref_{i}_K", T_out_seg.get(
                    i, ligne[f"T_out_comp_{i}_K"]))
                ligne.setdefault(f"Q_ref_{i}_w", 0.0)
                ligne.setdefault(f"Q_sup_seuil_{i}_w", 0.0)
                ligne.setdefault(f"eps_{i}", eps.get(i, 0.0))
                if a_des_cuves:
                    ligne.setdefault(f"Q_cuve_{i}_w", 0.0)
            cumul["Q_poly"] += Q_poly_w * dt
            cumul["Q_ref"] += Q_ref_w * dt
            cumul["Q_sup"] += Q_sup_w * dt
            cumul["E_air_perdu"] += E_perdu_w * dt
            cumul["Q_paroi"] += flux_res["q_perte_w"] * dt
            cumul["Q_ext"] += flux_res["q_ext_w"] * dt
            cumul["m_in"] += m_res * dt
            cumul["H_amb_in"] += m_res * h_amb * dt
            cumul["Q_cuves"] += Q_cuves_w * dt
            cumul["eau_entree"] += m_asp * w_amb * dt
            cumul["eau_condensee"] += eau_cond_s * dt
            cumul["eau_separee"] += eau_sep_s * dt
            cumul["eau_reservoir"] += m_res * etat_fin.w_total_kg_kg * dt
            cumul["Q_latente"] += Q_lat_w * dt
            ligne.update({
                "t_s": t - t0_s,
                "p_res_pa": res.p_abs_pa,
                "T_res_K": res.T_K,
                "T_paroi_K": res.T_paroi_K,
                "m_res_kg": res.masse_kg,
                "p_refoulement_pa": comp.p_refoulement_pa,
                "P_el_w": P_el,
                "P_pol_w": P_pol,
                "E_el_j": cumul["E_el"],
                "m_dot_asp_kg_s": m_asp,
                "m_dot_res_kg_s": m_res,
                "rendement_mecanique": comp.rendement_mecanique(),
                "Q_poly_w": Q_poly_w,
                "Q_ref_w": Q_ref_w,
                "Q_sup_seuil_w": Q_sup_w,
                "Q_paroi_res_w": flux_res["q_perte_w"],
                "T_entree_res_K": etat_fin.T_K,
                "T_amb_K": ctx.T_amb_K,
                "w_entree_res_kg_kg": etat_fin.w_total_kg_kg,
                "w_vapeur_res_kg_kg": res.w_vapeur_kg_kg,
                "eau_liquide_res_kg": res.eau_liquide_kg,
                "T_rosee_res_K": res.T_rosee_K,
            })
            lignes.append(ligne)

        series = pd.DataFrame(lignes)
        dU = res.energie_interne_j - U0
        # Énergie stockée, comptée par rapport à l'enthalpie de l'air aspiré
        # (qui peut varier avec le profil météo) : formules.md#F13.
        E_stock = dU - cumul["H_amb_in"]
        somme = (
            (cumul["E_el"] - cumul["E_pol"]) + cumul["Q_poly"]
            + cumul["Q_ref"] + cumul["E_air_perdu"] + cumul["Q_paroi"]
            + E_stock + cumul["Q_cuves"]
        )
        bilan = {
            "E_el_j": cumul["E_el"],
            "pertes_mec_el_j": cumul["E_el"] - cumul["E_pol"],
            "Q_poly_rejete_j": cumul["Q_poly"],
            "Q_refroidisseurs_j": cumul["Q_ref"],
            "E_air_perdu_j": cumul["E_air_perdu"],
            "Q_paroi_reservoir_j": cumul["Q_paroi"],
            "E_stockee_relative_j": E_stock,
            "Q_cuves_j": cumul["Q_cuves"],
            "dU_reservoir_j": dU,
            "somme_j": somme,
            "residu_relatif": ((cumul["E_el"] - somme) / cumul["E_el"]
                               if cumul["E_el"] else 0.0),
            "masse_entree_kg": cumul["m_in"],
            "masse_stockee_kg": res.masse_kg - m0,
        }
        duree = t - t0_s
        totaux = {
            "duree_s": duree,
            "duree_h": duree / 3600.0,
            "energie_electrique_kwh": cumul["E_el"] * WH_PAR_J,
            "puissance_moyenne_kw": (cumul["E_el"] / duree / 1e3
                                     if duree else 0.0),
            "chaleur_refroidisseurs_kwh": cumul["Q_ref"] * WH_PAR_J,
            "chaleur_sup_seuil_kwh": cumul["Q_sup"] * WH_PAR_J,
            "chaleur_poly_rejetee_kwh": cumul["Q_poly"] * WH_PAR_J,
            "chaleur_paroi_reservoir_kwh": cumul["Q_paroi"] * WH_PAR_J,
            "masse_stockee_kg": res.masse_kg - m0,
            "p_finale_bar": res.p_abs_pa / 1e5,
            "T_finale_degC": res.T_K - 273.15,
            "debit_aspire_kg_s": (series["m_dot_asp_kg_s"].iloc[-1]
                                  if len(series) else 0.0),
            "debit_reservoir_kg_s": (series["m_dot_res_kg_s"].iloc[-1]
                                     if len(series) else 0.0),
            "chaleur_cuves_kwh": cumul["Q_cuves"] * WH_PAR_J,
            "p_initiale_bar": p_init / 1e5,
            "T_initiale_degC": T_init - 273.15,
            "eau_entree_kg": cumul["eau_entree"],
            "eau_condensee_kg": cumul["eau_condensee"],
            "eau_separee_kg": cumul["eau_separee"],
            "eau_reservoir_kg": cumul["eau_reservoir"],
            "eau_condensee_reservoir_kg": res.eau_liquide_kg,
            "chaleur_condensation_kwh": cumul["Q_latente"] * WH_PAR_J,
            "T_rosee_reservoir_degC": res.T_rosee_K - 273.15,
        }
        for i in range(nb):
            totaux[f"chaleur_refroidisseur_{i + 1}_kwh"] = (
                Q_ref_etage[i] * WH_PAR_J)
            totaux[f"chaleur_sup_seuil_{i + 1}_kwh"] = (
                Q_sup_etage[i] * WH_PAR_J)
            totaux[f"chaleur_cuve_{i + 1}_kwh"] = Q_cuve_etage[i] * WH_PAR_J
        resultat = ResultatCharge(
            scenario=self.scenario, series=series, totaux=totaux,
            bilan=bilan, arret=arret,
            parametres={
                "T0_K": amb.T_amb_K, "p0_pa": amb.p_amb_pa,
                "T_aspiration_K": amb.T_aspiration_K,
                "rendement_volumetrique": _fraction_perte_debit(ch),
                "volume_m3": res.volume_m3,
                "p_initiale_pa": p_init, "T_initiale_K": T_init,
            },
        )
        resultat.reservoir = res.modele_phys  # type: ignore[attr-defined]
        return resultat

    def simuler_decharge(self, reprise: bool = False,
                         t0_s: float = 0.0) -> ResultatDecharge:
        """Décharge jusqu'à l'arrêt du détendeur (formules.md#F17 à #F20)."""
        if self.decharge is None:
            raise ErreurAssemblage(f"{self.nom} : pas de chaîne de décharge")
        de = self.decharge
        air, amb = self.air, self.ambiance
        res, det, turb = de.reservoir, de.detente, de.turbine
        dt, t_max = de.dt_s, de.duree_max_s
        if not reprise or not res.initialise:
            ei = de.etat_initial
            if ei is None:
                raise ErreurAssemblage(
                    f"{self.nom} : decharge.reservoir_initial manquant")
            res.initialiser(air, ei["p"], ei["T"], ei.get("T_paroi"),
                            w_kg_kg=amb.w_kg_kg)
        self._initialiser_stockages(t0_s)
        m_dot = (turb.debit_massique_kg_s if turb is not None
                 else float(de.debit_impose_kg_s))  # type: ignore[arg-type]
        m_dot_total = 0.0
        p_init, T_init = res.p_abs_pa, res.T_K
        m0, U0, Tp0 = res.masse_kg, res.energie_interne_j, res.T_paroi_K
        nb = turb.nb_etages if turb is not None else 0
        Q_etage = np.zeros(nb)
        givre_etage = np.zeros(nb)
        eau_sortie = 0.0
        givre_detendeur = 0.0
        chaleur_par_source: dict[str, float] = {}
        sources_etages: dict[int, str] = {}
        cumul = {k: 0.0 for k in (
            "E_el", "E_mec", "E_pol", "Q_rech", "E_sortie_res", "Q_paroi",
            "Q_ext", "E_detendeur", "E_air_rejete", "Q_turbine_res",
            "m_out")}
        lignes: list[dict[str, float]] = []
        t = t0_s
        arret = "pression d'arrêt du détendeur atteinte"
        T_rejet_min = float("inf")
        p_arret = (det.p_arret_pa if det is not None
                   else (turb.etage(1).p_entree_pa if turb else 0.0))
        while res.p_abs_pa >= p_arret:
            if t - t0_s >= t_max:
                arret = "durée maximale atteinte"
                break
            ctx = Contexte(air, amb, t, dt)
            if turb is not None:
                p_disp = (det.p_sortie_pour(res.p_abs_pa) if det is not None
                          else res.p_abs_pa)
                m_dot = turb.preparer(p_disp)
                if m_dot <= 0:
                    arret = "débit nul (pression insuffisante)"
                    break
            etat = res.etat_sortie(m_dot)
            ligne: dict[str, float] = {}
            dh_det = 0.0
            T_avant = etat.T_K
            pending: list[tuple[str, float]] = []
            P_el = P_mec = P_pol = Q_rech = Q_res_turb = 0.0
            try:
                for k, el in enumerate(de.elements[1:], 1):
                    if el.type_ == "detente":
                        etat, flux = el.composant.pas(  # type: ignore
                            etat, ctx)
                        dh_det = flux.resultat.dh
                        ligne["T_sortie_detendeur_K"] = etat.T_K
                        ligne["p_sortie_detendeur_pa"] = etat.p_abs_pa
                        ligne["T_rosee_detendeur_K"] = flux.T_rosee_K
                        ligne["givre_detendeur_kg_s"] = (
                            max(flux.eau_condensee_kg_s, 0.0) if flux.givre
                            else 0.0)
                        givre_detendeur += ligne["givre_detendeur_kg_s"] * dt
                        T_avant = etat.T_K
                    elif el.type_ == "stockage_chaleur":
                        st: StockageChaleur = el.composant  # type: ignore
                        etat, flux = st.rechauffer(etat, ctx, de.cibles[k])
                        if flux.Q_ajoute_w > 0:
                            pending.append((flux.source,
                                            flux.Q_ajoute_w / m_dot))
                    elif el.type_ == "turbine":
                        i = el.etage or 0
                        maillon = el.composant.etage(i)  # type: ignore
                        etat, flux = maillon.pas(etat, ctx)
                        r = flux.resultat
                        q = sum(qq for _, qq in pending)
                        for src, qq in pending:
                            chaleur_par_source[src] = (
                                chaleur_par_source.get(src, 0.0)
                                + m_dot * qq * dt)
                            if (src != "externe"
                                    or i not in sources_etages):
                                sources_etages[i] = src
                        Q_etage[i - 1] += m_dot * q * dt
                        ligne[f"T_avant_rech_{i}_K"] = T_avant
                        ligne[f"T_in_turb_{i}_K"] = r.T_in_K
                        ligne[f"T_out_turb_{i}_K"] = r.T_out_K
                        ligne[f"p_in_turb_{i}_pa"] = r.p_in_pa
                        ligne[f"p_out_turb_{i}_pa"] = r.p_out_pa
                        ligne[f"Q_rech_{i}_w"] = m_dot * q
                        ligne[f"P_mec_{i}_w"] = m_dot * r.w_mec
                        ligne[f"P_el_{i}_w"] = m_dot * r.w_el
                        ligne[f"T_rosee_sortie_{i}_K"] = flux.T_rosee_K
                        ligne[f"givre_{i}_kg_s"] = (
                            max(flux.eau_condensee_kg_s, 0.0) if flux.givre
                            else 0.0)
                        givre_etage[i - 1] += ligne[f"givre_{i}_kg_s"] * dt
                        P_el += m_dot * r.w_el
                        P_mec += m_dot * r.w_mec
                        P_pol += m_dot * r.w_pol
                        Q_rech += m_dot * q
                        Q_res_turb += m_dot * r.q_residuel
                        pending = []
                        T_avant = etat.T_K
            except HorsDomaine as err:
                (turb if turb is not None else res).avertir(
                    str(err))
                arret = ("air hors du domaine du modèle (voir "
                         "les avertissements)")
                break
            h_rejet = air.h(etat.p_abs_pa, etat.T_K)
            T_rejet = etat.T_K
            eau_sortie += etat.w_total_kg_kg * m_dot * dt
            T_rejet_min = min(T_rejet_min, T_rejet)
            flux_res = res.vider(ctx, m_dot)
            t += dt
            cumul["E_el"] += P_el * dt
            cumul["E_mec"] += P_mec * dt
            cumul["E_pol"] += P_pol * dt
            cumul["Q_rech"] += Q_rech * dt
            cumul["E_sortie_res"] += m_dot * flux_res["h_sortie_j_kg"] * dt
            cumul["Q_paroi"] += flux_res["q_perte_w"] * dt
            cumul["Q_ext"] += flux_res["q_ext_w"] * dt
            cumul["E_detendeur"] += m_dot * dh_det * dt
            cumul["E_air_rejete"] += m_dot * h_rejet * dt
            cumul["Q_turbine_res"] += Q_res_turb * dt
            cumul["m_out"] += m_dot * dt
            m_dot_total += m_dot * dt
            ligne.update({
                "t_s": t - t0_s,
                "p_res_pa": res.p_abs_pa,
                "T_res_K": res.T_K,
                "T_paroi_K": res.T_paroi_K,
                "m_res_kg": res.masse_kg,
                "m_dot_kg_s": m_dot,
                "P_el_w": P_el,
                "P_mec_w": P_mec,
                "Q_rech_w": Q_rech,
                "Q_paroi_res_w": flux_res["q_perte_w"],
                "E_el_j": cumul["E_el"],
                "T_rejet_K": T_rejet,
                "T_amb_K": ctx.T_amb_K,
                "w_sortie_res_kg_kg": res.w_vapeur_kg_kg,
                "w_rejet_kg_kg": etat.w_total_kg_kg,
                "T_rosee_rejet_K": point_de_rosee(etat.p_abs_pa,
                                                  etat.w_total_kg_kg),
            })
            ligne.setdefault("T_sortie_detendeur_K", ligne.get(
                "T_avant_rech_1_K", T_rejet))
            ligne.setdefault("p_sortie_detendeur_pa", res.p_abs_pa)
            lignes.append(ligne)

        series = pd.DataFrame(lignes)
        dU = res.energie_interne_j - U0
        residu_res = dU + cumul["E_sortie_res"] + cumul["Q_paroi"]
        gauche = cumul["E_sortie_res"] + cumul["Q_rech"] + cumul["E_detendeur"]
        droite = (cumul["E_air_rejete"] + cumul["E_mec"]
                  + cumul["Q_turbine_res"])
        ref = max(abs(gauche), 1.0)
        bilan = {
            "dU_reservoir_j": dU,
            "E_sortie_reservoir_j": cumul["E_sortie_res"],
            "Q_paroi_reservoir_j": cumul["Q_paroi"],
            "Q_paroi_vers_ambiant_j": cumul["Q_ext"],
            "residu_reservoir_j": residu_res,
            "Q_rechauffage_j": cumul["Q_rech"],
            "E_detendeur_j": cumul["E_detendeur"],
            "E_air_rejete_j": cumul["E_air_rejete"],
            "E_mecanique_j": cumul["E_mec"],
            "E_polytropique_j": cumul["E_pol"],
            "Q_turbine_residuel_j": cumul["Q_turbine_res"],
            "pertes_electriques_j": cumul["E_mec"] - cumul["E_el"],
            "E_electrique_j": cumul["E_el"],
            "residu_relatif": (gauche - droite) / ref,
            "masse_sortie_kg": cumul["m_out"],
            "masse_soutiree_kg": m0 - res.masse_kg,
        }
        duree = t - t0_s
        totaux = {
            "duree_s": duree,
            "duree_min": duree / 60.0,
            "energie_electrique_kwh": cumul["E_el"] * WH_PAR_J,
            "energie_mecanique_kwh": cumul["E_mec"] * WH_PAR_J,
            "puissance_electrique_moyenne_kw": (
                cumul["E_el"] / duree / 1e3 if duree else 0.0),
            "chaleur_rechauffage_kwh": cumul["Q_rech"] * WH_PAR_J,
            "masse_initiale_kg": m0,
            "masse_soutiree_kg": m0 - res.masse_kg,
            "masse_morte_kg": res.masse_kg,
            "p_finale_bar": res.p_abs_pa / 1e5,
            "T_finale_degC": res.T_K - 273.15,
            "T_paroi_finale_degC": res.T_paroi_K - 273.15,
            "T_paroi_initiale_degC": Tp0 - 273.15,
            "T_rejet_min_degC": T_rejet_min - 273.15,
            "debit_kg_s": m_dot_total / duree if duree else m_dot,
            "p_initiale_bar": p_init / 1e5,
            "T_initiale_degC": T_init - 273.15,
        }
        if len(series):
            totaux["T_sortie_detendeur_moyenne_degC"] = (
                series["T_sortie_detendeur_K"].mean() - 273.15)
            totaux["T_sortie_detendeur_finale_degC"] = (
                series["T_sortie_detendeur_K"].iloc[-1] - 273.15)
        totaux["eau_sortie_kg"] = eau_sortie
        totaux["givre_detendeur_kg"] = givre_detendeur
        totaux["givre_total_kg"] = float(givre_etage.sum()) + givre_detendeur
        totaux["eau_condensee_reservoir_kg"] = res.eau_liquide_kg
        for i in range(nb):
            totaux[f"chaleur_rechauffage_{i + 1}_kwh"] = (
                Q_etage[i] * WH_PAR_J)
            totaux[f"givre_{i + 1}_kg"] = float(givre_etage[i])
        resultat = ResultatDecharge(
            scenario=self.scenario, series=series, totaux=totaux,
            bilan=bilan,
            chaleur_par_source={k: v * WH_PAR_J
                                for k, v in chaleur_par_source.items()},
            arret=arret,
            parametres={
                "T0_K": amb.T_amb_K, "p0_pa": amb.p_amb_pa,
                "volume_m3": res.volume_m3,
                "p_initiale_pa": p_init, "T_initiale_K": T_init,
            },
        )
        resultat.reservoir = res.modele_phys  # type: ignore[attr-defined]
        resultat.sources_etages = sources_etages  # type: ignore
        return resultat

    def attendre(self, t0_s: float) -> tuple[dict[str, float], float]:
        """Attente entre charge et décharge ; retourne (pertes, t final)."""
        if self.attente is None:
            return {"duree_s": 0.0, "Q_perte_cuves_j": 0.0,
                    "Q_perte_reservoir_j": 0.0}, t0_s
        ctx = Contexte(self.air, self.ambiance, t0_s, 0.0)
        pertes = self.attente.executer(ctx, self.reservoir,
                                       [s for s in self.stockages
                                        if s.a_un_etat])
        return pertes, ctx.t_s

    def simuler_cycles(self) -> ResultatSimulation:
        """Charge → attente → décharge jusqu'au régime stable."""
        if self.charge is None or self.decharge is None:
            raise ErreurAssemblage(
                f"{self.nom} : le mode « cycles » exige les deux chaînes")
        air, amb = self.air, self.ambiance
        res = self.charge.reservoir
        opts = self.options
        n_max = int(opts.get("nombre_max", 6))
        tol = float(opts.get("tolerance", 0.01))
        p0 = float(opts["p_initiale"])
        T0 = amb.T_amb_K
        t = 0.0
        res.initialiser(air, p0, amb.T_amb_a(t), amb.T_amb_a(t),
                        w_kg_kg=amb.w_kg_kg)
        for st in self.stockages:
            st.initialiser(amb.T_amb_a(t))
        cuves = [s for s in self.stockages if s.physique]
        cycles: list[Cycle] = []
        E_prec: float | None = None
        converge = False
        for k in range(1, n_max + 1):
            Ex0 = {s.nom: s.exergie_j(T0) for s in self.stockages}
            Q0 = sum(s.energie_stockee_j(T0) for s in cuves)
            ch = self.simuler_charge(reprise=True, t0_s=t)
            t += ch.totaux["duree_s"]
            for i, st in self.charge.stockage_par_etage.items():
                ch.totaux[f"dEx_cuve_{i}_j"] = st.exergie_j(T0) - Ex0[st.nom]
            pertes, t = self.attendre(t)
            Ex1 = {s.nom: s.exergie_j(T0) for s in self.stockages}
            d = self.simuler_decharge(reprise=True, t0_s=t)
            t += d.totaux["duree_s"]
            for s in cuves:
                d.totaux[f"dEx_{s.nom}_j"] = s.exergie_j(T0) - Ex1[s.nom]
            Q_fin = sum(s.energie_stockee_j(T0) for s in cuves)
            cycles.append(Cycle(
                numero=k, charge=ch, decharge=d,
                attente_h=pertes["duree_s"] / 3600.0,
                chaleur_cuves_debut_kwh=Q0 * WH_PAR_J,
                chaleur_cuves_fin_kwh=Q_fin * WH_PAR_J,
                pertes_attente_kwh=pertes["Q_perte_cuves_j"] * WH_PAR_J,
            ))
            E = d.totaux["energie_electrique_kwh"]
            Q_stable = (not cuves) or abs(Q_fin - Q0) <= tol * max(Q_fin, 1.0)
            if (E_prec is not None and abs(E - E_prec) <= tol * max(E, 1e-9)
                    and Q_stable):
                converge = True
                break
            E_prec = E
        return ResultatSimulation(self, "cycles", cycles=cycles,
                                  converge=converge)


def _traverser_charge(el: ElementChaine, etat: EtatAir,
                      ctx: Contexte) -> tuple[EtatAir, Flux]:
    c = el.composant
    if el.type_ == "compresseur":
        return c.etage(el.etage).pas(etat, ctx)  # type: ignore[union-attr]
    if el.type_ == "stockage_chaleur":
        return c.charger_air(etat, ctx)  # type: ignore[union-attr]
    return c.pas(etat, ctx)  # type: ignore[union-attr]


def _fraction_perte_debit(ch: ChaineCharge) -> float:
    """Rendement volumétrique équivalent (pour le bilan d'exergie) :
    produit des fractions conservées des maillons ``perte_debit``."""
    f = 1.0
    for el in ch.elements:
        if el.type_ == "perte_debit":
            f *= el.composant.fraction_conservee  # type: ignore[attr-defined]
    return f


# ----------------------------------------------------------------------
# Construction
# ----------------------------------------------------------------------


def _element(nom: str, composants: dict[str, Composant],
             chaine: str) -> ElementChaine:
    base, _, etage = nom.partition(".")
    if base not in composants:
        raise ErreurAssemblage(
            f"chaîne {chaine} : composant « {base} » inconnu "
            f"(déclarés : {list(composants)})")
    c = composants[base]
    if etage:
        if c.TYPE not in ("compresseur", "turbine"):
            raise ErreurAssemblage(
                f"chaîne {chaine} : « {nom} » : seuls les compresseurs et "
                f"les turbines ont des étages")
        try:
            num = int(etage)
        except ValueError as err:
            raise ErreurAssemblage(
                f"chaîne {chaine} : numéro d'étage invalide « {nom} »"
            ) from err
        c.etage(num)  # type: ignore[union-attr]  # vérifie l'existence
        return ElementChaine(c, num)
    return ElementChaine(c)


def _developper(noms: list[str], composants: dict[str, Composant],
                chaine: str) -> list[ElementChaine]:
    """Résout les noms ; « compresseur » seul = tous ses étages."""
    elements: list[ElementChaine] = []
    for nom in noms:
        if not isinstance(nom, str):
            raise ErreurAssemblage(
                f"chaîne {chaine} : chaque maillon est un nom (texte)")
        el = _element(nom, composants, chaine)
        if el.etage is None and el.type_ in ("compresseur", "turbine"):
            n = el.composant.nb_etages  # type: ignore[union-attr]
            elements.extend(ElementChaine(el.composant, i + 1)
                            for i in range(n))
        else:
            elements.append(el)
    return elements


def _etat_initial(bloc: dict[str, Any] | None) -> dict[str, float] | None:
    if not bloc:
        return None
    for cle in ("p", "T"):
        if bloc.get(cle) is None:
            raise ErreurAssemblage(
                f"reservoir_initial : « {cle} » manquant (p, T, T_paroi)")
    out = {"p": float(bloc["p"]), "T": float(bloc["T"])}
    if bloc.get("T_paroi") is not None:
        out["T_paroi"] = float(bloc["T_paroi"])
    return out


def _construire_charge(bloc: dict[str, Any],
                       composants: dict[str, Composant]) -> ChaineCharge:
    noms = bloc.get("chaine")
    if not noms:
        raise ErreurAssemblage("charge.chaine manquante")
    elements = _developper(list(noms), composants, "charge")
    reservoirs = [e for e in elements if e.type_ == "reservoir_air"]
    if len(reservoirs) != 1 or elements[-1].type_ != "reservoir_air":
        raise ErreurAssemblage(
            "charge.chaine : exactement un réservoir, en dernier")
    comps = {e.composant.nom for e in elements if e.type_ == "compresseur"}
    if len(comps) != 1:
        raise ErreurAssemblage(
            "charge.chaine : exactement un compresseur (multi-étages)")
    etages = [e.etage for e in elements if e.type_ == "compresseur"]
    comp: Compresseur = next(
        e.composant for e in elements if e.type_ == "compresseur"
    )  # type: ignore[assignment]
    attendu = list(range(1, comp.nb_etages + 1))
    if etages != attendu:
        raise ErreurAssemblage(
            f"charge.chaine : les étages de {comp.nom} doivent apparaître "
            f"une fois chacun, dans l'ordre {attendu} (trouvé {etages})")
    if elements[0].type_ != "compresseur":
        raise ErreurAssemblage(
            "charge.chaine : commence par le premier étage du compresseur")
    segments: list[Segment] = []
    stockage_par_etage: dict[int, StockageChaleur] = {}
    for e in elements[:-1]:
        if e.type_ == "compresseur":
            segments.append(Segment(e.etage or 0))
            continue
        if e.type_ not in TYPES_ENTRE_ETAGES_CHARGE:
            raise ErreurAssemblage(
                f"charge.chaine : « {e.nom} » ({e.type_}) n'a pas sa place "
                f"dans une chaîne de charge")
        segments[-1].elements.append(e)
        if (e.type_ == "stockage_chaleur"
                and e.composant.a_un_etat
                and segments[-1].etage not in stockage_par_etage):
            stockage_par_etage[segments[-1].etage] = (
                e.composant)  # type: ignore[assignment]
    for c in composants.values():
        if isinstance(c, Refroidisseur) and c.nom_recuperateur:
            cible = composants.get(str(c.nom_recuperateur))
            if not isinstance(cible, StockageChaleur):
                raise ErreurAssemblage(
                    f"{c.nom} : recuperation_vers « {c.nom_recuperateur} » "
                    f"n'est pas un stockage de chaleur")
            if cible.modele != "huile_ideale":
                raise ErreurAssemblage(
                    f"{c.nom} : la récupération depuis un refroidisseur "
                    f"n'est définie que pour le modèle « huile_ideale »")
            c.recuperateur = cible
    for cle in ("p_cible", "dt"):
        if bloc.get(cle) is None:
            raise ErreurAssemblage(f"charge.{cle} manquant")
    aval = sum(float(getattr(e.composant, "perte_de_charge_pa", 0.0))
               for e in segments[-1].elements)
    return ChaineCharge(
        elements=elements, compresseur=comp,
        reservoir=reservoirs[0].composant,  # type: ignore[arg-type]
        segments=segments, stockage_par_etage=stockage_par_etage,
        p_cible_pa=float(bloc["p_cible"]), dt_s=float(bloc["dt"]),
        duree_max_s=float(bloc.get("duree_max", 48 * 3600.0)),
        etat_initial=_etat_initial(bloc.get("reservoir_initial")),
        surpression_aval_pa=aval,
    )


def _construire_decharge(bloc: dict[str, Any],
                         composants: dict[str, Composant]) -> ChaineDecharge:
    noms = bloc.get("chaine")
    if not noms:
        raise ErreurAssemblage("decharge.chaine manquante")
    elements = _developper(list(noms), composants, "decharge")
    if elements[0].type_ != "reservoir_air":
        raise ErreurAssemblage("decharge.chaine : commence par le réservoir")
    if sum(1 for e in elements if e.type_ == "reservoir_air") != 1:
        raise ErreurAssemblage("decharge.chaine : un seul réservoir")
    reservoir: ReservoirAir = elements[0].composant  # type: ignore
    detentes = [e for e in elements if e.type_ == "detente"]
    if len(detentes) > 1 or (detentes and elements[1].type_ != "detente"):
        raise ErreurAssemblage(
            "decharge.chaine : au plus un détendeur, juste après le "
            "réservoir")
    detente: Detente | None = (
        detentes[0].composant if detentes else None)  # type: ignore
    turbines = {e.composant.nom for e in elements if e.type_ == "turbine"}
    if len(turbines) > 1:
        raise ErreurAssemblage("decharge.chaine : une seule turbine")
    turbine: Turbine | None = None
    etages = [e.etage for e in elements if e.type_ == "turbine"]
    if turbines:
        turbine = next(e.composant for e in elements
                       if e.type_ == "turbine")  # type: ignore[assignment]
        attendu = list(range(1, turbine.nb_etages + 1))
        if etages != attendu:
            raise ErreurAssemblage(
                f"decharge.chaine : les étages de {turbine.nom} doivent "
                f"apparaître une fois chacun, dans l'ordre {attendu}")
    for e in elements[1:]:
        if e.type_ not in ("detente", "stockage_chaleur", "turbine"):
            raise ErreurAssemblage(
                f"decharge.chaine : « {e.nom} » ({e.type_}) n'a pas sa "
                f"place dans une chaîne de décharge")
    # cibles des réchauffeurs : la température nominale du prochain étage
    cibles: dict[int, float | None] = {}
    segments: list[Segment] = []
    en_attente: list[ElementChaine] = []
    for k, e in enumerate(elements):
        if e.type_ == "stockage_chaleur":
            en_attente.append(e)
            prochain = next((f for f in elements[k + 1:]
                             if f.type_ == "turbine"), None)
            if prochain is None:
                raise ErreurAssemblage(
                    f"decharge.chaine : « {e.nom} » n'est suivi d'aucun "
                    f"étage de turbine à réchauffer")
            cibles[k] = prochain.composant.etage(  # type: ignore
                prochain.etage).T_entree_cible_K
        elif e.type_ == "turbine":
            segments.append(Segment(e.etage or 0, en_attente))
            en_attente = []
    # pressions compatibles
    avis_liaison: list[str] = []
    if turbine is not None:
        premier = turbine.etage(1)
        if detente is None and premier.p_entree_pa is None:
            raise ErreurAssemblage(
                f"{turbine.nom} : sans détendeur, le premier étage doit "
                f"donner p_entree (ou utiliser une détente "
                f"« pression_glissante » avec p_min)")
        if (detente is not None and not detente.glissante
                and premier.p_entree_pa is not None
                and abs(detente.p_consigne_pa  # type: ignore[operator]
                        - premier.p_entree_pa) > 1.0):
            raise ErreurAssemblage(
                f"la consigne du détendeur "
                f"({detente.p_consigne_pa / 1e5:.2f} bar) "  # type: ignore
                f"doit égaler la pression d'entrée du premier étage de "
                f"turbine ({premier.p_entree_pa / 1e5:.2f} bar)")
        if (detente is not None and detente.glissante
                and not turbine.pression_entree_variable):
            avis_liaison.append(
                f"pression glissante avec une turbine à point fixe "
                f"({turbine.modele}) : l'air sera laminé à la pression "
                f"nominale de l'étage 1 ; préférer isentropique, "
                f"polytropique_rendement ou flugel")
        for i in range(1, turbine.nb_etages):
            amont, aval = turbine.etage(i), turbine.etage(i + 1)
            if aval.p_entree_pa is None or turbine.modele == "flugel":
                amont.p_sortie_liaison_pa = amont.p_sortie_pa
                continue
            if aval.p_entree_pa > amont.p_sortie_pa + 1.0:
                raise ErreurAssemblage(
                    f"{turbine.nom} : l'étage {i + 1} demande "
                    f"{aval.p_entree_pa / 1e5:.2f} bar mais l'étage {i} "
                    f"sort à {amont.p_sortie_pa / 1e5:.2f} bar")
            amont.p_sortie_liaison_pa = aval.p_entree_pa
        debit = None
    else:
        if bloc.get("debit") is None:
            raise ErreurAssemblage(
                "decharge.debit requis quand il n'y a pas de turbine "
                "(mode ventilation)")
        debit = float(bloc["debit"])
        if detente is None:
            raise ErreurAssemblage(
                "decharge.chaine : sans turbine, il faut un détendeur")
    if bloc.get("dt") is None:
        raise ErreurAssemblage("decharge.dt manquant")
    chaine = ChaineDecharge(
        elements=elements, reservoir=reservoir, detente=detente,
        turbine=turbine, segments=segments, cibles=cibles,
        debit_impose_kg_s=debit, dt_s=float(bloc["dt"]),
        duree_max_s=float(bloc.get("duree_max", 6 * 3600.0)),
        etat_initial=_etat_initial(bloc.get("reservoir_initial")),
    )
    chaine.avis = avis_liaison  # type: ignore[attr-defined]
    return chaine


def construire_installation(
    sc: Scenario, registre: Registre | None = None, air: Air | None = None,
) -> Installation:
    """Construit l'installation décrite par un scénario résolu (SI)."""
    reg = registre or Registre.charger()
    air = air or air_par_defaut()
    v = sc.valeurs
    inconnues = set(v) - CLES_SCENARIO
    if inconnues:
        raise ErreurAssemblage(
            f"{sc.nom} : clés inconnues {sorted(inconnues)} ; attendues : "
            f"{sorted(CLES_SCENARIO)} (plus nom, description)")
    dossier = sc.chemin.parent if sc.chemin else None
    ambiance = ambiance_depuis_valeurs(v.get("ambiance"), sc.provenance,
                                       dossier)
    bloc_c = v.get("composants")
    if not isinstance(bloc_c, dict) or not bloc_c:
        raise ErreurAssemblage(f"{sc.nom} : section « composants » vide")
    composants: dict[str, Composant] = {}
    for nom, params in bloc_c.items():
        if not NOM_VALIDE.match(nom):
            raise ErreurAssemblage(
                f"nom de composant invalide « {nom} » (lettres, chiffres, "
                f"soulignés ; pas de point)")
        if not isinstance(params, dict) or "type" not in params:
            raise ErreurAssemblage(f"composant « {nom} » : « type » manquant")
        type_ = str(params["type"])
        if type_ not in FABRIQUES:
            raise ErreurAssemblage(
                f"composant « {nom} » : type « {type_} » inconnu ; choix : "
                f"{sorted(FABRIQUES)}")
        prov = {k[len(f"composants.{nom}."):]: p
                for k, p in sc.provenance.items()
                if k.startswith(f"composants.{nom}.")}
        cls = FABRIQUES[type_]
        if cls is StockageChaleur:
            composants[nom] = StockageChaleur(nom, params, prov, registre=reg)
        else:
            composants[nom] = cls(nom, params, prov)
    sim = v.get("simulation") or {}
    mode = str(sim.get("mode", "cycles"))
    if mode not in MODES:
        raise ErreurAssemblage(
            f"simulation.mode « {mode} » inconnu ; choix : {MODES}")
    charge = decharge = None
    if v.get("charge") is not None:
        charge = _construire_charge(v["charge"], composants)
    if v.get("decharge") is not None:
        decharge = _construire_decharge(v["decharge"], composants)
    if mode == "charge" and charge is None:
        raise ErreurAssemblage("mode « charge » : section charge manquante")
    if mode == "decharge" and decharge is None:
        raise ErreurAssemblage(
            "mode « decharge » : section decharge manquante")
    attente = None
    if mode == "cycles":
        if charge is None or decharge is None:
            raise ErreurAssemblage(
                "mode « cycles » : sections charge et decharge requises")
        if charge.reservoir is not decharge.reservoir:
            raise ErreurAssemblage(
                "mode « cycles » : la charge et la décharge doivent "
                "utiliser le même réservoir")
        if sim.get("p_initiale") is None:
            raise ErreurAssemblage(
                "mode « cycles » : simulation.p_initiale manquante")
        nom_att = sim.get("attente")
        if nom_att is not None:
            att = composants.get(str(nom_att))
            if not isinstance(att, Attente):
                raise ErreurAssemblage(
                    f"simulation.attente « {nom_att} » n'est pas un "
                    f"composant de type attente")
            attente = att
        # cuves présentes en décharge mais jamais chargées
        charges = {e.composant.nom for e in charge.elements}
        for e in decharge.elements:
            if (e.type_ == "stockage_chaleur"
                    and e.composant.modele == "gravier"
                    and e.composant.nom not in charges):
                raise ErreurAssemblage(
                    f"{e.composant.nom} : cuve de gravier présente en "
                    f"décharge mais absente de la chaîne de charge")
    inst = Installation(
        nom=sc.nom, description=sc.description, scenario=sc,
        ambiance=ambiance, air=air, registre=reg, composants=composants,
        mode=mode, charge=charge, decharge=decharge, attente=attente,
        options=dict(sim),
    )
    inst.avis_statiques = inst.avis_assemblage
    for texte in getattr(decharge, "avis", []):
        inst.avis_assemblage.append(Avertissement("decharge", texte))
    if charge is not None and charge.compresseur.modele == (
            "polytropique_dormoy"):
        if any(getattr(e.composant, "perte_de_charge_pa", 0.0) > 0
               for e in charge.elements):
            inst.avis_assemblage.append(Avertissement(
                "charge", "pertes de charge entre les étages avec le "
                "compresseur de Dormoy : ses rapports fixes ne les "
                "compensent pas, la pression finale sera plus basse"))
    if mode == "cycles" and decharge is not None and decharge.detente:
        p0 = float(sim["p_initiale"])
        if abs(p0 - decharge.detente.p_arret_pa) > 0.5e5:
            inst.avis_assemblage.append(Avertissement(
                "simulation",
                f"p_initiale ({p0 / 1e5:.0f} bar) diffère de la pression "
                f"d'arrêt du détendeur "
                f"({decharge.detente.p_arret_pa / 1e5:.0f} bar) : le "
                f"premier cycle part d'un autre état que les suivants"))
    return inst


def appliquer_modifications(sc: Scenario,
                            modifications: list[str]) -> Scenario:
    """Applique des remplacements « chemin=valeur[unite] » (ligne de
    commande), par exemple ``ambiance.T_amb=-20degC``."""
    if not modifications:
        return sc
    changements: dict[str, Any] = {}
    for texte in modifications:
        if "=" not in texte:
            raise ErreurAssemblage(
                f"modification « {texte} » : attendu chemin=valeur[unite]")
        chemin, brut = texte.split("=", 1)
        m = re.match(r"^\s*([-+]?[0-9.]+(?:[eE][-+]?\d+)?)\s*([^\s]*)\s*$",
                     brut)
        if m is None:
            valeur: Any = brut.strip()
            if valeur in ("true", "false"):
                valeur = valeur == "true"
        else:
            nombre, unite = float(m.group(1)), m.group(2)
            if unite:
                if unite not in UNITES:
                    raise ErreurAssemblage(
                        f"modification « {texte} » : unité inconnue "
                        f"« {unite} »")
                facteur, decalage = UNITES[unite][1:]
                valeur = nombre * facteur + decalage
            else:
                valeur = nombre
        changements[chemin.strip()] = valeur
    return sc.avec(changements, "modifie")


def charger_installation(
    chemin: Path | str | Scenario,
    registre: Registre | None = None,
    air: Air | None = None,
    modifications: list[str] | None = None,
) -> Installation:
    """Lit un scénario YAML (format phase 6) et assemble l'installation."""
    reg = registre or Registre.charger()
    sc = (chemin if isinstance(chemin, Scenario)
          else charger_scenario(chemin, reg))
    sc = appliquer_modifications(sc, modifications or [])
    return construire_installation(sc, reg, air)


def simuler(chemin: Path | str | Scenario, registre: Registre | None = None,
            modifications: list[str] | None = None) -> ResultatSimulation:
    """Raccourci : charge le scénario, vérifie et simule."""
    return charger_installation(chemin, registre,
                                modifications=modifications).simuler()
