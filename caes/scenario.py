"""Chargement des fichiers de scénario (YAML).

Un scénario décrit un cas à simuler. Chaque valeur physique y est
donnée sous l'une de ces formes, pour rester traçable :

* ``registre:<id>`` : la valeur du registre, convertie en SI ;
  ``registre:<id>#min``, ``#max`` ou ``#moyen`` pour une plage ;
* ``{valeur: 20, unite: degC, source: "pourquoi"}`` : une valeur propre
  au scénario, convertie en SI avec la table d'unités du registre ;
* un nombre nu : accepté seulement pour les grandeurs sans dimension ou
  déjà en SI (compteurs, booléens, options). À éviter pour la physique.

Le résultat est un dictionnaire imbriqué de valeurs SI, accompagné d'un
dictionnaire ``provenance`` qui dit d'où vient chaque feuille.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from caes.registre import UNITES, ErreurRegistre, Registre

PREFIXE_REGISTRE = "registre:"
DOSSIER_SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"


@dataclass
class Scenario:
    """Scénario résolu : valeurs SI et provenance de chaque feuille."""

    nom: str
    description: str
    valeurs: dict[str, Any]
    provenance: dict[str, str] = field(default_factory=dict)
    chemin: Path | None = None

    def __getitem__(self, cle: str) -> Any:
        """Accès par chemin pointé : ``sc["reservoir.volume"]``."""
        noeud: Any = self.valeurs
        for partie in cle.split("."):
            if isinstance(noeud, list):
                noeud = noeud[int(partie)]
            else:
                noeud = noeud[partie]
        return noeud

    def get(self, cle: str, defaut: Any = None) -> Any:
        try:
            return self[cle]
        except (KeyError, IndexError, TypeError):
            return defaut

    def avec(self, modifications: dict[str, Any], suffixe: str) -> Scenario:
        """Copie du scénario avec des feuilles remplacées (valeurs SI).

        ``modifications`` associe un chemin pointé à une nouvelle valeur ;
        la provenance note « modifié par <suffixe> ».
        """
        import copy

        nouveau = copy.deepcopy(self)
        nouveau.nom = f"{self.nom}_{suffixe}"
        for cle, val in modifications.items():
            parties = cle.split(".")
            noeud: Any = nouveau.valeurs
            for partie in parties[:-1]:
                if isinstance(noeud, list):
                    noeud = noeud[int(partie)]
                else:
                    noeud = noeud.setdefault(partie, {})
            if isinstance(noeud, list):
                noeud[int(parties[-1])] = val
            else:
                noeud[parties[-1]] = val
            nouveau.provenance[cle] = f"modifié par {suffixe} : {val}"
        return nouveau


def _resoudre_registre(texte: str, registre: Registre) -> tuple[Any, str]:
    corps = texte[len(PREFIXE_REGISTRE):]
    if "#" in corps:
        id_, mode = corps.split("#", 1)
    else:
        id_, mode = corps, ""
    par = registre[id_]
    if par.unite == "texte":
        return par.valeur, f"{id_} [{par.niveau_preuve}, {par.source_id}]"
    base = f"{id_} [{par.niveau_preuve}, {par.source_id}, {par.localisation}]"
    if mode == "":
        return par.valeur_si, base
    if mode == "min":
        return par.valeur_min_si, base + " (borne basse)"
    if mode == "max":
        return par.valeur_max_si, base + " (borne haute)"
    if mode == "moyen":
        vmin, vmax = par.valeur_min_si, par.valeur_max_si
        if vmin is None or vmax is None:
            raise ErreurRegistre(f"{id_} : pas de plage pour #moyen")
        return 0.5 * (vmin + vmax), base + " (milieu de plage : hypothèse)"
    raise ErreurRegistre(f"mode inconnu « #{mode} » pour {id_}")


def _convertir(valeur: float, unite: str) -> float:
    if unite not in UNITES:
        raise ErreurRegistre(f"unité inconnue dans le scénario : {unite}")
    _, facteur, decalage = UNITES[unite]
    return valeur * facteur + decalage


def _resoudre(
    noeud: Any, chemin: str, registre: Registre, provenance: dict[str, str]
) -> Any:
    if isinstance(noeud, str) and noeud.startswith(PREFIXE_REGISTRE):
        val, prov = _resoudre_registre(noeud, registre)
        provenance[chemin] = prov
        return val
    if isinstance(noeud, dict):
        if "valeur" in noeud and "unite" in noeud:
            val = _convertir(float(noeud["valeur"]), noeud["unite"])
            source = noeud.get("source", "source non indiquée")
            provenance[chemin] = (
                f"scénario : {noeud['valeur']} {noeud['unite']} ({source})"
            )
            return val
        return {
            cle: _resoudre(
                sous, f"{chemin}.{cle}" if chemin else cle, registre,
                provenance,
            )
            for cle, sous in noeud.items()
        }
    if isinstance(noeud, list):
        return [
            _resoudre(sous, f"{chemin}.{i}", registre, provenance)
            for i, sous in enumerate(noeud)
        ]
    if isinstance(noeud, (int, float)) and not isinstance(noeud, bool):
        provenance[chemin] = f"scénario : {noeud} (nombre nu, SI supposé)"
    return noeud


def charger_scenario(
    chemin: Path | str, registre: Registre | None = None
) -> Scenario:
    """Lit un fichier YAML et résout toutes ses valeurs en SI."""
    chemin = Path(chemin)
    if not chemin.exists() and (DOSSIER_SCENARIOS / chemin).exists():
        chemin = DOSSIER_SCENARIOS / chemin
    reg = registre or Registre.charger()
    with open(chemin, encoding="utf-8") as f:
        brut = yaml.safe_load(f)
    nom = brut.pop("nom", chemin.stem)
    description = brut.pop("description", "")
    provenance: dict[str, str] = {}
    valeurs = _resoudre(brut, "", reg, provenance)
    return Scenario(
        nom=nom,
        description=description,
        valeurs=valeurs,
        provenance=provenance,
        chemin=chemin,
    )
