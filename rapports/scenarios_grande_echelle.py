# -*- coding: utf-8 -*-
"""Scénario d'exemple 4 (phase 11) : grande échelle (Shi 2024, 100 MW).

    python rapports/scenarios_grande_echelle.py

Question : la même bibliothèque de composants décrit-elle une centrale
de 100 MW / 600 MWh, et qu'est-ce qui change avec la taille ? Simule
``scenarios/validation/shi_100MW.yaml`` (réservoir adiabatique de
118 000 m³, eau sous pression, turbine en pression glissante) et le
met en regard du module de Dormoy (``scenarios/D.yaml``) : énergie par
mètre cube de réservoir, par tonne d'air, rendement, durées, rôle de
la paroi et du détendeur. Écrit ``rapports/scenarios/grande_echelle.md``.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from caes.analyse.lot import simuler_scenarios  # noqa: E402
from caes.registre import Registre  # noqa: E402

DOSSIER = RACINE / "rapports" / "scenarios"
SHI = RACINE / "scenarios" / "validation" / "shi_100MW.yaml"
D = RACINE / "scenarios" / "D.yaml"


def _f(x: float, nd: int = 1) -> str:
    if x is None or math.isnan(x):
        return "–"
    if abs(x) >= 10000:
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.{nd}f}"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    reg = Registre.charger()
    DOSSIER.mkdir(parents=True, exist_ok=True)
    shi, d = simuler_scenarios([(SHI, []), (D, [])], procs=2)
    for nom, r in (("Shi", shi), ("D", d)):
        if not r.valide:
            raise SystemExit(f"{nom} : {r.erreur}")
    V_shi = reg.si("shi.reservoir.volume")
    V_d = reg.si("reservoir.volume_total")
    lignes = []

    def ajouter(nom: str, f_shi, f_d, nd: int = 1) -> None:
        lignes.append(f"| {nom} | {_f(f_shi(shi), nd)} | {_f(f_d(d), nd)} |")

    L = ["# Scénario d'exemple : grande échelle (centrale de 100 MW)\n",
         "*Généré par `rapports/scenarios_grande_echelle.py` à partir de "
         "`scenarios/validation/shi_100MW.yaml` (cas test de Shi 2024, "
         "prépublication non révisée) et de `scenarios/D.yaml` (module "
         "de Dormoy avec gravier). Mêmes composants, mêmes équations : "
         "seuls les modèles choisis et les nombres changent.*\n",
         "**Question.** Que change la taille ? Un réservoir de "
         f"{V_shi:,.0f} m³ contre {V_d:.2f} m³, 100 MW contre 60 kW, "
         "quatre étages à 10 MPa contre 19 MPa, eau sous pression contre "
         "gravier, pression glissante contre détendeur.\n".replace(",", " "),
         "## Les deux installations, dernier cycle\n",
         "| Grandeur | Shi 2024 (100 MW) | Dormoy D (gravier) |",
         "|---|---|---|"]
    ajouter("Volume du réservoir d'air (m³)", lambda r: V_shi,
            lambda r: V_d, 2)
    ajouter("Pression de travail (bar)",
            lambda r: r.charge["p_finale_bar"],
            lambda r: r.charge["p_finale_bar"], 0)
    ajouter("Masse d'air stockée par cycle (t)",
            lambda r: r.charge["masse_stockee_kg"] / 1e3,
            lambda r: r.charge["masse_stockee_kg"] / 1e3, 2)
    ajouter("Durée de la charge (h)", lambda r: r.charge["duree_h"],
            lambda r: r.charge["duree_h"], 2)
    ajouter("Électricité consommée (MWh)",
            lambda r: r.rendements["energie_consommee_kwh"] / 1e3,
            lambda r: r.rendements["energie_consommee_kwh"] / 1e3, 3)
    ajouter("Durée de la décharge (h)",
            lambda r: r.decharge["duree_min"] / 60,
            lambda r: r.decharge["duree_min"] / 60, 2)
    ajouter("Électricité livrée (MWh)",
            lambda r: r.rendements["energie_produite_kwh"] / 1e3,
            lambda r: r.rendements["energie_produite_kwh"] / 1e3, 3)
    ajouter("Puissance électrique moyenne (MW)",
            lambda r: r.decharge["puissance_electrique_moyenne_kw"] / 1e3,
            lambda r: r.decharge["puissance_electrique_moyenne_kw"] / 1e3, 3)
    ajouter("Rendement aller-retour (%)",
            lambda r: r.rendements["rte_sans_chaleur"] * 100,
            lambda r: r.rendements["rte_sans_chaleur"] * 100, 1)
    ajouter("Électricité livrée par m³ de réservoir (kWh/m³)",
            lambda r: r.rendements["energie_produite_kwh"] / V_shi,
            lambda r: r.rendements["energie_produite_kwh"] / V_d, 2)
    ajouter("Électricité livrée par tonne d'air (kWh/t)",
            lambda r: r.rendements["energie_produite_kwh"]
            / (r.charge["masse_stockee_kg"] / 1e3),
            lambda r: r.rendements["energie_produite_kwh"]
            / (r.charge["masse_stockee_kg"] / 1e3), 1)
    ajouter("Température finale du réservoir après charge (°C)",
            lambda r: r.charge["T_finale_degC"],
            lambda r: r.charge["T_finale_degC"], 0)
    ajouter("Air rejeté, minimum (°C)",
            lambda r: r.decharge["T_rejet_min_degC"],
            lambda r: r.decharge["T_rejet_min_degC"], 0)
    L += lignes
    L.append("")
    L.append("## Ce qui change avec la taille\n")
    L.append("- **La paroi ne compte plus.** Les 20 bouteilles de Dormoy "
             "(65 m² pour 5,86 m³) évacuent la chaleur de compression en "
             "quelques heures ; la caverne de Shi est modélisée "
             "adiabatique (F38) : l'air y reste chaud, la pression cible "
             "est atteinte avec moins de masse, et cette chaleur ressort "
             "à la décharge. Même composant `reservoir_air`, modèle "
             "`paroi` contre `adiabatique`.\n"
             "- **Le détendeur disparaît.** Shi fait entrer la première "
             "turbine directement à la pression du réservoir (pression "
             "glissante, F39) ; Dormoy jette l'exergie de 190 à 40 bar "
             "dans un détendeur (phase 3 : 68 % de l'exergie stockée dans "
             "le cas de base). C'est la première raison de l'écart de "
             "rendement.\n"
             "- **La chaleur est stockée dans l'eau sous pression** (18 "
             "bar, F40) et rendue par des échangeurs à pincement de 10 K ; "
             "le gravier de D est traversé directement par l'air. Les "
             "deux sont des stockages sensibles ; l'eau est limitée par "
             "son ébullition (plafond à 202 °C), le gravier par le front "
             "thermique.\n"
             "- **La pression de travail est plus basse** (4 à 10 MPa) : "
             "l'air humide reste dans le domaine de sa formulation "
             "(F42), le travail de compression par kilogramme est plus "
             "petit, mais il faut 20 000 fois plus de volume.\n"
             "- **Ce que le tableau de bord dit de ce cas** (phase 8) : "
             "compresseurs 1 à 3 à 0,1 %, turbines à 3 %, rendement "
             "65,0 % contre 67,64 % publié ; durées et masse à −6 à −9 % "
             "(réservoir adiabatique, quatrième refroidisseur) ; ce n'est "
             "pas une validation, aucune mesure n'existe pour cette "
             "centrale.\n")
    L.append(f"*2 simulations, {time.perf_counter() - t0:.0f} s.*\n")
    chemin = DOSSIER / "grande_echelle.md"
    chemin.write_text("\n".join(L), encoding="utf-8")
    print("rapport écrit :", chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
