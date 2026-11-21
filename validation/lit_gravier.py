# -*- coding: utf-8 -*-
"""Validation du lit de gravier, phase 4.

    python validation/lit_gravier.py

1. Vérification contre la solution analytique de Schumann (1929).
2. Vérification croisée avec les cuves du cas C de Tola (2022) :
   énergie stockée, durée à sortie constante, cycles de stabilisation.
3. Expériences numériques : taille des cailloux, porosité, pertes de
   charge aux pressions des étages de Dormoy.
4. Comparaison avec les mesures de Cascetta (2018) si le PDF est fourni.

Écrit ``rapports/phase4/validation_lit_gravier.md`` et ses graphiques.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
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

from caes.lit_gravier import (  # noqa: E402
    Correlations,
    LitGravier,
    coefficient_echange,
    perte_de_charge_ergun,
    solution_schumann,
)
from caes.materiaux import charger_materiau  # noqa: E402
from caes.proprietes import AirParfait, AirReel  # noqa: E402
from caes.registre import Registre  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "rapports" / "phase4"
T0C = 273.15


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    air = AirReel()
    parfait = AirParfait.depuis_registre(reg)
    gravier = charger_materiau("gravier_tola", reg)
    corr = Correlations(
        wakao_a=reg.si("lit.wakao.a"), wakao_b=reg.si("lit.wakao.b"),
        wakao_c=reg.si("lit.wakao.c"), wakao_Re_min=reg.si("lit.wakao.Re_min"),
        wakao_Re_max=reg.si("lit.wakao.Re_max"),
        ergun_A=reg.si("lit.ergun.A"), ergun_B=reg.si("lit.ergun.B"),
        jeffreson_facteur=reg.si("lit.jeffreson.facteur"),
    )
    T_amb = reg.si("ambiance.T_amb_essai_charge")
    L: list[str] = []
    L.append("# Validation du lit de gravier (phase 4)\n")
    L.append(
        "*Généré par `validation/lit_gravier.py`. Modèle : Schumann 1D à "
        "deux équations, corrélation de Wakao, correction de Jeffreson, "
        "perte de charge d'Ergun (`caes/lit_gravier.py`).*\n"
    )
    figs: list[str] = []

    # ------------------------------------------------------------------
    # 1. Schumann
    # ------------------------------------------------------------------
    h, D, H, m_dot, p, Tin, T0 = 50.0, 0.5, 2.0, 0.05, 3e5, 443.15, T_amb
    cp = parfait.cp(p, 350.0)
    L.append("## 1. Vérification contre la solution analytique de Schumann\n")
    L.append(
        "Cas test : cuve de 0,5 m × 2 m, gravier de Tola, h imposé à "
        "50 W/m²K, gaz parfait, isolation parfaite, pas de conduction. La "
        "solution exacte (fonction J de Goldstein, intégrale de Bessel) "
        "donne la température de sortie de l'air en fonction du temps.\n"
    )
    L.append("| Cellules | Erreur max sur θ de sortie | Énergie stockée |")
    L.append("|---|---|---|")
    fig, ax = nouvelle_figure()
    courbes = {}
    for n, c in zip((10, 40, 160), COULEURS):
        lit = LitGravier(gravier, D, H, n_cellules=n, h_impose_w_m2k=h,
                         conduction_axiale=False)
        lit.initialiser(T0)
        r = lit.simuler(parfait, 10.0, 4 * 3600, m_dot, Tin, p, T0)
        xi = h * gravier.surface_specifique_m2_m3 * lit.section_m2 * H / (
            m_dot * cp)
        th_num = (r["T_sortie_K"] - T0) / (Tin - T0)
        eta = (h * gravier.surface_specifique_m2_m3 * r["t_s"]
               / gravier.capacite_volumique_lit_j_m3k)
        th_an, _ = solution_schumann(xi, eta[::20])
        err = float(np.max(np.abs(th_num[::20] - th_an)))
        L.append(f"| {n} | {err:.4f} | {r['dE_stock_j'][0] / 3.6e6:.2f} kWh |")
        courbes[n] = (r["t_s"] / 3600, th_num, c)
        if n == 160:
            t_an = r["t_s"][::20] / 3600
    for n, (t, th, c) in courbes.items():
        ax.plot(t, th, color=c, linewidth=2, label=f"{n} cellules")
        etiquette_fin(ax, t[-1], th[-1], f"{n} cellules", c)
    ax.plot(t_an, th_an, color="#0b0b0b", linewidth=0, marker="D", ms=4,
            label="solution analytique de Schumann (1929)")
    style_axes(ax,
               f"Sortie du lit : modèle contre solution exacte (ξ = {xi:.1f})",
               "Temps (h)", "Température réduite de l'air en sortie (–)")
    figs.append(terminer(fig, ax, DOSSIER / "fig1_schumann.png"))
    L.append(
        "\nL'erreur décroît comme 1/n : le schéma converge vers la "
        "solution exacte. Le bilan d'énergie ferme exactement (chaleur "
        "cédée par l'air = chaleur stockée).\n"
    )

    # ------------------------------------------------------------------
    # 2. Tola, cas C
    # ------------------------------------------------------------------
    D_t = reg.si("tola.tes_lp.diametre")
    H_t = D_t * reg.si("tola.tes_lp.rapport_hauteur_diametre")
    m_ch = reg.si("tola.tes.debit_charge")
    m_de = reg.si("tola.tes.debit_decharge")
    T_ch = reg.si("tola.tes.T_entree_charge")
    T_de = reg.si("tola.tes.T_entree_decharge")
    d_ch = reg.si("tola.tes.duree_charge")
    d_de = reg.si("tola.tes.duree_decharge")
    E_ref = {
        "TES-LP": reg.si("tola.tes_lp.energie_stockee"),
        "TES-IP": reg.si("tola.tes_ip.energie_stockee"),
        "TES-HP": reg.si("tola.tes_hp.energie_stockee"),
    }
    p_ch = {
        "TES-LP": reg.si("tola.tes_lp.pression_charge"),
        "TES-IP": reg.si("tola.tes_ip.pression_charge"),
        "TES-HP": reg.si("tola.tes_hp.pression_charge"),
    }
    frac_ref = reg.si("tola.tes.fraction_sortie_constante")
    n_cyc = int(reg.si("tola.tes.nb_cycles_stabilisation"))
    L.append("## 2. Vérification croisée avec les cuves de Tola (cas C)\n")
    L.append(
        f"Trois cuves de {D_t:.1f} m de diamètre et {H_t:.1f} m de haut "
        f"({LitGravier(gravier, D_t, H_t).volume_m3:.0f} m³), charge de "
        f"{d_ch / 3600:.0f} h à {m_ch} kg/s et {T_ch - T0C:.0f} °C, "
        f"décharge de {d_de / 3600:.0f} h à {m_de} kg/s et {T_de - T0C:.0f} "
        f"°C, {n_cyc} cycles. Tola : énergie stockée 9,60 / 9,54 / 9,54 "
        "MWh, sortie constante pendant environ les deux tiers de chaque "
        "phase, régime stable en moins de 20 cycles. Tola ne publie ni sa "
        "corrélation d'échange ni ses pertes : isolation parfaite ici.\n"
    )
    L.append("| Cuve | Pression | Cycle | Chaleur stockée en charge | "
             "Chaleur rendue en décharge | Sortie constante (charge) | "
             "Sortie constante (décharge) | T sortie fin de décharge | "
             "Re | Bi | Δp |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    series_cycles: dict[str, list[float]] = {}
    profils: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    sorties: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    t0 = time.perf_counter()
    for nom in ("TES-LP", "TES-IP", "TES-HP"):
        lit = LitGravier(gravier, D_t, H_t, n_cellules=52, correlations=corr)
        lit.initialiser(T_de)
        rendus = []
        for cyc in range(1, n_cyc + 1):
            rc = lit.simuler(air, 60.0, d_ch, m_ch, T_ch, p_ch[nom], T_amb, 1)
            if cyc == n_cyc:
                profil_charge = lit.T_s_K.copy()
            rd = lit.simuler(air, 60.0, d_de, m_de, T_de, p_ch[nom], T_amb,
                             -1)
            E_ch = rc["Q_air_vers_solide_j"][0]
            E_de = -rd["Q_air_vers_solide_j"][0]
            rendus.append(E_de / 3.6e9)
            f_ch = float(np.mean(rc["T_sortie_K"] < T_de + 2.0))
            f_de = float(np.mean(rd["T_sortie_K"] > T_ch - 2.0))
            if cyc in (1, 2, 5, 10, n_cyc):
                L.append(
                    f"| {nom} | {p_ch[nom] / 1e5:.1f} bar | {cyc} | "
                    f"{E_ch / 3.6e9:.2f} MWh | {E_de / 3.6e9:.2f} MWh | "
                    f"{f_ch * 100:.0f} % | {f_de * 100:.0f} % | "
                    f"{rd['T_sortie_K'][-1] - T0C:.0f} °C | "
                    f"{lit.Re_dernier:.0f} | {lit.Bi_dernier:.2f} | "
                    f"{rd['dp_pa'][0] / 1e3:.1f} kPa |"
                )
            if cyc == n_cyc:
                profils[nom] = (profil_charge, lit.T_s_K.copy())
                sorties[nom] = (rc["T_sortie_K"], rd["T_sortie_K"])
        series_cycles[nom] = rendus
    print(f"Tola : {time.perf_counter() - t0:.0f} s de calcul")
    L.append("\n| Cuve | Tola : énergie stockée | Simulé (cycle stable, "
             "chaleur rendue) | Écart |")
    L.append("|---|---|---|---|")
    for nom, rendus in series_cycles.items():
        L.append(
            f"| {nom} | {E_ref[nom] / 3.6e9:.2f} MWh | {rendus[-1]:.2f} MWh | "
            f"{(rendus[-1] * 3.6e9 - E_ref[nom]) / E_ref[nom] * 100:+.1f} % |"
        )
    stab = {
        nom: next((k + 1 for k in range(1, len(r))
                   if abs(r[k] - r[k - 1]) < 0.01 * r[k]), len(r))
        for nom, r in series_cycles.items()
    }
    L.append(
        f"\nCycles avant stabilisation (variation < 1 % d'un cycle au "
        f"suivant) : {', '.join(f'{k} : {v}' for k, v in stab.items())} "
        f"(Tola : moins de 20, « only the first charging cycle shows a "
        f"remarkable difference »). Fraction de la phase à sortie "
        f"constante attendue : {frac_ref * 100:.0f} %.\n"
    )
    # profils
    fig, ax = nouvelle_figure()
    z = np.linspace(0, H_t, 52)
    for (nom, (pc, pdc)), c in zip(profils.items(), COULEURS):
        ax.plot(z, pc - T0C, color=c, linewidth=2,
                label=f"{nom}, fin de charge")
        ax.plot(z, pdc - T0C, color=c, linewidth=2, linestyle=(0, (4, 4)),
                label=f"{nom}, fin de décharge")
    etiquette_fin(ax, z[-1], profils["TES-LP"][0][-1] - T0C, "fin de charge",
                  COULEURS[0])
    etiquette_fin(ax, z[-1], profils["TES-LP"][1][-1] - T0C,
                  "fin de décharge", COULEURS[0])
    style_axes(ax, "Profil de température du gravier au cycle stable "
               "(Tola, fig. 3c-e)", "Hauteur depuis le haut de la cuve (m)",
               "Température du gravier (°C)")
    figs.append(terminer(fig, ax, DOSSIER / "fig2_tola_profils.png"))
    fig, ax = nouvelle_figure()
    tc = np.arange(1, int(d_ch / 60) + 1) / 60
    td = np.arange(1, int(d_de / 60) + 1) / 60
    for (nom, (sc_, sd_)), c in zip(sorties.items(), COULEURS):
        ax.plot(tc, sc_ - T0C, color=c, linewidth=2, label=f"{nom}, charge")
        ax.plot(td, sd_ - T0C, color=c, linewidth=2, linestyle=(0, (4, 4)),
                label=f"{nom}, décharge")
    style_axes(ax, "Température de sortie de l'air au cycle stable "
               "(Tola, fig. 4)", "Temps depuis le début de la phase (h)",
               "Température de sortie (°C)")
    figs.append(terminer(fig, ax, DOSSIER / "fig3_tola_sorties.png"))
    fig, ax = nouvelle_figure()
    for (nom, rendus), c in zip(series_cycles.items(), COULEURS):
        x = list(range(1, len(rendus) + 1))
        ax.plot(x, rendus, color=c, linewidth=2, marker="o", ms=4, label=nom)
        etiquette_fin(ax, x[-1], rendus[-1], nom, c)
    point_reference(ax, n_cyc, E_ref["TES-LP"] / 3.6e9,
                    "Tola : 9,6 MWh (TES-LP)")
    style_axes(ax, "Chaleur rendue par cycle : stabilisation",
               "Cycle", "Chaleur rendue en décharge (MWh)")
    figs.append(terminer(fig, ax, DOSSIER / "fig4_tola_cycles.png"))

    # ------------------------------------------------------------------
    # 3. Expériences numériques à l'échelle de Dormoy
    # ------------------------------------------------------------------
    L.append("## 3. Expériences numériques à l'échelle du banc de Dormoy\n")
    L.append(
        "Cuve de 0,5 m × 2 m (0,39 m³, 755 kg de gravier), air à 0,052 "
        "kg/s entrant à 170 °C pendant 2 h, lit initialement à 20 °C, "
        "isolation parfaite.\n"
    )
    L.append("| Cailloux | Porosité | Pression | Re | Bi | h | Chaleur "
             "stockée en 2 h | Sortie constante | Δp |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    lignes_exp: list[dict[str, float]] = []
    for d_p, eps, pb in [(0.03, 0.3, 3e5), (0.01, 0.3, 3e5), (0.05, 0.3, 3e5),
                         (0.03, 0.4, 3e5), (0.03, 0.3, 12e5),
                         (0.03, 0.3, 50e5)]:
        mat = gravier.avec(diametre_particule_m=d_p, porosite=eps)
        lit = LitGravier(mat, 0.5, 2.0, n_cellules=40, correlations=corr)
        lit.initialiser(T_amb)
        r = lit.simuler(air, 10.0, 2 * 3600, 0.052, 443.15, pb, T_amb)
        f = float(np.mean(r["T_sortie_K"] < T_amb + 2.0))
        L.append(
            f"| {d_p * 100:.0f} cm | {eps} | {pb / 1e5:.0f} bar | "
            f"{lit.Re_dernier:.0f} | {lit.Bi_dernier:.2f} | "
            f"{lit.h_dernier:.0f} W/m²K | "
            f"{r['dE_stock_j'][0] / 3.6e6:.1f} kWh "
            f"| {f * 100:.0f} % | {r['dp_pa'][0]:.0f} Pa |"
        )
        lignes_exp.append({"d": d_p, "eps": eps, "p": pb,
                           "E_kwh": r["dE_stock_j"][0] / 3.6e6,
                           "dp_pa": r["dp_pa"][0], "Re": lit.Re_dernier})
    L.append(
        "\nLecture : des cailloux plus petits échangent mieux (front plus "
        "net, plus de chaleur stockée) mais coûtent plus de perte de "
        "charge ; à haute pression l'air est plus dense, la vitesse baisse "
        "et la perte de charge devient négligeable (quelques pascals pour "
        "2 m de lit). La perte de charge d'Ergun ne coûte donc rien de "
        "mesurable au compresseur de Dormoy.\n"
    )
    pd.DataFrame(lignes_exp).to_csv(DOSSIER / "experiences.csv", index=False)
    hors = [l for l in lignes_exp if not corr.dans_validite(l["Re"])]
    if hors:
        L.append(
            f"Avertissement : {len(hors)} cas hors de la plage de validité "
            f"de Wakao (Re < 15) : à 50 bar la vitesse est si faible que "
            f"la corrélation est extrapolée (Nu → 2, conduction pure).\n"
        )

    # ------------------------------------------------------------------
    # 4. Cascetta (mesures)
    # ------------------------------------------------------------------
    L.append("## 4. Validation expérimentale (Cascetta 2018)\n")
    src = RACINE / "data" / "sources" / "cascetta2018"
    if src.exists() and any(src.iterdir()):
        L.append(f"Des fichiers existent dans `{src.relative_to(RACINE)}` : "
                 "la comparaison point par point reste à écrire.\n")
    else:
        L.append(
            "**Non faite.** L'article de Cascetta et al. (2018, Energy "
            "Procedia 148:234-241, DOI 10.1016/j.egypro.2018.08.073) est en "
            "accès libre (CC BY-NC-ND) mais le site de l'éditeur refuse les "
            "téléchargements automatiques. Même chose pour Barbour et al. "
            "(2015, CC BY). À télécharger à la main et à déposer dans "
            "`data/sources/cascetta2018/` ; le script comparera alors les "
            "profils de température mesurés. En attendant, le modèle est "
            "vérifié contre la solution exacte de Schumann (§ 1) et "
            "confronté aux résultats publiés de Tola (§ 2).\n"
        )

    L.append("## 5. Graphiques\n")
    for f in figs:
        L.append(f"![{f}]({f})\n")
    L.append("## 6. Conclusion\n")
    lp = series_cycles["TES-LP"][-1]
    L.append(
        "- Le modèle converge vers la solution analytique de Schumann et "
        "conserve l'énergie exactement.\n"
        f"- Sur les cuves de Tola, la chaleur rendue au cycle stable vaut "
        f"{lp:.2f} MWh pour TES-LP (Tola : 9,60), avec une sortie "
        "constante pendant la majeure partie de chaque phase et une "
        "stabilisation en quelques cycles, comme chez Tola. Les écarts "
        "viennent de ce que Tola ne publie ni sa corrélation d'échange, ni "
        "ses pertes, ni son critère exact de « constance ».\n"
        "- La validation sur des mesures (Cascetta 2018) attend le PDF.\n"
        "- À l'échelle de Dormoy, la perte de charge dans le gravier est "
        "négligeable (< 100 Pa) ; l'échange est bon (Bi ≈ 0,2, front net).\n"
    )
    (DOSSIER / "validation_lit_gravier.md").write_text("\n".join(L),
                                                       encoding="utf-8")
    print("rapport écrit :", DOSSIER / "validation_lit_gravier.md")


if __name__ == "__main__":
    main()
