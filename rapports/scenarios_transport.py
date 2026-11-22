# -*- coding: utf-8 -*-
"""Scénario d'exemple 2 (phase 11) : transport et conservation de la
chaleur.

    python rapports/scenarios_transport.py [--procs N]

Question : si on charge l'installation D (gravier direct) au départ,
qu'on la transporte pendant 7 à 56 jours, puis qu'on la décharge à
l'arrivée, que reste-t-il de la chaleur des cuves et de l'électricité ?

1. Durée d'attente 7, 14, 21, 28, 42, 56 jours × isolant 10, 20, 40 cm,
   à 20 °C constant : chaleur restante et électricité livrée.
2. Hiver québécois (profil autour de −20 °C) et été (30 °C), 20 cm,
   mêmes durées.
3. Effet d'échelle : cuves × 1, × 4 et × 16 (une cuve plus grosse perd
   proportionnellement moins), 28 jours.
4. Fuites d'air du réservoir : 0, 0,5 et 2 % par jour, 28 jours.
5. Solution de repli : chaudière d'appoint après chaque cuve
   (``transport_appoint.yaml``) : chaleur externe nécessaire.
6. Vérification à la main : constante de temps d'une cuve de 2 m³ sous
   20 cm de laine (≈ 23 jours attendus).

Écrit ``rapports/scenarios/transport.md`` et deux figures.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from caes.analyse.lot import ResumeSimulation, simuler_lot  # noqa: E402
from caes.graphiques import (  # noqa: E402
    COULEURS,
    etiquette_fin,
    nouvelle_figure,
    style_axes,
    terminer,
)
from caes.registre import Registre  # noqa: E402

DOSSIER = RACINE / "rapports" / "scenarios"
EXEMPLE = RACINE / "scenarios" / "exemples" / "transport"
SCENARIO = EXEMPLE / "transport.yaml"
APPOINT = EXEMPLE / "transport_appoint.yaml"
DUREES_J = (7, 14, 21, 28, 42, 56)
EPAISSEURS_CM = (10, 20, 40)
ECHELLES = (1, 4, 16)
FUITES_PCT = (0.0, 0.5, 2.0)


def _modifs(duree_j: float, epaisseur_cm: float | None = None,
            profil: str | None = None, echelle: float | None = None,
            fuite_pct: float | None = None) -> list[str]:
    m = [f"composants.attente.duree={duree_j}j"]
    if epaisseur_cm is not None:
        m += [f"composants.cuve_{i}.isolation.epaisseur="
              f"{epaisseur_cm / 100:.3f}m" for i in (1, 2, 3)]
    if profil is not None:
        m.append(f"ambiance.profil={profil}")
        T = -20 if "hiver" in profil else 30
        m.append(f"ambiance.T_amb={T}degC")
        m.append(f"ambiance.T_aspiration={T + 32}degC")
    if echelle is not None and echelle != 1:
        base = {1: 0.35, 2: 0.2, 3: 0.7}
        m += [f"composants.cuve_{i}.volume={v * echelle:.4f}m3"
              for i, v in base.items()]
        m += [f"composants.cuve_{i}.n_cellules=20" for i in (1, 2, 3)]
    if fuite_pct is not None:
        m.append(f"composants.reservoir.fuite_par_jour={fuite_pct}%")
    return m


def _lignes(r: ResumeSimulation) -> dict[str, float]:
    """Chaleur après la charge, restante après l'attente, électricité."""
    Q_apres_charge = (r.chaleur_cuves_debut_kwh
                      + r.charge.get("chaleur_cuves_kwh", float("nan")))
    Q_restante = Q_apres_charge - r.pertes_attente_kwh
    return {
        "Q_apres_charge": Q_apres_charge,
        "pertes": r.pertes_attente_kwh,
        "Q_restante": Q_restante,
        "fraction": (Q_restante / Q_apres_charge if Q_apres_charge > 0
                     else float("nan")),
        "E_charge": r.charge.get("energie_electrique_kwh", float("nan")),
        "E_produite": r.decharge.get("energie_electrique_kwh",
                                     float("nan")),
        "rte": r.rendements.get("rte_sans_chaleur", float("nan")),
        "rte_ext": r.rendements.get("rte_avec_chaleur_externe",
                                    float("nan")),
        "Q_externe": r.rendements.get("chaleur_externe_kwh", 0.0),
        "T_rejet": r.decharge.get("T_rejet_min_degC", float("nan")),
        "fuite_kg": r.masse_fuite_kg,
        "masse_init": r.decharge.get("masse_initiale_kg", float("nan")),
    }


def _f(x: float, nd: int = 1) -> str:
    return "–" if x is None or math.isnan(x) else f"{x:.{nd}f}"


def constante_de_temps(reg: Registre, volume_m3: float,
                       epaisseur_m: float) -> dict[str, float]:
    """τ = m·cp / (U·A) d'une cuve cylindrique (H = 2 D) de gravier sous
    un isolant plan (F29, F41) : vérification à la main."""
    rho = reg.si("materiau.gravier_tola.masse_volumique")
    cp = reg.si("materiau.gravier_tola.cp")
    eps = reg.si("materiau.gravier_tola.porosite")
    k = reg.si("materiau.laine_minerale.conductivite")
    h = reg.si("isolation.h_ext")
    D = (4.0 * volume_m3 / (math.pi * 2.0)) ** (1.0 / 3.0)
    H = 2.0 * D
    A = math.pi * D * H + 2.0 * math.pi * D**2 / 4.0
    U = 1.0 / (epaisseur_m / k + 1.0 / h)
    C = volume_m3 * (1.0 - eps) * rho * cp
    tau = C / (U * A)
    return {"D_m": D, "A_m2": A, "U": U, "C_j_k": C, "tau_j": tau / 86400}


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

    def rappel(i: int, n: int, r: ResumeSimulation) -> None:
        etat = "" if r.valide else f" ÉCHEC {r.erreur[:70]}"
        print(f"  {i}/{n} [{time.perf_counter() - t0:.0f} s] "
              f"{' '.join(r.modifications)[:60]}{etat}", flush=True)

    # --- lot 1 : durées × isolant, hiver / été, échelle, fuites --------
    lot: list[list[str]] = []
    cles: list[tuple] = []
    for e in EPAISSEURS_CM:
        for d in DUREES_J:
            lot.append(_modifs(d, e))
            cles.append(("iso", e, d))
    for prof in ("meteo_hiver.csv", "meteo_ete.csv"):
        for d in DUREES_J:
            lot.append(_modifs(d, 20, profil=prof))
            cles.append(("meteo", prof, d))
    for ech in ECHELLES:
        lot.append(_modifs(28, 20, echelle=ech))
        cles.append(("echelle", ech, 28))
    for fu in FUITES_PCT:
        lot.append(_modifs(28, 20, fuite_pct=fu))
        cles.append(("fuite", fu, 28))
    print(f"lot principal : {len(lot)} simulations, {args.procs} processus")
    res = dict(zip(cles, simuler_lot(SCENARIO, lot, args.procs,
                                     rappel=rappel)))
    lot2 = [_modifs(d, 20) for d in DUREES_J]
    print(f"lot appoint : {len(lot2)} simulations")
    res_app = dict(zip(DUREES_J, simuler_lot(APPOINT, lot2, args.procs,
                                             rappel=rappel)))
    echecs = [k for k, r in list(res.items())
              + [(("appoint", d, 20), r) for d, r in res_app.items()]
              if not r.valide]

    L = ["# Scénario d'exemple : transport et conservation de la chaleur\n",
         "*Généré par `rapports/scenarios_transport.py` à partir de "
         "`scenarios/exemples/transport/transport.yaml` (architecture D, "
         "gravier direct, 20 cm de laine minérale, un cycle : charge au "
         "départ, attente pendant le transport, décharge à l'arrivée). "
         "Chaque case est une simulation complète ; les hypothèses sont "
         "dans le fichier YAML et au registre.*\n",
         "**Question.** On charge l'installation (air à 190 bar, cuves de "
         "gravier chaudes) puis on la transporte. Combien de chaleur "
         "reste-t-il à l'arrivée, et combien d'électricité ? À partir de "
         "quand le gravier ne sert plus à rien ?\n"]
    L.append("## 1. Durée du transport et épaisseur d'isolant (20 °C "
             "constant)\n")
    L.append("Chaleur après la charge : ce que les cuves contiennent "
             "au-dessus de l'ambiant au départ (toutes les cases partent "
             "du même état chargé). Restante : après l'attente. "
             "Électricité : de la décharge à l'arrivée, cuves telles "
             "qu'elles sont (sans appoint). Rendement : électricité "
             "produite / consommée à la charge.\n")
    L.append("| Isolant | Durée | Chaleur après charge (kWh) | Pertes "
             "(kWh) | Restante (kWh) | Part restante | Électricité livrée "
             "(kWh) | Rendement | Air rejeté min (°C) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    fig1_data: dict[int, list[tuple[int, float, float]]] = {}
    for e in EPAISSEURS_CM:
        for d in DUREES_J:
            r = res[("iso", e, d)]
            if not r.valide:
                L.append(f"| {e} cm | {d} j | échec : {r.erreur[:60]} |"
                         + " |" * 7)
                continue
            li = _lignes(r)
            fig1_data.setdefault(e, []).append(
                (d, li["fraction"], li["E_produite"]))
            L.append(f"| {e} cm | {d} j | {_f(li['Q_apres_charge'])} | "
                     f"{_f(li['pertes'])} | {_f(li['Q_restante'])} | "
                     f"{_f(li['fraction'] * 100, 0)} % | "
                     f"{_f(li['E_produite'], 2)} | "
                     f"{_f(li['rte'] * 100)} % | {_f(li['T_rejet'], 0)} |")
    L.append("")
    # référence sans attente : charge puis décharge immédiate
    ref = simuler_lot(SCENARIO, [_modifs(0.04, 20)], 1)[0]
    if ref.valide:
        lr = _lignes(ref)
        L.append(f"Référence sans transport (attente d'une heure, 20 cm) : "
                 f"{_f(lr['E_produite'], 2)} kWh livrés, rendement "
                 f"{_f(lr['rte'] * 100)} %, chaleur après charge "
                 f"{_f(lr['Q_apres_charge'])} kWh.\n")

    # --- 2. hiver / été ---------------------------------------------------
    L.append("## 2. Hiver québécois et été (profil météo, 20 cm)\n")
    L.append("Profil : sinusoïde journalière de ± 5 K (hypothèse) autour "
             "de −20 °C (`meteo_hiver.csv`) ou de 30 °C (`meteo_ete.csv`), "
             "appliquée à tout le cycle : l'air aspiré, les refroidisseurs, "
             "les pertes des cuves et du réservoir suivent la température "
             "extérieure (F32). L'air aspiré reste 32 K au-dessus de "
             "l'extérieur (conteneur du compresseur).\n")
    L.append("| Climat | Durée | Électricité consommée (kWh) | Chaleur "
             "après charge | Restante | Part | Électricité livrée | "
             "Rendement | Air rejeté min (°C) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    fig2: dict[str, list[tuple[int, float]]] = {}
    for prof, nom in (("meteo_hiver.csv", "hiver (−20 °C)"),
                      ("meteo_ete.csv", "été (30 °C)")):
        for d in DUREES_J:
            r = res[("meteo", prof, d)]
            if not r.valide:
                L.append(f"| {nom} | {d} j | échec : {r.erreur[:60]} |"
                         + " |" * 7)
                continue
            li = _lignes(r)
            fig2.setdefault(nom, []).append((d, li["E_produite"]))
            L.append(f"| {nom} | {d} j | {_f(li['E_charge'])} | "
                     f"{_f(li['Q_apres_charge'])} | {_f(li['Q_restante'])} "
                     f"| {_f(li['fraction'] * 100, 0)} % | "
                     f"{_f(li['E_produite'], 2)} | {_f(li['rte'] * 100)} % "
                     f"| {_f(li['T_rejet'], 0)} |")
    L.append("")
    avis_hiver = sorted(set(
        a.split("]")[1].split(" (×")[0].strip()
        for a in res[("meteo", "meteo_hiver.csv", 14)].avertissements
        if "givre" in a or "condensation" in a))
    if avis_hiver:
        L.append("Avertissements propres à l'hiver (14 j) : "
                 + " ; ".join(avis_hiver[:4]) + ".\n")

    # --- 3. échelle ---------------------------------------------------------
    L.append("## 3. Effet d'échelle (28 jours, 20 cm)\n")
    L.append("Les trois cuves sont multipliées par 1, 4 et 16 en volume "
             "(même forme, H = 2 D) ; le réservoir d'air et le compresseur "
             "ne changent pas, donc la chaleur à stocker non plus : une "
             "cuve plus grosse a moins de surface par mètre cube et une "
             "constante de temps plus longue (τ ∝ V/A ∝ D).\n")
    L.append("| Cuves | Volume total (m³) | Chaleur après charge (kWh) | "
             "Pertes 28 j (kWh) | Part restante | Électricité livrée (kWh) "
             "| Rendement |")
    L.append("|---|---|---|---|---|---|---|")
    for ech in ECHELLES:
        r = res[("echelle", ech, 28)]
        if not r.valide:
            L.append(f"| × {ech} | échec : {r.erreur[:60]} |" + " |" * 5)
            continue
        li = _lignes(r)
        L.append(f"| × {ech} | {1.25 * ech:.2f} | {_f(li['Q_apres_charge'])} "
                 f"| {_f(li['pertes'])} | {_f(li['fraction'] * 100, 0)} % | "
                 f"{_f(li['E_produite'], 2)} | {_f(li['rte'] * 100)} % |")
    L.append("")

    # --- 4. fuites -----------------------------------------------------------
    L.append("## 4. Fuites d'air du réservoir (28 jours, 20 cm)\n")
    L.append("`fuite_par_jour` : fraction de la masse d'air qui s'échappe "
             "chaque jour pendant l'attente (F12 ; 0,5 %/j est l'hypothèse "
             "du registre, 2 %/j un réservoir en mauvais état).\n")
    L.append("| Fuite | Air perdu (kg) | Masse au début de la décharge (kg) "
             "| Électricité livrée (kWh) | Rendement |")
    L.append("|---|---|---|---|---|")
    for fu in FUITES_PCT:
        r = res[("fuite", fu, 28)]
        if not r.valide:
            L.append(f"| {fu} %/j | échec : {r.erreur[:60]} |" + " |" * 3)
            continue
        li = _lignes(r)
        L.append(f"| {fu} %/j | {_f(li['fuite_kg'], 0)} | "
                 f"{_f(li['masse_init'], 0)} | {_f(li['E_produite'], 2)} | "
                 f"{_f(li['rte'] * 100)} % |")
    L.append("")

    # --- 5. appoint ----------------------------------------------------------
    L.append("## 5. Solution de repli : chaudière d'appoint (20 cm, 20 °C)\n")
    L.append("`transport_appoint.yaml` ajoute une source externe après "
             "chaque cuve : l'air atteint toujours 130 / 90 / 90 °C. La "
             "chaleur externe est comptée ; le rendement est donné sans "
             "elle (électricité seule) et avec elle (électricité + chaleur "
             "au dénominateur).\n")
    L.append("| Durée | Électricité livrée (kWh) | Chaleur externe (kWh) | "
             "Rendement sans chaleur | Rendement avec chaleur externe | "
             "Air rejeté min (°C) |")
    L.append("|---|---|---|---|---|---|")
    for d in DUREES_J:
        r = res_app[d]
        if not r.valide:
            L.append(f"| {d} j | échec : {r.erreur[:60]} |" + " |" * 4)
            continue
        li = _lignes(r)
        L.append(f"| {d} j | {_f(li['E_produite'], 2)} | "
                 f"{_f(li['Q_externe'])} | {_f(li['rte'] * 100)} % | "
                 f"{_f(li['rte_ext'] * 100)} % | {_f(li['T_rejet'], 0)} |")
    L.append("")

    # --- 6. constante de temps -----------------------------------------------
    L.append("## 6. Vérification à la main : constante de temps\n")
    ct = constante_de_temps(reg, 2.0, 0.2)
    ct3 = {i: constante_de_temps(reg, v, 0.2)
           for i, v in ((1, 0.35), (2, 0.2), (3, 0.7))}
    L.append(f"Cuve de 2 m³ de gravier (H = 2 D : D = {ct['D_m']:.2f} m, "
             f"A = {ct['A_m2']:.1f} m²) sous 20 cm de laine minérale "
             f"(k = {reg.si('materiau.laine_minerale.conductivite'):.3f} "
             f"W/m·K, h_ext = {reg.si('isolation.h_ext'):.1f} W/m²K) : "
             f"U = {ct['U']:.3f} W/m²K, capacité "
             f"{ct['C_j_k'] / 1e6:.2f} MJ/K, **τ = C / (U·A) = "
             f"{ct['tau_j']:.0f} jours** (fiche Dormoy : ≈ 23 jours). Les "
             f"cuves du scénario sont plus petites : τ = "
             + ", ".join(f"{ct3[i]['tau_j']:.0f} j (cuve {i}, "
                         f"{v} m³)" for i, v in ((1, 0.35), (2, 0.2),
                                                 (3, 0.7)))
             + ". Après un temps t, une cuve isolée garde e^(−t/τ) de sa "
             "chaleur au-dessus de l'ambiant : la colonne « part restante "
             "» du tableau 1 doit suivre cette loi, aux pertes par les "
             "fonds et aux gradients internes près.\n")

    # --- figures ------------------------------------------------------------
    fig, ax = nouvelle_figure()
    for k, (e, pts) in enumerate(sorted(fig1_data.items())):
        xs = [pt[0] for pt in pts]
        ys = [pt[1] * 100 for pt in pts]
        c = COULEURS[k % len(COULEURS)]
        ax.plot(xs, ys, color=c, linewidth=2, marker="o", ms=4)
        etiquette_fin(ax, xs[-1], ys[-1], f"{e} cm", c)
    tau = ct3[3]["tau_j"]
    xs = list(range(0, 57, 1))
    ax.plot(xs, [100 * math.exp(-x / tau) for x in xs], color="#52514e",
            linewidth=1, linestyle=(0, (4, 3)))
    etiquette_fin(ax, 56, 100 * math.exp(-56 / tau),
                  f"e^(−t/τ), τ = {tau:.0f} j (cuve 3)", "#52514e")
    style_axes(ax, "Chaleur restante dans les cuves après le transport "
               "(20 °C)", "Durée du transport (jours)",
               "Part de la chaleur après charge (%)")
    f1 = terminer(fig, ax, DOSSIER / "transport_chaleur.png", None)
    fig, ax = nouvelle_figure()
    series = {"20 °C, 20 cm": [(d, fig1_data[20][i][2])
                               for i, d in enumerate(DUREES_J)
                               if 20 in fig1_data and i < len(fig1_data[20])]}
    series.update(fig2)
    for k, (nom, pts) in enumerate(series.items()):
        xs = [pt[0] for pt in pts]
        ys = [pt[1] for pt in pts]
        c = COULEURS[k % len(COULEURS)]
        ax.plot(xs, ys, color=c, linewidth=2, marker="o", ms=4)
        etiquette_fin(ax, xs[-1], ys[-1], nom, c)
    style_axes(ax, "Électricité livrée à l'arrivée selon le climat "
               "(20 cm d'isolant)", "Durée du transport (jours)",
               "Électricité livrée (kWh)")
    f2 = terminer(fig, ax, DOSSIER / "transport_electricite.png", None)
    L.append(f"![chaleur]({f1})\n\n![électricité]({f2})\n")
    if echecs:
        L.append(f"Simulations échouées : {echecs}\n")
    L.append(f"*{len(lot) + len(lot2) + 1} simulations, "
             f"{time.perf_counter() - t0:.0f} s.*\n")
    chemin = DOSSIER / "transport.md"
    chemin.write_text("\n".join(L), encoding="utf-8")
    print("rapport écrit :", chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
