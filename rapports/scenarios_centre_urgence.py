# -*- coding: utf-8 -*-
"""Scénario d'exemple 3 (phase 11) : centre d'urgence à demande variable.

    python rapports/scenarios_centre_urgence.py [--procs N]

Question : un centre d'urgence consomme 100 kW en moyenne pendant 72 h
(7,2 MWh) avec un profil jour / nuit. Combien de modules « D isolée »
(réservoir de Dormoy, cuves de gravier) faut-il pour le tenir, que
pèsent-ils, et comment se comparent-ils à des batteries en conteneur
et à une génératrice diesel ?

1. Un module : décharge simulée (courbe de puissance, énergie, durée).
2. Répartition seconde par seconde de la flotte sur la demande
   (``caes/flotte.py``, F47) : nombre de modules nécessaire, énergie non
   servie, démarrages, écrêtage.
3. Variantes : module à 250 bar ; demande constante ; hiver (−20 °C).
4. Comparaison avec des Megapack (fiche Tesla 2020) et une génératrice
   Cat D100 GC (fiche 2020) : énergie, masse, volume, carburant, coût
   (NREL 2023, Bazdar via Dormoy).
5. « Qu'est-ce qu'il faudrait pour être viable ? » : énergie par tonne
   et par mètre cube à atteindre.

Écrit ``rapports/scenarios/centre_urgence.md`` et une figure.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from caes.analyse.lot import ResumeSimulation, simuler_lot  # noqa: E402
from caes.analyse.masse import masse_reservoir_paroi_mince  # noqa: E402
from caes.flotte import (  # noqa: E402
    CourbeModule,
    ResultatFlotte,
    modules_necessaires,
    repartir,
)
from caes.graphiques import (  # noqa: E402
    COULEURS,
    ENCRE_2,
    nouvelle_figure,
    style_axes,
    terminer,
)
from caes.registre import Registre  # noqa: E402

DOSSIER = RACINE / "rapports" / "scenarios"
EXEMPLE = RACINE / "scenarios" / "exemples" / "centre_urgence"
SCENARIO = EXEMPLE / "module.yaml"
DEMANDE = EXEMPLE / "demande_72h.csv"
WH = 1.0 / 3.6e6


def _f(x: float, nd: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if abs(x) >= 10000:
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.{nd}f}"


def charger_demande(dt_s: float) -> np.ndarray:
    tab = pd.read_csv(DEMANDE)
    t = tab["t_min"].to_numpy(dtype=float) * 60.0
    P = tab["P_kW"].to_numpy(dtype=float) * 1e3
    grille = np.arange(0.0, t[-1] + 60.0, dt_s)
    return np.interp(grille, t, P, right=P[-1])


def courbe_module(r: ResumeSimulation, dt_s: float) -> CourbeModule:
    s = r.series_decharge
    assert s is not None
    return CourbeModule.depuis_series(s["t_s"].to_numpy(),
                                      s["P_el_w"].to_numpy(), dt_s)


def masse_module(reg: Registre, r: ResumeSimulation,
                 p_max_pa: float) -> dict[str, float]:
    """Masse d'un module : réservoirs (F44, à la pression de conception),
    gravier des cuves (volumes du scénario), compresseur et turbine
    exclus (non publiés)."""
    V = reg.si("reservoir.volume_total")
    m_res = masse_reservoir_paroi_mince(
        p_max_pa - reg.si("ambiance.p_amb_essai"), V,
        reg.si("reservoir.diametre_interieur"),
        reg.si("reservoir.resistance_specifique_equivalente"),
        reg.si("reservoir.coefficient_securite")).masse_kg
    v_cuves = 0.35 + 0.2 + 0.7
    m_grav = (v_cuves * (1 - reg.si("materiau.gravier_tola.porosite"))
              * reg.si("materiau.gravier_tola.masse_volumique"))
    return {"reservoirs_kg": m_res, "gravier_kg": m_grav,
            "total_kg": m_res + m_grav, "volume_reservoirs_m3": V,
            "volume_cuves_m3": v_cuves}


def conso_diesel(reg: Registre, P_w: np.ndarray,
                 dt_s: float) -> tuple[float, int]:
    """Volume de carburant [m³] et nombre de génératrices : autant de
    machines que la pointe l'exige, charge partagée à parts égales,
    consommation interpolée sur la courbe (50, 75, 100 % de charge) de
    la fiche Cat D100 GC ; sous 50 % de charge, consommation de 50 %
    (hypothèse prudente, machines en marche continue)."""
    Pn = reg.si("groupe_diesel.puissance")
    n = int(math.ceil(float(P_w.max()) / Pn))
    charges = np.array([0.5, 0.75, 1.0])
    conso = np.array([reg.si("groupe_diesel.conso_50"),
                      reg.si("groupe_diesel.conso_75"),
                      reg.si("groupe_diesel.conso_100")])
    frac = np.clip(P_w / (n * Pn), 0.5, 1.0)
    return float(n * np.sum(np.interp(frac, charges, conso)) * dt_s), n


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--procs", type=int,
                   default=max(1, (os.cpu_count() or 2) - 2))
    args = p.parse_args(argv)
    t0 = time.perf_counter()
    reg = Registre.charger()
    DOSSIER.mkdir(parents=True, exist_ok=True)
    dt = 1.0
    demande = charger_demande(dt)
    duree_s = demande.size * dt
    E_dem_kwh = demande.sum() * dt * WH
    P_moy = reg.si("centre_urgence.puissance_moyenne")
    rte_mp = reg.si("megapack.rendement_aller_retour")

    variantes = {
        "base": [],
        "250 bar": ["charge.p_cible=250bar"],
        "hiver": ["ambiance.T_amb=-20degC", "ambiance.T_aspiration=12degC"],
    }
    print(f"{len(variantes)} modules à simuler ({args.procs} processus)")
    res = dict(zip(variantes, simuler_lot(SCENARIO, list(variantes.values()),
                                          args.procs, series=True)))
    for nom, r in res.items():
        if not r.valide:
            raise SystemExit(f"module « {nom} » : {r.erreur}")

    L = ["# Scénario d'exemple : centre d'urgence à demande variable\n",
         "*Généré par `rapports/scenarios_centre_urgence.py` à partir de "
         "`scenarios/exemples/centre_urgence/module.yaml` (un module = "
         "architecture D isolée, chargée la veille) et de "
         "`demande_72h.csv` (profil jour / nuit, hypothèse). Les "
         "comparaisons viennent du registre (fiches Tesla 2020 et "
         "Caterpillar 2020, rapport NREL 2023, Bazdar via Dormoy).*\n",
         f"**Question.** Tenir {E_dem_kwh / 1e3:.1f} MWh sur "
         f"{duree_s / 3600:.0f} h ({P_moy / 1e3:.0f} kW en moyenne, "
         f"{demande.max() / 1e3:.0f} kW le jour, {demande.min() / 1e3:.0f} "
         f"kW la nuit) avec des modules d'air comprimé chargés d'avance. "
         f"Combien en faut-il, que pèsent-ils, et est-ce raisonnable face "
         f"aux solutions existantes ?\n"]

    # --- 1. un module --------------------------------------------------------
    L.append("## 1. Un module\n")
    L.append("| Module | Électricité pour le charger (kWh) | Électricité "
             "livrée (kWh) | Durée de décharge (min) | Puissance "
             "nominale (kW) | Rendement | Air rejeté min (°C) | Masse "
             "réservoirs + gravier (t) |")
    L.append("|---|---|---|---|---|---|---|---|")
    courbes: dict[str, CourbeModule] = {}
    masses: dict[str, dict[str, float]] = {}
    for nom, r in res.items():
        c = courbe_module(r, dt)
        courbes[nom] = c
        p_max = 250e5 if nom == "250 bar" else reg.si(
            "essai_charge.pression_finale")
        masses[nom] = masse_module(reg, r, p_max)
        L.append(f"| {nom} | {_f(r.charge['energie_electrique_kwh'])} | "
                 f"{_f(c.energie_j * WH, 2)} | {_f(c.duree_s / 60)} | "
                 f"{_f(c.P_nominale_w / 1e3)} | "
                 f"{_f(r.rendements['rte_sans_chaleur'] * 100)} % | "
                 f"{_f(r.decharge['T_rejet_min_degC'], 0)} | "
                 f"{_f(masses[nom]['total_kg'] / 1e3, 2)} |")
    L.append("\nLa puissance d'un module n'est pas constante : elle suit "
             "la pression du réservoir et la température des cuves "
             "(figure). La masse compte les 20 bouteilles (F44, à la "
             "pression de conception) et le gravier ; compresseur, "
             "turbine et échangeurs ne sont pas comptés (non publiés).\n")

    # --- 2. flotte -----------------------------------------------------------
    L.append("## 2. Répartition de la flotte sur la demande (F47)\n")
    L.append("Règle : à chaque seconde, on démarre un module de plus si "
             "la puissance en marche ne couvre pas la demande ; on met le "
             "dernier en pause (vanne fermée, air conservé) si l'excédent "
             "dépasse la puissance d'un module ; entre les deux, "
             "l'excédent est écrêté. Nombre de modules : le plus petit "
             "qui fournit au moins 99,9 % de l'énergie demandée.\n")
    L.append("| Module | Demande | Modules nécessaires | Énergie "
             "demandée (MWh) | Fournie | Non servie | Écrêtée | "
             "Démarrages | Masse de la flotte (t) | Volume des bouteilles "
             "(m³) | Électricité pour charger la flotte (MWh) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    flottes: dict[tuple[str, str], tuple[int, ResultatFlotte]] = {}
    demandes = {"jour / nuit": demande,
                "constante 100 kW": np.full_like(
                    demande, reg.si("centre_urgence.puissance_moyenne"))}
    for nom, c in courbes.items():
        for nd, dem in demandes.items():
            if nom != "base" and nd != "jour / nuit":
                continue
            n, rf = modules_necessaires(c, dem, dt)
            flottes[(nom, nd)] = (n, rf)
            E_ch = res[nom].charge["energie_electrique_kwh"] * n / 1e3
            L.append(f"| {nom} | {nd} | **{n}** | "
                     f"{_f(rf.energie_demandee_j * WH / 1e3, 2)} | "
                     f"{_f(rf.couverture * 100)} % | "
                     f"{_f(rf.energie_non_servie_j * WH)} kWh | "
                     f"{_f(rf.energie_ecretee_j * WH)} kWh | "
                     f"{rf.demarrages} | "
                     f"{_f(masses[nom]['total_kg'] * n / 1e3, 0)} | "
                     f"{_f(masses[nom]['volume_reservoirs_m3'] * n, 0)} | "
                     f"{_f(E_ch, 1)} |")
    L.append("")
    n_base, rf_base = flottes[("base", "jour / nuit")]
    E_mod = courbes["base"].energie_j * WH
    L.append(f"Borne énergétique : {E_dem_kwh:.0f} kWh / "
             f"{E_mod:.1f} kWh par module = "
             f"{E_dem_kwh / E_mod:.1f} modules ; la répartition en demande "
             f"{n_base} parce que la puissance d'un module tombe en fin "
             f"de décharge et que l'écrêtage en perd un peu.\n")

    # --- 3. comparaison ------------------------------------------------------
    L.append("## 3. Comparaison avec les solutions existantes\n")
    E_mp = reg.si("megapack.energie") * WH
    n_mp = math.ceil(E_dem_kwh / E_mp)
    m_mp = reg.si("megapack.masse")
    v_mp = (reg.si("megapack.longueur") * reg.si("megapack.largeur")
            * reg.si("megapack.hauteur"))
    V_fuel, n_gen = conso_diesel(reg, demande, dt)
    m_fuel = V_fuel * reg.si("groupe_diesel.masse_volumique")
    m_gen = reg.si("groupe_diesel.masse")
    cout_bat = {k: reg.si(f"batterie.cout_2030_{k}") * 3.6e6
                for k in ("bas", "moyen", "haut")}
    c_caes = reg["caes.cout_reservoir_hors_sol"]
    c_caes_min = c_caes.valeur_min_si * 3.6e6
    c_caes_max = c_caes.valeur_max_si * 3.6e6
    m_flotte = masses["base"]["total_kg"] * n_base
    E_charge_flotte = (res["base"].charge["energie_electrique_kwh"] * n_base
                       / 1e3)
    v_flotte = masses["base"]["volume_reservoirs_m3"] * n_base
    L.append("| Solution | Unités | Énergie disponible (MWh) | Masse (t) "
             "| Volume ou emprise (m³) | Consommable | Coût d'après les "
             "sources (M$ US) | Source |")
    L.append("|---|---|---|---|---|---|---|---|")
    L.append(f"| Modules d'air comprimé (D isolée, 190 bar) | {n_base} "
             f"modules | {n_base * E_mod / 1e3:.1f} | {m_flotte / 1e3:.0f} "
             f"| {v_flotte:.0f} (bouteilles seules) | "
             f"{E_charge_flotte:.0f} MWh d'électricité pour charger | "
             f"{E_dem_kwh * c_caes_min / 1e6:.1f} à "
             f"{E_dem_kwh * c_caes_max / 1e6:.1f} (réservoirs seuls, "
             f"{c_caes_min:.0f}–{c_caes_max:.0f} $/kWh) | Dormoy tableau 1 "
             f"(Bazdar 2022) |")
    L.append(f"| Batteries lithium-ion en conteneur (Megapack 4 h, 2020) | "
             f"{n_mp} | {n_mp * E_mp / 1e3:.1f} | "
             f"{n_mp * m_mp / 1e3:.0f} | {n_mp * v_mp:.0f} | "
             f"{E_dem_kwh / rte_mp / 1e3:.1f} MWh d'électricité pour "
             f"charger | "
             f"{E_dem_kwh * cout_bat['bas'] / 1e6:.1f} à "
             f"{E_dem_kwh * cout_bat['haut'] / 1e6:.1f} (projection 2030, "
             f"{cout_bat['bas']:.0f}–{cout_bat['haut']:.0f} $/kWh) | "
             f"Tesla 2020, NREL 2023 |")
    L.append(f"| Génératrices diesel Cat D100 GC (100 kW) + carburant | "
             f"{n_gen} + {m_fuel / 1e3:.2f} t de diesel | illimitée tant "
             f"qu'il y a du carburant | {(n_gen * m_gen + m_fuel) / 1e3:.1f} "
             f"| "
             f"{V_fuel:.1f} m³ de carburant | {V_fuel * 1e3:.0f} L de "
             f"diesel sur 72 h | non chiffré | Caterpillar 2020 |")
    L.append("")
    L.append(f"Une génératrice fait "
             f"{reg.si('groupe_diesel.puissance') / 1e3:.0f} kW : la "
             f"pointe de {demande.max() / 1e3:.0f} kW en demande {n_gen}, "
             f"qui se partagent la charge ; sous 50 % de charge la "
             f"consommation est prise à sa valeur de 50 % (prudent). "
             f"Carburant : {V_fuel * 1e3:.0f} L en 72 h, soit "
             f"{V_fuel * 1e3 / E_dem_kwh:.2f} L/kWh.\n")

    # --- 4. viabilité --------------------------------------------------------
    L.append("## 4. Qu'est-ce qu'il faudrait pour être viable ?\n")
    dens_caes = E_mod / (masses["base"]["total_kg"] / 1e3)
    dens_mp = E_mp / (m_mp / 1e3)
    vol_caes = E_mod / masses["base"]["volume_reservoirs_m3"]
    vol_mp = E_mp / v_mp
    L.append("| Indicateur | Module D isolée | Megapack | Rapport |")
    L.append("|---|---|---|---|")
    L.append(f"| Électricité livrée par tonne (kWh/t) | {dens_caes:.1f} | "
             f"{dens_mp:.0f} | × {dens_mp / dens_caes:.0f} |")
    L.append(f"| Électricité livrée par m³ (kWh/m³) | {vol_caes:.1f} | "
             f"{vol_mp:.0f} | × {vol_mp / vol_caes:.0f} |")
    L.append(f"| Rendement aller-retour | "
             f"{res['base'].rendements['rte_sans_chaleur'] * 100:.1f} % | "
             f"{rte_mp * 100:.0f} % | "
             f"× {rte_mp / res['base'].rendements['rte_sans_chaleur']:.1f} |")
    L.append("")
    L.append("Pour qu'une flotte d'air comprimé pèse autant que les "
             "batteries qui font le même travail, il faudrait multiplier "
             f"l'électricité livrée par tonne par {dens_mp / dens_caes:.0f}. "
             "Les leviers connus du simulateur (phases 3, 5, 7 et 10) : "
             "supprimer le détendeur (pression glissante), monter la "
             "pression, réduire les cuves, améliorer le compresseur ; "
             "leur somme ne dépasse pas un facteur 2 à 3 sur le rendement. "
             "L'air comprimé hors sol n'est pas une solution de secours "
             "transportable pour 72 h à cette échelle ; son intérêt est "
             "ailleurs : stockage fixe de longue durée, caverne, "
             "cogénération de chaleur (phases 4, 8 et scénario 4).\n")

    # --- figure --------------------------------------------------------------
    fig, ax = nouvelle_figure(8.0, 4.5)
    t_h = np.arange(demande.size) * dt / 3600.0
    pas = max(1, demande.size // 4000)
    ax.plot(t_h[::pas], demande[::pas] / 1e3, color=ENCRE_2, linewidth=1.5,
            label="demande")
    ax.plot(t_h[::pas], rf_base.fournie_w[::pas] / 1e3, color=COULEURS[0],
            linewidth=1, label=f"fournie ({n_base} modules)")
    ax2 = ax.twinx()
    ax2.plot(t_h[::pas], rf_base.modules_en_marche[::pas], color=COULEURS[1],
             linewidth=1, linestyle=(0, (3, 2)), label="modules en marche")
    ax2.set_ylabel("Modules en marche", color=COULEURS[1])
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    style_axes(ax, "Centre d'urgence : demande et flotte de modules (72 h)",
               "Temps (h)", "Puissance (kW)")
    f1 = terminer(fig, ax, DOSSIER / "centre_urgence_flotte.png", None)
    fig, ax = nouvelle_figure(8.0, 4.0)
    for k, (nom, c) in enumerate(courbes.items()):
        tt = np.arange(c.P_w.size) * c.dt_s / 60.0
        ax.plot(tt, c.P_w / 1e3, color=COULEURS[k % 4], linewidth=2,
                label=nom)
    ax.legend(frameon=False, fontsize=8)
    style_axes(ax, "Puissance d'un module pendant sa décharge",
               "Temps depuis le démarrage (min)", "Puissance (kW)")
    f2 = terminer(fig, ax, DOSSIER / "centre_urgence_module.png", None)
    L.append(f"![flotte]({f1})\n\n![module]({f2})\n")
    L.append(f"*{len(variantes)} simulations de module, répartition au pas "
             f"de {dt:.0f} s sur {duree_s / 3600:.0f} h, "
             f"{time.perf_counter() - t0:.0f} s.*\n")
    chemin = DOSSIER / "centre_urgence.md"
    chemin.write_text("\n".join(L), encoding="utf-8")
    print("rapport écrit :", chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
