# -*- coding: utf-8 -*-
"""Tableau « 1000 unités » : où va l'énergie utile, étape par étape.

    python rapports/tableau_1000_unites.py

Pour chaque cas, enchaîne une charge et une décharge (la décharge part
de l'état final de la charge), calcule les bilans d'exergie
(``caes.exergie``) et écrit dans ``rapports/phase3/`` :

* ``tableau_1000_<cas>.md`` : le tableau (colonnes exergie et chaleur) ;
* ``cascade_<cas>.png`` : le graphique en cascade de l'exergie ;
* ``exergie.md`` : synthèse et comparaison avec le calcul à la main de
  la fiche Dormoy (section 4 de `dormoy-2024-caes-hors-sol.md`).

1000 unités = l'électricité consommée pendant la charge. Le tableau et
la cascade sont produits par ``caes.tableau_1000`` (phase 6) ; ce script
garde l'enchaînement des cas de Dormoy et la synthèse de la phase 3.
"""

from __future__ import annotations

import sys
from pathlib import Path

from caes.registre import Registre
from caes.scenario import Scenario, charger_scenario
from caes.systeme import simuler_charge, simuler_decharge
from caes.tableau_1000 import Cas, cas_depuis_resultats, u
from caes.tableau_1000 import cascade as cascade_vers
from caes.tableau_1000 import tableau_markdown as tableau_markdown_cas

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "rapports" / "phase3"


def enchainer(
    code: str, titre: str, sc_charge: Scenario, sc_decharge: Scenario
) -> Cas:
    ch = simuler_charge(sc_charge)
    sc_d = sc_decharge.avec(
        {"reservoir.p_initiale": ch.series["p_res_pa"].iloc[-1],
         "reservoir.T_initiale": ch.series["T_res_K"].iloc[-1],
         "reservoir.T_paroi_initiale": ch.series["T_paroi_K"].iloc[-1]},
        "enchaine",
    )
    d = simuler_decharge(sc_d)
    return cas_depuis_resultats(code, titre, ch, d)


def tableau_markdown(cas: Cas) -> str:
    return tableau_markdown_cas(cas, "`rapports/tableau_1000_unites.py`")


def cascade(cas: Cas, fichier: str) -> str:
    """Cascade écrite dans ``DOSSIER`` (modifiable par les autres rapports)."""
    return cascade_vers(cas, DOSSIER / fichier)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    charge_B = charger_scenario(
        "v1/dormoy_charge_1_190_aspiration_chaude.yaml", reg)
    charge_A = charger_scenario("v1/dormoy_charge_1_190.yaml", reg)
    base = charger_scenario("v1/dormoy_decharge_base.yaml", reg)
    trois = charger_scenario("v1/dormoy_decharge_3etages.yaml", reg)
    p18 = reg.si("cas_base.pression_arret")
    p55 = reg.si("charge_55_190.pression_min")
    cas = [
        enchainer("base", "cas de base de Dormoy (1 étage, sans réchauffage)",
                  charge_B.avec({"reservoir.p_initiale": p18}, "depuis18"),
                  base),
        enchainer("3etages",
                  "3 étages avec réchauffage externe (130/90/90 °C)",
                  charge_B.avec({"reservoir.p_initiale": p55}, "depuis55"),
                  trois),
        enchainer("base_chargeA", "cas de base, charge A (air aspiré à 20 °C)",
                  charge_A.avec({"reservoir.p_initiale": p18}, "depuis18"),
                  base),
    ]
    synthese = [
        "# Phase 3 : bilan d'exergie et tableau « 1000 unités »\n",
        "*Généré par `rapports/tableau_1000_unites.py`. Un tableau détaillé "
        "et une cascade par cas.*\n",
        "## 1. Résumé des cas\n",
        "| Cas | Charge | 1000 unités = | Stocké | Électricité rendue | "
        "Chaleur externe (énergie) | RTE | Résidus (charge / décharge) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in cas:
        bc, bd = c.bilan_charge, c.bilan_decharge
        stock = u(c, bc.sorties_utiles_j[
            "exergie stockée dans les réservoirs"])
        elec = u(c, bd.sorties_utiles_j["électricité produite"])
        q_ext = sum(v for k, v in bd.chaleurs_j.items() if "réchauffage" in k)
        synthese.append(
            f"| {c.code} | {c.charge.scenario.nom} | "
            f"{c.charge.totaux['energie_electrique_kwh']:.1f} kWh | "
            f"{stock:.0f} | {elec:.0f} | {u(c, q_ext):.0f} | "
            f"{elec / 10:.1f} % | {bc.residu_relatif * 100:+.2f} % / "
            f"{bd.residu_relatif * 100:+.2f} % |"
        )
        texte = tableau_markdown(c)
        (DOSSIER / f"tableau_1000_{c.code}.md").write_text(texte,
                                                            encoding="utf-8")
        fig = cascade(c, f"cascade_{c.code}.png")
        print(c.code, "->", DOSSIER / f"tableau_1000_{c.code}.md", fig)

    b = cas[0]
    bc, bd = b.bilan_charge, b.bilan_decharge
    pc = {k: u(b, v) for k, v in bc.postes.items()}
    pd_ = {k: u(b, v) for k, v in bd.postes.items()}
    stock = u(b, bc.sorties_utiles_j["exergie stockée dans les réservoirs"])
    elec = u(b, bd.sorties_utiles_j["électricité produite"])
    moteur = pc["moteur et mécanique"]
    air_vol = pc["air rejeté (rendement volumétrique)"]
    air_sech = pc["air rejeté (sécheur)"]
    compression = sum(v for k, v in pc.items() if "comprimant" in k)
    refroid = sum(v for k, v in pc.items() if k.startswith("refroidisseur"))
    reservoir_c = (pc["laminage vers le réservoir"]
                   + pc["remplissage du réservoir (mélange)"]
                   + pc["chaleur perdue par les parois"])
    coussin = u(b, bd.sorties_utiles_j[
        "exergie restant dans les réservoirs (coussin)"])
    detendeur = pd_["détendeur (laminage)"]
    turbine = sum(v for k, v in pd_.items()
                  if "turbine" in k or "génératrice" in k)
    rejet = pd_["air rejeté à l'atmosphère"]
    res_d = (pd_["réservoir (détente interne)"]
             + pd_["chaleur reçue des parois (exergie de froid perdue)"])
    q_refroid = u(b, sum(
        v for k, v in bc.chaleurs_j.items()
        if k.startswith("refroidisseur") and "seuil" not in k
    ))
    synthese += [
        "\n## 2. Comparaison avec le calcul à la main de la fiche Dormoy "
        "(cas de base)\n",
        "Le calcul à la main (fiche `dormoy-2024-caes-hors-sol.md`, section "
        "2) supposait un gaz parfait à 15 °C, un détendeur réglé à 35 bar "
        "et un arrêt à 50 bar. Le simulateur montre (phase 2) que le cas de "
        "base de Dormoy utilise l'étage 3 seul, donc un détendeur à 3 bar "
        "et un arrêt à 18 bar : la répartition des pertes change beaucoup.\n",
        "| Étape | Calcul à la main (fiche) | Simulateur | Explication |",
        "|---|---|---|---|",
        f"| Moteur et mécanique | 285 | {moteur:.0f} (+ {air_vol:.0f} d'air "
        f"non refoulé) | la fiche prenait 69-74 % sans le rendement "
        f"électrique (94,5 %) ; le modèle applique le travail au débit "
        f"aspiré, d'où la ligne « air non refoulé » à lire avec celle-ci |",
        f"| Compression « chaude » | 271 | {compression:.0f} + "
        f"{refroid:.0f} (refroidisseurs) | la fiche comptait l'excès de "
        f"travail par rapport à l'isotherme ; l'exergie compte la valeur "
        f"de la chaleur rejetée, plus faible parce qu'une partie est tiède |",
        f"| Sécheur | 84 | {air_sech:.0f} | même logique (19 % de l'air à "
        f"l'état de sortie) ; exergie réelle au lieu du gaz parfait |",
        f"| Réservoir (laminage, remplissage, parois) | 0 | "
        f"{reservoir_c:.0f} | non compté dans la fiche |",
        f"| **Stocké** | **360** | **{stock:.0f}** | |",
        f"| Masse morte / coussin | 65 (arrêt à 50 bar) | {coussin:.0f} "
        f"(arrêt à 18 bar) | pas une perte par cycle : l'air reste |",
        f"| Détendeur | 74 (190 → 35 bar) | {detendeur:.0f} (190 → 3 bar) | "
        f"**la vraie perte dominante du cas de base** |",
        f"| Réservoir en décharge | 0 | {res_d:.0f} | détente interne et "
        f"chaleur reçue des parois |",
        f"| Turbine (et génératrice) | 175 | {turbine:.0f} | avec le "
        f"détendeur à 3 bar, il reste peu d'exergie à détruire dans la "
        f"turbine |",
        f"| Air rejeté froid | 0 | {rejet:.0f} | l'air sort à −60 °C : son "
        f"« froid » est une exergie perdue |",
        f"| **Électricité rendue** | **46** | **{elec:.0f}** | Dormoy : "
        f"43-46 ; écart de −15 % connu depuis la phase 2 |",
        "\n### Ce que le simulateur change dans l'histoire\n",
        "- La recharge coûte toujours les deux tiers : moteur, air non "
        "refoulé, chaleur rejetée et sécheur. Les refroidisseurs rejettent "
        f"{q_refroid:.0f} "
        "unités de **chaleur**, mais seulement "
        f"{refroid:.0f} unités d'**exergie** : la chaleur tiède vaut peu, "
        "c'est la part au-dessus de 130 °C qui compte pour la turbine.\n"
        "- Dans le cas de base, le détendeur n'est pas une perte parmi "
        "d'autres : il détruit "
        f"{detendeur / (stock + u(b, bc.exergie_initiale_j)) * 100:.0f} % "
        "de l'exergie disponible, parce qu'il fait chuter la pression de "
        "190 à 3 bar sans rien produire. La turbine à 3 étages (détendeur à "
        "40 bar) est d'abord un moyen de réduire cette perte.\n"
        "- La « masse morte » du cas de base est petite (arrêt à 18 bar) et "
        "n'est pas une perte par cycle.\n",
    ]
    c3 = cas[1]
    bc3, bd3 = c3.bilan_charge, c3.bilan_decharge
    pd3 = {k: u(c3, v) for k, v in bd3.postes.items()}
    rejet3 = pd3["air rejeté à l'atmosphère"]
    turb3 = sum(v for k, v in pd3.items()
                if "turbine" in k or "génératrice" in k)
    q3 = u(c3, sum(v for k, v in bd3.chaleurs_j.items()
                   if "réchauffage" in k))
    stock3 = u(c3, bc3.sorties_utiles_j["exergie stockée dans les réservoirs"])
    coussin3 = u(c3, bd3.sorties_utiles_j[
        "exergie restant dans les réservoirs (coussin)"])
    elec3 = u(c3, bd3.sorties_utiles_j["électricité produite"])
    synthese += [
        "\n## 3. Cas à 3 étages : où va l'exergie du réchauffage\n",
        f"| Poste | Unités |", "|---|---|",
        f"| Exergie stockée par la charge (55 → 190 bar) | {stock3:.0f} |",
        f"| Coussin initial (55 bar) | {u(c3, bc3.exergie_initiale_j):.0f} |",
        f"| Réchauffage externe : chaleur fournie (énergie) | {q3:.0f} |",
        f"| Réchauffage externe : exergie apportée à l'air | "
        f"{u(c3, bd3.exergie_rechauffage_j):.0f} |",
        f"| Détendeur (190 → 40 bar) | {pd3['détendeur (laminage)']:.0f} |",
        f"| Turbines (3 étages) et génératrices | {turb3:.0f} |",
        f"| Air rejeté | {rejet3:.0f} |",
        f"| Coussin final (55 bar) | {coussin3:.0f} |",
        f"| **Électricité rendue** | **{elec3:.0f}** |",
        "\nLa chaleur de réchauffage apporte beaucoup d'énergie mais "
        "nettement moins d'exergie (facteur de Carnot à 130 °C : 27 %). "
        "Si elle vient des refroidisseurs du compresseur (phases 4 et 5), "
        "elle ne coûte rien ; si elle vient d'une source externe, il faut "
        "l'ajouter à la consommation (phase 2, deux définitions du "
        "rendement).\n",
        "\n## 4. Fichiers\n",
    ]
    for c in cas:
        synthese.append(
            f"- `tableau_1000_{c.code}.md`, `cascade_{c.code}.png`"
        )
        synthese.append(f"\n![cascade {c.code}](cascade_{c.code}.png)\n")
    (DOSSIER / "exergie.md").write_text("\n".join(synthese), encoding="utf-8")
    print("synthèse :", DOSSIER / "exergie.md")


if __name__ == "__main__":
    main()
