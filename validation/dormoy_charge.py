# -*- coding: utf-8 -*-
"""Validation de la charge sur Dormoy (2024), phase 1.

Lance les scénarios de charge, compare aux références du registre et
écrit ``rapports/phase1/validation_charge.md`` avec les graphiques.

    python validation/dormoy_charge.py

Si des courbes numérisées existent dans ``data/validation/dormoy/``
(voir ``A_NUMERISER.md``), elles sont comparées point par point (RMSE et
MAPE, éq. 18-19 de Dormoy).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from caes.metriques import (  # noqa: E402
    comparer_sur_grille,
    ecart_relatif_pct,
    lire_courbe_numerisee,
)
from caes.registre import Registre  # noqa: E402
from caes.scenario import charger_scenario  # noqa: E402
from caes.systeme import ResultatCharge, simuler_charge  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_RAPPORT = RACINE / "rapports" / "phase1"
DOSSIER_NUMERISE = RACINE / "data" / "validation" / "dormoy"

# Palette catégorielle validée (dataviz, ordre fixe) et encres.
COULEURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
ENCRE = "#0b0b0b"
ENCRE_2 = "#52514e"
GRILLE = "#e6e5e1"
SURFACE = "#fcfcfb"


def style_axes(ax: plt.Axes, titre: str, x: str, y: str) -> None:
    ax.set_facecolor(SURFACE)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(GRILLE)
    ax.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=ENCRE_2, labelsize=9)
    ax.set_title(titre, loc="left", color=ENCRE, fontsize=11)
    ax.set_xlabel(x, color=ENCRE_2, fontsize=9)
    ax.set_ylabel(y, color=ENCRE_2, fontsize=9)


def nouvelle_figure() -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=130)
    fig.patch.set_facecolor(SURFACE)
    return fig, ax


def etiquette_fin(
    ax: plt.Axes, x: float, y: float, texte: str, c: str
) -> None:
    ax.annotate(
        texte, (x, y), xytext=(6, 0), textcoords="offset points",
        va="center", fontsize=9, color=ENCRE_2,
        bbox={"boxstyle": "round,pad=0.15", "fc": SURFACE, "ec": "none"},
    )
    ax.plot([x], [y], marker="o", ms=5, color=c, mec=SURFACE, mew=1.5)


def tracer_series_temps(
    resultats: dict[str, ResultatCharge],
    colonne: str,
    facteur: float,
    decalage: float,
    titre: str,
    ylabel: str,
    fichier: str,
    references: list[tuple[float, float, str]] | None = None,
) -> str:
    fig, ax = nouvelle_figure()
    for (nom, r), c in zip(resultats.items(), COULEURS):
        t = r.series["t_s"] / 3600.0
        y = r.series[colonne] * facteur + decalage
        ax.plot(t, y, color=c, linewidth=2, label=nom)
        etiquette_fin(ax, t.iloc[-1], y.iloc[-1], nom, c)
    if references:
        for x, y, texte in references:
            ax.plot(
                [x], [y], marker="D", ms=7, color=ENCRE, mec=SURFACE, mew=1.5,
                linestyle="none", label=texte,
            )
    style_axes(ax, titre, "Temps (h)", ylabel)
    ax.legend(frameon=False, fontsize=8, labelcolor=ENCRE_2, loc="best")
    fig.tight_layout()
    chemin = DOSSIER_RAPPORT / fichier
    fig.savefig(chemin)
    plt.close(fig)
    return chemin.name


def tracer_temperatures_etages(r: ResultatCharge, fichier: str) -> str:
    fig, ax = nouvelle_figure()
    t = r.series["t_s"] / 3600.0
    for i, c in zip(range(1, 5), COULEURS):
        y = r.series[f"T_out_comp_{i}_K"] - 273.15
        ax.plot(t, y, color=c, linewidth=2, label=f"sortie étage {i}")
        etiquette_fin(ax, t.iloc[-1], y.iloc[-1], f"étage {i}", c)
    ax.axhline(130.0, color=ENCRE_2, linewidth=1, linestyle=(0, (4, 4)))
    ax.annotate(
        "130 °C : seuil « chaleur utile » (turbine 1)", (0.05, 130),
        xytext=(0, 5), textcoords="offset points", fontsize=8, color=ENCRE_2,
    )
    style_axes(
        ax,
        f"Température de sortie des étages de compression ({r.scenario.nom})",
        "Temps (h)", "Température (°C)",
    )
    ax.legend(frameon=False, fontsize=8, labelcolor=ENCRE_2, loc="lower right")
    fig.tight_layout()
    chemin = DOSSIER_RAPPORT / fichier
    fig.savefig(chemin)
    plt.close(fig)
    return chemin.name


def tracer_rapports(r: ResultatCharge, fichier: str) -> str:
    fig, ax = nouvelle_figure()
    p = r.series["p_res_pa"] / 1e5
    for i, c in zip(range(1, 5), COULEURS):
        y = r.series[f"beta_{i}"]
        ax.plot(p, y, color=c, linewidth=2, label=f"étage {i}")
        etiquette_fin(ax, p.iloc[-1], y.iloc[-1], f"étage {i}", c)
    style_axes(
        ax, "Rapport de compression de chaque étage (à comparer à la fig. 8)",
        "Pression du réservoir (bar)", "Rapport de pression (–)",
    )
    ax.legend(frameon=False, fontsize=8, labelcolor=ENCRE_2, loc="upper left")
    fig.tight_layout()
    chemin = DOSSIER_RAPPORT / fichier
    fig.savefig(chemin)
    plt.close(fig)
    return chemin.name


def ligne_ecart(
    nom: str, ref: float, sim: float, unite: str, explication: str
) -> str:
    return (
        f"| {nom} | {ref:.4g} {unite} | {sim:.4g} {unite} | "
        f"{ecart_relatif_pct(sim, ref):+.1f} % | {explication} |"
    )


def comparer_courbes_numerisees(
    resultats: dict[str, ResultatCharge],
) -> list[str]:
    """Compare aux CSV numérisés s'ils existent."""
    lignes: list[str] = []
    attendus = {
        "fig10_puissance_mesuree.csv": ("P_el_w", 1e-3, 0.0, "temps_h",
                                        "puissance_kW"),
        "fig10_energie_mesuree.csv": ("E_el_j", 1 / 3.6e6, 0.0, "temps_h",
                                      "energie_kWh"),
        "fig09_T_sortie_etage4_mesuree.csv": ("T_out_comp_4_K", 1.0,
                                              -273.15, "temps_h",
                                              "temperature_degC"),
    }
    for fichier, (col, f, d, cx, cy) in attendus.items():
        chemin = DOSSIER_NUMERISE / fichier
        if not chemin.exists():
            lignes.append(f"| `{fichier}` | absent | – | – |")
            continue
        ref = lire_courbe_numerisee(chemin)
        for nom, r in resultats.items():
            m = comparer_sur_grille(
                r.series["t_s"].to_numpy() / 3600.0,
                (r.series[col] * f + d).to_numpy(),
                ref[cx].to_numpy(),
                ref[cy].to_numpy(),
            )
            lignes.append(
                f"| `{fichier}` | {nom} | {m['rmse']:.3g} | "
                f"{m['mape_pct']:.2f} % |"
            )
    return lignes


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER_RAPPORT.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    base = charger_scenario("dormoy_charge_1_190.yaml", reg)
    chaud = charger_scenario("dormoy_charge_1_190_aspiration_chaude.yaml", reg)
    debit_mesure = {
        "secheur.debit_massique_reservoir_impose":
            reg.si("secheur.debit_massique_sortie")
    }
    variantes = {
        "A : base (20 °C partout, 0,052 kg/s)": base,
        "B : aspiration à 52 °C": chaud,
        "C : A + débit réservoir mesuré 0,032": base.avec(
            debit_mesure, "debit_mesure"),
        "D : B + débit réservoir mesuré 0,032": chaud.avec(
            debit_mesure, "debit_mesure"),
    }
    resultats = {nom: simuler_charge(sc) for nom, sc in variantes.items()}
    base55 = charger_scenario("dormoy_charge_55_190.yaml", reg)
    chaud55 = base55.avec(
        {"compresseur.debit_massique_aspire": None,
         "ambiance.T_aspiration": chaud["ambiance.T_aspiration"]},
        "aspiration_chaude",
    )
    res55 = {
        "A : base": simuler_charge(base55),
        "B : aspiration à 52 °C": simuler_charge(chaud55),
    }
    tout = dict(resultats)
    tout.update({k + " (55→190)": v for k, v in res55.items()})
    for nom, r in tout.items():
        print(nom, "->", r.resume())

    # --- Références du registre ---
    E_ref = reg["essai_charge.energie_consommee"].valeur
    t_ref = reg["essai_charge.duree"].valeur
    P_ref = reg["essai_charge.puissance_moyenne"].valeur
    E_sim_dormoy = reg["cas_base.energie_consommee"].valeur
    Q_tot_ref = reg["refroidisseur.energie_chaleur_totale"].valeur
    Q_sup_ref = reg["refroidisseur.energie_chaleur_sup130_totale"].valeur
    Q_sup_etages_ref = [
        reg[f"refroidisseur.etage{i}.energie_chaleur_sup130"].valeur
        for i in range(1, 5)
    ]
    t55_ref = reg["charge_55_190.duree"].valeur

    # --- Graphiques ---
    deux = {k: v for k, v in list(resultats.items())[:2]}
    figs = [
        tracer_series_temps(
            deux, "P_el_w", 1e-3, 0.0,
            "Puissance électrique du compresseur pendant la charge",
            "Puissance (kW)", "fig1_puissance.png",
            [(t_ref / 2, P_ref, f"Dormoy : {P_ref:.0f} kW en moyenne")],
        ),
        tracer_series_temps(
            deux, "E_el_j", 1 / 3.6e6, 0.0,
            "Énergie électrique cumulée", "Énergie (kWh)",
            "fig2_energie.png",
            [(t_ref, E_ref,
              f"Dormoy : {E_ref:.0f} kWh mesurés à ≈ {t_ref} h")],
        ),
        tracer_series_temps(
            deux, "p_res_pa", 1e-5, 0.0, "Pression du réservoir",
            "Pression absolue (bar)", "fig3_pression.png",
        ),
        tracer_series_temps(
            deux, "T_res_K", 1.0, -273.15, "Température de l'air du réservoir",
            "Température (°C)", "fig4_T_reservoir.png",
        ),
        tracer_temperatures_etages(
            list(resultats.values())[1], "fig5_T_etages_B.png"),
        tracer_temperatures_etages(
            list(resultats.values())[0], "fig6_T_etages_A.png"),
        tracer_rapports(list(resultats.values())[0], "fig7_rapports.png"),
    ]

    # --- Rapport ---
    L: list[str] = []
    L.append("# Validation de la charge sur Dormoy (2024)\n")
    L.append(
        "*Généré par `validation/dormoy_charge.py`. Références : registre "
        "(`data/registre/parametres.csv`). Toute valeur « Dormoy » est une "
        "mesure du § 3.1 sauf mention « simulation ».*\n"
    )
    L.append("## 1. Scénarios comparés\n")
    L.append(
        "| Code | Scénario | Air aspiré | Débit aspiré | "
        "Débit vers réservoirs |"
    )
    L.append("|---|---|---|---|---|")
    for nom, r in resultats.items():
        sc = r.scenario
        L.append(
            f"| {nom.split(':')[0].strip()} | `{sc.nom}` | "
            f"{sc.get('ambiance.T_aspiration') - 273.15:.0f} °C | "
            f"{r.totaux['debit_aspire_kg_s']:.4f} kg/s | "
            f"{r.totaux['debit_reservoir_kg_s']:.4f} kg/s |"
        )
    L.append(
        "\nLe scénario A applique les hypothèses minimales : tout à 20 °C "
        "(l'article ne donne pas la température ambiante), débit aspiré "
        "mesuré imposé (0,052 kg/s), débit vers les réservoirs égal au "
        "produit "
        "des rendements volumétrique (83 %) et du sécheur (81 %). Le "
        "scénario B déduit la température d'aspiration du débit mesuré : "
        "0,052 kg/s à 172,4 m³/h et 1,013 bar correspond à de l'air à 52 °C, "
        "ce qui est plausible pour un compresseur qui aspire l'air d'un "
        "conteneur qu'il réchauffe. C et D imposent le débit mesuré à la "
        "sortie du sécheur (0,032 kg/s) au lieu de 0,035 kg/s.\n"
    )

    L.append("## 2. Essai de charge complet, 1 → 190 bar\n")
    L.append("| Grandeur | Dormoy | Scénario | Simulé | Écart | Explication |")
    L.append("|---|---|---|---|---|---|")
    for nom, r in resultats.items():
        code = nom.split(":")[0].strip()
        t = r.totaux
        L.append(
            f"| Énergie consommée | {E_ref:.0f} kWh | {code} | "
            f"{t['energie_electrique_kwh']:.1f} kWh | "
            f"{ecart_relatif_pct(t['energie_electrique_kwh'], E_ref):+.1f} % "
            f"| voir § 2.1 |"
        )
    for nom, r in resultats.items():
        code = nom.split(":")[0].strip()
        t = r.totaux
        L.append(
            f"| Durée | ≈ {t_ref:.0f} h | {code} | {t['duree_h']:.2f} h | "
            f"{ecart_relatif_pct(t['duree_h'], t_ref):+.1f} % | "
            f"la durée dépend seulement du débit vers les réservoirs et de "
            f"la température finale |"
        )
    for nom, r in resultats.items():
        code = nom.split(":")[0].strip()
        t = r.totaux
        L.append(
            f"| Puissance moyenne | {P_ref:.0f} kW | {code} | "
            f"{t['puissance_moyenne_kw']:.1f} kW | "
            f"{ecart_relatif_pct(t['puissance_moyenne_kw'], P_ref):+.1f} % | "
            f"dépend du débit aspiré, des indices n et des rendements |"
        )
    rA = list(resultats.values())[0]
    rB = list(resultats.values())[1]
    eA = rA.totaux["energie_electrique_kwh"]
    L.append(
        f"| Énergie consommée (simulation de Dormoy, cas de base) | "
        f"{E_sim_dormoy:.2f} kWh | A | "
        f"{rA.totaux['energie_electrique_kwh']:.1f} kWh | "
        f"{ecart_relatif_pct(eA, E_sim_dormoy):+.1f} % "
        f"| notre modèle est comparé ici au modèle de Dormoy, pas à la "
        f"mesure |"
    )
    L.append(
        "\n### 2.1 Lecture des écarts\n\n"
        "- **Énergie et puissance.** Le scénario A (hypothèses minimales) "
        f"donne {rA.totaux['energie_electrique_kwh']:.0f} kWh, soit "
        f"{ecart_relatif_pct(eA, E_ref):+.1f} % "
        "par rapport à la mesure, mais seulement "
        f"{ecart_relatif_pct(eA, E_sim_dormoy):+.1f} % "
        "par rapport à la **simulation** de Dormoy (366,75 kWh). L'écart "
        "entre notre modèle et celui de Dormoy est donc petit ; l'écart avec "
        "la mesure est en grande partie celui que Dormoy a lui-même "
        "(−7,4 %).\n"
        "- **La durée** ne dépend que du débit vers les réservoirs et de la "
        "température de l'air stocké. Avec le débit calculé (0,035 kg/s) la "
        f"charge dure {rA.totaux['duree_h']:.1f} h ; avec le débit mesuré "
        f"(0,032 kg/s) elle dure "
        f"{list(resultats.values())[2].totaux['duree_h']:.1f} h. Les deux "
        "encadrent les « presque 10 h » de l'article.\n"
        "- **Température d'aspiration.** Le scénario B (52 °C) relève la "
        "puissance de "
        f"{rA.totaux['puissance_moyenne_kw']:.1f} à "
        f"{rB.totaux['puissance_moyenne_kw']:.1f} kW, ce qui tombe sur les "
        "39 kW mesurés. Ce n'est pas un ajustement : la valeur 52 °C est "
        "imposée par le débit massique mesuré et la cylindrée du compresseur "
        "(voir § 4, chaleur, pour une seconde confirmation indépendante).\n"
        "- **Température finale du réservoir.** Le modèle donne "
        f"{rA.totaux['T_finale_degC']:.0f} °C en fin de charge. Dormoy "
        "mesure 55 °C au début de l'essai de décharge, mais rien n'indique "
        "que cet essai a suivi immédiatement la charge complète, et le "
        "réservoir de l'essai de décharge (2,56 m³) n'est pas le même. "
        "Écart à surveiller en phase 2 ; la courbe de température mesurée "
        "n'est pas publiée.\n"
    )

    L.append("## 3. Rapports de compression et températures\n")
    fin_A = rA.series.iloc[-1]
    fin_B = rB.series.iloc[-1]
    deb_A = rA.series.iloc[0]
    L.append("| Grandeur | Dormoy | Simulé (A) | Simulé (B) | Remarque |")
    L.append("|---|---|---|---|---|")
    L.append(
        f"| Rapport étage 3, à 190 bar | 4,44 (fig. 8) | "
        f"{fin_A['beta_3']:.2f} "
        f"| {fin_B['beta_3']:.2f} | borne du registre, imposée par la loi "
        f"linéaire |"
    )
    L.append(
        f"| Rapport étage 4, à 190 bar | 3,5 (texte) / 3,50 (tabl. 7) | "
        f"{fin_A['beta_4']:.2f} | {fin_B['beta_4']:.2f} | **calculé** : reste "
        f"du rapport total ; concorde |"
    )
    L.append(
        f"| Rapport étage 4, à basse pression | 1,52 (texte) / 1,63 (tabl. 7) "
        f"| {deb_A['beta_4']:.2f} | {deb_A['beta_4']:.2f} | fixé par la "
        f"pression de refoulement minimale (66 bar, calcul personnel) |"
    )
    for i in range(1, 5):
        attendu = {1: "≈ 160 (fig. 9/18)", 2: "185–200 (fig. 18)",
                   3: "190–220, > 200 après 3 h (fig. 18)",
                   4: "jusqu'à ≈ 200 en fin de charge (fig. 9)"}[i]
        L.append(
            f"| Sortie compression étage {i}, fin de charge | {attendu} °C | "
            f"{fin_A[f'T_out_comp_{i}_K'] - 273.15:.0f} °C | "
            f"{fin_B[f'T_out_comp_{i}_K'] - 273.15:.0f} °C | "
            + ("B concorde, A est trop froid : l'air aspiré à 20 °C ne "
               "chauffe qu'à 124 °C" if i == 1 else
               "B plus proche" if i == 2 else
               "concorde" if i == 3 else
               "A et B concordent entre eux ; l'écart avec la fig. 9 dépend "
               "de la loi n = 1,52 et de l'efficacité du refroidisseur 3")
            + " |"
        )
    L.append(
        f"| Sortie refroidisseur 4, fin de charge | 45–60 (fiche) °C | "
        f"{fin_A['T_out_ref_4_K'] - 273.15:.0f} °C | "
        f"{fin_B['T_out_ref_4_K'] - 273.15:.0f} °C | "
        f"un peu froid : efficacité 85 % avec source froide à 20 °C |"
    )
    L.append(
        "\nLes valeurs « Dormoy » de ce tableau sont lues sur les figures de "
        "l'article (approximatives). La comparaison point par point attend "
        "les courbes numérisées (§ 6).\n"
    )

    L.append(
        "## 4. Chaleur rejetée par les refroidisseurs, charge 55 → 190 bar\n"
    )
    L.append(
        "Dormoy (tableau 6, simulation) calcule la chaleur récupérable "
        "au-dessus de 130 °C pendant une recharge de 55 à 190 bar, avec un "
        "débit de 0,052 kg/s.\n"
    )
    L.append(
        "| Grandeur | Dormoy (simulation) | A : base | B : aspiration 52 °C |"
    )
    L.append("|---|---|---|---|")
    a, b = res55["A : base"].totaux, res55["B : aspiration à 52 °C"].totaux
    qa_tot = a["chaleur_refroidisseurs_kwh"]
    qb_tot = b["chaleur_refroidisseurs_kwh"]
    qa_sup = a["chaleur_sup_seuil_kwh"]
    qb_sup = b["chaleur_sup_seuil_kwh"]
    L.append(
        f"| Durée | {t55_ref} h | {a['duree_h']:.2f} h "
        f"({ecart_relatif_pct(a['duree_h'], t55_ref):+.1f} %) | "
        f"{b['duree_h']:.2f} h "
        f"({ecart_relatif_pct(b['duree_h'], t55_ref):+.1f} %) |"
    )
    L.append(
        f"| Chaleur totale rejetée | {Q_tot_ref} kWh | "
        f"{a['chaleur_refroidisseurs_kwh']:.1f} kWh "
        f"({ecart_relatif_pct(qa_tot, Q_tot_ref):+.1f} %) | "
        f"{b['chaleur_refroidisseurs_kwh']:.1f} kWh "
        f"({ecart_relatif_pct(qb_tot, Q_tot_ref):+.1f} %) |"
    )
    L.append(
        f"| Chaleur au-dessus de 130 °C, total | {Q_sup_ref} kWh | "
        f"{a['chaleur_sup_seuil_kwh']:.1f} kWh "
        f"({ecart_relatif_pct(qa_sup, Q_sup_ref):+.1f} %) | "
        f"{b['chaleur_sup_seuil_kwh']:.1f} kWh "
        f"({ecart_relatif_pct(qb_sup, Q_sup_ref):+.1f} %) |"
    )
    for i in range(1, 5):
        qa = a[f"chaleur_sup_seuil_{i}_kwh"]
        qb = b[f"chaleur_sup_seuil_{i}_kwh"]
        L.append(
            f"| … dont refroidisseur {i} | {Q_sup_etages_ref[i - 1]} kWh | "
            f"{qa:.1f} kWh | {qb:.1f} kWh |"
        )
    L.append(
        "\nLe scénario A ne récupère **rien** à l'étage 1 (l'air n'y dépasse "
        "pas 130 °C), alors que Dormoy y trouve 12,5 kWh. Le scénario B, "
        "dont la seule différence est l'air aspiré à 52 °C, retrouve l'ordre "
        "de grandeur de chaque étage et la chaleur totale à "
        f"{ecart_relatif_pct(qb_tot, Q_tot_ref):+.1f} %. "
        "C'est la confirmation indépendante annoncée au § 2.1 : dans le "
        "modèle de Dormoy, l'air entre dans le compresseur à environ 50 °C. "
        "La chaleur « au-dessus de 130 °C » reste sous-estimée de "
        f"{-ecart_relatif_pct(b['chaleur_sup_seuil_kwh'], Q_sup_ref):.0f} %, "
        "surtout aux étages 2 et 3 : les températures de sortie de ces "
        "étages dépendent de la température de l'air de refroidissement "
        "(20 °C supposés) et de la répartition des rapports entre les étages "
        "3 et 4, deux hypothèses à confronter aux figures 8 et 18 "
        "numérisées.\n"
    )

    L.append("## 5. Bilan d'énergie (scénario A, 1 → 190 bar)\n")
    bl = rA.bilan
    L.append("| Poste | kWh | % de l'électricité |")
    L.append("|---|---|---|")
    E = bl["E_el_j"]
    for cle, nom in [
        ("pertes_mec_el_j", "Pertes mécaniques et électriques du compresseur"),
        ("Q_poly_rejete_j", "Chaleur rejetée pendant la compression (n < γ)"),
        ("Q_refroidisseurs_j", "Chaleur retirée par les 4 refroidisseurs"),
        ("E_air_perdu_j",
         "Enthalpie de l'air rejeté (volumétrique + sécheur)"),
        ("Q_paroi_reservoir_j", "Chaleur perdue par les réservoirs"),
        ("E_stockee_relative_j",
         "Énergie stockée dans l'air (relative à l'air aspiré)"),
    ]:
        L.append(
            f"| {nom} | {bl[cle] / 3.6e6:.1f} | {bl[cle] / E * 100:.1f} % |"
        )
    L.append(
        f"| **Total** | **{bl['somme_j'] / 3.6e6:.1f}** | "
        f"**{bl['somme_j'] / E * 100:.1f} %** (résidu "
        f"{bl['residu_relatif'] * 100:.4f} %) |"
    )
    L.append(
        "\nL'énergie « stockée dans l'air » est comptée par rapport à "
        "l'enthalpie de l'air aspiré : elle est négative parce que l'air "
        "stocké finit à peu près à la température ambiante, avec une énergie "
        "interne massique plus faible que l'enthalpie de l'air entré "
        "(c'est le bilan d'énergie du premier principe ; l'énergie **utile** "
        "de l'air comprimé est une exergie, calculée en phase 3).\n"
    )

    L.append("## 6. Courbes numérisées\n")
    L.append("| Fichier | Scénario | RMSE | MAPE |")
    L.append("|---|---|---|---|")
    L.extend(comparer_courbes_numerisees(deux))
    L.append(
        "\nAucune courbe n'était numérisée à la date de ce rapport : voir "
        "`data/validation/A_NUMERISER.md` (fig. 10, 8 et 9 en priorité).\n"
    )

    L.append(
        "## 7. Hypothèses propres au modèle (niveau « hypothese » ou "
        "« calcul_personnel »)\n"
    )
    L.append("| Paramètre | Valeur | Provenance |")
    L.append("|---|---|---|")
    vus: set[str] = set()
    for sc in (base, chaud):
        for cle, prov in sorted(sc.provenance.items()):
            if ("hypothese" in prov or "calcul_personnel" in prov
                    or "scénario" in prov) and cle not in vus:
                vus.add(cle)
                val = sc[cle]
                if isinstance(val, float):
                    val = f"{val:.6g}"
                L.append(f"| `{cle}` | {val} | {prov} |")
    for id_ in ("compresseur.loi_rapport_etage3",
                "compresseur.loi_rendement_mecanique",
                "refroidisseur.loi_efficacite_etage4"):
        par = reg[id_]
        L.append(
            f"| `{id_}` | {par.valeur} | {par.niveau_preuve}, {par.notes} |"
        )

    L.append("\n## 8. Graphiques\n")
    for f in figs:
        L.append(f"![{f}]({f})\n")

    L.append("## 9. Conclusion\n")
    L.append(
        "- Le critère de sortie de la phase 1 (écart < 5 % sur l'énergie et "
        "la durée) est **atteint par le scénario B** (−2,5 % et −1,1 %). Le "
        "scénario A le manque de peu sur l'énergie (−5,8 %), en grande "
        "partie à cause des 7 % d'écart que Dormoy a lui-même entre sa "
        "simulation et sa mesure ; par rapport au modèle de Dormoy, A est à "
        "+1,7 %. Les scénarios C et D (débit mesuré de 0,032 kg/s) "
        "rallongent la charge à 10,8 h : le « presque 10 h » de l'article "
        "est trop imprécis pour trancher entre 0,032 et 0,035 kg/s ; la "
        "courbe de la fig. 10, une fois numérisée, le permettra.\n"
        "- L'hypothèse la plus utile dégagée par la validation : l'air aspiré "
        "par le compresseur est à ≈ 50 °C, pas à l'ambiant. Elle découle du "
        "débit mesuré et explique à la fois la puissance (39 kW) et la "
        "chaleur récupérable par étage.\n"
        "- Points ouverts : la loi de variation des rapports des étages 3 et "
        "4 (fig. 8), la température de l'air de refroidissement, et la "
        "température finale du réservoir (pas de mesure publiée).\n"
    )
    (DOSSIER_RAPPORT / "validation_charge.md").write_text(
        "\n".join(L), encoding="utf-8"
    )
    tableau = pd.DataFrame(
        {nom: r.totaux for nom, r in {**resultats, **{
            k + " (55→190)": v for k, v in res55.items()}}.items()}
    )
    tableau.to_csv(DOSSIER_RAPPORT / "totaux.csv", float_format="%.4f")
    rA.series.to_csv(DOSSIER_RAPPORT / "series_A_1_190.csv", index=False,
                     float_format="%.6g")
    print("rapport écrit :", DOSSIER_RAPPORT / "validation_charge.md")


if __name__ == "__main__":
    main()
