"""Tableau « 1000 unités » : où va l'énergie utile, étape par étape.

Format de sortie standard de toute configuration (phase 3, généralisé
en phase 6) : pour une charge suivie d'une décharge, les bilans
d'exergie (:mod:`caes.exergie`) sont mis bout à bout et exprimés en
millièmes de l'électricité consommée pendant la charge. Le tableau
Markdown et le graphique en cascade sont produits ici ; le script
``rapports/tableau_1000_unites.py`` les enchaîne sur les cas de Dormoy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from caes.exergie import (
    BilanExergie,
    bilan_exergie_charge,
    bilan_exergie_decharge,
)
from caes.graphiques import (
    COULEURS,
    ENCRE,
    ENCRE_2,
    SURFACE,
    nouvelle_figure,
    style_axes,
    terminer,
)
from caes.systeme import ResultatCharge, ResultatDecharge


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


def cas_depuis_resultats(code: str, titre: str, charge: ResultatCharge,
                         decharge: ResultatDecharge) -> Cas:
    """Construit un cas (et ses bilans d'exergie) à partir des résultats."""
    return Cas(code, titre, charge, decharge, bilan_exergie_charge(charge),
               bilan_exergie_decharge(decharge))


def u(cas: Cas, val_j: float) -> float:
    """Convertit des joules en « unités sur 1000 »."""
    return val_j / cas.unite_j


def lignes_tableau(cas: Cas) -> list[dict[str, object]]:
    """Lignes du tableau : étape, exergie perdue, exergie restante, chaleur."""
    bc, bd = cas.bilan_charge, cas.bilan_decharge
    L: list[dict[str, object]] = []
    reste = 1000.0
    L.append({"etape": "Électricité tirée du réseau", "perdu": None,
              "reste": reste, "chaleur": None, "note": "charge"})
    for nom, val in bc.postes.items():
        perdu = u(cas, val)
        reste -= perdu
        chaleur = None
        note = ""
        if nom.startswith("refroidisseur"):
            i = int(nom.split()[1])
            q_tot = u(cas, bc.chaleurs_j[f"refroidisseur {i}"])
            q_sup = u(cas, bc.chaleurs_j[f"refroidisseur {i} > seuil"])
            chaleur = (f"{q_tot:.0f} rejetées, dont {q_sup:.0f} au-dessus "
                       f"du seuil")
            note = "récupérable dans un stockage de chaleur"
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
    coussin0 = u(cas, bc.exergie_initiale_j)
    reste = stock + coussin0
    L.append({"etape": "Exergie disponible (stock + coussin initial)",
              "perdu": None, "reste": reste, "chaleur": None,
              "note": f"coussin initial {coussin0:.0f}"})
    rech = u(cas, bd.exergie_rechauffage_j)
    q = sum(v for k, v in bd.chaleurs_j.items() if "réchauffage" in k)
    if rech > 0:
        reste += rech
        L.append({"etape": "Réchauffage avant les turbines (source externe "
                           "ou huile idéale)",
                  "perdu": -rech, "reste": reste,
                  "chaleur": f"+{u(cas, q):.0f} fournies",
                  "note": "exergie apportée = gain de l'air ; à compter si "
                          "la source est externe"})
    puise = u(cas, bd.exergie_puisee_cuves_j)
    if puise > 0:
        reste += puise
        L.append({"etape": "Exergie puisée dans les cuves de gravier",
                  "perdu": -puise, "reste": reste,
                  "chaleur": f"+{u(cas, q):.0f} fournies à l'air",
                  "note": "chaleur de compression stockée pendant la charge"})
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


def tableau_markdown(cas: Cas,
                     generateur: str = "`caes.tableau_1000`") -> str:
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
        f"{generateur}.*\n",
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


def cascade(cas: Cas, chemin: Path) -> str:
    """Graphique en cascade de l'exergie (unités sur 1000)."""
    from matplotlib.patches import Patch

    L = lignes_tableau(cas)
    fig, ax = nouvelle_figure(11.0, 6.0)
    x = 0
    etiquettes: list[str] = []
    for l in L:
        perdu = l["perdu"]
        if perdu is None:
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
    ax.legend(
        handles=[Patch(color=COULEURS[0], label="total (stock, électricité)"),
                 Patch(color=COULEURS[1], label="exergie perdue ou détruite"),
                 Patch(color=COULEURS[2],
                       label="exergie apportée (réchauffage)"),
                 Patch(color=COULEURS[3],
                       label="coussin restant (pas une perte)")],
        frameon=False, fontsize=8, labelcolor=ENCRE_2, loc="upper right",
    )
    return terminer(fig, ax, Path(chemin), legende=None)
