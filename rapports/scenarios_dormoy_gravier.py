# -*- coding: utf-8 -*-
"""Scénario d'exemple 1 (phase 11) : le banc de Dormoy avec cuves de
gravier, cas de référence, dans le format « composants » de la phase 6.

    python rapports/scenarios_dormoy_gravier.py [--procs N]

Question : sur le banc mesuré par Dormoy (compresseur 45 kW, 20
bouteilles, 190 bar, turbine DEPRAG), que gagne-t-on en remplaçant la
chaleur « supposée » des réchauffeurs par des cuves de gravier qui
récupèrent la chaleur de compression, et que devient le résultat par
−20 °C ?

Simule les cinq architectures de la phase 5 (``scenarios/A.yaml`` à
``E.yaml``) jusqu'au régime stable, puis ``D_hiver.yaml``, et écrit
``rapports/scenarios/dormoy_gravier.md`` : électricité consommée et
livrée, chaleur récupérée et externe, rendements (deux définitions),
état des cuves, température de rejet, eau et givre.
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

from caes.analyse.lot import ResumeSimulation, simuler_scenarios  # noqa: E402
from caes.graphiques import (  # noqa: E402
    COULEURS,
    nouvelle_figure,
    style_axes,
    terminer,
)

DOSSIER = RACINE / "rapports" / "scenarios"
SCENARIOS = RACINE / "scenarios"
CAS = [
    ("A", "A.yaml", "1 étage, sans réchauffage (cas de base de Dormoy)"),
    ("B", "B.yaml", "3 étages réchauffés par une source externe comptée"),
    ("C", "C.yaml", "3 étages, réserve d'huile idéale (hypothèse "
                    "comptable de Dormoy)"),
    ("D", "D.yaml", "3 étages, cuves de gravier traversées par l'air "
                    "comprimé (cas C de Tola)"),
    ("E", "E.yaml", "3 étages, cuves de gravier et boucle d'air à "
                    "pression atmosphérique"),
    ("D hiver", "D_hiver.yaml", "D par −20 °C, air aspiré à la "
                                "température extérieure"),
]


def _f(x: float, nd: int = 1) -> str:
    return "–" if x is None or math.isnan(x) else f"{x:.{nd}f}"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--procs", type=int,
                   default=max(1, min(6, (os.cpu_count() or 2) - 2)))
    args = p.parse_args(argv)
    t0 = time.perf_counter()
    DOSSIER.mkdir(parents=True, exist_ok=True)

    def rappel(i: int, n: int, r: ResumeSimulation) -> None:
        print(f"  {i}/{n} [{time.perf_counter() - t0:.0f} s]"
              + ("" if r.valide else f" ÉCHEC {r.erreur[:70]}"), flush=True)

    print(f"{len(CAS)} scénarios ({args.procs} processus)")
    res = simuler_scenarios([(SCENARIOS / f, []) for _, f, _ in CAS],
                            args.procs, rappel=rappel)
    L = ["# Scénario d'exemple : le banc de Dormoy avec cuves de gravier\n",
         "*Généré par `rapports/scenarios_dormoy_gravier.py` à partir de "
         "`scenarios/A.yaml` à `E.yaml` et `D_hiver.yaml` (format "
         "« composants », phase 6). Chaque ligne est le dernier cycle "
         "d'une simulation « charge → attente d'une heure → décharge » "
         "répétée jusqu'au régime stable (1 % sur l'électricité livrée "
         "et la chaleur des cuves).*\n",
         "**Question.** Dormoy mesure 4,3 % de rendement sans réchauffage "
         "et simule 16,8 % en supposant 130 / 90 / 90 °C à l'entrée des "
         "turbines sans dire d'où vient la chaleur. Si cette chaleur "
         "vient de la compression, stockée dans du gravier (Tola), que "
         "reste-t-il du 16,8 % ? Et par −20 °C ?\n",
         "## Résultats\n",
         "| Cas | Architecture | Cycles | Électricité consommée (kWh) | "
         "Électricité livrée (kWh) | Chaleur rendue à l'air par les cuves "
         "(kWh) | Chaleur externe (kWh) | Rendement sans chaleur externe | "
         "Rendement avec chaleur externe | Chaleur restante dans les "
         "cuves (kWh) | Air rejeté min (°C) | Givre total (kg) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    barres: list[tuple[str, float, float]] = []
    for (nom, fichier, desc), r in zip(CAS, res):
        if not r.valide:
            L.append(f"| {nom} | {desc} | échec : {r.erreur[:70]} |"
                     + " |" * 9)
            continue
        rd = r.rendements
        Q_cuves = (r.decharge.get("chaleur_rechauffage_kwh", float("nan"))
                   - rd["chaleur_externe_kwh"])
        L.append(f"| **{nom}** | {desc} | {r.nombre_cycles}"
                 f"{'' if r.converge else ' (non stabilisé)'} | "
                 f"{_f(rd['energie_consommee_kwh'])} | "
                 f"{_f(rd['energie_produite_kwh'], 2)} | "
                 f"{_f(Q_cuves)} | "
                 f"{_f(rd['chaleur_externe_kwh'])} | "
                 f"{_f(rd['rte_sans_chaleur'] * 100)} % | "
                 f"{_f(rd['rte_avec_chaleur_externe'] * 100)} % | "
                 f"{_f(r.chaleur_cuves_fin_kwh)} | "
                 f"{_f(r.decharge.get('T_rejet_min_degC', float('nan')), 0)} "
                 f"| {_f(r.decharge.get('givre_total_kg', 0.0), 3)} |")
        barres.append((nom, rd["rte_sans_chaleur"] * 100,
                       rd["rte_avec_chaleur_externe"] * 100))
    L.append("")
    L.append("Lecture : le rendement « sans chaleur externe » ne compte "
             "que l'électricité ; le rendement « avec chaleur externe » "
             "met au dénominateur l'électricité de la charge plus la "
             "chaleur achetée (B). Pour A, C, D et E les deux sont égaux "
             "(aucune chaleur achetée) ; pour C, la chaleur vient d'une "
             "réserve parfaite jamais vide, ce qui est une hypothèse "
             "comptable, pas une installation. Le détail de chaque cas "
             "(bilans, tableau 1000 unités, séries) s'obtient avec "
             "`python -m caes simuler scenarios/D.yaml`.\n")
    avis: dict[str, list[str]] = {}
    for (nom, _, _), r in zip(CAS, res):
        for a in r.avertissements:
            if "givre" in a or "trop froide" in a or "condensation" in a:
                avis.setdefault(nom, []).append(a.split(" (×")[0])
    if avis:
        L.append("Avertissements à retenir : "
                 + " ; ".join(f"**{k}** : {len(v)} (par exemple « "
                              f"{v[0][:90]} »)" for k, v in avis.items())
                 + ".\n")
    fig, ax = nouvelle_figure(8.0, 4.0)
    x = range(len(barres))
    ax.bar([i - 0.2 for i in x], [b[1] for b in barres], width=0.4,
           color=COULEURS[0], label="sans chaleur externe")
    ax.bar([i + 0.2 for i in x], [b[2] for b in barres], width=0.4,
           color=COULEURS[1], label="avec chaleur externe")
    for i, b in enumerate(barres):
        ax.text(i - 0.2, b[1] + 0.3, f"{b[1]:.1f}", ha="center", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([b[0] for b in barres])
    ax.legend(frameon=False, fontsize=8)
    style_axes(ax, "Rendement aller-retour des architectures (régime "
               "stable)", "", "Rendement (%)")
    f1 = terminer(fig, ax, DOSSIER / "dormoy_gravier_rendements.png", None)
    L.append(f"![rendements]({f1})\n")
    L.append(f"*{len(CAS)} simulations, {time.perf_counter() - t0:.0f} s.*\n")
    chemin = DOSSIER / "dormoy_gravier.md"
    chemin.write_text("\n".join(L), encoding="utf-8")
    print("rapport écrit :", chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
