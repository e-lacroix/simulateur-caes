"""Exergie : où se perd l'énergie **utile**.

L'exergie d'une quantité d'air est le travail maximal qu'on peut en
tirer en la ramenant à l'état ambiant (T0, p0), appelé état mort.
Contrairement à l'énergie, elle se **détruit** à chaque irréversibilité
(frottement, laminage, échange de chaleur avec écart de température),
ce qui permet de dire, composant par composant, où l'énergie utile
disparaît. Voir formules.md#F21 à #F24.

Deux fonctions principales reconstruisent le bilan d'exergie d'une
simulation de charge ou de décharge à partir de ses séries
temporelles, en calculant chaque destruction par un bilan d'entropie
(D = T0 · S_générée). La fermeture du bilan global est alors une
vérification numérique réelle, pas une tautologie.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from caes.proprietes import Air, air_par_defaut
from caes.systeme import ResultatCharge, ResultatDecharge


def temperature_log_moyenne(T1_K: float, T2_K: float) -> float:
    """Température logarithmique moyenne entre T1 et T2 [K]."""
    if abs(T2_K - T1_K) < 1e-9:
        return T1_K
    return (T2_K - T1_K) / math.log(T2_K / T1_K)


class Exergie:
    """Fonctions d'exergie pour un état mort (T0, p0) donné."""

    def __init__(self, air: Air, T0_K: float, p0_pa: float) -> None:
        self.air = air
        self.T0 = T0_K
        self.p0 = p0_pa
        self.h0 = air.h(p0_pa, T0_K)
        self.s0 = air.s(p0_pa, T0_K)
        rho0 = air.rho(p0_pa, T0_K)
        self.v0 = 1.0 / rho0
        self.u0 = air.u_de_rho_T(rho0, T0_K)

    def flux(self, p_abs_pa: float, T_K: float) -> float:
        """Exergie massique d'un écoulement [J/kg] (formules.md#F21).

        ex = (h − h0) − T0 · (s − s0)
        """
        h = self.air.h(p_abs_pa, T_K)
        s = self.air.s(p_abs_pa, T_K)
        return (h - self.h0) - self.T0 * (s - self.s0)

    def fermee_massique(self, p_abs_pa: float, T_K: float) -> float:
        """Exergie massique d'une masse enfermée [J/kg] (formules.md#F22).

        ex = (u − u0) + p0 · (v − v0) − T0 · (s − s0)
        """
        rho = self.air.rho(p_abs_pa, T_K)
        u = self.air.u_de_rho_T(rho, T_K)
        s = self.air.s(p_abs_pa, T_K)
        return (u - self.u0) + self.p0 * (1.0 / rho - self.v0) - self.T0 * (
            s - self.s0
        )

    def fermee(self, masse_kg: float, p_abs_pa: float, T_K: float) -> float:
        """Exergie d'un réservoir [J] : masse × exergie massique fermée."""
        return masse_kg * self.fermee_massique(p_abs_pa, T_K)

    def chaleur(self, Q_j: float, T_K: float) -> float:
        """Exergie d'une chaleur Q échangée à T [J] (formules.md#F23).

        Ex = Q · (1 − T0/T). Négative sous T0 (« froid »).
        """
        return Q_j * (1.0 - self.T0 / T_K)

    def air_comprime_gaz_parfait(
        self, volume_m3: float, p_abs_pa: float
    ) -> float:
        """Éq. 22 de Baniamerian (2025) : gaz parfait à T0 (formules.md#F22).

        Ex = V · p0 · (r · ln r − (r − 1)), r = p / p0.
        """
        r = p_abs_pa / self.p0
        return volume_m3 * self.p0 * (r * math.log(r) - (r - 1.0))


@dataclass
class BilanExergie:
    """Postes d'un bilan d'exergie [J], dans l'ordre du tableau.

    ``entree_j`` est l'exergie qui entre (électricité pour une charge ;
    exergie initiale des réservoirs + exergie du réchauffage pour une
    décharge). ``postes`` sont les exergies détruites ou perdues,
    ``sorties_utiles_j`` ce qui reste utile (stock, électricité).
    ``chaleurs_j`` sont des **énergies** (chaleurs échangées), données
    pour la colonne « chaleur » du tableau.
    """

    nom: str
    T0_K: float
    p0_pa: float
    entree_j: float
    postes: dict[str, float] = field(default_factory=dict)
    chaleurs_j: dict[str, float] = field(default_factory=dict)
    sorties_utiles_j: dict[str, float] = field(default_factory=dict)
    exergie_initiale_j: float = 0.0
    exergie_rechauffage_j: float = 0.0
    rechauffage_j: dict[str, float] = field(default_factory=dict)
    exergie_puisee_cuves_j: float = 0.0

    @property
    def total_postes_j(self) -> float:
        return sum(self.postes.values()) + sum(self.sorties_utiles_j.values())

    @property
    def residu_relatif(self) -> float:
        """(entrée − somme des postes) / entrée."""
        if self.entree_j == 0:
            return 0.0
        return (self.entree_j - self.total_postes_j) / self.entree_j


def _etat_initial(
    res: ResultatCharge | ResultatDecharge,
) -> tuple[float, float]:
    """État initial réel du réservoir (p, T), tel que la simulation l'a
    vu (y compris quand elle a repris un réservoir existant)."""
    return res.parametres["p_initiale_pa"], res.parametres["T_initiale_K"]


def exergie_etage_compression(
    ex: Exergie,
    p_in_pa: float,
    T_in_K: float,
    p_out_pa: float,
    T_out_K: float,
    q_poly_j_kg: float,
) -> tuple[float, float]:
    """Destruction et exergie de la chaleur rejetée, par kg (formules.md#F24).

    Bilan d'entropie de l'étage : S_gen = (s_out − s_in) − q/T_q, avec
    q < 0 la chaleur rejetée pendant la compression à la température
    logarithmique moyenne T_q. D = T0 · S_gen ; Ex_q = |q| · (1 − T0/T_q).
    Un compresseur isotherme réversible à T0 donne D = 0 et Ex_q = 0.
    """
    s_in = ex.air.s(p_in_pa, T_in_K)
    s_out = ex.air.s(p_out_pa, T_out_K)
    T_q = temperature_log_moyenne(T_in_K, T_out_K)
    S_gen = (s_out - s_in) - q_poly_j_kg / T_q
    D = ex.T0 * S_gen
    Ex_q = -q_poly_j_kg * (1.0 - ex.T0 / T_q)
    return D, Ex_q


def bilan_exergie_charge(
    res: ResultatCharge, air: Air | None = None
) -> BilanExergie:
    """Bilan d'exergie d'une charge, poste par poste [J]."""
    air = air or air_par_defaut()
    sc = res.scenario
    par = res.parametres
    T0 = par["T0_K"]
    p0 = par["p0_pa"]
    ex = Exergie(air, T0, p0)
    s = res.series
    t = s["t_s"].to_numpy()
    dt = np.diff(np.concatenate(([0.0], t)))
    nb = sum(1 for c in s.columns if c.startswith("beta_"))
    eta_vol = par["rendement_volumetrique"]

    P = {
        "moteur et mécanique": 0.0,
    }
    for i in range(1, nb + 1):
        P[f"compression étage {i} (chaleur échangée en comprimant)"] = 0.0
    for i in range(1, nb + 1):
        P[f"refroidisseur {i} (chaleur rejetée)"] = 0.0
    P["air rejeté (rendement volumétrique)"] = 0.0
    P["air rejeté (sécheur)"] = 0.0
    P["laminage vers le réservoir"] = 0.0
    P["remplissage du réservoir (mélange)"] = 0.0
    P["chaleur perdue par les parois"] = 0.0
    cuves = [
        i for i in range(1, nb + 1)
        if f"Q_cuve_{i}_w" in s.columns
        and s[f"Q_cuve_{i}_w"].abs().sum() > 0
    ]
    for i in cuves:
        P[f"cuve {i} (échange air-gravier en charge)"] = 0.0
    Q: dict[str, float] = {}
    for i in range(1, nb + 1):
        Q[f"refroidisseur {i}"] = 0.0
        Q[f"refroidisseur {i} > seuil"] = 0.0
        Q[f"compression étage {i}"] = 0.0
    for i in cuves:
        Q[f"cuve {i}"] = 0.0
    Q["parois du réservoir"] = 0.0
    Ex_vers_cuves = {i: 0.0 for i in cuves}

    S_in_res = 0.0
    S_q_res = 0.0
    E_el = 0.0
    m_asp = s["m_dot_asp_kg_s"].to_numpy()
    m_res = s["m_dot_res_kg_s"].to_numpy()
    for k in range(len(s)):
        row = s.iloc[k]
        d = dt[k]
        ma = m_asp[k] * d
        mr = m_res[k] * d
        E_el += row["P_el_w"] * d
        P["moteur et mécanique"] += (row["P_el_w"] - row["P_pol_w"]) * d
        p_ref = row["p_refoulement_pa"]
        for i in range(1, nb + 1):
            p_in = row[f"p_in_comp_{i}_pa"]
            p_out = p_in * row[f"beta_{i}"]
            T_in = row[f"T_in_comp_{i}_K"]
            T_out = row[f"T_out_comp_{i}_K"]
            T_ref = row[f"T_out_ref_{i}_K"]
            D, Exq = exergie_etage_compression(
                ex, p_in, T_in, p_out, T_out, row[f"q_poly_{i}_j_kg"]
            )
            # Le modèle polytropique est intérieurement réversible
            # (D ≈ 0) : la seule perte est l'exergie de la chaleur
            # échangée avec l'extérieur pendant la compression (négative
            # si n > γ : le modèle absorbe alors un peu de chaleur).
            P[f"compression étage {i} (chaleur échangée en comprimant)"] += (
                ma * (D + Exq)
            )
            Q[f"compression étage {i}"] += -ma * row[f"q_poly_{i}_j_kg"]
            T_in_ref = row.get(f"T_in_ref_{i}_K", T_out)
            if i in cuves:
                Ex_vers_cuves[i] += ma * (
                    ex.flux(p_out, T_out) - ex.flux(p_out, T_in_ref)
                )
                Q[f"cuve {i}"] += row[f"Q_cuve_{i}_w"] * d
            P[f"refroidisseur {i} (chaleur rejetée)"] += ma * (
                ex.flux(p_out, T_in_ref) - ex.flux(p_out, T_ref)
            )
            Q[f"refroidisseur {i}"] += row[f"Q_ref_{i}_w"] * d
            Q[f"refroidisseur {i} > seuil"] += row[f"Q_sup_seuil_{i}_w"] * d
        T_sortie = row["T_entree_res_K"]
        ex_sortie = ex.flux(p_ref, T_sortie)
        perdu = ma - mr
        vol = min(perdu, ma * (1.0 - eta_vol))
        P["air rejeté (rendement volumétrique)"] += vol * ex_sortie
        P["air rejeté (sécheur)"] += (perdu - vol) * ex_sortie
        p_res = row["p_res_pa"]
        T_lam = air.T_de_p_h(p_res, air.h(p_ref, T_sortie))
        P["laminage vers le réservoir"] += mr * (
            ex_sortie - ex.flux(p_res, T_lam)
        )
        S_in_res += mr * air.s(p_res, T_lam)
        T_res = row["T_res_K"]
        q = row["Q_paroi_res_w"] * d
        S_q_res += q / T_res
        P["chaleur perdue par les parois"] += ex.chaleur(q, T_res)
        Q["parois du réservoir"] += q

    V = par["volume_m3"]
    p_i, T_i = _etat_initial(res)
    m_i = air.rho(p_i, T_i) * V
    fin = s.iloc[-1]
    m_f, p_f, T_f = fin["m_res_kg"], fin["p_res_pa"], fin["T_res_K"]
    dS_res = m_f * air.s(p_f, T_f) - m_i * air.s(p_i, T_i)
    S_gen_res = dS_res - S_in_res + S_q_res
    P["remplissage du réservoir (mélange)"] = T0 * S_gen_res
    stock = ex.fermee(m_f, p_f, T_f) - ex.fermee(m_i, p_i, T_i)
    sorties = {"exergie stockée dans les réservoirs": float(stock)}
    for i in cuves:
        dEx = float(res.totaux.get(f"dEx_cuve_{i}_j", 0.0))
        sorties[f"exergie stockée dans la cuve {i}"] = dEx
        P[f"cuve {i} (échange air-gravier en charge)"] = (
            Ex_vers_cuves[i] - dEx)
    return BilanExergie(
        nom=sc.nom,
        T0_K=T0,
        p0_pa=p0,
        entree_j=float(E_el),
        postes={k: float(v) for k, v in P.items()},
        chaleurs_j={k: float(v) for k, v in Q.items()},
        sorties_utiles_j=sorties,
        exergie_initiale_j=float(ex.fermee(m_i, p_i, T_i)),
    )


def bilan_exergie_decharge(
    res: ResultatDecharge, air: Air | None = None
) -> BilanExergie:
    """Bilan d'exergie d'une décharge, poste par poste [J].

    L'entrée est l'exergie initiale des réservoirs plus l'exergie
    apportée par le réchauffage (comptée comme le gain d'exergie de
    l'air, soit le minimum qu'une source doit fournir).
    """
    air = air or air_par_defaut()
    sc = res.scenario
    par = res.parametres
    T0 = par["T0_K"]
    p0 = par["p0_pa"]
    ex = Exergie(air, T0, p0)
    s = res.series
    t = s["t_s"].to_numpy()
    dt = np.diff(np.concatenate(([0.0], t)))
    nb = sum(1 for c in s.columns if c.startswith("T_in_turb_"))
    turbine = nb > 0

    P: dict[str, float] = {
        "réservoir (détente interne)": 0.0,
        "chaleur reçue des parois (exergie de froid perdue)": 0.0,
        "détendeur (laminage)": 0.0,
    }
    for i in range(1, nb + 1):
        if i > 1:
            P[f"chute de pression avant l'étage {i}"] = 0.0
        P[f"turbine étage {i} (irréversibilité)"] = 0.0
        P[f"génératrice étage {i}"] = 0.0
    P["air rejeté à l'atmosphère"] = 0.0
    Q: dict[str, float] = {"parois du réservoir": 0.0}
    rech: dict[str, float] = {}
    for i in range(1, nb + 1):
        Q[f"réchauffage étage {i}"] = 0.0
        rech[f"réchauffage étage {i} (exergie apportée)"] = 0.0
    E_el = 0.0
    S_out_res = 0.0
    S_q_res = 0.0

    V = par["volume_m3"]
    p_prev, T_prev = _etat_initial(res)
    m_i = air.rho(p_prev, T_prev) * V
    for k in range(len(s)):
        row = s.iloc[k]
        d = dt[k]
        m = row["m_dot_kg_s"] * d
        E_el += row["P_el_w"] * d
        S_out_res += m * air.s(p_prev, T_prev)
        T_res = row["T_res_K"]
        q = row["Q_paroi_res_w"] * d
        S_q_res += q / T_res
        P["chaleur reçue des parois (exergie de froid perdue)"] += (
            ex.chaleur(q, T_res)
        )
        Q["parois du réservoir"] += q
        p_det = row["p_sortie_detendeur_pa"]
        T_det = row["T_sortie_detendeur_K"]
        P["détendeur (laminage)"] += m * (
            ex.flux(p_prev, T_prev) - ex.flux(p_det, T_det)
        )
        p_amont, T_amont = p_det, T_det
        if turbine:
            for i in range(1, nb + 1):
                p_in = row[f"p_in_turb_{i}_pa"]
                p_out = row[f"p_out_turb_{i}_pa"]
                T_av = row[f"T_avant_rech_{i}_K"]
                T_in = row[f"T_in_turb_{i}_K"]
                T_out = row[f"T_out_turb_{i}_K"]
                chute = m * (ex.flux(p_amont, T_amont) - ex.flux(p_in, T_av))
                if i > 1:
                    P[f"chute de pression avant l'étage {i}"] += chute
                else:
                    P["détendeur (laminage)"] += chute
                rech[f"réchauffage étage {i} (exergie apportée)"] += m * (
                    ex.flux(p_in, T_in) - ex.flux(p_in, T_av)
                )
                Q[f"réchauffage étage {i}"] += row[f"Q_rech_{i}_w"] * d
                w_mec = row[f"P_mec_{i}_w"] * d
                P[f"turbine étage {i} (irréversibilité)"] += (
                    m * (ex.flux(p_in, T_in) - ex.flux(p_out, T_out)) - w_mec
                )
                P[f"génératrice étage {i}"] += (
                    w_mec - row[f"P_el_{i}_w"] * d
                )
                p_amont, T_amont = p_out, T_out
        P["air rejeté à l'atmosphère"] += m * ex.flux(p_amont, T_amont)
        p_prev, T_prev = row["p_res_pa"], T_res

    fin = s.iloc[-1]
    m_f, p_f, T_f = fin["m_res_kg"], fin["p_res_pa"], fin["T_res_K"]
    p_i, T_i = _etat_initial(res)
    dS_res = m_f * air.s(p_f, T_f) - m_i * air.s(p_i, T_i)
    S_gen_res = dS_res + S_out_res + S_q_res
    P["réservoir (détente interne)"] = T0 * S_gen_res
    Ex_i = ex.fermee(m_i, p_i, T_i)
    Ex_f = ex.fermee(m_f, p_f, T_f)
    # Réchauffage par des cuves (phase 5) : l'entrée est l'exergie
    # puisée dans la cuve ; la différence avec le gain de l'air est
    # détruite dans l'échange gravier → air.
    sources: dict[int, str] = getattr(res, "sources_etages", {})
    rech_externe = 0.0
    puise_cuves = 0.0
    for i in range(1, nb + 1):
        gain = rech[f"réchauffage étage {i} (exergie apportée)"]
        src = sources.get(i, "")
        if src and f"dEx_{src}_j" in res.totaux:
            puise = -float(res.totaux[f"dEx_{src}_j"])
            puise_cuves += puise
            etiquette = src.replace("_", " ")
            P[f"{etiquette} (restitution gravier → air)"] = puise - gain
        else:
            rech_externe += gain
    entree = Ex_i + rech_externe + puise_cuves
    sorties = {"électricité produite": float(E_el),
               "exergie restant dans les réservoirs (coussin)": float(Ex_f)}
    return BilanExergie(
        nom=sc.nom, T0_K=T0, p0_pa=p0, entree_j=float(entree),
        postes={k: float(v) for k, v in P.items()},
        chaleurs_j={k: float(v) for k, v in Q.items()},
        sorties_utiles_j=sorties,
        exergie_initiale_j=float(Ex_i),
        exergie_rechauffage_j=float(rech_externe),
        rechauffage_j={k: float(v) for k, v in rech.items()},
        exergie_puisee_cuves_j=float(puise_cuves),
    )
