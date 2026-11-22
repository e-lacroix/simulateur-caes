# -*- coding: utf-8 -*-
"""Validation de la décharge sur Dormoy (2024), phase 2.

    python validation/dormoy_decharge.py

Écrit ``rapports/phase2/validation_decharge.md`` et ses graphiques :

1. essai de décharge mesuré (190 → 50 bar, 38 min) ;
2. cas de base simulé (1 étage, 16,93 kWh) et diagnostics ;
3. cas à 3 étages avec réchauffage (tableau 5, 16 %) ;
4. tendances des figures 11 à 16 (température ambiante, pression
   maximale, indice polytropique, nombre d'étages).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style_graphiques import (  # noqa: E402
    COULEURS,
    ENCRE_2,
    etiquette_fin,
    nouvelle_figure,
    point_reference,
    style_axes,
    terminer,
)

from caes.metriques import ecart_relatif_pct  # noqa: E402
from caes.registre import Registre  # noqa: E402
from caes.scenario import Scenario, charger_scenario  # noqa: E402
from caes.systeme import (  # noqa: E402
    ResultatCharge,
    ResultatDecharge,
    rendements_aller_retour,
    simuler_charge,
    simuler_decharge,
)

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "rapports" / "phase2"
T0C = 273.15


def pct(sim: float, ref: float) -> str:
    return f"{ecart_relatif_pct(sim, ref):+.1f} %"


def charge_depuis(
    base: Scenario, p0_pa: float, suffixe: str, **mods: object
) -> ResultatCharge:
    m: dict[str, object] = {"reservoir.p_initiale": p0_pa}
    m.update(mods)
    return simuler_charge(base.avec(m, suffixe))


def decharge_depuis_charge(
    sc: Scenario, charge: ResultatCharge, suffixe: str, **mods: object
) -> ResultatDecharge:
    """Décharge qui part de l'état final de la charge (p, T air, paroi)."""
    T_fin = charge.series["T_res_K"].iloc[-1]
    m: dict[str, object] = {
        "reservoir.p_initiale": charge.series["p_res_pa"].iloc[-1],
        "reservoir.T_initiale": T_fin,
        "reservoir.T_paroi_initiale": charge.series["T_paroi_K"].iloc[-1],
    }
    m.update(mods)
    return simuler_decharge(sc.avec(m, suffixe))


def tracer_essai(r_iso: ResultatDecharge, r_ch: ResultatDecharge) -> list[str]:
    noms = []
    fig, ax = nouvelle_figure()
    t = r_iso.series["t_s"] / 60.0
    ax.plot(t, r_iso.series["p_res_pa"] / 1e5, color=COULEURS[0],
            linewidth=2, label="pression du réservoir (simulée)")
    etiquette_fin(ax, t.iloc[-1], r_iso.series["p_res_pa"].iloc[-1] / 1e5,
                  "arrêt à 50 bar", COULEURS[0])
    point_reference(ax, 38.0, 50.0, "Dormoy : 50 bar atteints à 38 min")
    style_axes(ax, "Essai de décharge mesuré : 2,56 m³, 190 → 50 bar",
               "Temps (min)", "Pression absolue (bar)")
    noms.append(terminer(fig, ax, DOSSIER / "fig1_essai_pression.png"))

    fig, ax = nouvelle_figure()
    series = [
        ("air du réservoir", r_iso.series["T_res_K"], COULEURS[0], "-"),
        ("paroi des réservoirs", r_iso.series["T_paroi_K"], COULEURS[1],
         "-"),
        ("sortie du détendeur, isenthalpique",
         r_iso.series["T_sortie_detendeur_K"], COULEURS[2], "-"),
        ("sortie du détendeur, Cheayb",
         r_ch.series["T_sortie_detendeur_K"], COULEURS[3], (0, (4, 4))),
    ]
    for nom, y, c, style in series:
        ax.plot(t, y - T0C, color=c, linewidth=2, label=nom, linestyle=style)
        if "Cheayb" not in nom:
            texte = nom if "détendeur" not in nom else "sortie du détendeur"
            etiquette_fin(ax, t.iloc[-1], y.iloc[-1] - T0C, texte, c)
    style_axes(ax, "Essai de décharge : températures (aucune courbe "
               "mesurée publiée ; MAPE de Dormoy ≤ 1,1 %)",
               "Temps (min)", "Température (°C)")
    noms.append(terminer(fig, ax, DOSSIER / "fig2_essai_temperatures.png",
                         "upper right"))
    return noms


def tracer_3etages(r: ResultatDecharge) -> list[str]:
    noms = []
    fig, ax = nouvelle_figure()
    t = r.series["t_s"] / 60.0
    for i, c in zip((1, 2, 3), COULEURS):
        y = r.series[f"Q_rech_{i}_w"] / 1e3
        ax.plot(t, y, color=c, linewidth=2, label=f"réchauffage étage {i}")
        etiquette_fin(ax, t.iloc[-1], y.iloc[-1], f"étage {i}", c)
    point_reference(ax, 20.0, 35.75,
                    "Dormoy, tableau 5 : 33,5–38,0 / 9,6 / 22,5 kW")
    ax.plot([20.0, 20.0], [9.6, 22.5], marker="D", ms=7, color="#0b0b0b",
            mec="#fcfcfb", mew=1.5, linestyle="none")
    style_axes(ax, "Puissance de réchauffage avant chaque étage de turbine "
               "(source : externe)", "Temps (min)", "Puissance thermique (kW)")
    noms.append(terminer(fig, ax, DOSSIER / "fig3_3etages_chaleur.png"))

    fig, ax = nouvelle_figure()
    for i, c in zip((1, 2, 3), COULEURS):
        y = r.series[f"T_out_turb_{i}_K"] - T0C
        ax.plot(t, y, color=c, linewidth=2, label=f"sortie turbine {i}")
        etiquette_fin(ax, t.iloc[-1], y.iloc[-1], f"sortie {i}", c)
    y = r.series["T_sortie_detendeur_K"] - T0C
    ax.plot(t, y, color=COULEURS[3], linewidth=2,
            label="sortie du détendeur (avant réchauffage 1)")
    etiquette_fin(ax, t.iloc[-1], y.iloc[-1], "détendeur", COULEURS[3])
    style_axes(ax, "Températures dans la chaîne de détente à 3 étages",
               "Temps (min)", "Température (°C)")
    noms.append(terminer(fig, ax, DOSSIER / "fig4_3etages_temperatures.png"))
    return noms


def tracer_tendance(
    x: list[float], courbes: dict[str, list[float]], titre: str,
    xlabel: str, ylabel: str, fichier: str,
    references: list[tuple[float, float, str]] | None = None,
) -> str:
    fig, ax = nouvelle_figure()
    for (nom, y), c in zip(courbes.items(), COULEURS):
        ax.plot(x, y, color=c, linewidth=2, marker="o", ms=5, label=nom)
        etiquette_fin(ax, x[-1], y[-1], nom, c)
    for xr, yr, texte in references or []:
        point_reference(ax, xr, yr, texte)
    style_axes(ax, titre, xlabel, ylabel)
    return terminer(fig, ax, DOSSIER / fichier)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    L: list[str] = []

    # ------------------------------------------------------------------
    # 1. Essai mesuré
    # ------------------------------------------------------------------
    sc_essai = charger_scenario("v1/dormoy_decharge_essai.yaml", reg)
    r_iso = simuler_decharge(sc_essai)
    r_ch = simuler_decharge(sc_essai.avec({"detendeur.modele": "cheayb"},
                                          "cheayb"))
    r_Kg = simuler_decharge(sc_essai.avec(
        {"reservoir.modele_thermique": "K_global"}, "K_global"))
    r_Tp20 = simuler_decharge(sc_essai.avec(
        {"reservoir.T_paroi_initiale": 293.15}, "paroi20"))
    duree_ref = reg["essai_decharge.duree"].valeur
    dT_jt = (r_iso.series["T_res_K"].mean()
             - r_iso.series["T_sortie_detendeur_K"].mean())
    dT_ch = abs(r_ch.totaux["T_sortie_detendeur_moyenne_degC"]
                - r_iso.totaux["T_sortie_detendeur_moyenne_degC"])
    print("essai :", r_iso.resume())
    L.append("# Validation de la décharge sur Dormoy (2024)\n")
    L.append(
        "*Généré par `validation/dormoy_decharge.py`. Références : registre "
        "(`data/registre/parametres.csv`).*\n"
    )
    L.append("## 1. Essai de décharge mesuré (§ 3.1)\n")
    L.append(
        "2,56 m³ (8 réservoirs de 320 L) à 190 bar et 55 °C, détendeur à "
        "35 bar, débit mesuré de 0,148 kg/s imposé, arrêt à 50 bar. Modèle "
        "thermique « paroi » (h_int = 25,42 et h_ext = 2,47 W/m²K calibrés "
        "par Dormoy sur cet essai), paroi initialement à 55 °C (hypothèse).\n"
    )
    L.append("| Grandeur | Dormoy | Simulé | Écart | Remarque |")
    L.append("|---|---|---|---|---|")
    L.append(
        f"| Durée jusqu'à 50 bar | {duree_ref:.0f} min | "
        f"{r_iso.totaux['duree_min']:.1f} min | "
        f"{pct(r_iso.totaux['duree_min'], duree_ref)} | la durée ne dépend "
        f"que de la masse soutirée, donc de la température de l'air |"
    )
    L.append(
        f"| Durée, paroi initiale à 20 °C | {duree_ref:.0f} min | "
        f"{r_Tp20.totaux['duree_min']:.1f} min | "
        f"{pct(r_Tp20.totaux['duree_min'], duree_ref)} | la chaleur stockée "
        f"dans la structure compte (remarque de Dormoy, § 3.2) |"
    )
    L.append(
        f"| Durée, modèle « K global » (charge) | {duree_ref:.0f} min | "
        f"{r_Kg.totaux['duree_min']:.1f} min | "
        f"{pct(r_Kg.totaux['duree_min'], duree_ref)} | sans la capacité "
        f"thermique de la paroi, l'air se refroidit plus |"
    )
    L.append(
        f"| Masse soutirée | – | {r_iso.totaux['masse_soutiree_kg']:.0f} kg "
        f"| – | 0,148 kg/s × durée |"
    )
    L.append(
        f"| Température de l'air en fin d'essai | non publiée | "
        f"{r_iso.totaux['T_finale_degC']:.1f} °C | – | MAPE de Dormoy sur "
        f"la température du réservoir : 1,10 % |"
    )
    L.append(
        f"| Sortie du détendeur, modèle isenthalpique | MAPE 0,39 % | "
        f"{r_iso.totaux['T_sortie_detendeur_moyenne_degC']:.1f} °C en "
        f"moyenne | – | refroidissement Joule-Thomson : {dT_jt:.1f} K "
        f"sous la température du réservoir |"
    )
    L.append(
        f"| Sortie du détendeur, modèle de Cheayb | MAPE 0,21 % | "
        f"{r_ch.totaux['T_sortie_detendeur_moyenne_degC']:.1f} °C en "
        f"moyenne | – | hors de sa plage de validité (25–150 bar) au-dessus "
        f"de 150 bar ; écart avec l'isenthalpique {dT_ch:.1f} K |"
    )
    L.append(
        "\nLa durée mesurée est retrouvée à 2 % près avec les coefficients "
        "calibrés de Dormoy, sans aucun réglage. Les deux modèles de "
        "détendeur donnent la même température à 1 K près ; comme Dormoy "
        "ne publie pas la courbe mesurée, on ne peut pas les départager.\n"
    )

    # ------------------------------------------------------------------
    # 2. Cas de base
    # ------------------------------------------------------------------
    sc_base = charger_scenario("v1/dormoy_decharge_base.yaml", reg)
    sc_ch_A = charger_scenario("v1/dormoy_charge_1_190.yaml", reg)
    sc_ch_B = charger_scenario(
        "v1/dormoy_charge_1_190_aspiration_chaude.yaml", reg)
    E_ref = reg["cas_base.energie_produite"].valeur
    E_cons_ref = reg["cas_base.energie_consommee"].valeur
    p_arret = reg.si("cas_base.pression_arret")
    r_base = simuler_decharge(sc_base)
    variantes_base = {
        "T₀ = 55 °C (défaut, état mesuré avant décharge)": r_base,
        "T₀ = 20 °C (air à l'ambiant)": simuler_decharge(sc_base.avec(
            {"reservoir.T_initiale": 293.15,
             "reservoir.T_paroi_initiale": 293.15}, "T20")),
        "Diagnostic : détendeur sans refroidissement JT": simuler_decharge(
            sc_base.avec({"detendeur.modele": "isotherme"}, "isoJT")),
        "Diagnostic : réservoir isotherme (h_int → ∞)": simuler_decharge(
            sc_base.avec({"reservoir.h_int": 1e6}, "isoRes")),
        "Diagnostic : les deux": simuler_decharge(sc_base.avec(
            {"detendeur.modele": "isotherme", "reservoir.h_int": 1e6},
            "iso2")),
        "Arrêt à 3 bar au lieu de 18 bar": simuler_decharge(sc_base.avec(
            {"detendeur.ecart_min": 0.0}, "sansMarge")),
    }
    ch_A18 = charge_depuis(sc_ch_A, p_arret, "depuis18")
    ch_B18 = charge_depuis(sc_ch_B, p_arret, "depuis18")
    r_pre = simuler_decharge(sc_base.avec(
        {"turbine.etages.0.T_entree_cible": reg.si(
            "turbine.etage3.temperature_entree")}, "prechauffe"))
    print("base :", r_base.resume())
    L.append("## 2. Cas de base simulé (1 étage, sans réchauffage, § 3.3)\n")
    L.append(
        "Dormoy : « a single-stage expansion device represented by the last "
        "stage of the selected turbine » → étage 3 de la DEPRAG (3 → 1 bar, "
        "n = 1,27, η_méc 73 %, η_él 92 %, 0,321 kg/s). Le détendeur est donc "
        "réglé à 3 bar et la décharge s'arrête à 18 bar (3 + 15). "
        f"Référence : {E_ref} kWh produits pour {E_cons_ref} kWh consommés.\n"
    )
    L.append("| Variante | Énergie produite | Écart | Durée | T moyenne à "
             "l'entrée de la turbine | T finale du réservoir |")
    L.append("|---|---|---|---|---|---|")
    for nom, r in variantes_base.items():
        s = r.series
        L.append(
            f"| {nom} | {r.totaux['energie_electrique_kwh']:.2f} kWh | "
            f"{pct(r.totaux['energie_electrique_kwh'], E_ref)} | "
            f"{r.totaux['duree_min']:.0f} min | "
            f"{s['T_in_turb_1_K'].mean() - T0C:.0f} °C | "
            f"{r.totaux['T_finale_degC']:.0f} °C |"
        )
    E_base = r_base.totaux["energie_electrique_kwh"]
    rte_A = E_base / ch_A18.totaux["energie_electrique_kwh"]
    rte_B = E_base / ch_B18.totaux["energie_electrique_kwh"]
    E_iso2 = variantes_base["Diagnostic : les deux"].totaux[
        "energie_electrique_kwh"]
    gain_marge = variantes_base["Arrêt à 3 bar au lieu de 18 bar"].totaux[
        "energie_electrique_kwh"] - E_base
    rte_pre = (r_pre.totaux["energie_electrique_kwh"]
               / ch_A18.totaux["energie_electrique_kwh"] * 100)
    L.append(
        "\n### 2.1 Lecture\n\n"
        f"- Le modèle donne **{r_base.totaux['energie_electrique_kwh']:.1f} "
        f"kWh**, soit {pct(r_base.totaux['energie_electrique_kwh'], E_ref)} "
        "par rapport aux 16,93 kWh de Dormoy. **Cet écart n'est pas "
        "expliqué.** Il ne dépend pas de la température initiale (une "
        "décharge plus chaude soutire moins de masse, ce qui compense), ni "
        "du modèle thermique.\n"
        "- Les diagnostics montrent d'où vient l'énergie manquante : le "
        "refroidissement Joule-Thomson dans le détendeur (190 → 3 bar) et "
        "le refroidissement de l'air qui se détend dans le réservoir "
        "coûtent chacun environ 1,4 kWh. En supprimant artificiellement les "
        f"deux, on obtient "
        f"{E_iso2:.1f} kWh, "
        "proche de la valeur de Dormoy. Son modèle contient pourtant ces "
        "deux effets (détendeur isenthalpique validé, bilan du réservoir "
        "validé en décharge). Hypothèses restantes : état initial différent, "
        "ou détail du modèle de turbine non publié (par exemple le travail "
        "calculé avec les températures nominales du tableau 9 plutôt "
        "qu'avec la température réelle d'entrée).\n"
        "- Sans la marge de 15 bar du détendeur (arrêt à 3 bar), on "
        f"gagnerait {gain_marge:.1f} "
        "kWh : c'est la « masse morte » du cas de base, bien plus petite que "
        "celle supposée dans la fiche Dormoy (section 4), qui prenait un "
        "arrêt à 50 bar. À corriger dans le tableau « 1000 unités » "
        "(phase 3).\n"
        "- L'air sort de la turbine à "
        f"{r_base.totaux['T_rejet_min_degC']:.0f} °C au plus froid : sans "
        "réchauffage, le givrage est certain (Dormoy l'évoque pour "
        "justifier le sécheur).\n"
        f"- Rendement aller-retour : {rte_A * 100:.1f} % avec la charge A "
        f"({ch_A18.totaux['energie_electrique_kwh']:.0f} kWh de 18 à 190 "
        f"bar) et {rte_B * 100:.1f} % avec la charge B "
        f"({ch_B18.totaux['energie_electrique_kwh']:.0f} kWh). Dormoy : "
        "4,3 % (16,93 / 396) ou 4,6 % (16,93 / 366,75). Avec réchauffage à "
        f"90 °C (fig. 16, 1 étage) : "
        f"{r_pre.totaux['energie_electrique_kwh']:.1f} kWh, soit "
        f"{rte_pre:.1f} % (Dormoy : 5,5 %).\n"
    )

    # ------------------------------------------------------------------
    # 3. Trois étages
    # ------------------------------------------------------------------
    sc3 = charger_scenario("v1/dormoy_decharge_3etages.yaml", reg)
    r3 = simuler_decharge(sc3)
    r3_20 = simuler_decharge(sc3.avec(
        {"reservoir.T_initiale": 293.15, "reservoir.T_paroi_initiale": 293.15},
        "T20"))
    ch55_A = simuler_charge(charger_scenario("v1/dormoy_charge_55_190.yaml", reg))
    ch55_B = simuler_charge(charger_scenario(
        "v1/dormoy_charge_55_190.yaml", reg).avec(
        {"compresseur.debit_massique_aspire": None,
         "ambiance.T_aspiration": sc_ch_B["ambiance.T_aspiration"]},
        "aspiration_chaude"))
    rte3_A = rendements_aller_retour(ch55_A, r3)
    rte3_B = rendements_aller_retour(ch55_B, r3)
    rte3_20_A = (r3_20.totaux["energie_electrique_kwh"]
                 / ch55_A.totaux["energie_electrique_kwh"] * 100)
    Q_ref = [reg[f"turbine.etage{i}.energie_chaleur_requise"].valeur
             for i in (1, 2, 3)]
    Q_tot_ref = reg["turbine.energie_chaleur_requise_totale"].valeur
    d3_ref = reg["decharge_3etages.duree"].valeur
    rte3_ref = reg["cas_etages.rte_3etages_prechauffe"].valeur
    Ec3_ref = reg["cas_etages.energie_consommee_3etages"].valeur
    P_nom = reg["turbine.puissance_electrique_totale"].valeur
    print("3 étages :", r3.resume())
    L.append("## 3. Turbine à 3 étages avec réchauffage (§ 3.3.4 et 3.3.5)\n")
    L.append(
        "Décharge de 190 à 55 bar, turbine DEPRAG complète, air réchauffé à "
        "130 / 90 / 90 °C par une source **externe** (comme Dormoy, qui ne "
        "la compte pas dans le rendement). État initial : 55 °C (air et "
        "paroi).\n"
    )
    L.append("| Grandeur | Dormoy (simulation) | Simulé, T₀ = 55 °C | "
             "Simulé, T₀ = 20 °C | Écart (55 °C) |")
    L.append("|---|---|---|---|---|")
    L.append(
        f"| Durée de la décharge | {d3_ref:.0f} min | "
        f"{r3.totaux['duree_min']:.1f} min | {r3_20.totaux['duree_min']:.1f} "
        f"min | {pct(r3.totaux['duree_min'], d3_ref)} |"
    )
    L.append(
        f"| Chaleur de réchauffage, total | {Q_tot_ref} kWh | "
        f"{r3.totaux['chaleur_rechauffage_kwh']:.1f} kWh | "
        f"{r3_20.totaux['chaleur_rechauffage_kwh']:.1f} kWh | "
        f"{pct(r3.totaux['chaleur_rechauffage_kwh'], Q_tot_ref)} |"
    )
    for i in (1, 2, 3):
        L.append(
            f"| … avant l'étage {i} | {Q_ref[i - 1]} kWh | "
            f"{r3.totaux[f'chaleur_rechauffage_{i}_kwh']:.1f} kWh | "
            f"{r3_20.totaux[f'chaleur_rechauffage_{i}_kwh']:.1f} kWh | "
            f"{pct(r3.totaux[f'chaleur_rechauffage_{i}_kwh'], Q_ref[i - 1])} |"
        )
    L.append(
        f"| Température avant le réchauffage 1 (implicite dans le tableau 5 : "
        f"13 à 27 °C) | 13–27 °C | "
        f"{r3.series['T_sortie_detendeur_K'].iloc[-1] - T0C:.0f} à "
        f"{r3.series['T_sortie_detendeur_K'].iloc[0] - T0C:.0f} °C | "
        f"{r3_20.series['T_sortie_detendeur_K'].iloc[-1] - T0C:.0f} à "
        f"{r3_20.series['T_sortie_detendeur_K'].iloc[0] - T0C:.0f} °C | "
        f"concorde à 55 °C |"
    )
    L.append(
        f"| Puissance électrique | {P_nom} kW (tableau 9) | "
        f"{r3.totaux['puissance_electrique_moyenne_kw']:.1f} kW | "
        f"{r3_20.totaux['puissance_electrique_moyenne_kw']:.1f} kW | "
        f"{pct(r3.totaux['puissance_electrique_moyenne_kw'], P_nom)} |"
    )
    L.append(
        f"| Énergie produite | 16 % × {Ec3_ref:.0f} = "
        f"{rte3_ref / 100 * Ec3_ref:.1f} kWh ; ou {P_nom} kW × {d3_ref:.0f} "
        f"min = {P_nom * d3_ref / 60:.1f} kWh | "
        f"{r3.totaux['energie_electrique_kwh']:.1f} kWh | "
        f"{r3_20.totaux['energie_electrique_kwh']:.1f} kWh | "
        f"{pct(r3.totaux['energie_electrique_kwh'], P_nom * d3_ref / 60)} "
        f"(contre 62 kW × 40 min) |"
    )
    L.append(
        f"| Énergie consommée, recharge 55 → 190 bar | {Ec3_ref:.0f} kWh | "
        f"A : {ch55_A.totaux['energie_electrique_kwh']:.0f} kWh ; B : "
        f"{ch55_B.totaux['energie_electrique_kwh']:.0f} kWh | idem | "
        f"{pct(ch55_B.totaux['energie_electrique_kwh'], Ec3_ref)} (B) |"
    )
    L.append(
        f"| RTE sans compter la chaleur (définition de Dormoy) | "
        f"{rte3_ref} % | A : {rte3_A['rte_sans_chaleur'] * 100:.1f} % ; "
        f"B : {rte3_B['rte_sans_chaleur'] * 100:.1f} % | "
        f"A : {rte3_20_A:.1f} % | – |"
    )
    L.append(
        f"| RTE en comptant la chaleur externe | non calculé par Dormoy | "
        f"A : {rte3_A['rte_avec_chaleur_externe'] * 100:.1f} % ; "
        f"B : {rte3_B['rte_avec_chaleur_externe'] * 100:.1f} % | – | – |"
    )
    L.append(
        "\n### 3.1 Lecture\n\n"
        "- **La chaleur de réchauffage du tableau 5 est reproduite étage "
        "par étage** (écarts de quelques pour cent) quand l'air part de "
        "55 °C, l'état mesuré au début de l'essai de décharge. Avec un "
        "départ à 20 °C, l'air arrive trop froid au premier réchauffeur et "
        "la chaleur de l'étage 1 est surestimée de 50 %. C'est ce qui a fixé "
        "l'hypothèse « 55 °C » du registre "
        "(`cas_base.temperature_initiale_decharge`).\n"
        "- **Incohérence relevée chez Dormoy.** Avec la turbine à sa "
        f"puissance nominale ({P_nom} kW) pendant les {d3_ref:.0f} min du "
        f"tableau 5, l'énergie produite vaut {P_nom * d3_ref / 60:.1f} kWh, "
        f"soit {P_nom * d3_ref / 60 / Ec3_ref * 100:.1f} % de 290 kWh, et "
        "non 16,0 %. Le 16 % suppose 45 min de décharge, ou une "
        "consommation de 258 kWh. Notre résultat "
        f"({rte3_B['rte_sans_chaleur'] * 100:.1f} % avec la charge B) se "
        "situe entre les deux lectures.\n"
        "- **La chaleur externe compte.** Si on l'ajoute au dénominateur, "
        f"le rendement tombe à {rte3_B['rte_avec_chaleur_externe'] * 100:.1f} "
        "%. Cette chaleur ne devient « gratuite » que si elle vient des "
        "refroidisseurs du compresseur (phases 4 et 5), qui en rejettent "
        "191 kWh pendant la recharge, dont 66 kWh au-dessus de 130 °C "
        "(phase 1).\n"
    )

    # ------------------------------------------------------------------
    # 4. Tendances (fig. 11 à 16)
    # ------------------------------------------------------------------
    L.append("## 4. Tendances de l'analyse paramétrique (fig. 11 à 16)\n")
    L.append(
        "Chaque point enchaîne une charge (modèle de la phase 1) et une "
        "décharge qui part de l'état final de la charge (pression, "
        "température de l'air et de la paroi). Les courbes « avec "
        "réchauffage » chauffent l'air à 90 °C avant l'étage unique. La "
        "charge part de la pression d'arrêt de la décharge (18 bar pour un "
        "étage).\n"
    )
    figs_t: list[str] = []

    # 4.1 Température ambiante
    T_ambs = [-15.0, -5.0, 5.0, 15.0, 25.0]
    lignes_T: list[dict[str, float]] = []
    for Ta in T_ambs:
        TK = Ta + T0C
        ch = charge_depuis(
            sc_ch_A, p_arret, f"Tamb{Ta:g}",
            **{"ambiance.T_amb": TK, "ambiance.T_aspiration": TK,
               "reservoir.T_initiale": TK,
               "compresseur.debit_massique_aspire": None})
        d0 = decharge_depuis_charge(
            sc_base, ch, f"Tamb{Ta:g}", **{"ambiance.T_amb": TK})
        d1 = decharge_depuis_charge(
            sc_base, ch, f"Tamb{Ta:g}p",
            **{"ambiance.T_amb": TK,
               "turbine.etages.0.T_entree_cible": 363.15})
        lignes_T.append({
            "T_amb": Ta,
            "debit": ch.totaux["debit_aspire_kg_s"],
            "E_cons": ch.totaux["energie_electrique_kwh"],
            "duree_charge": ch.totaux["duree_h"],
            "E_sans": d0.totaux["energie_electrique_kwh"],
            "E_avec": d1.totaux["energie_electrique_kwh"],
            "rte_sans": d0.totaux["energie_electrique_kwh"]
            / ch.totaux["energie_electrique_kwh"] * 100,
            "rte_avec": d1.totaux["energie_electrique_kwh"]
            / ch.totaux["energie_electrique_kwh"] * 100,
        })
    dfT = pd.DataFrame(lignes_T)
    L.append("### 4.1 Température ambiante (fig. 11 et 12)\n")
    L.append("| T ambiante | Débit aspiré | Énergie de charge | Durée de "
             "charge | Produit sans réchauffage | Produit avec | RTE sans | "
             "RTE avec |")
    L.append("|---|---|---|---|---|---|---|---|")
    for _, l in dfT.iterrows():
        L.append(
            f"| {l.T_amb:.0f} °C | {l.debit:.3f} kg/s | {l.E_cons:.0f} kWh | "
            f"{l.duree_charge:.1f} h | {l.E_sans:.1f} kWh | {l.E_avec:.1f} "
            f"kWh | {l.rte_sans:.1f} % | {l.rte_avec:.1f} % |"
        )
    L.append(
        "\nDormoy : débit 0,065 → 0,056 kg/s, énergie produite avec "
        "réchauffage 27 → 22 kWh, RTE avec réchauffage 6,3 → 5,4 %, durée "
        "de charge 595 min à 25 °C, RTE sans réchauffage à peu près "
        "constant. Les tendances sont retrouvées ; les niveaux dépendent de "
        "l'écart du cas de base (§ 2).\n"
    )
    figs_t.append(tracer_tendance(
        T_ambs,
        {"avec réchauffage à 90 °C": list(dfT.rte_avec),
         "sans réchauffage": list(dfT.rte_sans)},
        "Rendement aller-retour selon la température ambiante (fig. 12)",
        "Température ambiante (°C)", "RTE (%)", "fig5_tendance_Tamb.png",
        [(-15.0, 6.3, "Dormoy, avec réchauffage : 6,3 % → 5,4 %"),
         (25.0, 5.4, "")],
    ))

    # 4.2 Pression maximale
    p_maxs = [75.0, 100.0, 125.0, 150.0, 190.0, 250.0, 300.0]
    p_amb = reg.si("essai_charge.pression_initiale")
    lignes_p: list[dict[str, float]] = []
    for pm in p_maxs:
        ch = charge_depuis(sc_ch_B, p_arret, f"p{pm:g}",
                           **{"simulation.p_cible": pm * 1e5})
        ch1 = charge_depuis(sc_ch_B, p_amb, f"p{pm:g}_1bar",
                            **{"simulation.p_cible": pm * 1e5})
        d0 = decharge_depuis_charge(sc_base, ch, f"p{pm:g}")
        d1 = decharge_depuis_charge(
            sc_base, ch, f"p{pm:g}p",
            **{"turbine.etages.0.T_entree_cible": 363.15})
        E_sans = d0.totaux["energie_electrique_kwh"]
        E_avec = d1.totaux["energie_electrique_kwh"]
        E_cyc = ch.totaux["energie_electrique_kwh"]
        E_1b = ch1.totaux["energie_electrique_kwh"]
        lignes_p.append({
            "p_max": pm, "E_cons": E_cyc, "E_cons_1bar": E_1b,
            "P_comp": ch.series["P_el_w"].iloc[-1] / 1e3,
            "E_sans": E_sans, "E_avec": E_avec,
            "rte_sans": E_sans / E_cyc * 100,
            "rte_avec": E_avec / E_cyc * 100,
            "rte_sans_1bar": E_sans / E_1b * 100,
            "rte_avec_1bar": E_avec / E_1b * 100,
        })
    dfp = pd.DataFrame(lignes_p)
    L.append("### 4.2 Pression maximale de stockage (fig. 13)\n")
    L.append(
        "Deux conventions pour l'énergie consommée : la recharge depuis la "
        "pression d'arrêt (18 bar, cycle réel) ou depuis 1 bar (« full "
        "capacity », convention du cas de base de Dormoy, dont les 366,75 "
        "kWh partent de la pression atmosphérique).\n"
    )
    L.append("| p max | Charge depuis 18 bar | Charge depuis 1 bar | "
             "Puissance en fin de charge | Produit sans | Produit avec | "
             "RTE sans (18 bar) | RTE avec (18 bar) | RTE sans (1 bar) | "
             "RTE avec (1 bar) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for _, l in dfp.iterrows():
        L.append(
            f"| {l.p_max:.0f} bar | {l.E_cons:.0f} kWh | {l.E_cons_1bar:.0f} "
            f"kWh | {l.P_comp:.1f} kW | {l.E_sans:.1f} kWh | {l.E_avec:.1f} "
            f"kWh | {l.rte_sans:.2f} % | {l.rte_avec:.2f} % | "
            f"{l.rte_sans_1bar:.2f} % | {l.rte_avec_1bar:.2f} % |"
        )
    i_sans = int(dfp.rte_sans_1bar.idxmax())
    i_avec = int(dfp.rte_avec_1bar.idxmax())
    L.append(
        f"\nDormoy : optimum à 125 bar sans réchauffage (4,2 → 3,8 %) et "
        f"150 bar avec (5,3 → 5,1 %) ; puissance du compresseur 39 → 48 kW à "
        f"300 bar. Simulé avec la convention « depuis 1 bar » : maximum à "
        f"{dfp.p_max[i_sans]:.0f} bar sans et {dfp.p_max[i_avec]:.0f} bar "
        f"avec réchauffage ; puissance {dfp.P_comp.iloc[-1]:.0f} kW à 300 "
        "bar. L'optimum n'existe que parce que la charge de 1 à 18 bar est "
        "une dépense fixe qui pèse plus quand p max est faible ; avec la "
        "convention « cycle » (depuis 18 bar), le rendement baisse de façon "
        "monotone avec la pression, parce que le travail par kilogramme "
        "augmente. Au-delà de 190 bar, les rapports de pression des étages 3 "
        "et 4 sont extrapolés (loi linéaire bornée) : tendance indicative "
        "seulement.\n"
    )
    figs_t.append(tracer_tendance(
        p_maxs,
        {"avec réchauffage, charge depuis 1 bar": list(dfp.rte_avec_1bar),
         "sans réchauffage, charge depuis 1 bar": list(dfp.rte_sans_1bar),
         "avec réchauffage, charge depuis 18 bar": list(dfp.rte_avec),
         "sans réchauffage, charge depuis 18 bar": list(dfp.rte_sans)},
        "Rendement aller-retour selon la pression maximale (fig. 13)",
        "Pression maximale (bar)", "RTE (%)", "fig6_tendance_pmax.png",
        [(150.0, 5.3, "Dormoy : optimum 150 bar (avec) / 125 bar (sans)"),
         (125.0, 4.2, "")],
    ))

    # 4.3 Indice polytropique
    ns = [1.0, 1.1, 1.2, 1.3, 1.4]
    lignes_n: list[dict[str, float]] = []
    for n in ns:
        mods = {f"compresseur.etages.{i}.indice_polytropique": n
                for i in range(4)}
        ch = charge_depuis(sc_ch_B, p_arret, f"n{n:g}", **mods)
        d0 = decharge_depuis_charge(sc_base, ch, f"n{n:g}")
        d1 = decharge_depuis_charge(
            sc_base, ch, f"n{n:g}p",
            **{"turbine.etages.0.T_entree_cible": 363.15})
        lignes_n.append({
            "n": n,
            "E_cons": ch.totaux["energie_electrique_kwh"],
            "P_comp": ch.totaux["puissance_moyenne_kw"],
            "duree": ch.totaux["duree_h"],
            "E_sans": d0.totaux["energie_electrique_kwh"],
            "E_avec": d1.totaux["energie_electrique_kwh"],
            "rte_sans": d0.totaux["energie_electrique_kwh"]
            / ch.totaux["energie_electrique_kwh"] * 100,
            "rte_avec": d1.totaux["energie_electrique_kwh"]
            / ch.totaux["energie_electrique_kwh"] * 100,
        })
    dfn = pd.DataFrame(lignes_n)
    L.append("### 4.3 Indice polytropique du compresseur (fig. 14 et 15)\n")
    L.append("Les quatre étages reçoivent le même indice n.\n")
    L.append("| n | Énergie de charge | Puissance moyenne | Durée | Produit "
             "sans | Produit avec | RTE sans | RTE avec |")
    L.append("|---|---|---|---|---|---|---|---|")
    for _, l in dfn.iterrows():
        L.append(
            f"| {l.n:.1f} | {l.E_cons:.0f} kWh | {l.P_comp:.1f} kW | "
            f"{l.duree:.1f} h | {l.E_sans:.1f} kWh | {l.E_avec:.1f} kWh | "
            f"{l.rte_sans:.1f} % | {l.rte_avec:.1f} % |"
        )
    L.append(
        "\nDormoy à n = 1 : puissance < 36 kW, 17,9 kWh sans réchauffage, "
        "22,8 kWh avec, RTE 7,5 % avec réchauffage. Tendances retrouvées : "
        "le compresseur isotherme consomme moins et stocke plus de masse "
        "(air plus froid). Le niveau de l'énergie produite porte l'écart du "
        "cas de base.\n"
    )
    figs_t.append(tracer_tendance(
        ns,
        {"avec réchauffage à 90 °C": list(dfn.rte_avec),
         "sans réchauffage": list(dfn.rte_sans)},
        "Rendement aller-retour selon l'indice polytropique (fig. 15)",
        "Indice polytropique n du compresseur", "RTE (%)",
        "fig7_tendance_n.png", [(1.0, 7.5, "Dormoy, n = 1, avec : 7,5 %")],
    ))

    # 4.4 Nombre d'étages
    etages_sc = sc3["turbine.etages"]
    configs = {
        1: ([etages_sc[2]], reg.si("cas_base.pression_arret")),
        2: ([etages_sc[1], etages_sc[2]],
            reg.si("cas_2etages.pression_arret")),
        3: (list(etages_sc), reg.si("charge_55_190.pression_min")),
    }
    lignes_e: list[dict[str, float]] = []
    for k, (etages, p_stop) in configs.items():
        ch = charge_depuis(sc_ch_B, p_stop, f"{k}etages")
        d = decharge_depuis_charge(
            sc3, ch, f"{k}etages",
            **{"turbine.etages": [dict(e) for e in etages],
               "detendeur.p_consigne": etages[0]["p_entree"]})
        lignes_e.append({
            "k": k, "p_stop": p_stop / 1e5,
            "E_cons": ch.totaux["energie_electrique_kwh"],
            "duree_charge": ch.totaux["duree_h"],
            "E_prod": d.totaux["energie_electrique_kwh"],
            "Q": d.totaux["chaleur_rechauffage_kwh"],
            "duree_dech": d.totaux["duree_min"],
            "rte": d.totaux["energie_electrique_kwh"]
            / ch.totaux["energie_electrique_kwh"] * 100,
            "rte_q": d.totaux["energie_electrique_kwh"]
            / (ch.totaux["energie_electrique_kwh"]
               + d.totaux["chaleur_rechauffage_kwh"]) * 100,
        })
    dfe = pd.DataFrame(lignes_e)
    L.append(
        "### 4.4 Nombre d'étages de détente, avec réchauffage (fig. 16)\n"
    )
    L.append("| Étages | Arrêt | Énergie de charge | Durée de charge | "
             "Produit | Chaleur externe | Durée de décharge | RTE sans "
             "chaleur | RTE avec chaleur |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for _, l in dfe.iterrows():
        L.append(
            f"| {l.k:.0f} | {l.p_stop:.0f} bar | {l.E_cons:.0f} kWh | "
            f"{l.duree_charge:.1f} h | {l.E_prod:.1f} kWh | {l.Q:.1f} kWh | "
            f"{l.duree_dech:.0f} min | {l.rte:.1f} % | {l.rte_q:.1f} % |"
        )
    L.append(
        "\nDormoy : consommation « nearly 380 » → 290 kWh et RTE 5,5 → "
        "16,0 % de 1 à 3 étages (chaleur non comptée). Le gain vient à la "
        "fois d'une détente mieux étagée (plus de travail par kilogramme) "
        "et d'une recharge plus courte (le coussin d'air de 55 bar n'est "
        "pas perdu : il reste dans les réservoirs d'un cycle à l'autre).\n"
    )
    figs_t.append(tracer_tendance(
        [1, 2, 3],
        {"RTE sans compter la chaleur": list(dfe.rte),
         "RTE en comptant la chaleur externe": list(dfe.rte_q)},
        "Rendement selon le nombre d'étages de détente (fig. 16)",
        "Nombre d'étages (avec réchauffage)", "RTE (%)",
        "fig8_tendance_etages.png",
        [(1, 5.5, "Dormoy : 5,5 % → 16,0 %"), (3, 16.0, "")],
    ))

    # ------------------------------------------------------------------
    # 5. Bilan d'énergie, hypothèses, graphiques
    # ------------------------------------------------------------------
    L.append("## 5. Bilan d'énergie de la décharge à 3 étages\n")
    b = r3.bilan
    L.append("| Poste | kWh |")
    L.append("|---|---|")
    for cle, nom in [
        ("E_sortie_reservoir_j", "Enthalpie sortie des réservoirs"),
        ("Q_paroi_reservoir_j",
         "Chaleur cédée par l'air à la paroi (négative : la paroi chauffe "
         "l'air)"),
        ("dU_reservoir_j", "Variation d'énergie interne du réservoir"),
        ("Q_rechauffage_j", "Chaleur de réchauffage (externe)"),
        ("E_detendeur_j", "Écart d'enthalpie dans le détendeur"),
        ("E_mecanique_j", "Travail à l'arbre des turbines"),
        ("pertes_electriques_j", "Pertes des génératrices"),
        ("E_electrique_j", "Électricité produite"),
        ("Q_turbine_residuel_j",
         "Chaleur implicite des turbines (chute d'enthalpie − travail)"),
        ("E_air_rejete_j", "Enthalpie de l'air rejeté à 1 bar"),
    ]:
        L.append(f"| {nom} | {b[cle] / 3.6e6:.1f} |")
    L.append(
        f"| Résidu du bilan de la chaîne | {b['residu_relatif'] * 100:.4f} % "
        f"|"
    )
    L.append(
        f"| Résidu du bilan du réservoir | "
        f"{b['residu_reservoir_j'] / 3.6e6:.4f} kWh |\n"
    )

    L.append("## 6. Hypothèses propres à la phase 2\n")
    L.append("| Paramètre | Valeur | Provenance |")
    L.append("|---|---|---|")
    for id_ in ("cas_base.temperature_initiale_decharge",
                "essai_decharge.temperature_paroi_initiale",
                "cas_base.turbine", "cas_base.pression_arret",
                "cas_2etages.pression_arret", "turbine.rechauffage.source"):
        par = reg[id_]
        if par.unite == "texte":
            val = str(par.valeur)
        else:
            val = f"{par.valeur} {par.unite}"
        L.append(
            f"| `{id_}` | {val} | {par.niveau_preuve} ; {par.notes} |"
        )

    figs = tracer_essai(r_iso, r_ch) + tracer_3etages(r3) + figs_t
    L.append("\n## 7. Graphiques\n")
    for f in figs:
        L.append(f"![{f}]({f})\n")

    L.append("## 8. Conclusion\n")
    L.append(
        "- **Essai mesuré reproduit** : durée à "
        f"{pct(r_iso.totaux['duree_min'], duree_ref)} avec les coefficients "
        "calibrés de Dormoy. Les deux modèles de détendeur concordent.\n"
        "- **Cas à 3 étages** : chaleur de réchauffage du tableau 5 "
        "reproduite étage par étage (à condition de partir de 55 °C), "
        "énergie produite cohérente avec 62 kW × durée, rendement "
        f"{rte3_B['rte_sans_chaleur'] * 100:.1f} % sans compter la chaleur "
        f"et {rte3_B['rte_avec_chaleur_externe'] * 100:.1f} % en la "
        "comptant. Le « 16 % » de Dormoy est incohérent avec ses propres "
        "40 min de décharge (14,2 %).\n"
        f"- **Cas de base** : {r_base.totaux['energie_electrique_kwh']:.1f} "
        "kWh contre 16,93 : écart de −15 % **non expliqué**, hors du "
        "critère de sortie (17 ± 1 kWh). Les diagnostics localisent "
        "l'énergie manquante dans le refroidissement de l'air (détendeur et "
        "réservoir), que Dormoy modélise pourtant aussi. Point ouvert "
        "signalé dans le journal.\n"
        "- **Tendances** des figures 11 à 16 retrouvées qualitativement "
        "(sens de variation, optimum de pression, gain des étages).\n"
        "- **Masse morte** : avec l'étage 3 seul, l'arrêt est à 18 bar et "
        "non à 50 bar : le tableau « 1000 unités » de la fiche Dormoy devra "
        "être refait en phase 3.\n"
    )
    (DOSSIER / "validation_decharge.md").write_text(
        "\n".join(L), encoding="utf-8"
    )
    for nom, df in (("tendance_Tamb", dfT), ("tendance_pmax", dfp),
                    ("tendance_n", dfn), ("tendance_etages", dfe)):
        df.to_csv(DOSSIER / f"{nom}.csv", index=False, float_format="%.4f")
    r3.series.to_csv(DOSSIER / "series_3etages.csv", index=False,
                     float_format="%.6g")
    print("rapport écrit :", DOSSIER / "validation_decharge.md")


if __name__ == "__main__":
    main()
