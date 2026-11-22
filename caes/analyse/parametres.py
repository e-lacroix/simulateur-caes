# -*- coding: utf-8 -*-
"""Fichier d'analyse (YAML) : scénario de base, paramètres et plages.

Un paramètre d'analyse désigne une ou plusieurs feuilles du scénario
(chemins pointés) et une plage. La plage a une **origine** :

* ``plage: registre`` : bornes ``valeur_min`` / ``valeur_max`` du
  paramètre du registre référencé par la feuille (niveau de preuve
  conservé) ;
* ``plage: hypothese`` : ± ``ecart_hypothese`` (fraction, défaut 20 %)
  autour de la valeur du scénario, pour un paramètre au niveau
  « hypothèse » sans plage publiée ;
* ``plage: {min, max}`` dans ``unite`` : choix de l'analyse ;
* ``facteur: {min, max}`` : la valeur du scénario est multipliée par un
  facteur (utile pour faire varier plusieurs feuilles ensemble, par
  exemple les trois cuves).

Les valeurs sont stockées en SI ; ``unite`` ne sert qu'à l'affichage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from caes.registre import UNITES, Registre
from caes.scenario import DOSSIER_SCENARIOS, Scenario, charger_scenario

ECART_HYPOTHESE_DEFAUT = 0.2
"""Demi-largeur relative de la plage d'un paramètre « hypothèse » sans
plage publiée (choix de l'analyse, affiché dans le rapport)."""


class ErreurAnalyse(ValueError):
    """Fichier d'analyse incohérent."""


def vers_si(valeur: float, unite: str) -> float:
    if unite in ("", "-", None):
        return float(valeur)
    if unite not in UNITES:
        raise ErreurAnalyse(f"unité inconnue « {unite} »")
    facteur, decalage = UNITES[unite][1:]
    return float(valeur) * facteur + decalage


def depuis_si(valeur: float, unite: str) -> float:
    if unite in ("", "-", None):
        return float(valeur)
    facteur, decalage = UNITES[unite][1:]
    return (float(valeur) - decalage) / facteur


@dataclass(frozen=True)
class ParametreAnalyse:
    """Un paramètre que l'analyse fait varier."""

    nom: str
    chemins: tuple[str, ...]
    etiquette: str
    unite: str
    nominaux: tuple[float, ...]
    """Valeur SI de chaque chemin dans le scénario de base."""
    minimum: float
    maximum: float
    """Bornes SI (mode « valeur ») ou facteurs (mode « facteur »)."""
    mode: str
    origine: str
    niveau: str

    @property
    def nominal(self) -> float:
        return 1.0 if self.mode == "facteur" else self.nominaux[0]

    def modifications(self, x: float) -> dict[str, float]:
        """Les feuilles du scénario à remplacer pour la valeur ``x``."""
        if self.mode == "facteur":
            return {c: n * x for c, n in zip(self.chemins, self.nominaux)}
        return {c: x for c in self.chemins}

    def affichage(self, x: float) -> float:
        """``x`` dans l'unité d'affichage (facteur : tel quel)."""
        if self.mode == "facteur":
            return x
        return depuis_si(x, self.unite)

    def depuis_normalise(self, u: float) -> float:
        """u ∈ [0, 1] → valeur dans la plage."""
        return self.minimum + u * (self.maximum - self.minimum)

    def texte_plage(self) -> str:
        if self.mode == "facteur":
            return f"× {self.minimum:g} à × {self.maximum:g}"
        a, b = self.affichage(self.minimum), self.affichage(self.maximum)
        u = "" if self.unite in ("", "-") else f" {self.unite}"
        return f"{a:g} à {b:g}{u}"


@dataclass
class Analyse:
    """Contenu résolu d'un fichier d'analyse."""

    nom: str
    description: str
    chemin: Path
    scenario: Scenario
    modifications_de_base: list[str]
    sorties: list[str]
    parametres: list[ParametreAnalyse]
    sobol: dict[str, Any] = field(default_factory=dict)
    incertitudes: dict[str, Any] = field(default_factory=dict)
    pareto: dict[str, Any] = field(default_factory=dict)
    masse: dict[str, Any] = field(default_factory=dict)
    ecart_hypothese: float = ECART_HYPOTHESE_DEFAUT

    def parametre(self, nom: str) -> ParametreAnalyse:
        for p in self.parametres:
            if p.nom == nom:
                return p
        raise ErreurAnalyse(f"paramètre d'analyse « {nom} » inconnu")

    def selection(self, noms: list[str] | None) -> list[ParametreAnalyse]:
        if not noms:
            return list(self.parametres)
        return [self.parametre(n) for n in noms]


def _valeur_scenario(sc: Scenario, chemin: str) -> float:
    try:
        v = sc[chemin]
    except (KeyError, IndexError, TypeError) as err:
        raise ErreurAnalyse(
            f"chemin « {chemin} » absent du scénario {sc.nom}") from err
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ErreurAnalyse(
            f"chemin « {chemin} » : la feuille n'est pas un nombre ({v!r})")
    return float(v)


def _plage_registre(sc: Scenario, chemin: str,
                    reg: Registre) -> tuple[float, float, str]:
    id_ = sc.references.get(chemin)
    if id_ is None:
        raise ErreurAnalyse(
            f"chemin « {chemin} » : plage « registre » demandée mais la "
            f"feuille ne vient pas du registre")
    par = reg[id_]
    vmin, vmax = par.valeur_min_si, par.valeur_max_si
    if vmin is None or vmax is None:
        raise ErreurAnalyse(
            f"paramètre du registre « {id_} » : pas de plage "
            f"valeur_min / valeur_max")
    return vmin, vmax, par.niveau_preuve


def _construire_parametre(brut: dict[str, Any], sc: Scenario,
                          reg: Registre,
                          ecart_hyp: float) -> ParametreAnalyse:
    nom = str(brut.get("nom", ""))
    if not nom:
        raise ErreurAnalyse("paramètre d'analyse sans « nom »")
    if "chemins" in brut:
        chemins = tuple(str(c) for c in brut["chemins"])
    elif "chemin" in brut:
        chemins = (str(brut["chemin"]),)
    else:
        raise ErreurAnalyse(f"paramètre « {nom} » : « chemin » manquant")
    unite = str(brut.get("unite", "-"))
    nominaux = tuple(_valeur_scenario(sc, c) for c in chemins)
    niveau = ""
    for c in chemins:
        id_ = sc.references.get(c)
        if id_ is not None:
            niveau = reg[id_].niveau_preuve
            break
    if "facteur" in brut:
        f = brut["facteur"]
        mode, origine = "facteur", "facteur (choix de l'analyse)"
        vmin, vmax = float(f["min"]), float(f["max"])
    else:
        mode = "valeur"
        plage = brut.get("plage")
        if plage == "registre":
            if len(chemins) != 1:
                raise ErreurAnalyse(
                    f"paramètre « {nom} » : plage « registre » exige un "
                    f"seul chemin")
            vmin, vmax, niveau = _plage_registre(sc, chemins[0], reg)
            origine = "registre (plage publiée)"
        elif plage == "hypothese":
            vmin = nominaux[0] * (1.0 - ecart_hyp)
            vmax = nominaux[0] * (1.0 + ecart_hyp)
            origine = f"hypothèse ± {ecart_hyp * 100:.0f} %"
            niveau = niveau or "hypothese"
        elif isinstance(plage, dict) and "min" in plage and "max" in plage:
            vmin = vers_si(plage["min"], unite)
            vmax = vers_si(plage["max"], unite)
            origine = "plage (choix de l'analyse)"
        else:
            raise ErreurAnalyse(
                f"paramètre « {nom} » : « plage » doit valoir registre, "
                f"hypothese ou {{min, max}}, ou donner « facteur »")
        if len(set(nominaux)) > 1:
            raise ErreurAnalyse(
                f"paramètre « {nom} » : plusieurs chemins avec des valeurs "
                f"différentes ; utiliser « facteur »")
    if vmin >= vmax:
        raise ErreurAnalyse(f"paramètre « {nom} » : min ≥ max")
    return ParametreAnalyse(
        nom=nom, chemins=chemins,
        etiquette=str(brut.get("etiquette", nom)), unite=unite,
        nominaux=nominaux, minimum=vmin, maximum=vmax, mode=mode,
        origine=origine, niveau=niveau or "scénario")


def charger_analyse(chemin: Path | str,
                    registre: Registre | None = None) -> Analyse:
    """Lit un fichier d'analyse et résout ses paramètres."""
    reg = registre or Registre.charger()
    chemin = Path(chemin)
    if not chemin.exists() and (DOSSIER_SCENARIOS / chemin).exists():
        chemin = DOSSIER_SCENARIOS / chemin
    brut = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    if not isinstance(brut, dict) or "scenario" not in brut:
        raise ErreurAnalyse(f"{chemin} : clé « scenario » manquante")
    chemin_sc = Path(str(brut["scenario"]))
    candidats = [chemin_sc, chemin.parent / chemin_sc,
                 DOSSIER_SCENARIOS / chemin_sc]
    for c in candidats:
        if c.exists():
            chemin_sc = c
            break
    else:
        raise ErreurAnalyse(f"{chemin} : scénario « {brut['scenario']} » "
                            f"introuvable")
    sc = charger_scenario(chemin_sc, reg)
    modifs = [str(m) for m in brut.get("modifications_de_base", []) or []]
    if modifs:
        from caes.assembleur import appliquer_modifications

        sc = appliquer_modifications(sc, modifs)
    ecart_hyp = float(brut.get("ecart_hypothese", ECART_HYPOTHESE_DEFAUT))
    params = [_construire_parametre(b, sc, reg, ecart_hyp)
              for b in brut.get("parametres", []) or []]
    noms = [p.nom for p in params]
    if len(set(noms)) != len(noms):
        raise ErreurAnalyse(f"{chemin} : noms de paramètres en double")
    sorties = [str(s) for s in brut.get("sorties", []) or []]
    if not sorties:
        raise ErreurAnalyse(f"{chemin} : « sorties » vide")
    analyse = Analyse(
        nom=str(brut.get("nom", chemin.stem)),
        description=str(brut.get("description", "")),
        chemin=chemin, scenario=sc, modifications_de_base=modifs,
        sorties=sorties, parametres=params,
        sobol=dict(brut.get("sobol", {}) or {}),
        incertitudes=dict(brut.get("incertitudes", {}) or {}),
        pareto=dict(brut.get("pareto", {}) or {}),
        masse=dict(brut.get("masse", {}) or {}),
        ecart_hypothese=ecart_hyp,
    )
    for bloc in ("sobol", "incertitudes"):
        d = getattr(analyse, bloc)
        analyse.selection(d.get("parametres"))
    if analyse.pareto:
        obj = analyse.pareto.get("objectifs", [])
        if len(obj) != 2:
            raise ErreurAnalyse(f"{chemin} : pareto.objectifs doit "
                                f"contenir exactement deux objectifs")
        for o in obj:
            if o.get("sortie") not in sorties:
                raise ErreurAnalyse(
                    f"{chemin} : objectif « {o.get('sortie')} » absent de "
                    f"« sorties »")
            if o.get("sens") not in ("min", "max"):
                raise ErreurAnalyse(
                    f"{chemin} : objectif « {o.get('sortie')} » : « sens » "
                    f"doit valoir min ou max")
        analyse.selection(analyse.pareto.get("variables"))
    return analyse
