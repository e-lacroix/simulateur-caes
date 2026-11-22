# -*- coding: utf-8 -*-
"""Phase 9 : peut-on remplacer le sécheur par un refroidissement et un
séparateur d'eau, et dans quelles conditions ambiantes ?

    python rapports/phase9_humidite.py

1. Les six scénarios de ``scenarios/humidite/`` (architectures A et B ×
   sécheur de Dormoy / séparateurs / séparateurs + appoint) à 20 °C et
   50 % : eau à chaque étape, condensation dans le réservoir, givre aux
   sorties de turbine, énergie et rendement.
2. Balayage du climat : humidité relative 30, 60, 90 % × température
   ambiante −20, 0, 20, 30 °C, pour A et B avec séparateurs seulement
   (et B avec le sécheur de Dormoy en référence).
3. Verdict : conditions où le sécheur est évitable.

Écrit ``rapports/phase9/humidite.md`` et deux figures. Durée ≈ 4 min.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from caes.assembleur import ResultatSimulation  # noqa: E402
from caes.assembleur import charger_installation  # noqa: E402
from caes.graphiques import (  # noqa: E402
    COULEURS,
    etiquette_fin,
    nouvelle_figure,
    style_axes,
    terminer,
)
from caes.registre import Registre  # noqa: E402

DOSSIER = RACINE / "rapports" / "phase9"
HUM = RACINE / "scenarios" / "humidite"
T0C = 273.15
ECART_ASPIRATION_K = 32.0
"""Air aspiré 32 K au-dessus de l'ambiant (air du conteneur, phase 1)."""
HUMIDITES = (0.3, 0.6, 0.9)
TEMPERATURES_C = (-20, 0, 20, 30)


def simuler(nom: str, reg: Registre,
            modifs: list[str] | None = None) -> ResultatSimulation:
    return charger_installation(HUM / nom, reg, modifications=modifs).simuler()


def bilan_eau(r: ResultatSimulation) -> dict[str, float]:
    c = r.dernier_cycle
    assert c is not None
    ch, d = c.charge, c.decharge
    t_ch, t_d = ch.totaux, d.totaux
    givre = {i: t_d.get(f"givre_{i}_kg", 0.0) for i in (1, 2, 3)}
    return {
        "E_c": t_ch["energie_electrique_kwh"],
        "E_p": t_d["energie_electrique_kwh"],
        "rte": t_d["energie_electrique_kwh"] / t_ch["energie_electrique_kwh"],
        "eau_entree": t_ch["eau_entree_kg"],
        "eau_condensee": t_ch["eau_condensee_kg"],
        "eau_separee": t_ch["eau_separee_kg"],
        "eau_reservoir": t_ch["eau_reservoir_kg"],
        "eau_cond_res": t_d["eau_condensee_reservoir_kg"],
        "T_rosee_res": t_ch["T_rosee_reservoir_degC"],
        "Q_lat": t_ch["chaleur_condensation_kwh"],
        "givre_det": t_d["givre_detendeur_kg"],
        "givre": givre,
        "givre_total": t_d["givre_total_kg"],
        "T_rejet_min": t_d["T_rejet_min_degC"],
        "eau_sortie": t_d["eau_sortie_kg"],
        "avis": [a for a in r.avertissements
                 if "givre" in a.message or "condensation" in a.message],
    }


def verdict(b: dict[str, float]) -> str:
    probleme = []
    if b["eau_cond_res"] > 1e-3:
        probleme.append("condensation dans le réservoir")
    if b["givre_total"] > 1e-3:
        probleme.append("givre")
    if not probleme:
        return "eau maîtrisée"
    return "eau non maîtrisée (" + ", ".join(probleme) + ")"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    t0 = time.perf_counter()
    L = ["# Phase 9 : humidité, sécheur et séparateur sur le banc de "
         "Dormoy\n",
         "*Généré par `rapports/phase9_humidite.py`. L'eau est suivie de "
         "l'aspiration au rejet (formules F42 et F43) : condensation dans "
         "les refroidisseurs, séparateurs, sécheur, condensation dans le "
         "réservoir, givre aux sorties du détendeur et des turbines. Les "
         "hypothèses (point de rosée de −40 °C du sécheur, séparateurs à "
         "98 %, appoint à 5 % de purge) sont au registre avec le niveau "
         "« hypothèse ».*\n"]

    # --- 1. six scénarios à 20 °C, 50 % ----------------------------------
    L.append("## 1. Trois façons de traiter l'eau, à 20 °C et 50 % "
             "d'humidité (ambiance de Dormoy, hypothèse)\n")
    L.append("| Scénario | Électricité charge (kWh) | Produit (kWh) | RTE | "
             "Eau aspirée (kg/charge) | Condensée dans les refroidisseurs | "
             "Séparée ou purgée | Vers le réservoir | Condensée dans le "
             "réservoir | T de rosée du réservoir (°C) | Givre détendeur / "
             "turbines (kg) | Air rejeté min (°C) | Verdict |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    resultats: dict[str, dict] = {}
    for f in sorted(HUM.glob("*.yaml")):
        t1 = time.perf_counter()
        r = simuler(f.name, reg)
        b = bilan_eau(r)
        resultats[f.stem] = b
        print(f"[{time.perf_counter() - t1:.0f} s] {r.resume()}")
        g = " / ".join(f"{b['givre'][i]:.3f}" for i in (1, 2, 3)
                       if f.stem.startswith("B") or i == 1)
        L.append(
            f"| `{f.name}` | {b['E_c']:.1f} | {b['E_p']:.2f} | "
            f"{b['rte'] * 100:.1f} % | {b['eau_entree']:.1f} | "
            f"{b['eau_condensee']:.1f} | {b['eau_separee']:.1f} | "
            f"{b['eau_reservoir']:.2f} | {b['eau_cond_res']:.3f} | "
            f"{b['T_rosee_res']:.0f} | {b['givre_det']:.3f} / {g} | "
            f"{b['T_rejet_min']:.0f} | {verdict(b)} |")
    L.append(
        "\nLecture : le sécheur purge 19 % de l'air ; les séparateurs ne "
        "coûtent rien en air mais laissent l'air saturé à la température "
        "du dernier refroidisseur, sous la pression du réservoir. "
        "L'énergie et le rendement ne dépendent que de la purge (le bilan "
        "d'énergie est fait sur l'air sec ; la chaleur de condensation est "
        "donnée à part). Sans séparateur, les gouttes d'un refroidisseur "
        "repartent avec l'air et s'évaporent dans l'étage suivant : la "
        "somme de ce que condensent les refroidisseurs dépasse alors l'eau "
        "aspirée, et seul le sécheur, au bout de la chaîne, la retire. "
        "L'air déjà présent dans le réservoir au départ est supposé aussi "
        "sec que ce que la chaîne refoule (F43).\n")

    # --- 2. balayage du climat ---------------------------------------------
    L.append("## 2. Balayage du climat : séparateurs seulement\n")
    L.append("Humidité relative 30, 60 et 90 % × température ambiante −20, "
             "0, 20 et 30 °C (air aspiré 32 K plus chaud, comme le "
             "conteneur de Dormoy), un cycle. Chaque case : condensation "
             "dans le réservoir (kg) / givre total au détendeur et aux "
             "turbines (kg) / verdict. L'humidité aspirée ne change rien "
             "aux colonnes : quelle qu'elle soit, l'air quitte le dernier "
             "refroidisseur saturé ; seule compte la température de ce "
             "refroidisseur face aux températures les plus froides que "
             "l'air rencontre ensuite (réservoir, détendeur, turbines).\n")
    figs: dict[str, dict[float, list[float]]] = {}
    for arch, titre in (("A", "A : 1 étage sans réchauffage"),
                        ("B", "B : 3 étages réchauffés à 130/90/90 °C")):
        L.append(f"### {titre}\n")
        L.append("| T ambiante | " + " | ".join(f"φ = {h * 100:.0f} %"
                                                 for h in HUMIDITES) + " |")
        L.append("|---|" + "---|" * len(HUMIDITES))
        figs[arch] = {}
        for T_c in TEMPERATURES_C:
            cases = []
            for h in HUMIDITES:
                t1 = time.perf_counter()
                r = simuler(f"{arch}_separateur.yaml", reg, [
                    f"ambiance.T_amb={T_c}degC",
                    f"ambiance.T_aspiration={T_c + ECART_ASPIRATION_K}degC",
                    f"ambiance.humidite_relative={h}",
                    "simulation.nombre_max=1"])
                b = bilan_eau(r)
                figs[arch].setdefault(h, []).append(b["givre_total"])
                print(f"[{time.perf_counter() - t1:.0f} s] {arch} {T_c} °C "
                      f"{h * 100:.0f} % : givre {b['givre_total']:.3f} kg, "
                      f"réservoir {b['eau_cond_res']:.3f} kg")
                cases.append(f"{b['eau_cond_res']:.3f} / "
                             f"{b['givre_total']:.3f} / {verdict(b)}")
            L.append(f"| {T_c:+d} °C | " + " | ".join(cases) + " |")
        L.append("")
    # sécheurs en référence (A et B, −20 et 30 °C, 90 %)
    L.append("### Référence : sécheur de Dormoy et sécheur d'appoint "
             "(90 % d'humidité, un cycle)\n")
    L.append("| Architecture | Traitement | T ambiante | Eau vers le "
             "réservoir (kg) | Condensée dans le réservoir | Givre | "
             "Verdict |")
    L.append("|---|---|---|---|---|---|---|")
    for arch in ("A", "B"):
        for nom, desc in (("secheur_adsorption", "sécheur de Dormoy (19 %)"),
                          ("separateur_appoint",
                           "séparateurs + appoint (5 %)")):
            for T_c in (-20, 30):
                r = simuler(f"{arch}_{nom}.yaml", reg, [
                    f"ambiance.T_amb={T_c}degC",
                    f"ambiance.T_aspiration={T_c + ECART_ASPIRATION_K}degC",
                    "ambiance.humidite_relative=0.9",
                    "simulation.nombre_max=1"])
                b = bilan_eau(r)
                L.append(f"| {arch} | {desc} | {T_c:+d} °C | "
                         f"{b['eau_reservoir']:.3f} | "
                         f"{b['eau_cond_res']:.3f} | "
                         f"{b['givre_total']:.3f} | {verdict(b)} |")

    # figure
    fig, ax = nouvelle_figure()
    for k, (arch, serie) in enumerate(figs.items()):
        for j, (h, ys) in enumerate(serie.items()):
            c = COULEURS[(k * 3 + j) % len(COULEURS)]
            style = "-" if arch == "B" else (0, (4, 3))
            ax.plot(TEMPERATURES_C, ys, color=c, linewidth=2, marker="o",
                    ms=4, linestyle=style)
            if j == len(serie) - 1:
                etiquette_fin(ax, TEMPERATURES_C[-1], ys[-1],
                              f"{arch} (30, 60 et 90 % confondus)", c)
    style_axes(ax, "Givre aux sorties du détendeur et des turbines par "
               "cycle, séparateurs seulement", "Température ambiante (°C)",
               "Givre (kg par décharge)")
    fig_g = terminer(fig, ax, DOSSIER / "fig_givre.png", None)

    # --- 3. verdict ---------------------------------------------------------
    L.append(f"\n![givre]({fig_g})\n")
    L.append("## 3. Verdict\n")
    L.append(
        "**Le sécheur ne peut pas être évité, mais il peut être petit.**\n\n"
        "- **Séparateurs seuls : jamais suffisants.** Les gouttes sont "
        "drainées, mais l'air quitte le dernier refroidisseur *saturé* à sa "
        "température de sortie (≈ 45 °C à 20 °C d'ambiance). Dès que le "
        "réservoir refroidit en dessous (attente, détente), l'eau condense "
        "au fond : 0,04 kg par cycle à −20 °C, 0,2 kg à 0 °C, 0,5 à 0,6 kg "
        "à 20 °C, 0,8 à 1,0 kg à 30 °C, pour les deux architectures et "
        "quelle que soit l'humidité aspirée. La condition pour s'en passer "
        "serait un dernier refroidisseur plus froid que tout ce que le "
        "réservoir rencontre ensuite ; avec un refroidisseur à l'air "
        "ambiant, elle n'est jamais remplie, été comme hiver.\n"
        "- **L'hiver assèche le réservoir mais givre le détendeur.** À "
        "−20 °C, le refroidisseur sort l'air plus froid, donc plus sec "
        "sous pression (25 fois moins d'eau au réservoir qu'à 30 °C) ; en "
        "revanche le détendeur de B, qui sort l'air vers −5 °C à 20 °C "
        "d'ambiance, givre (5 à 12 g par décharge entre −20 et 0 °C, rien "
        "à 30 °C). En A, c'est l'inverse : l'air rejeté à −74 °C givre "
        "d'autant plus que le réservoir est humide (8 g à −20 °C, 190 g à "
        "30 °C).\n"
        "- **Sécheur à −40 °C de point de rosée sous pression** (Dormoy, "
        "19 % d'air purgé) : aucune condensation dans le réservoir ni "
        "givre en B, dans les douze climats ; en A, où l'air sort de la "
        "turbine sous −74 °C, l'eau résiduelle du point de rosée de −40 °C "
        "laisse 0,2 g de givre par décharge à 20 °C et 2 g à −20 °C "
        "(le verdict compte tout givre au-dessus de 1 g). Le même point "
        "de rosée avec 5 % de "
        "purge (séparateurs + appoint) donne le même résultat sur l'eau et "
        "rend 19,7 % au lieu de 16,8 % en B (RTE), 5,1 % au lieu de 4,3 % "
        "en A : ce qui protège l'installation est le **point de rosée**, "
        "pas la quantité d'air purgée. La fraction de purge d'un sécheur "
        "réel dépend de sa technologie (régénération à chaud ou par "
        "détente) : les 5 % sont une hypothèse à remplacer par une fiche "
        "de fabricant.\n"
        "- **Règle pour un chercheur** : le point de rosée sous pression de "
        "l'air stocké doit être inférieur à la température la plus froide "
        "que l'air atteint ensuite : le réservoir en hiver (ambiance), la "
        "sortie du détendeur (B : vers −5 °C), la sortie de la turbine "
        "sans réchauffage (A : −74 °C, hors de portée d'un sécheur "
        "ordinaire : seul le réchauffage protège A). Un sécheur "
        "frigorifique (air refroidi à +3 °C avant le réservoir) n'est pas "
        "modélisé ; il couvrirait l'été mais pas l'hiver québécois.\n"
        "- Limites : bilan d'énergie sur l'air sec (l'eau est suivie en "
        "masse, sa chaleur latente est donnée à part) ; au-delà de 10 MPa "
        "la saturation est extrapolée (F42) ; équilibre instantané, la "
        "cinétique du givrage (dépôt sur les aubes) n'est pas modélisée ; "
        "séparateurs à 98 % et point de rosée de −40 °C sont des "
        "hypothèses, pas des mesures de Dormoy.\n")
    L.append(f"\n*Durée : {time.perf_counter() - t0:.0f} s.*\n")
    (DOSSIER / "humidite.md").write_text("\n".join(L), encoding="utf-8")
    print("rapport écrit :", DOSSIER / "humidite.md")


if __name__ == "__main__":
    main()
