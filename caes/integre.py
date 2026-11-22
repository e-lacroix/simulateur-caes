"""Système intégré : banc de Dormoy + cuves de gravier (phase 5).

Cinq architectures, décrites par un scénario ``scenarios/v1/A.yaml`` à
``E.yaml`` :

* A : base Dormoy, 1 étage, sans réchauffage ;
* B : 3 étages, chaleur externe (comme Dormoy) ;
* C : 3 étages, huile idéale : la chaleur des refroidisseurs au-dessus du
  seuil est mise de côté sans perte et rendue à la turbine ;
* D : 3 étages, gravier direct : une cuve après les étages 1, 2 et 3,
  traversée par l'air comprimé, puis le refroidisseur ; cuve 3 → turbine
  1, cuve 2 → turbine 2, cuve 1 → turbine 3 ;
* E : 3 étages, gravier + boucle d'air : cuves à pression atmosphérique,
  deux échangeurs à pincement (≈ 20 K chacun).

Le cycle (charge → attente → décharge) est répété jusqu'au régime
stable. Les cuves fixent la température d'entrée des turbines : si une
cuve ne peut pas atteindre la cible, la turbine reçoit de l'air moins
chaud (pas d'appoint magique). Voir formules.md#F30 et #F31.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from caes.exergie import Exergie
from caes.lit_gravier import Correlations, LitGravier
from caes.materiaux import Materiau, charger_materiau
from caes.proprietes import Air, air_par_defaut
from caes.registre import Registre
from caes.reservoir import Reservoir
from caes.scenario import Scenario, charger_scenario
from caes.systeme import (
    EtatChaine,
    ResultatCharge,
    ResultatDecharge,
    construire_reservoir,
    simuler_charge,
    simuler_decharge,
)

ARCHITECTURES = ("A", "B", "C", "D", "E")


def exergie_cuve(lit: LitGravier, T0_K: float) -> float:
    """Exergie du gravier [J] : Σ C·[(T − T0) − T0·ln(T/T0)] (#F31)."""
    T = lit.T_s_K
    return float(lit.capacite_cellule_j_k * np.sum(
        (T - T0_K) - T0_K * np.log(T / T0_K)))


@dataclass
class ConfigCuves:
    """Réglages des cuves de gravier d'une architecture D ou E."""

    materiau: Materiau
    volumes_m3: list[float]
    rapport_hauteur_diametre: float = 2.0
    n_cellules: int = 30
    pression: str = "etage"  # ou "atmospherique"
    pincement_K: float = 0.0
    coefficient_perte_w_m2k: float = 0.0
    bypass: bool = True
    T_initiale_K: float = 293.15
    correlations: Correlations = field(default_factory=Correlations)

    def construire(self) -> list[LitGravier]:
        cuves = []
        for V in self.volumes_m3:
            rap = self.rapport_hauteur_diametre
            D = (4.0 * V / (math.pi * rap)) ** (1 / 3)
            lit = LitGravier(
                self.materiau, D, self.rapport_hauteur_diametre * D,
                n_cellules=self.n_cellules,
                coefficient_perte_w_m2k=self.coefficient_perte_w_m2k,
                correlations=self.correlations,
            )
            lit.initialiser(self.T_initiale_K)
            cuves.append(lit)
        return cuves


class CouplageCuvesCharge:
    """Cuves traversées (D) ou alimentées par une boucle d'air (E)."""

    def __init__(self, air: Air, cuves: list[LitGravier], config: ConfigCuves,
                 p_amb_pa: float, T_amb_K: float) -> None:
        self.air = air
        self.cuves = cuves
        self.config = config
        self.p_amb = p_amb_pa
        self.T_amb = T_amb_K
        self.m_dot = 0.0
        self.dt = 0.0
        self.Q_pas: list[float] = [0.0] * len(cuves)
        self.dp_pas: list[float] = [0.0] * len(cuves)

    def preparer(self, m_dot: float, dt: float) -> None:
        self.m_dot, self.dt = m_dot, dt
        self.Q_pas = [0.0] * len(self.cuves)

    def apres_etage(self, i: int, p_pa: float, T_K: float) -> float:
        if i >= len(self.cuves):
            return T_K
        pinch = self.config.pincement_K
        p_cuve = p_pa if self.config.pression == "etage" else self.p_amb
        r = self.cuves[i].pas(
            self.air, self.dt, self.m_dot, T_K - pinch, p_cuve, self.T_amb,
            sens=1,
        )
        self.Q_pas[i] = r["Q_air_vers_solide_j"]
        self.dp_pas[i] = r["dp_pa"]
        return min(T_K, r["T_sortie_K"] + pinch)

    def fin_de_pas(self, chaine: EtatChaine, m_dot: float,
                   dt: float) -> dict[str, float]:
        out = {f"Q_cuve_{i + 1}_j": q for i, q in enumerate(self.Q_pas)}
        out["Q_cuves_j"] = float(sum(self.Q_pas))
        return out


class CouplageHuileIdeale:
    """Architecture C : chaleur des refroidisseurs au-dessus du seuil mise
    de côté sans perte (hypothèse de Dormoy, § 3.3.5)."""

    def __init__(self) -> None:
        self.reserve_j = 0.0
        self.m_dot = 0.0
        self.dt = 0.0

    def preparer(self, m_dot: float, dt: float) -> None:
        self.m_dot, self.dt = m_dot, dt

    def apres_etage(self, i: int, p_pa: float, T_K: float) -> float:
        return T_K

    def fin_de_pas(self, chaine: EtatChaine, m_dot: float,
                   dt: float) -> dict[str, float]:
        self.reserve_j += m_dot * chaine.q_refroidisseurs_sup_seuil * dt
        return {"Q_cuves_j": 0.0}


class RechauffeurCuves:
    """Réchauffage des turbines par les cuves (D, E) : turbine i ← cuve
    n − i. Un bypass limite la température à la cible ; sans appoint."""

    def __init__(self, air: Air, cuves: list[LitGravier], config: ConfigCuves,
                 p_amb_pa: float, T_amb_K: float) -> None:
        self.air = air
        self.cuves = cuves
        self.config = config
        self.p_amb = p_amb_pa
        self.T_amb = T_amb_K
        self.m_dot = 0.0
        self.dt = 0.0
        self.Q_cuves_pas: list[float] = [0.0] * len(cuves)

    def preparer(self, m_dot: float, dt: float) -> None:
        self.m_dot, self.dt = m_dot, dt
        self.Q_cuves_pas = [0.0] * len(self.cuves)

    def indice_cuve(self, i_turbine: int) -> int:
        return len(self.cuves) - 1 - i_turbine

    def chauffer(self, i: int, p_pa: float, T_avant_K: float,
                 T_cible_K: float | None) -> tuple[float, str]:
        k = self.indice_cuve(i)
        if k < 0:
            return T_avant_K, ""
        cuve = self.cuves[k]
        pinch = self.config.pincement_K
        p_cuve = p_pa if self.config.pression == "etage" else self.p_amb
        T_in_cuve = T_avant_K + pinch
        T_plein = cuve.sortie_instantanee(
            self.air, self.m_dot, T_in_cuve, p_cuve, sens=-1) - pinch
        f = 0.0
        if (self.config.bypass and T_cible_K is not None
                and T_plein > T_cible_K and T_plein > T_avant_K):
            f = (T_plein - T_cible_K) / (T_plein - T_avant_K)
            f = min(max(f, 0.0), 0.999)
        m_cuve = self.m_dot * (1.0 - f)
        r = cuve.pas(self.air, self.dt, m_cuve, T_in_cuve, p_cuve,
                     self.T_amb, sens=-1)
        self.Q_cuves_pas[k] = -r["Q_air_vers_solide_j"]
        T_out = r["T_sortie_K"] - pinch
        T_mix = f * T_avant_K + (1.0 - f) * T_out
        if T_cible_K is not None:
            T_mix = min(T_mix, max(T_cible_K, T_avant_K))
        return max(T_mix, T_avant_K), f"cuve_{k + 1}"


class RechauffeurHuileIdeale:
    """Architecture C : puise dans la réserve, sinon source externe."""

    def __init__(self, air: Air, couplage: CouplageHuileIdeale) -> None:
        self.air = air
        self.couplage = couplage
        self.m_dot = 0.0
        self.dt = 0.0
        self.externe_j = 0.0

    def preparer(self, m_dot: float, dt: float) -> None:
        self.m_dot, self.dt = m_dot, dt

    def chauffer(self, i: int, p_pa: float, T_avant_K: float,
                 T_cible_K: float | None) -> tuple[float, str]:
        if T_cible_K is None or T_avant_K >= T_cible_K:
            return T_avant_K, ""
        q = self.m_dot * self.dt * (
            self.air.h(p_pa, T_cible_K) - self.air.h(p_pa, T_avant_K))
        if self.couplage.reserve_j >= q:
            self.couplage.reserve_j -= q
            return T_cible_K, "huile_ideale"
        self.externe_j += q
        return T_cible_K, "externe"


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
class ResultatIntegre:
    scenario: Scenario
    architecture: str
    cycles: list[Cycle]
    cuves: list[LitGravier] | None
    volumes_m3: list[float]
    converge: bool

    @property
    def dernier(self) -> Cycle:
        return self.cycles[-1]

    def resume(self) -> str:
        c = self.dernier
        rte = (c.decharge.totaux["energie_electrique_kwh"]
               / c.charge.totaux["energie_electrique_kwh"])
        return (
            f"{self.architecture} : cycle {c.numero}, charge "
            f"{c.charge.totaux['energie_electrique_kwh']:.1f} kWh, produit "
            f"{c.decharge.totaux['energie_electrique_kwh']:.2f} kWh, RTE "
            f"{rte * 100:.1f} %, chaleur {c.decharge.chaleur_par_source}"
        )


def _attente(reservoir: Reservoir, cuves: list[LitGravier] | None, air: Air,
             duree_s: float, T_amb_K: float, p_cuves: list[float]) -> float:
    """Attente entre charge et décharge : cuves et réservoir refroidissent."""
    if duree_s <= 0:
        return 0.0
    dt = min(600.0, duree_s)
    n = int(round(duree_s / dt))
    pertes = 0.0
    for _ in range(n):
        reservoir.pas(air, dt, 0.0, 0.0, T_amb_K)
        if cuves:
            for lit, p in zip(cuves, p_cuves):
                r = lit.pas(air, dt, 0.0, T_amb_K, p, T_amb_K)
                pertes += r["Q_perte_j"]
    return pertes


def simuler_cycles(
    scenario: Scenario | Path | str,
    registre: Registre | None = None,
    air: Air | None = None,
    volumes_m3: list[float] | None = None,
) -> ResultatIntegre:
    """Enchaîne des cycles charge → attente → décharge jusqu'au régime
    stable (variation de l'électricité produite < tolérance)."""
    reg = registre or Registre.charger()
    sc = (scenario if isinstance(scenario, Scenario)
          else charger_scenario(scenario, reg))
    air = air or air_par_defaut()
    arch = sc["architecture"]
    if arch not in ARCHITECTURES:
        raise ValueError(f"architecture inconnue : {arch}")
    p_arret = sc["pression_arret"]
    sc_ch = charger_scenario(sc["charge"], reg).avec(
        {"reservoir.p_initiale": p_arret,
         "simulation.dt": float(sc.get("cycles.dt_charge", 30.0))}, "cycle")
    sc_de = charger_scenario(sc["decharge"], reg).avec(
        {"simulation.dt": float(sc.get("cycles.dt_decharge", 5.0))}, "cycle")
    T_amb = sc_ch["ambiance.T_amb"]
    p_amb = sc_ch["ambiance.p_amb"]
    n_max = int(sc.get("cycles.nombre_max", 6))
    tol = float(sc.get("cycles.tolerance", 0.01))
    attente_s = float(sc.get("cycles.attente", 3600.0))

    # réservoir unique (modèle « paroi »), repart de la pression d'arrêt
    reservoir = construire_reservoir(sc_de)
    reservoir.initialiser(air, p_arret, T_amb, T_amb)

    cuves: list[LitGravier] | None = None
    couplage = None
    rechauffeur = None
    volumes: list[float] = []
    config: ConfigCuves | None = None
    if arch in ("D", "E"):
        c = sc["cuves"]
        volumes = list(volumes_m3) if volumes_m3 else [float(v) for v in
                                                        c["volumes"]]
        config = ConfigCuves(
            materiau=charger_materiau(c.get("materiau", "gravier_tola"), reg),
            volumes_m3=volumes,
            rapport_hauteur_diametre=float(c.get("rapport_hauteur_diametre",
                                                 2.0)),
            n_cellules=int(c.get("n_cellules", 30)),
            pression="atmospherique" if arch == "E" else "etage",
            pincement_K=float(c.get("pincement", 0.0)),
            coefficient_perte_w_m2k=float(c.get("coefficient_perte", 0.0)),
            bypass=bool(c.get("bypass", True)),
            T_initiale_K=T_amb,
            correlations=Correlations(
                wakao_a=reg.si("lit.wakao.a"), wakao_b=reg.si("lit.wakao.b"),
                wakao_c=reg.si("lit.wakao.c"),
                wakao_Re_min=reg.si("lit.wakao.Re_min"),
                wakao_Re_max=reg.si("lit.wakao.Re_max"),
                ergun_A=reg.si("lit.ergun.A"), ergun_B=reg.si("lit.ergun.B"),
                jeffreson_facteur=reg.si("lit.jeffreson.facteur"),
            ),
        )
        cuves = config.construire()
        couplage = CouplageCuvesCharge(air, cuves, config, p_amb, T_amb)
        rechauffeur = RechauffeurCuves(air, cuves, config, p_amb, T_amb)
    elif arch == "C":
        huile = CouplageHuileIdeale()
        couplage = huile
        rechauffeur = RechauffeurHuileIdeale(air, huile)

    ex = Exergie(air, T_amb, p_amb)
    cycles: list[Cycle] = []
    E_prec = None
    converge = False
    p_cuves = []
    for k in range(1, n_max + 1):
        Ex_c0 = [exergie_cuve(l, T_amb) for l in cuves] if cuves else []
        Q0 = sum(l.energie_stockee_j(T_amb) for l in cuves) if cuves else 0.0
        ch = simuler_charge(sc_ch, reg, air, couplage=couplage,
                            reservoir_initial=reservoir)
        if cuves:
            for i, l in enumerate(cuves):
                ch.totaux[f"dEx_cuve_{i + 1}_j"] = (
                    exergie_cuve(l, T_amb) - Ex_c0[i])
            # pression des cuves pendant l'attente : dernier état de charge
            p_cuves = [
                (ch.series[f"p_in_comp_{i + 1}_pa"].iloc[-1]
                 * ch.series[f"beta_{i + 1}"].iloc[-1])
                if config is not None and config.pression == "etage" else p_amb
                for i in range(len(cuves))
            ]
        Q_apres_charge = (sum(l.energie_stockee_j(T_amb) for l in cuves)
                          if cuves else 0.0)
        pertes = _attente(reservoir, cuves, air, attente_s, T_amb, p_cuves)
        Ex_c1 = [exergie_cuve(l, T_amb) for l in cuves] if cuves else []
        d = simuler_decharge(sc_de, reg, air, rechauffeur=rechauffeur,
                             reservoir_initial=reservoir)
        if cuves:
            for i, l in enumerate(cuves):
                d.totaux[f"dEx_cuve_{i + 1}_j"] = (
                    exergie_cuve(l, T_amb) - Ex_c1[i])
            d.sources_etages = {  # type: ignore[attr-defined]
                i + 1: f"cuve_{len(cuves) - i}"
                for i in range(len(sc_de["turbine.etages"]))
                if len(cuves) - i >= 1
            }
        Q_fin = (sum(l.energie_stockee_j(T_amb) for l in cuves)
                 if cuves else 0.0)
        cycles.append(Cycle(
            numero=k, charge=ch, decharge=d, attente_h=attente_s / 3600.0,
            chaleur_cuves_debut_kwh=Q0 / 3.6e6,
            chaleur_cuves_fin_kwh=Q_fin / 3.6e6,
            pertes_attente_kwh=pertes / 3.6e6,
        ))
        E = d.totaux["energie_electrique_kwh"]
        Q_stable = (not cuves) or abs(Q_fin - Q0) <= tol * max(Q_fin, 1.0)
        if (E_prec is not None and abs(E - E_prec) <= tol * max(E, 1e-9)
                and Q_stable):
            converge = True
            break
        E_prec = E
    del ex, Q_apres_charge
    res = ResultatIntegre(
        scenario=sc, architecture=arch, cycles=cycles, cuves=cuves,
        volumes_m3=volumes, converge=converge,
    )
    if isinstance(couplage, CouplageCuvesCharge):
        res.dp_cuves_pa = list(couplage.dp_pas)  # type: ignore[attr-defined]
    if isinstance(rechauffeur, RechauffeurHuileIdeale):
        res.huile_reserve_kwh = (  # type: ignore[attr-defined]
            couplage.reserve_j / 3.6e6)  # type: ignore[union-attr]
    return res
