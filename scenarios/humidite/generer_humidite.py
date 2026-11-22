# -*- coding: utf-8 -*-
"""Génère les scénarios de la phase 9 (humidité et sécheur) à partir des
architectures A (1 étage, sans réchauffage) et B (3 étages réchauffés)
du banc de Dormoy.

    python scenarios/humidite/generer_humidite.py

Trois façons de traiter l'eau, pour chaque architecture :

* ``secheur_adsorption`` : le sécheur de Dormoy (19 % d'air purgé) avec
  un point de rosée de sortie de −40 °C (hypothèse) ;
* ``separateur`` : un séparateur d'eau après chaque refroidisseur
  (98 % de l'eau liquide retenue, hypothèse) et pas de sécheur ;
* ``separateur_appoint`` : séparateurs plus un petit sécheur d'appoint
  (5 % d'air purgé, hypothèse).

Les fichiers produits sont suivis par git ; relancer ce script plutôt
que de les éditer.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import yaml

DOSSIER = Path(__file__).resolve().parent
SCENARIOS = DOSSIER.parent
ENTETE = ("# Fichier généré par scenarios/humidite/generer_humidite.py : "
          "ne pas éditer à la main.\n")

SEPARATEUR = {"type": "secheur", "modele": "separateur",
              "efficacite_separation": "registre:separateur.efficacite"}
ADSORPTION = {"type": "secheur", "modele": "perte_debit",
              "efficacite": "registre:secheur.efficacite",
              "point_de_rosee_sortie":
                  "registre:secheur.point_de_rosee_sortie"}
APPOINT = {"type": "secheur", "modele": "perte_debit",
           "efficacite": "registre:secheur.appoint.efficacite",
           "point_de_rosee_sortie": "registre:secheur.point_de_rosee_sortie"}
AUCUN = {"type": "secheur", "modele": "aucun"}


def _charger(nom: str) -> dict[str, Any]:
    return yaml.safe_load((SCENARIOS / nom).read_text(encoding="utf-8"))


def _avec_separateurs(brut: dict[str, Any]) -> None:
    chaine = brut["charge"]["chaine"]
    nouvelle: list[str] = []
    for maillon in chaine:
        nouvelle.append(maillon)
        if maillon.startswith("refroidisseur_"):
            i = maillon.split("_")[1]
            brut["composants"][f"separateur_{i}"] = copy.deepcopy(SEPARATEUR)
            nouvelle.append(f"separateur_{i}")
    brut["charge"]["chaine"] = nouvelle


def variantes() -> list[tuple[str, dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any]]] = []
    for arch, desc_arch in (("A", "1 étage sans réchauffage (cas de base)"),
                            ("B", "3 étages réchauffés à 130/90/90 °C")):
        base = _charger(f"{arch}.yaml")
        base["simulation"]["nombre_max"] = 2
        for nom, secheur, separateurs, desc in (
            ("secheur_adsorption", ADSORPTION, False,
             "sécheur par adsorption de Dormoy (19 % d'air purgé, point de "
             "rosée −40 °C)"),
            ("separateur", AUCUN, True,
             "séparateurs d'eau après chaque refroidisseur, sans sécheur"),
            ("separateur_appoint", APPOINT, True,
             "séparateurs plus un petit sécheur d'appoint (5 % d'air purgé)"),
        ):
            b = copy.deepcopy(base)
            b["nom"] = f"{arch}_{nom}"
            b["description"] = (f"Architecture {arch} ({desc_arch}) avec "
                                f"{desc} ; eau suivie de l'aspiration au "
                                f"rejet (phase 9).")
            b["composants"]["secheur"] = copy.deepcopy(secheur)
            if separateurs:
                _avec_separateurs(b)
            out.append((b["nom"] + ".yaml", b))
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for nom, brut in variantes():
        texte = yaml.safe_dump(brut, allow_unicode=True, sort_keys=False,
                               width=78)
        (DOSSIER / nom).write_text(ENTETE + texte, encoding="utf-8")
        print("écrit :", nom)


if __name__ == "__main__":
    main()
