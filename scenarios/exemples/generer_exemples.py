# -*- coding: utf-8 -*-
"""Génère les fichiers des scénarios d'exemple de la phase 11 qui
dérivent d'un scénario existant, et les profils (météo, demande).

    python scenarios/exemples/generer_exemples.py

* ``transport/transport.yaml`` : architecture D (gravier direct) avec
  20 cm de laine minérale autour des cuves, attente de 14 jours à
  20 °C, un cycle ; dérivé de ``variantes/cycles_gravier_isolant_14j``.
* ``transport/transport_appoint.yaml`` : le même avec une source de
  chaleur externe (chaudière) après chaque cuve : la solution de repli
  quand la chaleur stockée ne suffit plus (chaleur comptée « externe »).
* ``transport/meteo_hiver.csv``, ``meteo_ete.csv`` : température
  extérieure sur 60 jours, sinusoïde journalière autour de −20 °C et de
  30 °C (demi-amplitude ``meteo.amplitude_journaliere``, hypothèse).
* ``centre_urgence/module.yaml`` : un module = l'installation de
  transport avec un jour d'attente (modules chargés avant la panne).
* ``centre_urgence/demande_72h.csv`` : demande du centre, profil jour /
  nuit (``centre_urgence.*``, hypothèses), pas d'une minute.

Les fichiers produits sont suivis par git ; relancer ce script plutôt
que de les éditer.
"""

from __future__ import annotations

import copy
import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

DOSSIER = Path(__file__).resolve().parent
SCENARIOS = DOSSIER.parent
RACINE = SCENARIOS.parent
sys.path.insert(0, str(RACINE))

from caes.registre import Registre  # noqa: E402

ENTETE = ("# Fichier généré par scenarios/exemples/generer_exemples.py : "
          "ne pas éditer à la main.\n")


def _val(v: float, unite: str, source: str) -> dict[str, Any]:
    return {"valeur": v, "unite": unite, "source": source}


def _base() -> dict[str, Any]:
    brut = yaml.safe_load(
        (SCENARIOS / "variantes" / "cycles_gravier_isolant_14j.yaml")
        .read_text(encoding="utf-8"))
    brut["simulation"]["nombre_max"] = 1
    brut["composants"]["attente"]["duree"] = _val(
        14, "j", "transport de deux semaines (plan v2, scénario 2)")
    brut["composants"]["attente"]["dt"] = _val(
        10, "min", "pas des pertes statiques (choix numérique)")
    brut["composants"]["reservoir"]["fuite_par_jour"] = _val(
        0, "%", "réservoirs supposés étanches ; les fuites sont un "
        "balayage du rapport (registre reservoir.fuite_par_jour)")
    return brut


def transport() -> dict[str, Any]:
    b = _base()
    b["nom"] = "transport"
    b["description"] = (
        "Architecture D (gravier direct) chargée au départ, transportée "
        "14 jours avec 20 cm de laine minérale autour des cuves, puis "
        "déchargée : ce qui reste de la chaleur et de l'électricité "
        "(phase 11, scénario 2). Un seul cycle ; l'ambiance est constante "
        "ou suit un profil météo (meteo_hiver.csv, meteo_ete.csv).")
    return b


def transport_appoint() -> dict[str, Any]:
    b = transport()
    b["nom"] = "transport_appoint"
    b["description"] = (
        "Scénario de transport avec une chaudière d'appoint après chaque "
        "cuve : quand la chaleur stockée ne suffit plus, la source "
        "externe complète jusqu'à la cible (chaleur comptée « externe », "
        "rendement donné avec et sans elle).")
    comp = b["composants"]
    chaine = []
    for maillon in b["decharge"]["chaine"]:
        chaine.append(maillon)
        if maillon.startswith("cuve_"):
            nom = "appoint_" + maillon.split("_")[1]
            comp[nom] = {"type": "stockage_chaleur",
                         "modele": "source_externe"}
            chaine.append(nom)
    b["decharge"]["chaine"] = chaine
    return b


def module_centre() -> dict[str, Any]:
    b = transport()
    b["nom"] = "module_centre_urgence"
    b["description"] = (
        "Un module du centre d'urgence : l'installation de transport "
        "(D isolée) chargée avant la panne, un jour d'attente, puis "
        "déchargée à débit nominal. Sa courbe de puissance sert à la "
        "répartition de la flotte (caes/flotte.py, F47).")
    b["composants"]["attente"]["duree"] = _val(
        1, "j", "modules chargés la veille de la panne (choix du scénario)")
    return b


def ecrire_yaml(chemin: Path, brut: dict[str, Any]) -> None:
    texte = yaml.safe_dump(brut, allow_unicode=True, sort_keys=False,
                           width=78)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(ENTETE + texte, encoding="utf-8")
    print("écrit :", chemin.relative_to(RACINE))


def ecrire_meteo(chemin: Path, T_moy_degC: float, amplitude_K: float,
                 jours: int = 60) -> None:
    """Sinusoïde journalière (minimum à 5 h, maximum à 17 h), pas 1 h."""
    t_h = np.arange(0, jours * 24 + 1, dtype=float)
    T = T_moy_degC - amplitude_K * np.cos(2 * np.pi * (t_h - 5.0) / 24.0)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_h", "T_amb_degC"])
        for a, b in zip(t_h, T):
            w.writerow([f"{a:.0f}", f"{b:.2f}"])
    print("écrit :", chemin.relative_to(RACINE))


def ecrire_demande(chemin: Path, reg: Registre) -> None:
    from caes.flotte import profil_jour_nuit

    duree = reg.si("centre_urgence.duree")
    P = profil_jour_nuit(duree, reg.si("centre_urgence.puissance_moyenne"),
                         reg.si("centre_urgence.facteur_jour"),
                         reg.si("centre_urgence.facteur_nuit"), dt_s=60.0)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_min", "P_kW"])
        for k, p in enumerate(P):
            w.writerow([k, f"{p / 1e3:.1f}"])
    print("écrit :", chemin.relative_to(RACINE))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    reg = Registre.charger()
    tr = DOSSIER / "transport"
    ecrire_yaml(tr / "transport.yaml", transport())
    ecrire_yaml(tr / "transport_appoint.yaml", transport_appoint())
    amp = reg.si("meteo.amplitude_journaliere")
    ecrire_meteo(tr / "meteo_hiver.csv", -20.0, amp)
    ecrire_meteo(tr / "meteo_ete.csv", 30.0, amp)
    cu = DOSSIER / "centre_urgence"
    ecrire_yaml(cu / "module.yaml", module_centre())
    ecrire_demande(cu / "demande_72h.csv", reg)


if __name__ == "__main__":
    main()
