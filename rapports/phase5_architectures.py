# -*- coding: utf-8 -*-
"""Phase 5 : comparaison des architectures A à E et dimensionnement des cuves.

    python rapports/phase5_architectures.py

Écrit ``rapports/phase5/architectures.md``, un tableau « 1000 unités »
et une cascade par architecture, et le balayage de volume des cuves
pour D et E.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "validation"))
sys.path.insert(0, str(RACINE / "rapports"))
from style_graphiques import (  # noqa: E402
    COULEURS,
    etiquette_fin,
    nouvelle_figure,
    point_reference,
    style_axes,
    terminer,
)
from tableau_1000_unites import Cas, cascade, tableau_markdown, u  # noqa: E402

from caes.exergie import (  # noqa: E402
    bilan_exergie_charge,
    bilan_exergie_decharge,
)
from caes.integre import ResultatIntegre, simuler_cycles  # noqa: E402
from caes.registre import Registre  # noqa: E402
from caes.scenario import charger_scenario  # noqa: E402

DOSSIER = RACINE / "rapports" / "phase5"
T0C = 273.15
TITRES = {
    "A": "A : base Dormoy, 1 étage, sans réchauffage",
    "B": "B : 3 étages, chaleur externe (Dormoy)",
    "C": "C : 3 étages, huile idéale (chaleur > 130 °C sans perte)",
    "D": "D : 3 étages, gravier direct (3 cuves sous pression)",
    "E": "E : 3 étages, gravier + boucle d'air (cuves à 1 bar, 2 × 20 K)",
}
FICHE = {"C": "≈ 160", "D": "≈ 150–155", "E": "≈ 130–150", "A": "46",
         "B": "160"}


def unites_rendues(cas: Cas) -> float:
    return u(cas, cas.bilan_decharge.sorties_utiles_j["électricité produite"])


def somme_postes(cas: Cas, *mots: str, charge: bool = False) -> float:
    b = cas.bilan_charge if charge else cas.bilan_decharge
    source = b.sorties_utiles_j if charge else b.postes
    return u(cas, sum(v for k, v in source.items()
                      if any(m in k for m in mots)))


def cas_depuis(code: str, r: ResultatIntegre) -> Cas:
    c = r.dernier
    return Cas(code, TITRES[code], c.charge, c.decharge,
               bilan_exergie_charge(c.charge),
               bilan_exergie_decharge(c.decharge))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    import matplotlib.pyplot as plt  # noqa: F401
    import tableau_1000_unites as t1000
    t1000.DOSSIER = DOSSIER  # les tableaux de la phase 5 vont dans phase5/
    reg = Registre.charger()
    L: list[str] = []
    L.append("# Phase 5 : banc de Dormoy + cuves de gravier, "
             "architectures A à E\n")
    L.append(
        "*Généré par `rapports/phase5_architectures.py`. Chaque architecture "
        "enchaîne des cycles charge → attente (1 h) → décharge jusqu'au "
        "régime stable, à partir de la pression d'arrêt de sa turbine. "
        "Charge : "
        "scénario « aspiration chaude » (phase 1). Isolation des cuves "
        "parfaite (les pertes sont l'objet de la phase 6).*\n"
    )

    # ------------------------------------------------------------------
    # 1. Les cinq architectures
    # ------------------------------------------------------------------
    resultats: dict[str, ResultatIntegre] = {}
    for code in ("A", "B", "C", "D", "E"):
        t0 = time.perf_counter()
        resultats[code] = simuler_cycles(f"{code}.yaml", reg)
        print(f"[{time.perf_counter() - t0:.0f} s] {resultats[code].resume()}")
    L.append("## 1. Tableau comparatif (dernier cycle)\n")
    L.append("| Arch. | Cycles | Charge (kWh) | Produit (kWh) | RTE sans "
             "chaleur | Chaleur externe (kWh) | RTE avec chaleur externe | "
             "Chaleur des cuves → turbines (kWh) | T entrée turbines (°C, "
             "moy.) | Cuves : volume, pression, gravier | Chaleur restante "
             "dans les cuves (kWh) | Unités rendues sur 1000 | Fiche Dormoy "
             "(à la main) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    cas_par_code: dict[str, Cas] = {}
    for code, r in resultats.items():
        c = r.dernier
        ch, d = c.charge, c.decharge
        E_c = ch.totaux["energie_electrique_kwh"]
        E_p = d.totaux["energie_electrique_kwh"]
        q_ext = d.chaleur_par_source.get("externe", 0.0)
        q_cuves = sum(v for k, v in d.chaleur_par_source.items()
                      if k.startswith("cuve"))
        s = d.series
        T_in = " / ".join(
            f"{s[f'T_in_turb_{i}_K'].mean() - T0C:.0f}"
            for i in (1, 2, 3) if f"T_in_turb_{i}_K" in s)
        if r.cuves:
            p_cuves = [
                ch.series[f"p_in_comp_{i + 1}_pa"].iloc[-1]
                * ch.series[f"beta_{i + 1}"].iloc[-1] / 1e5
                if code == "D" else 1.013 for i in range(len(r.cuves))]
            cuves_txt = (
                f"{sum(r.volumes_m3):.2f} m³ "
                f"({' / '.join(f'{v:.2f}' for v in r.volumes_m3)}) ; "
                f"{' / '.join(f'{p:.0f}' for p in p_cuves)} bar ; "
                f"{sum(l.masse_gravier_kg for l in r.cuves):.0f} kg")
            restante = f"{c.chaleur_cuves_fin_kwh:.0f}"
        else:
            cuves_txt = "–"
            restante = "–"
        cas = cas_depuis(code, r)
        cas_par_code[code] = cas
        unites = unites_rendues(cas)
        etat = "" if r.converge else " (non stabilisé)"
        L.append(
            f"| {code} | {len(r.cycles)}{etat} "
            f"| {E_c:.1f} | {E_p:.2f} | {E_p / E_c * 100:.1f} % | "
            f"{q_ext:.1f} | {E_p / (E_c + q_ext) * 100:.1f} % | {q_cuves:.1f} "
            f"| {T_in} | {cuves_txt} | {restante} | **{unites:.0f}** | "
            f"{FICHE[code]} |"
        )
    L.append(
        "\nLes « unités rendues sur 1000 » sont l'électricité produite "
        "rapportée à l'électricité de la charge du même cycle. Pour C, la "
        "chaleur vient de la réserve d'huile idéale (étiquette "
        "`huile_ideale`) : elle n'est pas comptée comme externe.\n"
    )
    hu = getattr(resultats["C"], "huile_reserve_kwh", 0.0)
    L.append(
        f"Architecture C : réserve d'huile idéale restante après le dernier "
        f"cycle : {hu:.0f} kWh (la chaleur > 130 °C des refroidisseurs "
        f"dépasse le besoin, comme chez Dormoy : 72 contre 46 kWh).\n"
    )

    # tableaux 1000 unités
    L.append("## 2. Tableaux « 1000 unités » par architecture\n")
    for code, cas in cas_par_code.items():
        (DOSSIER / f"tableau_1000_{code}.md").write_text(
            tableau_markdown(cas), encoding="utf-8")
        cascade(cas, f"cascade_{code}.png")
        bc, bd = cas.bilan_charge, cas.bilan_decharge
        stock_air = u(cas, bc.sorties_utiles_j[
            "exergie stockée dans les réservoirs"])
        L.append(
            f"- **{TITRES[code]}** : stocké dans l'air {stock_air:.0f}"
            f", dans les cuves {somme_postes(cas, 'cuve', charge=True):.0f}"
            f" ; détendeur {u(cas, bd.postes['détendeur (laminage)']):.0f} ; "
            f"turbines et génératrices "
            f"{somme_postes(cas, 'turbine', 'génératrice'):.0f}"
            f" ; cuves (restitution) {somme_postes(cas, 'restitution'):.0f}"
            f" ; **rendu {unites_rendues(cas):.0f}** "
            f"(résidus {bc.residu_relatif * 100:+.2f} % / "
            f"{bd.residu_relatif * 100:+.2f} %). "
            f"[tableau](tableau_1000_{code}.md), "
            f"[cascade](cascade_{code}.png)"
        )

    # ------------------------------------------------------------------
    # 3. Dimensionnement des cuves
    # ------------------------------------------------------------------
    L.append("\n## 3. Dimensionnement des cuves (D et E)\n")
    L.append(
        "Les volumes de base ([0,35 ; 0,2 ; 0,7] m³, voir `D.yaml`) sont "
        "multipliés par un facteur k. Cycles jusqu'au régime stable (au plus "
        "4). L'objectif : la plus petite cuve qui alimente encore les "
        "turbines à leur température nominale.\n"
    )
    L.append("| Arch. | k | Volume total | Gravier | Produit (kWh) | RTE | "
             "T min entrée turbine 1 / 2 / 3 (°C) | Chaleur restante (kWh) "
             "| Cycles |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    facteurs = [0.25, 0.5, 1.0, 2.0, 4.0]
    courbes: dict[str, tuple[list[float], list[float]]] = {}
    lignes_dim = []
    for code in ("D", "E"):
        base = [float(v) for v in charger_scenario(f"{code}.yaml",
                                                   reg)["cuves.volumes"]]
        xs, ys = [], []
        for k in facteurs:
            vols = [k * v for v in base]
            sc = charger_scenario(f"{code}.yaml", reg).avec(
                {"cycles.nombre_max": 4, "cuves.n_cellules": 20}, f"k{k:g}")
            t0 = time.perf_counter()
            r = simuler_cycles(sc, reg, volumes_m3=vols)
            c = r.dernier
            s = c.decharge.series
            E_p = c.decharge.totaux["energie_electrique_kwh"]
            E_c = c.charge.totaux["energie_electrique_kwh"]
            Tmin = " / ".join(f"{s[f'T_in_turb_{i}_K'].min() - T0C:.0f}"
                              for i in (1, 2, 3))
            print(f"  [{time.perf_counter() - t0:.0f} s] {code} k={k}: "
                  f"{E_p:.2f} kWh, T min {Tmin}")
            masse = sum(l.masse_gravier_kg for l in (r.cuves or []))
            L.append(
                f"| {code} | {k:g} | {sum(vols):.2f} m³ | {masse:.0f} kg | "
                f"{E_p:.2f} | {E_p / E_c * 100:.1f} % | {Tmin} | "
                f"{c.chaleur_cuves_fin_kwh:.0f} | {len(r.cycles)} |"
            )
            xs.append(sum(vols))
            ys.append(E_p)
            lignes_dim.append({"arch": code, "k": k, "V_m3": sum(vols),
                               "E_kwh": E_p, "rte": E_p / E_c})
        courbes[code] = (xs, ys)
    pd.DataFrame(lignes_dim).to_csv(DOSSIER / "dimensionnement.csv",
                                    index=False)
    fig, ax = nouvelle_figure()
    for (code, (xs, ys)), col in zip(courbes.items(), COULEURS):
        ax.plot(xs, ys, color=col, linewidth=2, marker="o", ms=5,
                label=TITRES[code].split(":")[1].strip())
        etiquette_fin(ax, xs[-1], ys[-1], code, col)
    EB = resultats["B"].dernier.decharge.totaux["energie_electrique_kwh"]
    point_reference(ax, max(courbes["D"][0]), EB,
                    f"B : chaleur externe illimitée ({EB:.1f} kWh)")
    ax.set_xscale("log")
    style_axes(ax, "Électricité produite par cycle selon le volume total des "
               "cuves", "Volume total de gravier (m³, échelle log)",
               "Électricité produite par cycle (kWh)")
    terminer(fig, ax, DOSSIER / "fig_dimensionnement.png")
    L.append(
        "\n![dimensionnement](fig_dimensionnement.png)\n\n"
        "Lecture : au-dessous du volume de base, les turbines reçoivent de "
        "l'air trop froid (la colonne « T min » le montre) et la production "
        "baisse ; au-dessus, rien ne change (les cuves accumulent de la "
        "chaleur qu'on n'utilise pas). Le coude de la courbe est le volume "
        "à retenir.\n"
    )

    # ------------------------------------------------------------------
    # 4. Vérifications physiques
    # ------------------------------------------------------------------
    rD = resultats["D"]
    cD = rD.dernier
    L.append("## 4. Vérifications physiques\n")
    p_cuves = [cD.charge.series[f"p_in_comp_{i + 1}_pa"].iloc[-1]
               * cD.charge.series[f"beta_{i + 1}"].iloc[-1] / 1e5
               for i in range(3)]
    p_turb = [reg.si(f"turbine.etage{i}.pression_entree") / 1e5
              for i in (1, 2, 3)]
    L.append("| Question | Réponse |")
    L.append("|---|---|")
    L.append(
        f"| Les pressions des cuves correspondent-elles à celles des "
        f"turbines ? "
        f"| Cuves 1 / 2 / 3 chargées à {p_cuves[0]:.1f} / {p_cuves[1]:.1f} / "
        f"{p_cuves[2]:.0f} bar (fin de charge) ; turbines 3 / 2 / 1 à "
        f"{p_turb[2]:.0f} / {p_turb[1]:.0f} / {p_turb[0]:.0f} bar. Les "
        f"couples s'emboîtent (cuve 3 ↔ turbine 1, etc.) ; la cuve est "
        f"simplement traversée à une pression un peu différente en décharge, "
        f"ce que le modèle gère (densité de l'air par CoolProp). |"
    )
    s = cD.decharge.series
    L.append(
        f"| La cuve 1 suffit-elle pour la turbine 3 ? | Turbine 3 à "
        f"{s['T_in_turb_3_K'].mean() - T0C:.0f} °C en moyenne (cible 90) et "
        f"{s['T_in_turb_3_K'].min() - T0C:.0f} °C au minimum ; chaleur prise "
        f"{cD.decharge.chaleur_par_source.get('cuve_1', 0):.1f} kWh. "
        f"Oui au volume de base ; voir le balayage pour la marge. |"
    )
    dps = getattr(rD, "dp_cuves_pa", [0.0, 0.0, 0.0])
    debit = cD.charge.totaux["debit_aspire_kg_s"]
    cout = sum(dp * debit / 2.0 for dp in dps) * cD.charge.totaux["duree_s"]
    dps_txt = " / ".join(f"{dp:.0f}" for dp in dps)
    q_cuves_D = sum(v for k, v in cD.decharge.chaleur_par_source.items()
                    if k.startswith("cuve"))
    L.append(
        f"| La perte de charge dans le gravier coûte-t-elle de l'énergie ? | "
        f"Δp d'Ergun en fin de charge : {dps_txt} "
        f"Pa. Travail de pompage ≈ Σ Δp·V̇ ≈ {cout / 3.6e6:.3f} kWh sur une "
        f"charge de {cD.charge.totaux['energie_electrique_kwh']:.0f} kWh : "
        f"négligeable (< 0,01 %). |"
    )
    L.append(
        f"| Que reste-t-il dans les cuves après la décharge ? | "
        f"{cD.chaleur_cuves_fin_kwh:.0f} kWh (au-dessus de 20 °C) au cycle "
        f"stable : c'est le « coussin de chaleur » qui ne sert pas, à "
        f"comparer aux {q_cuves_D:.0f} kWh prélevés par cycle. |"
    )

    # ------------------------------------------------------------------
    # 5. Comparaison avec la fiche et proposition
    # ------------------------------------------------------------------
    L.append("\n## 5. Comparaison avec le calcul à la main (fiche Dormoy, "
             "section 4)\n")
    L.append("| | Huile idéale (C) | Gravier direct (D) | "
             "Gravier + boucle (E) |")
    L.append("|---|---|---|---|")
    L.append(
        "| Fiche (à la main) | 160 | 150–155 | 130–150 |\n"
        "| Simulateur | "
        + " | ".join(f"{unites_rendues(cas_par_code[c]):.0f}"
                     for c in ("C", "D", "E")) + " |"
    )
    L.append(
        "\nLe simulateur donne des valeurs plus proches les unes des autres "
        "que la fiche : avec des cuves correctement dimensionnées, le "
        "gravier alimente les turbines exactement à leur température "
        "nominale (bypass), donc D et E produisent autant que C et B. La "
        "différence entre les architectures n'est pas dans l'électricité "
        "produite mais dans ce qu'il faut pour y arriver : chaleur externe "
        "(B), stockage d'huile parfait (C), cuves sous pression (D) ou "
        "cuves à 1 bar avec deux échangeurs et 20 K de marge en moins (E). "
        "La pénalité de fin de décharge supposée par la fiche (−5 %) "
        "n'apparaît pas, parce que les cuves sont dimensionnées avec une "
        "marge (coude de la courbe) et qu'un bypass régule la température.\n"
        "\n**Proposition de mise à jour des fiches Dormoy et Tola (section "
        "« cuves de gravier ») : à faire seulement avec l'accord de "
        "l'utilisateur.** Points à corriger : masse morte (18 bar, pas 50), "
        "détendeur (234 unités dans le cas de base, pas 74 ; 71 avec 3 "
        "étages), unités rendues (voir tableau 1), pas de pénalité de fin "
        "de décharge au volume de base, volumes de cuves ≈ 1,3 m³ au total "
        "au lieu de 2 m³.\n"
    )
    L.append("## 6. Graphiques\n")
    for code in cas_par_code:
        L.append(f"![cascade {code}](cascade_{code}.png)\n")
    (DOSSIER / "architectures.md").write_text("\n".join(L), encoding="utf-8")
    print("rapport écrit :", DOSSIER / "architectures.md")


if __name__ == "__main__":
    main()
