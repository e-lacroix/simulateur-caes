# -*- coding: utf-8 -*-
"""Génère les scénarios d'exemple de la phase 7 : un par modèle nouveau,
dérivé du banc de Dormoy, avec le même bloc ``ambiance``.

    python scenarios/variantes/generer_variantes.py

Chaque variante part d'un scénario de référence de ``scenarios/``
(charge « aspiration chaude », décharge à 3 étages, architecture D) et
remplace un composant par un autre modèle. Les blocs de composants
(``BLOCS``) sont aussi utilisés par ``tests/test_combinaisons.py`` pour
parcourir toutes les combinaisons du noyau. Les fichiers produits sont
suivis par git ; ne pas les éditer à la main (relancer ce script).
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import yaml

DOSSIER = Path(__file__).resolve().parent
SCENARIOS = DOSSIER.parent
ENTETE = ("# Fichier généré par scenarios/variantes/generer_variantes.py : "
          "ne pas éditer à la main.\n")


def _reg(id_: str) -> str:
    return f"registre:{id_}"


def _val(valeur: float, unite: str, source: str) -> dict[str, Any]:
    return {"valeur": valeur, "unite": unite, "source": source}


SEUIL = _reg("turbine.etage1.temperature_entree")
DEPRAG = {
    i: {
        "p_entree": _reg(f"turbine.etage{i}.pression_entree"),
        "p_sortie": _reg(f"turbine.etage{i}.pression_sortie"),
        "indice_polytropique": _reg(f"turbine.etage{i}.indice_polytropique"),
        "rendement_mecanique": _reg(f"turbine.etage{i}.rendement_mecanique"),
        "rendement_electrique": _reg(
            f"turbine.etage{i}.rendement_electrique"),
        "T_entree_cible": _reg(f"turbine.etage{i}.temperature_entree"),
    }
    for i in (1, 2, 3)
}


def _etages_generiques(sans_p_entree_1: bool = False) -> list[dict]:
    """Les trois étages DEPRAG pour les modèles à rendement : pressions
    nominales, cibles et rendements mécanique / électrique par étage."""
    out = []
    for i in (1, 2, 3):
        e = {k: v for k, v in DEPRAG[i].items()
             if k != "indice_polytropique"}
        if sans_p_entree_1 and i == 1:
            del e["p_entree"]
        out.append(e)
    return out


# ----------------------------------------------------------------------
# Blocs de composants par (type, modèle), dérivés de Dormoy
# ----------------------------------------------------------------------

BLOCS: dict[tuple[str, str], dict[str, Any]] = {}

BLOCS[("compresseur", "isentropique")] = {
    "type": "compresseur", "modele": "isentropique",
    "debit_volumique_aspire": _reg("compresseur.debit_volumique_entree"),
    "debit_massique_aspire": None,
    "rendement_electrique": _reg("compresseur.rendement_electrique#moyen"),
    "rendement_mecanique": _reg("compresseur.rendement_mecanique#moyen"),
    "rendement_isentropique": _reg("shi.compresseur.rendement_isentropique"),
    "pression_refoulement_min": _reg("compresseur.pression_refoulement_min"),
    "etages": [
        {"rapport_pression": _reg("compresseur.rapport_compression_etage1")},
        {"rapport_pression": _reg("compresseur.rapport_compression_etage2")},
        {}, {},
    ],
}
BLOCS[("compresseur", "polytropique_rendement")] = {
    **BLOCS[("compresseur", "isentropique")],
    "modele": "polytropique_rendement",
    "rendement_polytropique": _reg("tola.compresseur.rendement_polytropique"),
}
del BLOCS[("compresseur", "polytropique_rendement")]["rendement_isentropique"]
BLOCS[("compresseur", "isotherme")] = {
    k: v for k, v in BLOCS[("compresseur", "isentropique")].items()
    if k != "rendement_isentropique"}
BLOCS[("compresseur", "isotherme")]["modele"] = "isotherme"

BLOCS[("refroidisseur", "pincement")] = {
    "type": "refroidisseur", "modele": "pincement",
    "pincement": _reg("tola.pincement_air"),
    "T_seuil_chaleur_utile": SEUIL,
}
BLOCS[("refroidisseur", "pincement_perte_de_charge")] = {
    **BLOCS[("refroidisseur", "pincement")],
    "modele": "pincement",
    "pincement": _reg("shi.pincement"),
    "perte_de_charge": _reg("shi.perte_charge_echangeur"),
}
BLOCS[("secheur", "aucun")] = {"type": "secheur", "modele": "aucun"}
BLOCS[("reservoir_air", "adiabatique")] = {
    "type": "reservoir_air", "modele": "adiabatique",
    "volume": _reg("reservoir.volume_total"),
    "surface": _reg("reservoir.surface_equivalente_totale"),
    "surpression_entree": _reg("shi.perte_charge_entree_reservoir"),
}
BLOCS[("detente", "pression_glissante")] = {
    "type": "detente", "modele": "pression_glissante",
    "p_min": _reg("charge_55_190.pression_min"),
}
BLOCS[("turbine", "isentropique")] = {
    "type": "turbine", "modele": "isentropique",
    "debit_massique": _reg("turbine.etage1.debit_massique"),
    "rendement_isentropique": _reg("shi.turbine.rendement_isentropique"),
    "rendement_mecanique": _reg("shi.rendement_mecanique"),
    "rendement_electrique": _reg("shi.rendement_electrique"),
    "etages": _etages_generiques(),
}
BLOCS[("turbine", "isentropique_glissante")] = {
    **BLOCS[("turbine", "isentropique")],
    "etages": _etages_generiques(sans_p_entree_1=True),
}
BLOCS[("turbine", "polytropique_rendement")] = {
    **BLOCS[("turbine", "isentropique")],
    "modele": "polytropique_rendement",
    "rendement_polytropique": _reg("tola.turbine.rendement_polytropique"),
}
del BLOCS[("turbine", "polytropique_rendement")]["rendement_isentropique"]
BLOCS[("turbine", "flugel")] = {
    **BLOCS[("turbine", "isentropique")],
    "modele": "flugel",
    "rendement_isentropique": _reg("zhangS.turbine.rendement_isentropique"),
    "t4": _reg("zhangS.flugel.t4"),
}
BLOCS[("stockage_chaleur", "huile_deux_reservoirs")] = {
    "type": "stockage_chaleur", "modele": "huile_deux_reservoirs",
    "masse": _val(1500, "kg", "calcul personnel : 57 kWh de chaleur de "
                  "compression par charge (phase 5) / (1,494 kJ/kg·K × "
                  "150 K) ≈ 920 kg, arrondi avec marge"),
    "cp": _reg("tola.huile.cp"),
    "pincement": _reg("tola.pincement_huile"),
}
BLOCS[("stockage_chaleur", "eau_sous_pression")] = {
    "type": "stockage_chaleur", "modele": "eau_sous_pression",
    "masse": _val(600, "kg", "calcul personnel : 57 kWh / (4,2 kJ/kg·K × "
                  "150 K) ≈ 330 kg, arrondi avec marge"),
    "pression_cuve": _val(18, "bar", "Shi 2024, figure 7 : eau chaude à "
                          "190 °C et 1,8 MPa"),
    "pincement": _reg("shi.pincement"),
    "marge_ebullition": _val(5, "K", "marge de sécurité sous T_sat (choix "
                             "du projet)"),
}
BLOCS[("isolation", "laine_minerale")] = {
    "materiau": "laine_minerale",
    "epaisseur": _val(0.2, "m", "épaisseur retenue dans le calcul "
                      "personnel de la fiche Dormoy (constante de temps "
                      "≈ 23 jours pour 2 m³)"),
}
BLOCS[("attente", "sans_pertes")] = {
    "type": "attente", "modele": "sans_pertes",
    "duree": _val(14, "j", "transport de deux semaines (plan v2, scénario "
                  "2)"),
}
BLOCS[("attente", "pertes_statiques_14j")] = {
    "type": "attente", "modele": "pertes_statiques",
    "duree": _val(14, "j", "transport de deux semaines (plan v2, scénario "
                  "2)"),
    "dt": _val(1, "h", "choix numérique (pertes lentes)"),
}


# ----------------------------------------------------------------------
# Variantes
# ----------------------------------------------------------------------


def _charger(nom: str) -> dict[str, Any]:
    return yaml.safe_load((SCENARIOS / nom).read_text(encoding="utf-8"))


def _ecrire(nom: str, brut: dict[str, Any]) -> None:
    texte = yaml.safe_dump(brut, allow_unicode=True, sort_keys=False,
                           width=78)
    (DOSSIER / nom).write_text(ENTETE + texte, encoding="utf-8")
    print("écrit :", nom)


def variantes() -> list[tuple[str, dict[str, Any]]]:
    """(nom de fichier, scénario brut) pour chaque modèle nouveau."""
    out: list[tuple[str, dict[str, Any]]] = []
    charge = _charger("dormoy_charge_1_190_aspiration_chaude.yaml")
    decharge = _charger("dormoy_decharge_3etages.yaml")
    D = _charger("D.yaml")

    def var(nom: str, base: dict, description: str,
            remplacements: dict[str, dict | None]) -> None:
        b = copy.deepcopy(base)
        b["nom"] = nom
        b["description"] = description
        for cle, bloc in remplacements.items():
            if bloc is None:
                del b["composants"][cle]
            else:
                b["composants"][cle] = copy.deepcopy(bloc)
        out.append((nom + ".yaml", b))

    # --- charge ------------------------------------------------------------
    var("charge_compresseur_isentropique", charge,
        "Charge de Dormoy avec un compresseur à rendement isentropique "
        "constant (Shi 2024, 86 %) ; rendements mécanique et électrique de "
        "Dormoy, rapports des étages 1 et 2 de Dormoy, étages 3 et 4 libres.",
        {"compresseur": BLOCS[("compresseur", "isentropique")]})
    var("charge_compresseur_polytropique_rendement", charge,
        "Charge de Dormoy avec un compresseur à rendement polytropique "
        "constant (Tola 2022, 88 %).",
        {"compresseur": BLOCS[("compresseur", "polytropique_rendement")]})
    var("charge_compresseur_isotherme", charge,
        "Charge de Dormoy avec la borne isotherme (Baniamerian 2025, éq. 8) :"
        " le travail minimal possible, aucune chaleur à récupérer.",
        {"compresseur": BLOCS[("compresseur", "isotherme")]})
    var("charge_refroidisseur_pincement", charge,
        "Charge de Dormoy avec des refroidisseurs à pincement de 20 K "
        "(Tola 2022, air/air) au lieu des efficacités calibrées.",
        {f"refroidisseur_{i}": BLOCS[("refroidisseur", "pincement")]
         for i in (1, 2, 3, 4)})
    var("charge_refroidisseur_perte_de_charge", charge,
        "Charge avec compresseur isentropique (Shi) et refroidisseurs à "
        "pincement de 10 K avec 0,04 MPa de perte de charge chacun (Shi "
        "2024) : les étages libres compensent les pertes.",
        {"compresseur": BLOCS[("compresseur", "isentropique")],
         **{f"refroidisseur_{i}":
            BLOCS[("refroidisseur", "pincement_perte_de_charge")]
            for i in (1, 2, 3, 4)}})
    var("charge_secheur_aucun", charge,
        "Charge de Dormoy sans sécheur (modèle « aucun ») : ce que coûte "
        "réellement le sécheur.",
        {"secheur": BLOCS[("secheur", "aucun")]})
    var("charge_reservoir_adiabatique", charge,
        "Charge de Dormoy avec un réservoir adiabatique (Shi 2024) et 0,2 MPa"
        " de surpression à l'entrée : montre pourquoi ce modèle vaut pour "
        "une caverne, pas pour 5,86 m³.",
        {"reservoir": BLOCS[("reservoir_air", "adiabatique")]})

    # --- décharge ----------------------------------------------------------
    var("decharge_turbine_isentropique", decharge,
        "Décharge à 3 étages avec une turbine à rendement isentropique "
        "constant (Shi 2024, 90 %) aux pressions nominales DEPRAG.",
        {"turbine": BLOCS[("turbine", "isentropique")]})
    var("decharge_turbine_polytropique_rendement", decharge,
        "Décharge à 3 étages avec une turbine à rendement polytropique "
        "constant (Tola 2022, 86 %).",
        {"turbine": BLOCS[("turbine", "polytropique_rendement")]})
    b = copy.deepcopy(decharge)
    b["composants"]["detendeur"] = BLOCS[("detente", "pression_glissante")]
    b["composants"]["turbine"] = BLOCS[("turbine", "isentropique_glissante")]
    b["nom"] = "decharge_pression_glissante"
    b["description"] = (
        "Pas de détendeur : l'étage 1 reçoit l'air à la pression du "
        "réservoir (190 → 55 bar), rendement isentropique constant (Shi "
        "2024). Borne optimiste : la turbine accepte n'importe quelle "
        "pression sans perdre de rendement.")
    out.append(("decharge_pression_glissante.yaml", b))
    b = copy.deepcopy(decharge)
    b["composants"]["detendeur"] = BLOCS[("detente", "pression_glissante")]
    b["composants"]["turbine"] = BLOCS[("turbine", "flugel")]
    b["nom"] = "decharge_flugel"
    b["description"] = (
        "Pression glissante avec la formule de Flügel (Zhang S. 2025) : le "
        "débit et le rendement de la turbine DEPRAG suivent la pression du "
        "réservoir ; très loin du point nominal (40 bar) au début.")
    out.append(("decharge_flugel.yaml", b))

    # --- cycles --------------------------------------------------------------
    def cycles_deux_reservoirs(nom: str, bloc: dict, desc: str) -> None:
        c = copy.deepcopy(D)
        for i in (1, 2, 3):
            del c["composants"][f"cuve_{i}"]
        c["composants"]["stockage"] = copy.deepcopy(bloc)
        c["charge"]["chaine"] = [
            "compresseur.1", "stockage", "refroidisseur_1",
            "compresseur.2", "stockage", "refroidisseur_2",
            "compresseur.3", "stockage", "refroidisseur_3",
            "compresseur.4", "refroidisseur_4", "refoulement", "secheur",
            "reservoir"]
        c["decharge"]["chaine"] = [
            "reservoir", "detendeur", "stockage", "turbine.1", "stockage",
            "turbine.2", "stockage", "turbine.3"]
        c["nom"] = nom
        c["description"] = desc
        c["simulation"]["nombre_max"] = 4
        out.append((nom + ".yaml", c))

    cycles_deux_reservoirs(
        "cycles_huile_deux_reservoirs",
        BLOCS[("stockage_chaleur", "huile_deux_reservoirs")],
        "Architecture D avec un stockage à deux réservoirs d'huile "
        "(Therminol 66 de Tola, pincement 10 K ; concept LTA-CAES de Wolf "
        "et Budt 2014) alimenté par les étages 1 à 3 et rendu aux trois "
        "turbines.")
    cycles_deux_reservoirs(
        "cycles_eau_sous_pression",
        BLOCS[("stockage_chaleur", "eau_sous_pression")],
        "Architecture D avec un stockage à deux réservoirs d'eau sous "
        "pression (18 bar, Shi 2024) : la température est plafonnée par "
        "l'ébullition alors que les compresseurs de Dormoy sortent à "
        "170-195 °C.")

    c = copy.deepcopy(D)
    for i in (1, 2, 3):
        c["composants"][f"cuve_{i}"]["isolation"] = copy.deepcopy(
            BLOCS[("isolation", "laine_minerale")])
        del c["composants"][f"cuve_{i}"]["coefficient_perte"]
        c["composants"][f"cuve_{i}"]["n_cellules"] = 20
    c["composants"]["attente"] = BLOCS[("attente", "pertes_statiques_14j")]
    c["simulation"]["nombre_max"] = 2
    c["nom"] = "cycles_gravier_isolant_14j"
    c["description"] = (
        "Architecture D avec 20 cm de laine minérale (Ablaoui 2023) autour "
        "de chaque cuve et 14 jours d'attente entre la charge et la "
        "décharge : ce qui reste de la chaleur après un transport.")
    out.append(("cycles_gravier_isolant_14j.yaml", c))
    c = copy.deepcopy(c)
    c["composants"]["attente"] = BLOCS[("attente", "sans_pertes")]
    c["nom"] = "cycles_attente_sans_pertes_14j"
    c["description"] = (
        "Même cas que cycles_gravier_isolant_14j avec une attente sans "
        "pertes : la borne optimiste (isolation parfaite).")
    out.append(("cycles_attente_sans_pertes_14j.yaml", c))
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for nom, brut in variantes():
        _ecrire(nom, brut)


if __name__ == "__main__":
    main()
