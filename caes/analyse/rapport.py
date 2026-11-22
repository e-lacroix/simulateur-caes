# -*- coding: utf-8 -*-
"""Exécution complète d'une analyse et écriture du rapport
(Markdown, CSV, figures) dans un dossier.

    from caes.analyse.rapport import executer, ecrire_rapport
    res = executer(analyse, procs=8)
    ecrire_rapport(analyse, res, Path("rapports/phase10"))

Étapes (chacune peut être omise) : ``tornade`` (un paramètre à la
fois), ``sobol``, ``incertitudes``, ``pareto``. Les avertissements de
domaine de validité émis pendant toutes les simulations sont
rassemblés dans une section du rapport.
"""

from __future__ import annotations

import csv
import math
import pickle
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from caes.analyse.evaluation import Evaluateur, ResultatPoint
from caes.analyse.incertitudes import ResultatIncertitudes, propager
from caes.analyse.pareto import ReglagesNSGA2, ResultatPareto, nsga2
from caes.analyse.parametres import Analyse, ParametreAnalyse
from caes.analyse.sensibilite import (
    ResultatSobol,
    ResultatTornade,
    indices_de_sobol,
    un_parametre_a_la_fois,
)
from caes.graphiques import (
    COULEURS,
    ENCRE_2,
    nouvelle_figure,
    style_axes,
    terminer,
)

ETAPES = ("tornade", "sobol", "incertitudes", "pareto")


@dataclass
class ResultatsAnalyse:
    nominal: ResultatPoint
    tornade: ResultatTornade | None = None
    sobol: ResultatSobol | None = None
    incertitudes: ResultatIncertitudes | None = None
    pareto: ResultatPareto | None = None
    pareto_variables: list[ParametreAnalyse] = field(default_factory=list)
    pareto_objectifs: list[dict] = field(default_factory=list)
    pareto_points: list[ResultatPoint] = field(default_factory=list)
    durees_s: dict[str, float] = field(default_factory=dict)
    procs: int = 1

    def tous_les_points(self) -> list[ResultatPoint]:
        pts = [self.nominal]
        if self.tornade:
            pts += self.tornade.resultats
        if self.sobol:
            pts += self.sobol.resultats
        if self.incertitudes:
            pts += self.incertitudes.resultats
        pts += self.pareto_points
        return pts


def _dire(texte: str) -> None:
    print(texte, flush=True)


def _rappel(etiquette: str) -> Callable[[int, int, ResultatPoint], None]:
    t0 = time.perf_counter()

    def f(n: int, total: int, r: ResultatPoint) -> None:
        if n == total or n % max(1, total // 8) == 0:
            etat = "" if r.valide else f" (échec : {r.erreur[:60]})"
            _dire(f"  {etiquette} : {n}/{total} "
                  f"[{time.perf_counter() - t0:.0f} s]{etat}")
    return f


def executer(an: Analyse, procs: int | None = None,
             etapes: tuple[str, ...] = ETAPES,
             rapide: bool = False) -> ResultatsAnalyse:
    """Lance les étapes demandées ; ``rapide`` réduit les tailles
    d'échantillon (essai de format, pas un résultat)."""
    ev = Evaluateur(an)
    out = ResultatsAnalyse(nominal=ev.evaluer(
        ev.point_nominal(an.parametres)), procs=procs or 1)
    if not out.nominal.valide:
        raise ValueError(f"simulation nominale échouée : "
                         f"{out.nominal.erreur or out.nominal.arret}")
    with ev.ouvrir(procs):
        if "tornade" in etapes:
            t = time.perf_counter()
            out.tornade = un_parametre_a_la_fois(
                ev, an.parametres, an.sorties, _rappel("tornade"))
            out.durees_s["tornade"] = time.perf_counter() - t
        if "sobol" in etapes and an.sobol:
            t = time.perf_counter()
            n = 4 if rapide else int(an.sobol.get("n", 64))
            out.sobol = indices_de_sobol(
                ev, an.selection(an.sobol.get("parametres")), an.sorties,
                n=n, graine=int(an.sobol.get("graine", 1)),
                bootstrap=not rapide, rappel=_rappel("sobol"))
            out.durees_s["sobol"] = time.perf_counter() - t
        if "incertitudes" in etapes and an.incertitudes:
            t = time.perf_counter()
            n = 6 if rapide else int(an.incertitudes.get("n", 64))
            out.incertitudes = propager(
                ev, an.selection(an.incertitudes.get("parametres")),
                an.sorties, n=n, graine=int(an.incertitudes.get("graine",
                                                                1)),
                rappel=_rappel("incertitudes"))
            out.durees_s["incertitudes"] = time.perf_counter() - t
        if "pareto" in etapes and an.pareto:
            t = time.perf_counter()
            _executer_pareto(ev, an, out, rapide)
            out.durees_s["pareto"] = time.perf_counter() - t
    return out


def _executer_pareto(ev: Evaluateur, an: Analyse, out: ResultatsAnalyse,
                     rapide: bool) -> None:
    cfg = an.pareto
    variables = an.selection(cfg.get("variables"))
    objectifs = list(cfg["objectifs"])
    signes = np.array([-1.0 if o["sens"] == "max" else 1.0
                       for o in objectifs])
    cles = [o["sortie"] for o in objectifs]
    reglages = ReglagesNSGA2(
        population=4 if rapide else int(cfg.get("population", 24)),
        generations=1 if rapide else int(cfg.get("generations", 15)),
        p_croisement=float(cfg.get("p_croisement", 0.9)),
        eta_croisement=float(cfg.get("eta_croisement", 15.0)),
        p_mutation=cfg.get("p_mutation"),
        eta_mutation=float(cfg.get("eta_mutation", 20.0)),
        graine=int(cfg.get("graine", 1)))
    noms = [v.nom for v in variables]
    rappel = _rappel("pareto")

    def evaluer(U: np.ndarray) -> np.ndarray:
        points = [{n: v.depuis_normalise(u) for n, v, u
                   in zip(noms, variables, ligne)} for ligne in U]
        res = ev.evaluer_points(points, rappel)
        out.pareto_points.extend(res)
        F = np.full((len(res), len(cles)), np.nan)
        for i, r in enumerate(res):
            if r.valide:
                F[i] = [r.sorties[c] for c in cles] * signes
        return F

    def rappel_gen(g: int, X: np.ndarray, F: np.ndarray) -> None:
        _dire(f"  pareto : génération {g}/{reglages.generations}, "
              f"meilleurs objectifs {np.nanmin(F, axis=0) * signes}")

    out.pareto = nsga2(evaluer, len(variables), reglages, rappel_gen)
    out.pareto_variables = variables
    out.pareto_objectifs = objectifs


# --- rapport ---------------------------------------------------------------
def _f(x: float, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if abs(x) >= 1000:
        return f"{x:,.0f}".replace(",", " ")
    return f"{x:.{nd}g}" if abs(x) < 1 else f"{x:.{nd + 1}g}"


def _etiquette_sortie(nom: str) -> str:
    return {
        "rte_sans_chaleur": "Rendement aller-retour (sans chaleur externe)",
        "rte_avec_chaleur_externe": "Rendement avec chaleur externe",
        "energie_consommee_kwh": "Électricité consommée (kWh)",
        "energie_produite_kwh": "Électricité produite (kWh)",
        "chaleur_externe_kwh": "Chaleur externe (kWh)",
        "masse_totale_kg": "Masse réservoirs + stockages (kg)",
        "masse_reservoirs_kg": "Masse des réservoirs d'air (kg)",
        "masse_cuves_kg": "Masse des stockages de chaleur (kg)",
        "volume_cuves_m3": "Volume des cuves (m³)",
        "pertes_attente_kwh": "Pertes pendant l'attente (kWh)",
    }.get(nom, nom)


def _nettoyer_avis(a: str) -> str:
    """Enlève le compteur « (×n) » d'un avertissement."""
    if a.endswith(")") and " (×" in a:
        return a[:a.rfind(" (×")]
    return a


def _section_parametres(an: Analyse, L: list[str]) -> None:
    L.append("## 1. Configuration analysée\n")
    L.append(f"Scénario : `{an.scenario.chemin}` ; modifications de base : "
             + (", ".join(f"`{m}`" for m in an.modifications_de_base)
                or "aucune") + ".\n")
    L.append("| Paramètre | Chemin(s) | Nominal | Plage | Origine de la "
             "plage | Niveau de preuve |")
    L.append("|---|---|---|---|---|---|")
    for p in an.parametres:
        if p.mode == "facteur":
            vals = ", ".join(_f(n) for n in p.nominaux)
            nominal = f"× 1 (valeurs : {vals} SI)"
        else:
            u = "" if p.unite in ("", "-") else f" {p.unite}"
            nominal = f"{_f(p.affichage(p.nominal))}{u}"
        L.append(f"| {p.etiquette} (`{p.nom}`) | "
                 + ", ".join(f"`{c}`" for c in p.chemins)
                 + f" | {nominal} | {p.texte_plage()} | {p.origine} | "
                 f"{p.niveau} |")
    L.append("")


def _section_nominal(an: Analyse, res: ResultatsAnalyse,
                     L: list[str]) -> None:
    L.append("## 2. Point nominal\n")
    L.append("| Sortie | Valeur |")
    L.append("|---|---|")
    for s in an.sorties:
        L.append(f"| {_etiquette_sortie(s)} | {_f(res.nominal.sorties[s])}"
                 " |")
    if res.nominal.arret:
        L.append(f"\nArrêt : {res.nominal.arret}.")
    if res.nominal.avertissements:
        L.append("\nAvertissements du point nominal : "
                 + " ; ".join(_nettoyer_avis(a)
                              for a in res.nominal.avertissements) + ".")
    L.append("")


def _fig_tornade(tor: ResultatTornade, sortie: str,
                 chemin: Path) -> str | None:
    lignes = [li for li in tor.classement(sortie)
              if not math.isnan(li.balancement)]
    if not lignes:
        return None
    lignes = lignes[::-1]
    fig, ax = nouvelle_figure(8.0, 0.5 + 0.45 * len(lignes))
    nominal = lignes[0].nominal
    for i, li in enumerate(lignes):
        ax.barh(i, li.haut - nominal, left=nominal, color=COULEURS[0],
                height=0.6, label="borne haute" if i == 0 else None)
        ax.barh(i, li.bas - nominal, left=nominal, color=COULEURS[1],
                height=0.6, label="borne basse" if i == 0 else None)
        ax.text(max(li.bas, li.haut), i,
                f"  basse → {_f(li.bas)}, haute → {_f(li.haut)}",
                va="center", fontsize=8, color=ENCRE_2)
    ax.axvline(nominal, color=ENCRE_2, linewidth=1)
    ax.set_yticks(range(len(lignes)))
    ax.set_yticklabels([li.parametre.etiquette for li in lignes],
                       fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    style_axes(ax, "Un paramètre à la fois, les autres au nominal",
               _etiquette_sortie(sortie), "")
    x0, x1 = ax.get_xlim()
    ax.set_xlim(x0, x1 + 0.55 * (x1 - x0))
    return terminer(fig, ax, chemin, None)


def _section_tornade(an: Analyse, res: ResultatsAnalyse, L: list[str],
                     dossier: Path) -> None:
    tor = res.tornade
    if tor is None:
        return
    L.append("## 3. Sensibilité « un paramètre à la fois » (tornade)\n")
    L.append(f"{len(tor.resultats)} simulations (nominal, puis chaque "
             f"paramètre à sa borne basse et à sa borne haute, les autres "
             f"au nominal), {_f(res.durees_s.get('tornade', 0), 2)} s. "
             f"Le balancement est l'écart entre les deux bornes ; il "
             f"classe les paramètres mais ignore les interactions "
             f"(voir Sobol).\n")
    for s in an.sorties:
        classement = tor.classement(s)
        L.append(f"### {_etiquette_sortie(s)}\n")
        L.append("| Rang | Paramètre | À la borne basse | À la borne "
                 "haute | Balancement | Balancement relatif |")
        L.append("|---|---|---|---|---|---|")
        nominal = classement[0].nominal if classement else float("nan")
        for k, li in enumerate(classement, 1):
            rel = (li.balancement / abs(nominal) if nominal
                   else float("nan"))
            L.append(f"| {k} | {li.parametre.etiquette} | {_f(li.bas)} | "
                     f"{_f(li.haut)} | {_f(li.balancement)} | "
                     f"{rel * 100:.1f} % |")
        L.append("")
    fig = _fig_tornade(tor, an.sorties[0], dossier / "tornade.png")
    if fig:
        L.append(f"![tornade]({fig})\n")
    if tor.echecs:
        L.append(f"Simulations échouées : {len(tor.echecs)} : "
                 + " ; ".join(f"{e.point} → {e.erreur or e.arret}"
                              for e in tor.echecs) + "\n")


def _fig_sobol(so: ResultatSobol, sortie: str, chemin: Path) -> str:
    i = so.sorties.index(sortie)
    ordre = np.argsort(so.total[i])
    d = len(ordre)
    fig, ax = nouvelle_figure(8.0, 0.8 + 0.5 * d)
    y = np.arange(d)
    ax.barh(y + 0.18, so.total[i][ordre], height=0.34, color=COULEURS[0],
            label="indice total S_T")
    ax.barh(y - 0.18, so.premier_ordre[i][ordre], height=0.34,
            color=COULEURS[2], label="premier ordre S_1")
    if so.total_ic is not None:
        err = np.vstack([so.total[i] - so.total_ic[0, i],
                         so.total_ic[1, i] - so.total[i]])[:, ordre]
        ax.errorbar(so.total[i][ordre], y + 0.18, xerr=np.abs(err),
                    fmt="none", ecolor=ENCRE_2, capsize=2, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([so.parametres[j].etiquette for j in ordre],
                       fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    style_axes(ax, f"Indices de Sobol : {_etiquette_sortie(sortie)}",
               "Part de la variance (0 à 1)", "")
    ax.set_xlim(min(0.0, float(np.nanmin(so.premier_ordre[i])) - 0.05),
                max(1.0, float(np.nanmax(so.total[i])) + 0.05))
    return terminer(fig, ax, chemin, None)


def _section_sobol(an: Analyse, res: ResultatsAnalyse, L: list[str],
                   dossier: Path) -> None:
    so = res.sobol
    if so is None:
        return
    d = len(so.parametres)
    L.append("## 4. Sensibilité globale : indices de Sobol\n")
    L.append(f"Estimateur de Saltelli (`scipy.stats.sobol_indices`), "
             f"n = {so.n} échantillons de base, {d} paramètres uniformes "
             f"dans leurs plages : n·(d + 2) = {so.n * (d + 2)} "
             f"simulations, {_f(res.durees_s.get('sobol', 0), 2)} s, "
             f"graine {so.graine}. S_1 : part de la variance due au "
             f"paramètre seul ; S_T : avec ses interactions ; intervalle "
             f"de confiance à 95 % par bootstrap quand il est donné. Les "
             f"indices sont bruités quand n est petit : un indice "
             f"légèrement négatif vaut zéro.")
    if so.echecs:
        L.append(f" **{so.echecs} simulations échouées**, remplacées par "
                 f"le point nominal (biais possible).")
    L.append("")
    for s in an.sorties:
        i = so.sorties.index(s)
        L.append(f"### {_etiquette_sortie(s)}\n")
        L.append("| Rang | Paramètre | S_1 | S_T | IC 95 % de S_T |")
        L.append("|---|---|---|---|---|")
        for k, (p, s1, st) in enumerate(so.classement(s), 1):
            j = so.parametres.index(p)
            ic = ("–" if so.total_ic is None else
                  f"[{so.total_ic[0, i, j]:.2f}, {so.total_ic[1, i, j]:.2f}]")
            L.append(f"| {k} | {p.etiquette} | {s1:.2f} | {st:.2f} | {ic} |")
        L.append("")
    fig = _fig_sobol(so, an.sorties[0], dossier / "sobol.png")
    L.append(f"![sobol]({fig})\n")


def _fig_incertitudes(inc: ResultatIncertitudes, sortie: str,
                      chemin: Path) -> str | None:
    j = inc.sorties.index(sortie)
    v = inc.valeurs[:, j]
    v = v[~np.isnan(v)]
    if v.size < 2:
        return None
    it = inc.intervalle(sortie)
    fig, ax = nouvelle_figure(8.0, 4.0)
    ax.hist(v, bins=max(6, min(20, v.size // 3)), color=COULEURS[0],
            alpha=0.85)
    ax.axvline(it.nominal, color=COULEURS[1], linewidth=2)
    ax.text(it.nominal, ax.get_ylim()[1] * 0.95, " nominal",
            color=COULEURS[1], fontsize=9, va="top")
    for x, t in ((it.p05, "5 %"), (it.p95, "95 %")):
        ax.axvline(x, color=ENCRE_2, linewidth=1, linestyle=(0, (4, 3)))
        ax.text(x, ax.get_ylim()[1] * 0.85, f" {t}", color=ENCRE_2,
                fontsize=8, va="top")
    style_axes(ax, f"Incertitude propagée : {_etiquette_sortie(sortie)} "
               f"({inc.n} tirages)", _etiquette_sortie(sortie),
               "Nombre de tirages")
    return terminer(fig, ax, chemin, None)


def _section_incertitudes(an: Analyse, res: ResultatsAnalyse,
                          L: list[str], dossier: Path) -> None:
    inc = res.incertitudes
    if inc is None:
        return
    L.append("## 5. Propagation des incertitudes du registre\n")
    L.append(f"Hypercube latin de {inc.n} tirages (graine {inc.graine}) "
             f"sur {len(inc.parametres)} paramètres tirés uniformément "
             f"dans leur plage ({_f(res.durees_s.get('incertitudes', 0), 2)}"
             f" s) : "
             + " ; ".join(f"{p.etiquette} {p.texte_plage()} ({p.origine})"
                          for p in inc.parametres) + ".")
    if inc.echecs:
        L.append(f" {inc.echecs} tirages échoués (exclus).")
    L.append("\n| Sortie | Nominal | Minimum | 5 % | Médiane | 95 % | "
             "Maximum | ± (90 %) | ± relatif |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for it in inc.intervalles:
        rel = (it.demi_largeur_90 / abs(it.nominal) * 100
               if it.nominal else float("nan"))
        L.append(f"| {_etiquette_sortie(it.sortie)} | {_f(it.nominal)} | "
                 f"{_f(it.minimum)} | {_f(it.p05)} | {_f(it.mediane)} | "
                 f"{_f(it.p95)} | {_f(it.maximum)} | "
                 f"{_f(it.demi_largeur_90)} | {rel:.1f} % |")
    L.append("\nCorrélation de rang (Spearman) paramètre → sortie : +1 "
             "quand la sortie monte toujours avec le paramètre, −1 "
             "quand elle descend, ≈ 0 sans effet monotone.\n")
    L.append("| Paramètre | " + " | ".join(_etiquette_sortie(s)
                                           for s in inc.sorties) + " |")
    L.append("|---|" + "---|" * len(inc.sorties))
    for k, p in enumerate(inc.parametres):
        L.append(f"| {p.etiquette} | "
                 + " | ".join(f"{inc.spearman[j, k]:+.2f}"
                              for j in range(len(inc.sorties))) + " |")
    L.append("")
    fig = _fig_incertitudes(inc, an.sorties[0], dossier / "incertitudes.png")
    if fig:
        L.append(f"![incertitudes]({fig})\n")


def _coude(F: np.ndarray) -> int | None:
    """Indice du point du front le plus loin de la corde qui joint ses
    deux extrémités (objectifs normalisés) : le « coude »."""
    if F.shape[0] < 3:
        return None
    G = (F - F.min(axis=0)) / np.where(np.ptp(F, axis=0) > 0,
                                       np.ptp(F, axis=0), 1.0)
    a, b = G[0], G[-1]
    ab = b - a
    n = np.hypot(*ab)
    if n == 0:
        return None
    dist = np.abs(ab[0] * (G[:, 1] - a[1]) - ab[1] * (G[:, 0] - a[0])) / n
    return int(np.argmax(dist))


def _fig_pareto(res: ResultatsAnalyse, chemin: Path) -> str:
    pa = res.pareto
    assert pa is not None
    obj = res.pareto_objectifs
    signes = np.array([-1.0 if o["sens"] == "max" else 1.0 for o in obj])
    F = pa.F * signes
    ok = ~np.isnan(F).any(axis=1)
    fig, ax = nouvelle_figure(8.0, 5.0)
    ax.scatter(F[ok, 0], F[ok, 1], s=12, color=ENCRE_2, alpha=0.35,
               label="toutes les évaluations")
    Ff = F[pa.front]
    ax.plot(Ff[:, 0], Ff[:, 1], color=COULEURS[1], linewidth=1.5,
            marker="o", ms=5, label="front de Pareto")
    k = _coude(pa.F[pa.front])
    if k is not None:
        ax.scatter([Ff[k, 0]], [Ff[k, 1]], s=90, facecolors="none",
                   edgecolors=COULEURS[0], linewidths=2, zorder=5)
        ax.annotate("coude", (Ff[k, 0], Ff[k, 1]), xytext=(8, 8),
                    textcoords="offset points", color=COULEURS[0],
                    fontsize=9)
    nom = [res.nominal.sorties[o["sortie"]] for o in obj]
    ax.scatter([nom[0]], [nom[1]], marker="s", s=60, color=COULEURS[2],
               zorder=6, label="nominal")
    ax.legend(frameon=False, fontsize=8)
    style_axes(ax, "Front de Pareto (NSGA-II)",
               _etiquette_sortie(obj[0]["sortie"])
               + (" ↑" if obj[0]["sens"] == "max" else " ↓"),
               _etiquette_sortie(obj[1]["sortie"])
               + (" ↑" if obj[1]["sens"] == "max" else " ↓"))
    return terminer(fig, ax, chemin, None)


def _section_pareto(an: Analyse, res: ResultatsAnalyse, L: list[str],
                    dossier: Path) -> None:
    pa = res.pareto
    if pa is None:
        return
    r = pa.reglages
    obj = res.pareto_objectifs
    vars_ = res.pareto_variables
    L.append("## 6. Front de Pareto (NSGA-II)\n")
    sens = {"max": "maximiser", "min": "minimiser"}
    L.append("Objectifs : "
             + " ; ".join(f"**{_etiquette_sortie(o['sortie'])}** "
                          f"({sens[o['sens']]})" for o in obj)
             + ". Variables : "
             + " ; ".join(f"{v.etiquette} {v.texte_plage()}" for v in vars_)
             + ".\n")
    L.append("| Réglage | Valeur |")
    L.append("|---|---|")
    p_mut = r.p_mutation if r.p_mutation is not None else 1.0 / len(vars_)
    for k, v in (("population", r.population),
                 ("générations", r.generations),
                 ("croisement SBX : probabilité", r.p_croisement),
                 ("croisement SBX : η", r.eta_croisement),
                 ("mutation polynomiale : probabilité par variable",
                  f"{p_mut:.3g}"),
                 ("mutation polynomiale : η", r.eta_mutation),
                 ("graine", r.graine),
                 ("évaluations", pa.evaluations),
                 ("échecs (pénalisés)", pa.echecs),
                 ("durée (s)", _f(res.durees_s.get("pareto", 0), 2))):
        L.append(f"| {k} | {v} |")
    L.append("")
    signes = np.array([-1.0 if o["sens"] == "max" else 1.0 for o in obj])
    L.append("| Point | " + " | ".join(v.etiquette for v in vars_) + " | "
             + " | ".join(_etiquette_sortie(o["sortie"]) for o in obj)
             + " |")
    L.append("|---|" + "---|" * (len(vars_) + len(obj)))
    k_coude = _coude(pa.F[pa.front])
    for n, i in enumerate(pa.front):
        etiquette = str(n + 1)
        if n == 0 or n == len(pa.front) - 1:
            etiquette += " (extrémité)"
        if k_coude is not None and n == k_coude:
            etiquette += " (coude)"
        vals = [v.affichage(v.depuis_normalise(u))
                for v, u in zip(vars_, pa.X[i])]
        L.append(f"| {etiquette} | " + " | ".join(_f(x) for x in vals)
                 + " | " + " | ".join(_f(x) for x in pa.F[i] * signes)
                 + " |")
    L.append("")
    fig = _fig_pareto(res, dossier / "pareto.png")
    L.append(f"![pareto]({fig})\n")
    for k, v in enumerate(vars_):
        u = pa.X[pa.front, k]
        for borne, nom in ((u <= 0.02, "basse"), (u >= 0.98, "haute")):
            part = float(borne.mean()) if u.size else 0.0
            if part >= 0.25:
                L.append(f"**Borne atteinte** : {v.etiquette} est à sa "
                         f"borne {nom} ({v.texte_plage()}) sur "
                         f"{part * 100:.0f} % du front : c'est la plage "
                         f"choisie qui limite le front, pas la physique ; "
                         f"élargir la plage (ou ajouter la contrainte qui "
                         f"la justifie) changerait le résultat.\n")
    if len(pa.front) >= 2:
        F = pa.F[pa.front] * signes
        a, b = F[0], F[-1]
        L.append(f"Lecture : d'une extrémité à l'autre du front, "
                 f"{_etiquette_sortie(obj[0]['sortie'])} passe de "
                 f"{_f(a[0])} à {_f(b[0])} pendant que "
                 f"{_etiquette_sortie(obj[1]['sortie'])} passe de "
                 f"{_f(a[1])} à {_f(b[1])}. Tout point sous le front est "
                 f"dominé : une autre configuration fait mieux sur un "
                 f"objectif sans faire pire sur l'autre. Le coude est le "
                 f"point le plus loin de la corde entre les extrémités : "
                 f"au-delà, chaque gain sur un objectif coûte de plus en "
                 f"plus sur l'autre.\n")


def _section_domaine(an: Analyse, res: ResultatsAnalyse,
                     L: list[str]) -> None:
    points = res.tous_les_points()
    compteur: Counter[str] = Counter()
    exemples: dict[str, dict[str, float]] = {}
    for r in points:
        for a in set(_nettoyer_avis(x) for x in r.avertissements):
            compteur[a] += 1
            exemples.setdefault(a, r.point)
    nominal = set(_nettoyer_avis(x) for x in res.nominal.avertissements)
    L.append("## 7. Avertissements de domaine de validité pendant les "
             "balayages\n")
    L.append(f"{len(points)} simulations au total. Chaque avertissement "
             f"est compté une fois par simulation ; « nominal » signale "
             f"qu'il apparaît déjà au point nominal. Les autres n'ont été "
             f"déclenchés que par des combinaisons de paramètres : ces "
             f"zones de l'espace exploré sortent du domaine d'une "
             f"corrélation et leurs résultats sont à lire avec cette "
             f"réserve.\n")
    L.append("| Avertissement | Simulations | Part | Nominal ? | Exemple "
             "de point (SI ou facteur) |")
    L.append("|---|---|---|---|---|")
    for a, n in compteur.most_common():
        ex = ", ".join(f"{k} = {_f(v)}" for k, v in exemples[a].items())
        L.append(f"| {a} | {n} | {n / len(points) * 100:.0f} % | "
                 f"{'oui' if a in nominal else 'non'} | {ex} |")
    echecs = [r for r in points if not r.valide]
    if echecs:
        motifs: Counter[str] = Counter(r.erreur[:90] for r in echecs)
        L.append(f"\nSimulations échouées : {len(echecs)} ("
                 + " ; ".join(f"{m} : {n}" for m, n in motifs.most_common())
                 + ").")
    L.append("")


def _ecrire_csv(an: Analyse, res: ResultatsAnalyse, dossier: Path) -> None:
    noms = [p.nom for p in an.parametres]
    with open(dossier / "evaluations.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["etape", *noms, *an.sorties, "arret", "erreur"])
        for etape, pts in (("nominal", [res.nominal]),
                           ("tornade", res.tornade.resultats
                            if res.tornade else []),
                           ("sobol", res.sobol.resultats
                            if res.sobol else []),
                           ("incertitudes", res.incertitudes.resultats
                            if res.incertitudes else []),
                           ("pareto", res.pareto_points)):
            for r in pts:
                w.writerow([etape, *[r.point.get(n, "") for n in noms],
                            *[r.sorties.get(s, "") for s in an.sorties],
                            r.arret, r.erreur])


def ecrire_rapport(an: Analyse, res: ResultatsAnalyse,
                   dossier: Path, commande: str = "") -> Path:
    dossier.mkdir(parents=True, exist_ok=True)
    L = [f"# Analyse « {an.nom} » : sensibilité, incertitudes, Pareto\n",
         f"*{an.description}*\n",
         f"*Généré par `{commande or 'python -m caes analyser'}` "
         f"({res.procs} processus) ; fichier d'analyse `{an.chemin}` ; "
         f"méthodes : formules F44 à F46 de `docs/formules.md`.*\n"]
    _section_parametres(an, L)
    _section_nominal(an, res, L)
    _section_tornade(an, res, L, dossier)
    _section_sobol(an, res, L, dossier)
    _section_incertitudes(an, res, L, dossier)
    _section_pareto(an, res, L, dossier)
    _section_domaine(an, res, L)
    total = sum(res.durees_s.values())
    L.append(f"*Durée totale des balayages : {total:.0f} s.*\n")
    chemin = dossier / "analyse.md"
    chemin.write_text("\n".join(L), encoding="utf-8")
    _ecrire_csv(an, res, dossier)
    with open(dossier / "resultats.pkl", "wb") as f:
        pickle.dump(res, f)
    return chemin


def relire_resultats(dossier: Path) -> ResultatsAnalyse:
    """Résultats d'une exécution précédente (``resultats.pkl``), pour
    réécrire le rapport sans resimuler (``--rendu``)."""
    with open(dossier / "resultats.pkl", "rb") as f:
        res = pickle.load(f)
    if not isinstance(res, ResultatsAnalyse):
        raise ValueError(f"{dossier / 'resultats.pkl'} : contenu inattendu")
    return res


def main(argv: list[str] | None = None) -> int:
    """Ligne de commande (appelée par ``python -m caes analyser``)."""
    import argparse

    from caes.analyse.parametres import charger_analyse

    p = argparse.ArgumentParser(
        prog="python -m caes analyser",
        description="Sensibilité, incertitudes et front de Pareto d'une "
                    "configuration (fichier d'analyse YAML).")
    p.add_argument("analyse", type=Path, help="fichier d'analyse YAML")
    p.add_argument("--sortie", "-s", type=Path, default=None,
                   help="dossier de sortie (défaut : rapports/analyse/"
                        "<nom>/)")
    p.add_argument("--procs", "-p", type=int, default=None,
                   help="processus en parallèle (défaut : cœurs − 2)")
    p.add_argument("--etapes", default=",".join(ETAPES),
                   help="étapes, séparées par des virgules : "
                        + ", ".join(ETAPES))
    p.add_argument("--rapide", action="store_true",
                   help="échantillons minuscules (essai du format, pas "
                        "un résultat)")
    p.add_argument("--rendu", action="store_true",
                   help="réécrit le rapport depuis resultats.pkl du "
                        "dossier de sortie, sans resimuler")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import os

    procs = args.procs if args.procs is not None else max(
        1, (os.cpu_count() or 2) - 2)
    etapes = tuple(e.strip() for e in args.etapes.split(",") if e.strip())
    inconnues = [e for e in etapes if e not in ETAPES]
    if inconnues:
        print(f"étapes inconnues : {inconnues}", file=sys.stderr)
        return 2
    an = charger_analyse(args.analyse)
    _dire(f"analyse « {an.nom} » : {len(an.parametres)} paramètres, "
          f"{len(an.sorties)} sorties, {procs} processus, étapes "
          f"{', '.join(etapes)}")
    t0 = time.perf_counter()
    sortie = args.sortie or Path("rapports") / "analyse" / an.nom
    if args.rendu:
        res = relire_resultats(sortie)
    else:
        res = executer(an, procs, etapes, args.rapide)
    chemin = ecrire_rapport(an, res, sortie,
                            "python -m caes analyser "
                            + " ".join(argv or sys.argv[1:]))
    _dire(f"rapport écrit : {chemin} ({time.perf_counter() - t0:.0f} s)")
    return 0
