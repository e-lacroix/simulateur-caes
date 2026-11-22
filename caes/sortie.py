"""Écriture des résultats d'une simulation dans un dossier (phase 6).

``python -m caes simuler scenario.yaml --sortie dossier/`` produit :

* ``resume.md`` : l'installation, les résultats, les rendements (deux
  définitions), les bilans d'énergie, les avertissements ;
* ``charge_series.csv``, ``decharge_series.csv`` (dernier cycle),
  ``cycles.csv`` (un cycle par ligne) ;
* ``tableau_1000.md`` et ``cascade.png`` (si charge et décharge), ou
  ``exergie.md`` (bilan d'exergie d'une charge ou d'une décharge seule) ;
* des graphiques (pression, températures, puissance, profils des cuves,
  cycles) ;
* ``provenance.md`` : chaque paramètre, sa valeur SI, sa source, et les
  références du registre citées (avec DOI).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from caes.assembleur import ResultatSimulation
from caes.exergie import BilanExergie, bilan_exergie_charge
from caes.exergie import bilan_exergie_decharge
from caes.graphiques import (
    COULEURS,
    etiquette_fin,
    nouvelle_figure,
    style_axes,
    terminer,
)
from caes.systeme import ResultatCharge, ResultatDecharge
from caes.tableau_1000 import cas_depuis_resultats, cascade, tableau_markdown

T0C = 273.15


def _f(x: Any, n: int = 2) -> str:
    if isinstance(x, (int, float)):
        return f"{x:.{n}f}"
    return str(x)


def _table(lignes: list[list[Any]], entete: list[str]) -> str:
    out = ["| " + " | ".join(entete) + " |",
           "|" + "---|" * len(entete)]
    for l in lignes:
        out.append("| " + " | ".join(str(v) for v in l) + " |")
    return "\n".join(out)


# ----------------------------------------------------------------------
# Graphiques
# ----------------------------------------------------------------------


def _graphiques_charge(ch: ResultatCharge, dossier: Path) -> list[str]:
    s = ch.series
    if s.empty:
        return []
    t = s["t_s"] / 3600.0
    noms: list[str] = []
    fig, ax = nouvelle_figure()
    ax.plot(t, s["p_res_pa"] / 1e5, color=COULEURS[0], linewidth=2)
    etiquette_fin(ax, t.iloc[-1], s["p_res_pa"].iloc[-1] / 1e5,
                  "réservoir", COULEURS[0])
    style_axes(ax, "Charge : pression du réservoir", "Temps (h)",
               "Pression absolue (bar)")
    noms.append(terminer(fig, ax, dossier / "charge_pression.png", None))

    fig, ax = nouvelle_figure()
    ax.plot(t, s["T_res_K"] - T0C, color=COULEURS[0], linewidth=2)
    etiquette_fin(ax, t.iloc[-1], s["T_res_K"].iloc[-1] - T0C,
                  "air du réservoir", COULEURS[0])
    nb = sum(1 for c in s.columns if c.startswith("beta_"))
    for i in range(1, nb + 1):
        c = COULEURS[(i) % len(COULEURS)]
        ax.plot(t, s[f"T_out_comp_{i}_K"] - T0C, color=c, linewidth=1.2)
        etiquette_fin(ax, t.iloc[-1], s[f"T_out_comp_{i}_K"].iloc[-1] - T0C,
                      f"sortie étage {i}", c)
    ax.plot(t, s["T_amb_K"] - T0C, color="#888", linewidth=1,
            linestyle="--")
    etiquette_fin(ax, t.iloc[-1], s["T_amb_K"].iloc[-1] - T0C, "ambiant",
                  "#888")
    style_axes(ax, "Charge : températures", "Temps (h)",
               "Température (°C)")
    noms.append(terminer(fig, ax, dossier / "charge_temperatures.png",
                         None))

    fig, ax = nouvelle_figure()
    ax.plot(t, s["P_el_w"] / 1e3, color=COULEURS[1], linewidth=2)
    etiquette_fin(ax, t.iloc[-1], s["P_el_w"].iloc[-1] / 1e3,
                  "électrique", COULEURS[1])
    ax.plot(t, s["Q_ref_w"] / 1e3, color=COULEURS[2], linewidth=1.5)
    etiquette_fin(ax, t.iloc[-1], s["Q_ref_w"].iloc[-1] / 1e3,
                  "chaleur des refroidisseurs", COULEURS[2])
    style_axes(ax, "Charge : puissance électrique et chaleur rejetée",
               "Temps (h)", "Puissance (kW)")
    noms.append(terminer(fig, ax, dossier / "charge_puissance.png", None))
    return noms


def _graphiques_decharge(d: ResultatDecharge, dossier: Path) -> list[str]:
    s = d.series
    if s.empty:
        return []
    t = s["t_s"] / 60.0
    noms: list[str] = []
    fig, ax = nouvelle_figure()
    ax.plot(t, s["p_res_pa"] / 1e5, color=COULEURS[0], linewidth=2)
    etiquette_fin(ax, t.iloc[-1], s["p_res_pa"].iloc[-1] / 1e5,
                  "réservoir", COULEURS[0])
    style_axes(ax, "Décharge : pression du réservoir", "Temps (min)",
               "Pression absolue (bar)")
    noms.append(terminer(fig, ax, dossier / "decharge_pression.png", None))

    fig, ax = nouvelle_figure()
    ax.plot(t, s["T_res_K"] - T0C, color=COULEURS[0], linewidth=2)
    etiquette_fin(ax, t.iloc[-1], s["T_res_K"].iloc[-1] - T0C,
                  "air du réservoir", COULEURS[0])
    ax.plot(t, s["T_sortie_detendeur_K"] - T0C, color=COULEURS[1],
            linewidth=1.5)
    etiquette_fin(ax, t.iloc[-1], s["T_sortie_detendeur_K"].iloc[-1] - T0C,
                  "sortie du détendeur", COULEURS[1])
    nb = sum(1 for c in s.columns if c.startswith("T_in_turb_"))
    for i in range(1, nb + 1):
        c = COULEURS[(i + 1) % len(COULEURS)]
        ax.plot(t, s[f"T_in_turb_{i}_K"] - T0C, color=c, linewidth=1.2)
        etiquette_fin(ax, t.iloc[-1], s[f"T_in_turb_{i}_K"].iloc[-1] - T0C,
                      f"entrée turbine {i}", c)
    ax.plot(t, s["T_rejet_K"] - T0C, color="#888", linewidth=1,
            linestyle="--")
    etiquette_fin(ax, t.iloc[-1], s["T_rejet_K"].iloc[-1] - T0C,
                  "air rejeté", "#888")
    style_axes(ax, "Décharge : températures", "Temps (min)",
               "Température (°C)")
    noms.append(terminer(fig, ax, dossier / "decharge_temperatures.png",
                         None))

    if (s["P_el_w"] > 0).any():
        fig, ax = nouvelle_figure()
        ax.plot(t, s["P_el_w"] / 1e3, color=COULEURS[1], linewidth=2)
        etiquette_fin(ax, t.iloc[-1], s["P_el_w"].iloc[-1] / 1e3,
                      "électrique", COULEURS[1])
        ax.plot(t, s["Q_rech_w"] / 1e3, color=COULEURS[2], linewidth=1.5)
        etiquette_fin(ax, t.iloc[-1], s["Q_rech_w"].iloc[-1] / 1e3,
                      "chaleur de réchauffage", COULEURS[2])
        style_axes(ax, "Décharge : puissance produite et chaleur reçue",
                   "Temps (min)", "Puissance (kW)")
        noms.append(terminer(fig, ax, dossier / "decharge_puissance.png",
                             None))
    return noms


def _graphique_cuves(res: ResultatSimulation, dossier: Path) -> list[str]:
    cuves = [s for s in res.installation.stockages if s.lit is not None]
    if not cuves:
        return []
    fig, ax = nouvelle_figure()
    for k, st in enumerate(cuves):
        T = st.profil_temperature_K()
        if T is None:
            continue
        z = [(i + 0.5) / len(T) * st.lit.hauteur_m for i in range(len(T))]
        c = COULEURS[k % len(COULEURS)]
        ax.plot(z, T - T0C, color=c, linewidth=2)
        etiquette_fin(ax, z[-1], T[-1] - T0C, st.nom, c)
    style_axes(ax, "Cuves de gravier : profil de température en fin de "
               "simulation", "Hauteur depuis le haut (m)", "Température (°C)")
    return [terminer(fig, ax, dossier / "cuves_profils.png", None)]


def _graphique_cycles(res: ResultatSimulation, dossier: Path) -> list[str]:
    if len(res.cycles) < 2:
        return []
    n = [c.numero for c in res.cycles]
    fig, ax = nouvelle_figure()
    E_c = [c.charge.totaux["energie_electrique_kwh"] for c in res.cycles]
    E_p = [c.decharge.totaux["energie_electrique_kwh"] for c in res.cycles]
    ax.plot(n, E_c, color=COULEURS[0], marker="o", linewidth=2)
    etiquette_fin(ax, n[-1], E_c[-1], "consommée", COULEURS[0])
    ax.plot(n, E_p, color=COULEURS[1], marker="o", linewidth=2)
    etiquette_fin(ax, n[-1], E_p[-1], "produite", COULEURS[1])
    if any(c.chaleur_cuves_fin_kwh for c in res.cycles):
        Q = [c.chaleur_cuves_fin_kwh for c in res.cycles]
        ax.plot(n, Q, color=COULEURS[2], marker="o", linewidth=1.5)
        etiquette_fin(ax, n[-1], Q[-1], "chaleur restante (cuves)",
                      COULEURS[2])
    ax.set_xticks(n)
    style_axes(ax, "Cycles jusqu'au régime stable", "Cycle",
               "Énergie (kWh)")
    return [terminer(fig, ax, dossier / "cycles.png", None)]


# ----------------------------------------------------------------------
# Textes
# ----------------------------------------------------------------------


def _bilan_exergie_markdown(b: BilanExergie, titre: str) -> str:
    L = [f"### {titre}\n",
         f"État mort : {b.T0_K - T0C:.1f} °C, {b.p0_pa / 1e5:.3f} bar. "
         f"Entrée : {b.entree_j / 3.6e6:.2f} kWh d'exergie. Résidu "
         f"{b.residu_relatif * 100:+.2f} %.\n",
         "| Poste | Exergie (kWh) | Part de l'entrée |", "|---|---|---|"]
    for k, v in b.postes.items():
        L.append(f"| {k} | {v / 3.6e6:.3f} | {v / b.entree_j * 100:.1f} % |")
    for k, v in b.sorties_utiles_j.items():
        L.append(f"| **{k}** | **{v / 3.6e6:.3f}** | "
                 f"**{v / b.entree_j * 100:.1f} %** |")
    return "\n".join(L) + "\n"


def _resume_markdown(res: ResultatSimulation, fichiers: list[str],
                     commande: str) -> str:
    inst = res.installation
    L = [f"# {inst.nom} : résultats de simulation\n",
         f"*{inst.description.strip() or 'Scénario sans description.'}*\n",
         f"Généré le {datetime.now():%Y-%m-%d %H:%M} par `{commande}`. "
         f"Mode : **{res.mode}**. Scénario : `{inst.scenario.chemin}`.\n",
         "## Installation\n",
         f"**Ambiance** : {inst.ambiance.description()}.\n",
         "**Composants** :\n"]
    for c in inst.composants.values():
        L.append(f"- {c.description()}")
    if inst.charge:
        L.append("\n**Chaîne de charge** : "
                 + " → ".join(e.nom for e in inst.charge.elements))
    if inst.decharge:
        L.append("\n**Chaîne de décharge** : "
                 + " → ".join(e.nom for e in inst.decharge.elements))
    if inst.attente:
        L.append(f"\n**Attente** : {inst.attente.duree_s / 3600:.2f} h")
    L.append("\n## Résultats\n")
    if res.cycles:
        lignes = []
        for c in res.cycles:
            ch, d = c.charge, c.decharge
            E_c = ch.totaux["energie_electrique_kwh"]
            E_p = d.totaux["energie_electrique_kwh"]
            src = ", ".join(f"{k} {v:.1f}" for k, v in
                            d.chaleur_par_source.items()) or "–"
            lignes.append([c.numero, _f(E_c, 1), _f(ch.totaux["duree_h"]),
                           _f(E_p), _f(d.totaux["duree_min"], 1),
                           f"{E_p / E_c * 100:.1f} %", src,
                           _f(c.chaleur_cuves_fin_kwh, 1),
                           _f(c.pertes_attente_kwh)])
        L.append(_table(lignes, ["Cycle", "Charge (kWh)", "Durée (h)",
                                 "Produit (kWh)", "Durée (min)", "RTE",
                                 "Chaleur de réchauffage par source (kWh)",
                                 "Chaleur restante dans les cuves (kWh)",
                                 "Pertes pendant l'attente (kWh)"]))
        etat = "atteint" if res.converge else "**non atteint**"
        tol = float(inst.options.get("tolerance", 0.01)) * 100
        L.append(f"\nRégime stable {etat} après {len(res.cycles)} cycle(s) "
                 f"(tolérance {tol:.0f} %).\n")
    ch, d = res.charge_finale, res.decharge_finale
    if ch is not None:
        t = ch.totaux
        L.append("### Charge" + (" (dernier cycle)" if res.cycles else "")
                 + "\n")
        L.append(_table([
            ["Arrêt", ch.arret],
            ["Pression initiale → finale (bar)",
             f"{t['p_initiale_bar']:.1f} → {t['p_finale_bar']:.1f}"],
            ["Durée (h)", _f(t["duree_h"])],
            ["Électricité consommée (kWh)",
             _f(t["energie_electrique_kwh"], 1)],
            ["Puissance moyenne (kW)", _f(t["puissance_moyenne_kw"], 1)],
            ["Chaleur rejetée par les refroidisseurs (kWh)",
             _f(t["chaleur_refroidisseurs_kwh"], 1)],
            ["dont au-dessus du seuil (kWh)",
             _f(t["chaleur_sup_seuil_kwh"], 1)],
            ["Chaleur stockée dans les cuves (kWh)",
             _f(t["chaleur_cuves_kwh"], 1)],
            ["Masse stockée (kg)", _f(t["masse_stockee_kg"], 1)],
            ["Température finale du réservoir (°C)",
             _f(t["T_finale_degC"], 1)],
            ["Résidu du bilan d'énergie",
             f"{ch.bilan['residu_relatif'] * 100:+.3f} %"],
        ] + ([
            ["Eau aspirée (kg)", _f(t["eau_entree_kg"])],
            ["Eau condensée dans les refroidisseurs et cuves (kg)",
             _f(t["eau_condensee_kg"])],
            ["Eau séparée ou purgée (kg)", _f(t["eau_separee_kg"])],
            ["Eau entrée dans le réservoir (kg)", _f(t["eau_reservoir_kg"])],
            ["Eau condensée au fond du réservoir (kg)",
             _f(t["eau_condensee_reservoir_kg"])],
            ["Point de rosée de l'air du réservoir (°C, sous pression)",
             _f(t["T_rosee_reservoir_degC"], 1)],
        ] if t.get("eau_entree_kg", 0.0) > 0 else []),
            ["Grandeur", "Valeur"]))
        L.append("")
    if d is not None:
        t = d.totaux
        L.append("### Décharge" + (" (dernier cycle)" if res.cycles else "")
                 + "\n")
        src = ", ".join(f"{k} : {v:.2f}" for k, v in
                        d.chaleur_par_source.items()) or "aucune"
        L.append(_table([
            ["Arrêt", d.arret],
            ["Pression initiale → finale (bar)",
             f"{t['p_initiale_bar']:.1f} → {t['p_finale_bar']:.1f}"],
            ["Durée (min)", _f(t["duree_min"], 1)],
            ["Électricité produite (kWh)", _f(t["energie_electrique_kwh"])],
            ["Puissance électrique moyenne (kW)",
             _f(t["puissance_electrique_moyenne_kw"], 1)],
            ["Chaleur de réchauffage (kWh)", _f(t["chaleur_rechauffage_kwh"])],
            ["Chaleur par source (kWh)", src],
            ["Masse soutirée / morte (kg)",
             f"{t['masse_soutiree_kg']:.1f} / {t['masse_morte_kg']:.1f}"],
            ["Température minimale de l'air rejeté (°C)",
             _f(t["T_rejet_min_degC"], 1)],
            ["Résidu du bilan d'énergie",
             f"{d.bilan['residu_relatif'] * 100:+.3f} %"],
        ] + ([
            ["Eau sortie avec l'air (kg)", _f(t["eau_sortie_kg"])],
            ["Givre au détendeur (kg)", _f(t["givre_detendeur_kg"], 3)],
            ["Givre aux sorties des turbines (kg)",
             _f(t["givre_total_kg"] - t["givre_detendeur_kg"], 3)],
        ] if t.get("eau_sortie_kg", 0.0) > 0 or t.get("givre_total_kg", 0.0)
            > 0 else []), ["Grandeur", "Valeur"]))
        L.append("")
    r = res.rendements()
    if r:
        L.append("### Rendement aller-retour (formules.md#F20)\n")
        L.append(_table([
            ["Électricité consommée (kWh)", _f(r["energie_consommee_kwh"], 1)],
            ["Électricité produite (kWh)", _f(r["energie_produite_kwh"])],
            ["Chaleur externe (kWh)", _f(r["chaleur_externe_kwh"])],
            ["**RTE sans compter la chaleur** (définition de Dormoy)",
             f"**{r['rte_sans_chaleur'] * 100:.2f} %**"],
            ["**RTE avec la chaleur externe comptée**",
             f"**{r['rte_avec_chaleur_externe'] * 100:.2f} %**"],
        ], ["Grandeur", "Valeur"]))
        L.append("\nLe rendement est un résultat du modèle, jamais une "
                 "entrée ; les deux définitions sont toujours données.\n")
    avis = res.avertissements
    L.append("## Avertissements\n")
    if avis:
        L.extend(f"- {a}" for a in avis)
    else:
        L.append("Aucun : tous les composants sont restés dans leur domaine "
                 "de validité.")
    L.append("\n## Fichiers produits\n")
    L.extend(f"- `{f}`" for f in fichiers)
    pngs = [f for f in fichiers if f.endswith(".png")]
    if pngs:
        L.append("")
        L.extend(f"![{f}]({f})\n" for f in pngs)
    return "\n".join(L) + "\n"


def _provenance_markdown(res: ResultatSimulation) -> str:
    inst = res.installation
    sc = inst.scenario
    L = [f"# Provenance des paramètres : {inst.nom}\n",
         "*Chaque valeur du scénario, convertie en SI, avec sa source. "
         "Les entrées « registre » portent le niveau de preuve, la "
         "référence et l'endroit dans la source ; les entrées « scénario » "
         "portent la justification écrite dans le fichier.*\n",
         "| Paramètre | Valeur (SI) | Provenance |", "|---|---|---|"]
    for chemin in sorted(sc.provenance):
        try:
            val = sc[chemin]
        except (KeyError, IndexError, TypeError):
            val = ""
        if isinstance(val, float):
            val_txt = f"{val:.6g}"
        else:
            val_txt = str(val)
        L.append(f"| `{chemin}` | {val_txt} | {sc.provenance[chemin]} |")
    ids = sorted(set(sc.references.values()))
    if ids:
        L.append("\n## Références du registre citées\n")
        L.append("| Référence | Citation | DOI ou URL | Accès |")
        L.append("|---|---|---|---|")
        sources = {}
        for id_ in ids:
            par = inst.registre[id_]
            sources.setdefault(par.source_id, []).append(id_)
        for src_id, pars in sorted(sources.items()):
            ref = inst.registre.references[src_id]
            L.append(f"| `{src_id}` ({len(pars)} paramètres) | "
                     f"{ref.auteurs} ({ref.annee}), {ref.titre}, "
                     f"{ref.revue} | {ref.doi_ou_url} | {ref.acces} |")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------


def ecrire_resultats(res: ResultatSimulation, dossier: Path | str,
                     graphiques: bool = True,
                     commande: str = "python -m caes simuler") -> Path:
    """Écrit tous les fichiers de résultats ; retourne le dossier."""
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    fichiers: list[str] = []
    inst = res.installation
    ch, d = res.charge_finale, res.decharge_finale
    if ch is not None:
        ch.series.to_csv(dossier / "charge_series.csv", index=False)
        fichiers.append("charge_series.csv")
    if d is not None:
        d.series.to_csv(dossier / "decharge_series.csv", index=False)
        fichiers.append("decharge_series.csv")
    if res.cycles:
        lignes = []
        for c in res.cycles:
            ligne: dict[str, Any] = {"cycle": c.numero,
                                     "attente_h": c.attente_h,
                                     "chaleur_cuves_debut_kwh":
                                         c.chaleur_cuves_debut_kwh,
                                     "chaleur_cuves_fin_kwh":
                                         c.chaleur_cuves_fin_kwh,
                                     "pertes_attente_kwh":
                                         c.pertes_attente_kwh}
            ligne.update({f"charge_{k}": v for k, v in c.charge.totaux.items()
                          if isinstance(v, (int, float))})
            ligne.update({f"decharge_{k}": v
                          for k, v in c.decharge.totaux.items()
                          if isinstance(v, (int, float))})
            for k, v in c.decharge.chaleur_par_source.items():
                ligne[f"chaleur_{k}_kwh"] = v
            lignes.append(ligne)
        pd.DataFrame(lignes).to_csv(dossier / "cycles.csv", index=False)
        fichiers.append("cycles.csv")
    if ch is not None and d is not None:
        cas = cas_depuis_resultats(inst.nom, inst.description.strip()
                                   or inst.nom, ch, d)
        (dossier / "tableau_1000.md").write_text(
            tableau_markdown(cas, f"`{commande}`"), encoding="utf-8")
        fichiers.append("tableau_1000.md")
        if graphiques:
            fichiers.append(cascade(cas, dossier / "cascade.png"))
    else:
        texte = ["# Bilan d'exergie\n"]
        if ch is not None:
            texte.append(_bilan_exergie_markdown(bilan_exergie_charge(ch),
                                                 "Charge"))
        if d is not None:
            texte.append(_bilan_exergie_markdown(bilan_exergie_decharge(d),
                                                 "Décharge"))
        (dossier / "exergie.md").write_text("\n".join(texte),
                                            encoding="utf-8")
        fichiers.append("exergie.md")
    if graphiques:
        if ch is not None:
            fichiers.extend(_graphiques_charge(ch, dossier))
        if d is not None:
            fichiers.extend(_graphiques_decharge(d, dossier))
        fichiers.extend(_graphique_cuves(res, dossier))
        fichiers.extend(_graphique_cycles(res, dossier))
    (dossier / "provenance.md").write_text(_provenance_markdown(res),
                                           encoding="utf-8")
    fichiers.append("provenance.md")
    (dossier / "resume.md").write_text(
        _resume_markdown(res, fichiers, commande), encoding="utf-8")
    return dossier
