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

1000 unités = l'électricité consommée pendant la charge.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validation"))
from style_graphiques import (  # noqa: E402
    COULEURS,
    ENCRE,
    ENCRE_2,
    SURFACE,
    nouvelle_figure,
    style_axes,
    terminer,
)

from caes.exergie import (  # noqa: E402
    BilanExergie,
    bilan_exergie_charge,
    bilan_exergie_decharge,
)
from caes.registre import Registre  # noqa: E402
from caes.scenario import Scenario, charger_scenario  # noqa: E402
from caes.systeme import (  # noqa: E402
    ResultatCharge,
    ResultatDecharge,
    simuler_charge,
    simuler_decharge,
)

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "rapports" / "phase3"


@dataclass
class Cas:
    code: str
    titre: str
    charge: ResultatCharge
    decharge: ResultatDecharge
    bilan_charge: BilanExergie
    bilan_decharge: BilanExergie

    @property
    def unite_j(self) -> float:
        return self.bilan_charge.entree_j / 1000.0


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
    return Cas(code, titre, ch, d, bilan_exergie_charge(ch),
               bilan_exergie_decharge(d))


def u(cas: Cas, val_j: float) -> float:
    return val_j / cas.unite_j


def lignes_tableau(cas: Cas) -> list[dict[str, object]]:
    """Lignes du tableau : étape, exergie perdue, exergie restante, chaleur."""
    bc, bd = cas.bilan_charge, cas.bilan_decharge
    L: list[dict[str, object]] = []
    reste = 1000.0
    L.append({"etape": "Électricité tirée du réseau", "perdu": None,
              "reste": reste, "chaleur": None, "note": "charge"})
    chaleur_cle = {
        "refroidisseur": lambda i: (
            f"{u(cas, bc.chaleurs_j[f'refroidisseur {i}']):.0f} rejetées, "
            f"dont {u(cas, bc.chaleurs_j[f'refroidisseur {i} > seuil']):.0f} "
            f"au-dessus de 130 °C"),
    }
    for nom, val in bc.postes.items():
        perdu = u(cas, val)
        reste -= perdu
        chaleur = None
        note = ""
        if nom.startswith("refroidisseur"):
            i = int(nom.split()[1])
            chaleur = chaleur_cle["refroidisseur"](i)
            note = "récupérable dans une cuve (phases 4-5)"
        elif "comprimant" in nom:
            i = int(nom.split()[2])
            q = u(cas, bc.chaleurs_j[f"compression étage {i}"])
            chaleur = f"{q:.0f} rejetées"
            if q < 0:
                note = "n > γ : le modèle absorbe un peu de chaleur"
        elif "parois" in nom:
            q_paroi = u(cas, bc.chaleurs_j["parois du réservoir"])
            chaleur = f"{q_paroi:.0f} perdues"
            note = "chaleur tiède : beaucoup d'énergie, peu d'exergie"
        elif "volumétrique" in nom:
            note = ("dans le modèle, l'air non refoulé a été comprimé : à "
                    "lire avec « moteur et mécanique »")
        L.append({"etape": nom, "perdu": perdu, "reste": reste,
                  "chaleur": chaleur, "note": note})
    stock = u(cas, bc.sorties_utiles_j["exergie stockée dans les réservoirs"])
    L.append({"etape": "**Exergie stockée dans les réservoirs**",
              "perdu": None, "reste": stock, "chaleur": None,
              "note": f"résidu du bilan de charge "
                      f"{bc.residu_relatif * 100:+.2f} %"})
    # Décharge : l'entrée est l'exergie initiale (= stock + coussin
    # initial) plus le réchauffage.
    coussin0 = u(cas, bc.exergie_initiale_j)
    reste = stock + coussin0
    L.append({"etape": "Exergie disponible (stock + coussin initial)",
              "perdu": None, "reste": reste, "chaleur": None,
              "note": f"coussin initial {coussin0:.0f}"})
    rech = u(cas, bd.exergie_rechauffage_j)
    if rech > 0:
        q = sum(v for k, v in bd.chaleurs_j.items() if "réchauffage" in k)
        reste += rech
        L.append({"etape": "Réchauffage avant les turbines (source externe)",
                  "perdu": -rech, "reste": reste,
                  "chaleur": f"+{u(cas, q):.0f} fournies",
                  "note": "exergie apportée = gain de l'air ; à compter si "
                          "la source est externe"})
    for nom, val in bd.postes.items():
        perdu = u(cas, val)
        reste -= perdu
        chaleur = None
        note = ""
        if "parois" in nom:
            chaleur = (f"{-u(cas, bd.chaleurs_j['parois du réservoir']):.0f} "
                       f"reçues des parois")
            note = "l'air se refroidit en se détendant ; la paroi le réchauffe"
        L.append({"etape": nom, "perdu": perdu, "reste": reste,
                  "chaleur": chaleur, "note": note})
    coussin = u(cas, bd.sorties_utiles_j[
        "exergie restant dans les réservoirs (coussin)"])
    elec = u(cas, bd.sorties_utiles_j["électricité produite"])
    L.append({"etape": "Exergie restant dans les réservoirs (coussin)",
              "perdu": coussin, "reste": reste - coussin, "chaleur": None,
              "note": "pas une perte : reste pour le cycle suivant (plus "
                      "froid et plus lourd que le coussin initial, d'où "
                      "une exergie un peu plus grande)"})
    L.append({"etape": "**Électricité rendue au réseau**", "perdu": None,
              "reste": elec, "chaleur": None,
              "note": f"résidu du bilan de décharge "
                      f"{bd.residu_relatif * 100:+.2f} %"})
    return L


def tableau_markdown(cas: Cas) -> str:
    L = lignes_tableau(cas)
    out = [
        f"# Tableau « 1000 unités » : {cas.titre}\n",
        f"*Cas `{cas.code}` : charge `{cas.charge.scenario.nom}` "
        f"({cas.charge.totaux['energie_electrique_kwh']:.1f} kWh = 1000 "
        f"unités, 1 unité = {cas.unite_j / 3.6e6 * 1000:.3f} Wh), puis "
        f"décharge `{cas.decharge.scenario.nom}` enchaînée "
        f"({cas.decharge.totaux['energie_electrique_kwh']:.2f} kWh "
        f"produits). État mort : {cas.bilan_charge.T0_K - 273.15:.0f} °C, "
        f"{cas.bilan_charge.p0_pa / 1e5:.3f} bar. Généré par "
        f"`rapports/tableau_1000_unites.py`.*\n",
        "| # | Étape | Exergie perdue | Exergie restante | Chaleur (énergie) "
        "| Remarque |",
        "|---|---|---|---|---|---|",
    ]
    for k, l in enumerate(L):
        perdu = "" if l["perdu"] is None else f"{l['perdu']:.0f}"
        chaleur = "" if l["chaleur"] is None else str(l["chaleur"])
        out.append(
            f"| {k} | {l['etape']} | {perdu} | {l['reste']:.0f} | {chaleur} "
            f"| {l['note']} |"
        )
    out.append(
        "\nLes colonnes « exergie » comptent l'énergie **utile** (travail "
        "maximal récupérable) ; la colonne « chaleur » compte de "
        "l'**énergie** thermique, dans la même unité. Les deux ne "
        "s'additionnent pas : 100 unités de chaleur à 45 °C ne valent que "
        "8 unités d'exergie.\n"
    )
    return "\n".join(out)


def cascade(cas: Cas, fichier: str) -> str:
    """Graphique en cascade de l'exergie (unités sur 1000)."""
    L = lignes_tableau(cas)
    fig, ax = nouvelle_figure(11.0, 6.0)
    x = 0
    etiquettes: list[str] = []
    for l in L:
        perdu = l["perdu"]
        if perdu is None:
            # barre pleine : total
            ax.bar(x, l["reste"], color=COULEURS[0], width=0.8)
            ax.text(x, l["reste"] + 8, f"{l['reste']:.0f}", ha="center",
                    fontsize=8, color=ENCRE)
        else:
            bas = l["reste"] if perdu > 0 else l["reste"] - abs(perdu)
            c = COULEURS[1] if perdu > 0 else COULEURS[2]
            if "coussin" in str(l["etape"]):
                c = COULEURS[3]
            ax.bar(x, abs(perdu), bottom=bas, color=c, width=0.8)
            if abs(perdu) >= 3:
                ax.text(x, bas + abs(perdu) + 8, f"{abs(perdu):.0f}",
                        ha="center", fontsize=8, color=ENCRE_2)
        etiquettes.append(str(l["etape"]).replace("**", ""))
        x += 1
    ax.set_xticks(range(len(etiquettes)))
    ax.set_xticklabels(etiquettes, rotation=60, ha="right", fontsize=7)
    style_axes(ax, f"Cascade d'exergie sur 1000 unités : {cas.titre}",
               "", "Unités (1000 = électricité consommée)")
    ax.set_facecolor(SURFACE)
    from matplotlib.patches import Patch
    ax.legend(
        handles=[Patch(color=COULEURS[0], label="total (stock, électricité)"),
                 Patch(color=COULEURS[1], label="exergie perdue ou détruite"),
                 Patch(color=COULEURS[2],
                       label="exergie apportée (réchauffage)"),
                 Patch(color=COULEURS[3],
                       label="coussin restant (pas une perte)")],
        frameon=False, fontsize=8, labelcolor=ENCRE_2, loc="upper right",
    )
    return terminer(fig, ax, DOSSIER / fichier, legende=None)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    charge_B = charger_scenario(
        "dormoy_charge_1_190_aspiration_chaude.yaml", reg)
    charge_A = charger_scenario("dormoy_charge_1_190.yaml", reg)
    base = charger_scenario("dormoy_decharge_base.yaml", reg)
    trois = charger_scenario("dormoy_decharge_3etages.yaml", reg)
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
