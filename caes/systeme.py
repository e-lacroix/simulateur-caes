"""Assemblage du système et simulation de la charge.

``simuler_charge`` enchaîne, à chaque pas de temps : aspiration →
(compression → refroidissement) × 4 → sécheur → laminage → réservoir,
jusqu'à la pression cible. Approche quasi stationnaire : la chaîne de
compression est en régime permanent à chaque pas, seul le réservoir a
une dynamique (comme chez Dormoy, 2024).

Le bilan d'énergie complet est accumulé pour être testé
(formules.md#F13).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

import numpy as np
import pandas as pd

from caes.compresseur import Compresseur, ResultatEtage, comprimer_etage
from caes.detendeur import CoefficientsCheayb, Detendeur
from caes.proprietes import Air, air_par_defaut
from caes.refroidisseur import Refroidisseur, ResultatRefroidisseur
from caes.registre import Registre
from caes.reservoir import Reservoir
from caes.scenario import Scenario, charger_scenario
from caes.secheur import Secheur
from caes.turbine import EtageTurbine, Turbine


@dataclass(frozen=True)
class EtatChaine:
    """Résultat stationnaire de la chaîne de compression à un instant."""

    p_refoulement_pa: float
    rapports: tuple[float, ...]
    etages: tuple[ResultatEtage, ...]
    refroidisseurs: tuple[ResultatRefroidisseur, ...]
    w_pol_total: float
    """Travail polytropique massique total [J/kg]."""
    q_poly_rejete: float
    """Chaleur rejetée pendant les compressions [J/kg], >= 0."""
    q_refroidisseurs: float
    """Chaleur retirée par les refroidisseurs [J/kg]."""
    q_refroidisseurs_sup_seuil: float
    T_sortie_K: float
    h_sortie_j_kg: float
    rendement_mecanique: float
    T_entree_refroidisseurs_K: tuple[float, ...] = ()
    """Température à l'entrée de chaque refroidisseur (après cuve)."""


class CouplageCharge(Protocol):
    """Crochets pour brancher des cuves de chaleur sur la charge.

    ``apres_etage`` est appelé après chaque étage de compression, avant
    le refroidisseur ; il reçoit l'indice (0 = étage 1), la pression et
    la température de sortie de l'étage, et renvoie la température à
    l'entrée du refroidisseur. ``fin_de_pas`` reçoit la chaîne du pas,
    pour les comptes (chaleur stockée, chaleur au-dessus du seuil).
    """

    def preparer(self, m_dot: float, dt: float) -> None: ...

    def apres_etage(self, i: int, p_pa: float, T_K: float) -> float: ...

    def fin_de_pas(self, chaine: "EtatChaine", m_dot: float,
                   dt: float) -> dict[str, float]: ...


def construire_compresseur(sc: Scenario) -> Compresseur:
    c = sc["compresseur"]
    etages = c["etages"]
    indices = tuple(float(e["indice_polytropique"]) for e in etages)
    fixes = tuple(
        float(e["rapport_pression"])
        for e in etages
        if e.get("rapport_pression") is not None
    )
    avant_dernier = etages[-2]
    return Compresseur(
        indices_polytropiques=indices,
        rapports_fixes=fixes,
        rapport_avant_dernier_min=avant_dernier["rapport_pression_min"],
        rapport_avant_dernier_max=avant_dernier["rapport_pression_max"],
        p_refoulement_min_pa=c["pression_refoulement_min"],
        p_refoulement_max_pa=sc["simulation.p_cible"],
        rendement_mecanique_min=c["rendement_mecanique_min"],
        rendement_mecanique_max=c["rendement_mecanique_max"],
        rendement_electrique=c["rendement_electrique"],
        debit_volumique_aspire_m3_s=c["debit_volumique_aspire"],
        rendement_volumetrique=c["rendement_volumetrique"],
        debit_massique_aspire_impose_kg_s=c.get("debit_massique_aspire"),
    )


def construire_refroidisseurs(sc: Scenario) -> list[Refroidisseur]:
    r = sc["refroidisseurs"]
    liste = [Refroidisseur(efficacite=float(e)) for e in r["efficacites"]]
    liste.append(
        Refroidisseur(
            efficacite=r["efficacite_dernier_min"],
            efficacite_max=r["efficacite_dernier_max"],
            p_min_pa=sc["compresseur.pression_refoulement_min"],
            p_max_pa=sc["simulation.p_cible"],
        )
    )
    return liste


def construire_reservoir(sc: Scenario) -> Reservoir:
    r = sc["reservoir"]
    return Reservoir(
        volume_m3=r["volume"],
        surface_m2=r["surface"],
        modele_thermique=r.get("modele_thermique", "K_global"),
        K_global_w_m2k=r.get("K_global", 0.0),
        h_int_w_m2k=r.get("h_int", 0.0),
        h_ext_w_m2k=r.get("h_ext", 0.0),
        capacite_paroi_j_k=r.get("capacite_thermique_paroi", 0.0),
    )


def chaine_compression(
    air: Air,
    compresseur: Compresseur,
    refroidisseurs: list[Refroidisseur],
    p_aspiration_pa: float,
    T_aspiration_K: float,
    T_froid_K: float,
    p_refoulement_pa: float,
    T_seuil_K: float,
    apres_etage: Callable[[int, float, float], float] | None = None,
) -> EtatChaine:
    """Chaîne compression / refroidissement en régime permanent.

    ``apres_etage(i, p, T)`` permet d'intercaler une cuve de chaleur
    entre l'étage i et son refroidisseur (phase 5).
    """
    rapports = compresseur.rapports_pression(p_aspiration_pa, p_refoulement_pa)
    p, T = p_aspiration_pa, T_aspiration_K
    etages: list[ResultatEtage] = []
    refs: list[ResultatRefroidisseur] = []
    T_entrees_ref: list[float] = []
    w_tot = q_poly = q_ref = q_sup = 0.0
    for i, (beta, n, refroidisseur) in enumerate(zip(
        rapports, compresseur.indices_polytropiques, refroidisseurs
    )):
        et = comprimer_etage(air, p, T, beta, n)
        etages.append(et)
        w_tot += et.w_pol
        q_poly += -et.q_poly
        T_ref_in = et.T_out_K
        if apres_etage is not None:
            T_ref_in = apres_etage(i, et.p_out_pa, et.T_out_K)
        T_entrees_ref.append(T_ref_in)
        rf = refroidisseur.refroidir(
            air, et.p_out_pa, T_ref_in, T_froid_K, T_seuil_K,
            p_refoulement_pa,
        )
        refs.append(rf)
        q_ref += rf.q
        q_sup += rf.q_sup_seuil
        p, T = et.p_out_pa, rf.T_out_K
    return EtatChaine(
        p_refoulement_pa=p_refoulement_pa,
        rapports=rapports,
        etages=tuple(etages),
        refroidisseurs=tuple(refs),
        w_pol_total=w_tot,
        q_poly_rejete=q_poly,
        q_refroidisseurs=q_ref,
        q_refroidisseurs_sup_seuil=q_sup,
        T_sortie_K=T,
        h_sortie_j_kg=air.h(p, T),
        rendement_mecanique=compresseur.rendement_mecanique(p_refoulement_pa),
        T_entree_refroidisseurs_K=tuple(T_entrees_ref),
    )


@dataclass
class ResultatCharge:
    """Séries temporelles et totaux d'une simulation de charge."""

    scenario: Scenario
    series: pd.DataFrame
    totaux: dict[str, float]
    bilan: dict[str, float]
    arret: str
    parametres: dict[str, float] = field(default_factory=dict)
    """Grandeurs de référence du bilan d'exergie (état mort, volume,
    état initial), indépendantes du format du scénario."""

    def resume(self) -> str:
        t = self.totaux
        return (
            f"{self.scenario.nom} : {t['duree_h']:.2f} h, "
            f"{t['energie_electrique_kwh']:.1f} kWh, "
            f"{t['puissance_moyenne_kw']:.1f} kW, "
            f"T finale {t['T_finale_degC']:.1f} °C, "
            f"résidu du bilan {self.bilan['residu_relatif'] * 100:.3f} %"
        )


def simuler_charge(
    scenario: Scenario | Path | str,
    registre: Registre | None = None,
    air: Air | None = None,
    couplage: CouplageCharge | None = None,
    reservoir_initial: Reservoir | None = None,
) -> ResultatCharge:
    """Simule la charge décrite par le scénario jusqu'à la pression cible.

    Le pas de temps vient de ``simulation.dt`` (1 s chez Dormoy ; 10 s
    suffisent, voir les tests de convergence). ``couplage`` branche des
    cuves de chaleur (phase 5) ; ``reservoir_initial`` permet de
    repartir de l'état laissé par une décharge (cycles).
    """
    sc = (
        scenario
        if isinstance(scenario, Scenario)
        else charger_scenario(scenario, registre)
    )
    air = air or air_par_defaut()
    compresseur = construire_compresseur(sc)
    refroidisseurs = construire_refroidisseurs(sc)
    secheur = Secheur(efficacite=sc["secheur.efficacite"])
    reservoir = construire_reservoir(sc)

    T_amb = sc["ambiance.T_amb"]
    p_amb = sc["ambiance.p_amb"]
    T_asp = sc.get("ambiance.T_aspiration", T_amb)
    T_seuil = sc["refroidisseurs.T_seuil_chaleur_utile"]
    p_cible = sc["simulation.p_cible"]
    dt = sc["simulation.dt"]
    t_max = sc.get("simulation.duree_max", 48 * 3600.0)
    debit_res_impose = sc.get("secheur.debit_massique_reservoir_impose")

    if reservoir_initial is not None:
        reservoir = reservoir_initial
    else:
        reservoir.initialiser(
            air, sc["reservoir.p_initiale"], sc["reservoir.T_initiale"],
            sc.get("reservoir.T_paroi_initiale"),
        )
    p_init, T_init = reservoir.p_abs_pa, reservoir.T_K
    h_amb = air.h(p_amb, T_asp)
    m_dot_asp = compresseur.debit_massique_aspire(air, p_amb, T_asp)
    if debit_res_impose is not None:
        m_dot_res = float(debit_res_impose)
    else:
        m_dot_res = secheur.debit_sortie(
            m_dot_asp * compresseur.rendement_volumetrique
        )
    m_dot_perdu = m_dot_asp - m_dot_res

    cache: dict[int, EtatChaine] = {}
    lignes: list[dict[str, float]] = []
    cumul = {
        "E_el": 0.0, "E_pol": 0.0, "Q_poly": 0.0, "Q_ref": 0.0,
        "Q_sup": 0.0, "E_air_perdu": 0.0, "Q_paroi": 0.0, "Q_ext": 0.0,
        "m_in": 0.0, "Q_cuves": 0.0,
    }
    nb = len(refroidisseurs)
    Q_ref_etage = np.zeros(nb)
    Q_sup_etage = np.zeros(nb)
    Q_cuve_etage = np.zeros(nb)
    U0 = reservoir.energie_interne_j
    m0 = reservoir.masse_kg
    t = 0.0
    arret = "pression cible atteinte"
    extra: dict[str, float] = {}
    while reservoir.p_abs_pa < p_cible:
        if t >= t_max:
            arret = "durée maximale atteinte"
            break
        p_ref = compresseur.p_refoulement(reservoir.p_abs_pa)
        cle = int(round(p_ref / 1.0e4))  # cache au 0,1 bar près
        if couplage is None:
            ch = cache.get(cle)
            if ch is None:
                ch = chaine_compression(
                    air, compresseur, refroidisseurs, p_amb, T_asp, T_amb,
                    cle * 1.0e4, T_seuil,
                )
                cache[cle] = ch
        else:
            couplage.preparer(m_dot_asp, dt)
            ch = chaine_compression(
                air, compresseur, refroidisseurs, p_amb, T_asp, T_amb,
                cle * 1.0e4, T_seuil, apres_etage=couplage.apres_etage,
            )
            extra = couplage.fin_de_pas(ch, m_dot_asp, dt)
            for i in range(nb):
                Q_cuve_etage[i] += extra.get(f"Q_cuve_{i + 1}_j", 0.0)
            cumul["Q_cuves"] += extra.get("Q_cuves_j", 0.0)
        P_pol = m_dot_asp * ch.w_pol_total
        P_el = compresseur.puissance_electrique(
            m_dot_asp, ch.w_pol_total, p_ref
        )
        flux = reservoir.pas(air, dt, m_dot_res, ch.h_sortie_j_kg, T_amb)

        cumul["E_el"] += P_el * dt
        cumul["E_pol"] += P_pol * dt
        cumul["Q_poly"] += m_dot_asp * ch.q_poly_rejete * dt
        cumul["Q_ref"] += m_dot_asp * ch.q_refroidisseurs * dt
        cumul["Q_sup"] += m_dot_asp * ch.q_refroidisseurs_sup_seuil * dt
        cumul["E_air_perdu"] += m_dot_perdu * (ch.h_sortie_j_kg - h_amb) * dt
        cumul["Q_paroi"] += flux["q_perte_w"] * dt
        cumul["Q_ext"] += flux["q_ext_w"] * dt
        cumul["m_in"] += m_dot_res * dt
        for i, rf in enumerate(ch.refroidisseurs):
            Q_ref_etage[i] += m_dot_asp * rf.q * dt
            Q_sup_etage[i] += m_dot_asp * rf.q_sup_seuil * dt
        t += dt

        ligne: dict[str, float] = {
            "t_s": t,
            "p_res_pa": reservoir.p_abs_pa,
            "T_res_K": reservoir.T_K,
            "T_paroi_K": reservoir.T_paroi_K,
            "m_res_kg": reservoir.masse_kg,
            "p_refoulement_pa": p_ref,
            "P_el_w": P_el,
            "P_pol_w": P_pol,
            "E_el_j": cumul["E_el"],
            "m_dot_asp_kg_s": m_dot_asp,
            "m_dot_res_kg_s": m_dot_res,
            "rendement_mecanique": ch.rendement_mecanique,
            "Q_poly_w": m_dot_asp * ch.q_poly_rejete,
            "Q_ref_w": m_dot_asp * ch.q_refroidisseurs,
            "Q_sup_seuil_w": m_dot_asp * ch.q_refroidisseurs_sup_seuil,
            "Q_paroi_res_w": flux["q_perte_w"],
            "T_entree_res_K": ch.T_sortie_K,
        }
        for i, (et, rf) in enumerate(zip(ch.etages, ch.refroidisseurs), 1):
            ligne[f"beta_{i}"] = et.rapport_pression
            ligne[f"p_in_comp_{i}_pa"] = et.p_in_pa
            ligne[f"T_in_comp_{i}_K"] = et.T_in_K
            ligne[f"T_out_comp_{i}_K"] = et.T_out_K
            ligne[f"T_in_ref_{i}_K"] = ch.T_entree_refroidisseurs_K[i - 1]
            ligne[f"T_out_ref_{i}_K"] = rf.T_out_K
            if couplage is not None:
                ligne[f"Q_cuve_{i}_w"] = extra.get(
                    f"Q_cuve_{i}_j", 0.0) / dt
            ligne[f"Q_ref_{i}_w"] = m_dot_asp * rf.q
            ligne[f"Q_sup_seuil_{i}_w"] = m_dot_asp * rf.q_sup_seuil
            ligne[f"w_pol_{i}_j_kg"] = et.w_pol
            ligne[f"q_poly_{i}_j_kg"] = et.q_poly
            ligne[f"eps_{i}"] = rf.efficacite
        lignes.append(ligne)

    series = pd.DataFrame(lignes)
    dU = reservoir.energie_interne_j - U0
    E_stock = dU - cumul["m_in"] * h_amb
    somme = (
        (cumul["E_el"] - cumul["E_pol"])
        + cumul["Q_poly"] + cumul["Q_ref"] + cumul["E_air_perdu"]
        + cumul["Q_paroi"] + E_stock + cumul["Q_cuves"]
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
        "residu_relatif": (cumul["E_el"] - somme) / cumul["E_el"]
        if cumul["E_el"] else 0.0,
        "masse_entree_kg": cumul["m_in"],
        "masse_stockee_kg": reservoir.masse_kg - m0,
    }
    totaux = {
        "duree_s": t,
        "duree_h": t / 3600.0,
        "energie_electrique_kwh": cumul["E_el"] / 3.6e6,
        "puissance_moyenne_kw": cumul["E_el"] / t / 1e3 if t else 0.0,
        "chaleur_refroidisseurs_kwh": cumul["Q_ref"] / 3.6e6,
        "chaleur_sup_seuil_kwh": cumul["Q_sup"] / 3.6e6,
        "chaleur_poly_rejetee_kwh": cumul["Q_poly"] / 3.6e6,
        "chaleur_paroi_reservoir_kwh": cumul["Q_paroi"] / 3.6e6,
        "masse_stockee_kg": reservoir.masse_kg - m0,
        "p_finale_bar": reservoir.p_abs_pa / 1e5,
        "T_finale_degC": reservoir.T_K - 273.15,
        "debit_aspire_kg_s": m_dot_asp,
        "debit_reservoir_kg_s": m_dot_res,
        "chaleur_cuves_kwh": cumul["Q_cuves"] / 3.6e6,
        "p_initiale_bar": p_init / 1e5,
        "T_initiale_degC": T_init - 273.15,
    }
    for i in range(nb):
        totaux[f"chaleur_refroidisseur_{i + 1}_kwh"] = Q_ref_etage[i] / 3.6e6
        totaux[f"chaleur_sup_seuil_{i + 1}_kwh"] = Q_sup_etage[i] / 3.6e6
        totaux[f"chaleur_cuve_{i + 1}_kwh"] = Q_cuve_etage[i] / 3.6e6
    res = ResultatCharge(
        scenario=sc, series=series, totaux=totaux, bilan=bilan, arret=arret,
        parametres={
            "T0_K": T_amb, "p0_pa": p_amb, "T_aspiration_K": T_asp,
            "rendement_volumetrique": compresseur.rendement_volumetrique,
            "volume_m3": reservoir.volume_m3,
            "p_initiale_pa": p_init, "T_initiale_K": T_init,
        },
    )
    res.reservoir = reservoir  # type: ignore[attr-defined]
    return res


def sauvegarder_series(resultat: ResultatCharge, chemin: Path | str) -> None:
    """Écrit les séries temporelles en CSV (unités SI dans les en-têtes)."""
    resultat.series.to_csv(chemin, index=False)


def totaux_en_dataframe(
    resultats: list[ResultatCharge] | list[ResultatDecharge],
) -> pd.DataFrame:
    """Tableau comparatif des totaux de plusieurs simulations."""
    lignes: list[dict[str, Any]] = []
    for r in resultats:
        ligne: dict[str, Any] = {"scenario": r.scenario.nom}
        ligne.update(r.totaux)
        lignes.append(ligne)
    return pd.DataFrame(lignes).set_index("scenario")


# ----------------------------------------------------------------------
# Décharge
# ----------------------------------------------------------------------


def construire_detendeur(sc: Scenario) -> Detendeur:
    d = sc["detendeur"]
    coef = None
    if d.get("cheayb"):
        c = d["cheayb"]
        coef = CoefficientsCheayb(
            a1=c["a1"], a2=c["a2"], a3=c["a3"], a4=c["a4"],
            b1=c["b1"], b2=c["b2"], b3=c["b3"], b4=c["b4"],
            p_min_validite_pa=c.get("p_min_validite", 25e5),
            p_max_validite_pa=c.get("p_max_validite", 150e5),
        )
    return Detendeur(
        p_consigne_pa=d["p_consigne"],
        ecart_min_pa=d["ecart_min"],
        modele=d.get("modele", "isenthalpique"),
        cheayb=coef,
    )


def construire_turbine(sc: Scenario) -> Turbine:
    t = sc["turbine"]
    etages = tuple(
        EtageTurbine(
            p_entree_pa=e["p_entree"],
            p_sortie_pa=e["p_sortie"],
            indice_polytropique=e["indice_polytropique"],
            rendement_mecanique=e["rendement_mecanique"],
            rendement_electrique=e["rendement_electrique"],
            T_entree_cible_K=e.get("T_entree_cible"),
        )
        for e in t["etages"]
    )
    return Turbine(
        etages=etages,
        debit_massique_kg_s=t["debit_massique"],
        source_chaleur=t.get("source_chaleur", "externe"),
    )


@dataclass
class ResultatDecharge:
    """Séries temporelles et totaux d'une simulation de décharge."""

    scenario: Scenario
    series: pd.DataFrame
    totaux: dict[str, float]
    bilan: dict[str, float]
    chaleur_par_source: dict[str, float]
    arret: str
    parametres: dict[str, float] = field(default_factory=dict)

    def resume(self) -> str:
        t = self.totaux
        return (
            f"{self.scenario.nom} : {t['duree_min']:.1f} min, "
            f"{t['energie_electrique_kwh']:.2f} kWh, "
            f"chaleur {t['chaleur_rechauffage_kwh']:.1f} kWh, "
            f"p finale {t['p_finale_bar']:.1f} bar, "
            f"masse morte {t['masse_morte_kg']:.0f} kg, "
            f"résidu {self.bilan['residu_relatif'] * 100:.3f} %"
        )


class RechauffeurDecharge(Protocol):
    """Source de chaleur de réchauffage branchable sur la décharge.

    ``preparer(m_dot, dt)`` est appelé à chaque pas avant la turbine ;
    ``chauffer(i, p, T_avant, T_cible)`` renvoie (T après réchauffage,
    étiquette de la source).
    """

    def preparer(self, m_dot: float, dt: float) -> None: ...

    def chauffer(self, i: int, p_pa: float, T_avant_K: float,
                 T_cible_K: float | None) -> tuple[float, str]: ...


def simuler_decharge(
    scenario: Scenario | Path | str,
    registre: Registre | None = None,
    air: Air | None = None,
    rechauffeur: RechauffeurDecharge | None = None,
    reservoir_initial: Reservoir | None = None,
) -> ResultatDecharge:
    """Simule la décharge jusqu'à l'arrêt du détendeur.

    Deux modes (``decharge.mode``) :

    * ``ventilation`` : débit imposé, l'air est rejeté après le détendeur
      (essai mesuré de Dormoy, sans turbine) ;
    * ``turbine`` : débit nominal de la turbine, réchauffage suivi par
      source, puissance électrique (formules.md#F17 à #F20).

    ``rechauffeur`` remplace la source externe par des cuves ou une
    huile idéale (phase 5) ; ``reservoir_initial`` reprend l'état laissé
    par une charge (cycles).
    """
    sc = (
        scenario
        if isinstance(scenario, Scenario)
        else charger_scenario(scenario, registre)
    )
    air = air or air_par_defaut()
    reservoir = construire_reservoir(sc)
    detendeur = construire_detendeur(sc)
    mode = sc["decharge.mode"]
    if mode not in ("ventilation", "turbine"):
        raise ValueError(f"mode de décharge inconnu : {mode}")
    turbine = construire_turbine(sc) if mode == "turbine" else None
    if turbine is not None:
        if abs(turbine.p_entree_pa - detendeur.p_consigne_pa) > 1.0:
            raise ValueError(
                "la consigne du détendeur doit égaler la pression d'entrée "
                "de la turbine"
            )
        m_dot = turbine.debit_massique_kg_s
    else:
        m_dot = float(sc["decharge.debit_impose"])

    T_amb = sc["ambiance.T_amb"]
    dt = sc["simulation.dt"]
    t_max = sc.get("simulation.duree_max", 6 * 3600.0)
    if reservoir_initial is not None:
        reservoir = reservoir_initial
    else:
        reservoir.initialiser(
            air,
            sc["reservoir.p_initiale"],
            sc["reservoir.T_initiale"],
            sc.get("reservoir.T_paroi_initiale"),
        )
    p_init, T_init = reservoir.p_abs_pa, reservoir.T_K
    m0 = reservoir.masse_kg
    U0 = reservoir.energie_interne_j
    Tp0 = reservoir.T_paroi_K

    nb = len(turbine.etages) if turbine else 0
    Q_etage = np.zeros(nb)
    chaleur_par_source: dict[str, float] = {}
    cumul = {
        "E_el": 0.0, "E_mec": 0.0, "E_pol": 0.0, "Q_rech": 0.0,
        "E_sortie_res": 0.0, "Q_paroi": 0.0, "Q_ext": 0.0,
        "E_detendeur": 0.0, "E_air_rejete": 0.0, "Q_turbine_res": 0.0,
        "m_out": 0.0,
    }
    lignes: list[dict[str, float]] = []
    t = 0.0
    arret = "pression d'arrêt du détendeur atteinte"
    T_rejet_min = float("inf")
    while detendeur.peut_fonctionner(reservoir.p_abs_pa):
        if t >= t_max:
            arret = "durée maximale atteinte"
            break
        det = detendeur.detendre(air, reservoir.p_abs_pa, reservoir.T_K)
        ligne: dict[str, float] = {}
        if turbine is not None:
            if rechauffeur is not None:
                rechauffeur.preparer(m_dot, dt)
                etages = turbine.produire(air, det.T_out_K,
                                          rechauffeur.chauffer)
            else:
                etages = turbine.produire(air, det.T_out_K)
            P_el = turbine.puissance_electrique(etages)
            P_mec = m_dot * sum(e.w_mec for e in etages)
            P_pol = m_dot * sum(e.w_pol for e in etages)
            Q_rech = m_dot * sum(e.q_rechauffage for e in etages)
            h_rejet = air.h(etages[-1].p_out_pa, etages[-1].T_out_K)
            T_rejet = etages[-1].T_out_K
            Q_res_turb = m_dot * sum(e.q_residuel for e in etages)
            for i, e in enumerate(etages):
                Q_etage[i] += m_dot * e.q_rechauffage * dt
                if e.q_rechauffage > 0:
                    chaleur_par_source[e.source_chaleur] = (
                        chaleur_par_source.get(e.source_chaleur, 0.0)
                        + m_dot * e.q_rechauffage * dt
                    )
                ligne[f"T_avant_rech_{i + 1}_K"] = e.T_avant_rechauffage_K
                ligne[f"T_in_turb_{i + 1}_K"] = e.T_in_K
                ligne[f"T_out_turb_{i + 1}_K"] = e.T_out_K
                ligne[f"p_in_turb_{i + 1}_pa"] = e.p_in_pa
                ligne[f"p_out_turb_{i + 1}_pa"] = e.p_out_pa
                ligne[f"Q_rech_{i + 1}_w"] = m_dot * e.q_rechauffage
                ligne[f"P_mec_{i + 1}_w"] = m_dot * e.w_mec
                ligne[f"P_el_{i + 1}_w"] = m_dot * e.w_el
        else:
            P_el = P_mec = P_pol = Q_rech = Q_res_turb = 0.0
            h_rejet = det.h_out
            T_rejet = det.T_out_K
        T_rejet_min = min(T_rejet_min, T_rejet)

        flux = reservoir.pas(
            air, dt, 0.0, 0.0, T_amb, debit_sortie_kg_s=m_dot
        )
        cumul["E_el"] += P_el * dt
        cumul["E_mec"] += P_mec * dt
        cumul["E_pol"] += P_pol * dt
        cumul["Q_rech"] += Q_rech * dt
        cumul["E_sortie_res"] += m_dot * flux["h_sortie_j_kg"] * dt
        cumul["Q_paroi"] += flux["q_perte_w"] * dt
        cumul["Q_ext"] += flux["q_ext_w"] * dt
        cumul["E_detendeur"] += m_dot * det.dh * dt
        cumul["E_air_rejete"] += m_dot * h_rejet * dt
        cumul["Q_turbine_res"] += Q_res_turb * dt
        cumul["m_out"] += m_dot * dt
        t += dt
        ligne.update({
            "t_s": t,
            "p_res_pa": reservoir.p_abs_pa,
            "T_res_K": reservoir.T_K,
            "T_paroi_K": reservoir.T_paroi_K,
            "m_res_kg": reservoir.masse_kg,
            "m_dot_kg_s": m_dot,
            "T_sortie_detendeur_K": det.T_out_K,
            "p_sortie_detendeur_pa": det.p_out_pa,
            "P_el_w": P_el,
            "P_mec_w": P_mec,
            "Q_rech_w": Q_rech,
            "Q_paroi_res_w": flux["q_perte_w"],
            "E_el_j": cumul["E_el"],
            "T_rejet_K": T_rejet,
        })
        lignes.append(ligne)

    series = pd.DataFrame(lignes)
    dU = reservoir.energie_interne_j - U0
    # Réservoir : ΔU = −E_sortie − Q_paroi (formules.md#F12)
    residu_res = dU + cumul["E_sortie_res"] + cumul["Q_paroi"]
    # Chaîne : E_sortie + Q_rech + E_detendeur = E_rejet + E_mec + Q_turb
    gauche = cumul["E_sortie_res"] + cumul["Q_rech"] + cumul["E_detendeur"]
    droite = cumul["E_air_rejete"] + cumul["E_mec"] + cumul["Q_turbine_res"]
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
        "masse_soutiree_kg": m0 - reservoir.masse_kg,
    }
    totaux = {
        "duree_s": t,
        "duree_min": t / 60.0,
        "energie_electrique_kwh": cumul["E_el"] / 3.6e6,
        "energie_mecanique_kwh": cumul["E_mec"] / 3.6e6,
        "puissance_electrique_moyenne_kw": (
            cumul["E_el"] / t / 1e3 if t else 0.0
        ),
        "chaleur_rechauffage_kwh": cumul["Q_rech"] / 3.6e6,
        "masse_initiale_kg": m0,
        "masse_soutiree_kg": m0 - reservoir.masse_kg,
        "masse_morte_kg": reservoir.masse_kg,
        "p_finale_bar": reservoir.p_abs_pa / 1e5,
        "T_finale_degC": reservoir.T_K - 273.15,
        "T_paroi_finale_degC": reservoir.T_paroi_K - 273.15,
        "T_paroi_initiale_degC": Tp0 - 273.15,
        "T_rejet_min_degC": T_rejet_min - 273.15,
        "debit_kg_s": m_dot,
    }
    if len(series):
        totaux["T_sortie_detendeur_moyenne_degC"] = (
            series["T_sortie_detendeur_K"].mean() - 273.15
        )
        totaux["T_sortie_detendeur_finale_degC"] = (
            series["T_sortie_detendeur_K"].iloc[-1] - 273.15
        )
    totaux["p_initiale_bar"] = p_init / 1e5
    totaux["T_initiale_degC"] = T_init - 273.15
    for i in range(nb):
        totaux[f"chaleur_rechauffage_{i + 1}_kwh"] = Q_etage[i] / 3.6e6
    res = ResultatDecharge(
        scenario=sc,
        series=series,
        totaux=totaux,
        bilan=bilan,
        chaleur_par_source={
            k: v / 3.6e6 for k, v in chaleur_par_source.items()
        },
        arret=arret,
        parametres={
            "T0_K": T_amb, "p0_pa": sc["ambiance.p_amb"],
            "volume_m3": reservoir.volume_m3,
            "p_initiale_pa": p_init, "T_initiale_K": T_init,
        },
    )
    res.reservoir = reservoir  # type: ignore[attr-defined]
    return res


def rendements_aller_retour(
    charge: ResultatCharge, decharge: ResultatDecharge
) -> dict[str, float]:
    """Les deux définitions du rendement (formules.md#F20).

    * ``rte_sans_chaleur`` : électricité produite / électricité consommée
      (définition de Dormoy, éq. 20) ;
    * ``rte_avec_chaleur_externe`` : électricité produite / (électricité
      consommée + chaleur de source ``externe``).
    """
    E_cons = charge.totaux["energie_electrique_kwh"]
    E_prod = decharge.totaux["energie_electrique_kwh"]
    Q_ext = decharge.chaleur_par_source.get("externe", 0.0)
    return {
        "energie_consommee_kwh": E_cons,
        "energie_produite_kwh": E_prod,
        "chaleur_externe_kwh": Q_ext,
        "rte_sans_chaleur": E_prod / E_cons,
        "rte_avec_chaleur_externe": E_prod / (E_cons + Q_ext),
    }
