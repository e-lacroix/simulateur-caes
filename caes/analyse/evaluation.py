# -*- coding: utf-8 -*-
"""Évaluer un point de l'espace des paramètres : scénario modifié →
simulation → sorties, en série ou dans un bassin de processus.

Les sorties disponibles (clés de ``sorties`` du fichier d'analyse) :

* ``rte_sans_chaleur``, ``rte_avec_chaleur_externe``,
  ``energie_consommee_kwh``, ``energie_produite_kwh``,
  ``chaleur_externe_kwh`` (rendements du dernier cycle, F20) ;
* ``charge.<total>`` et ``decharge.<total>`` : n'importe quel total du
  dernier cycle (par exemple ``charge.duree_h``,
  ``decharge.T_rejet_min_degC``, ``decharge.givre_total_kg``) ;
* ``pertes_attente_kwh``, ``nombre_cycles``, ``converge`` ;
* ``masse_reservoirs_kg``, ``masse_cuves_kg``, ``masse_totale_kg``,
  ``volume_reservoirs_m3``, ``volume_cuves_m3`` (bloc ``masse``, F44).

Une simulation qui échoue (assemblage impossible, air hors domaine sans
arrêt propre) donne des sorties ``nan`` et un message ; les méthodes
d'analyse comptent ces échecs et les signalent.
"""

from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from caes.analyse.masse import ParametresMasse, masses_installation
from caes.analyse.parametres import Analyse, ParametreAnalyse
from caes.assembleur import (
    ErreurAssemblage,
    Installation,
    ResultatSimulation,
    construire_installation,
)
from caes.composants.base import ErreurComposant
from caes.registre import ErreurRegistre, Registre
from caes.scenario import Scenario

SORTIES_RENDEMENT = ("rte_sans_chaleur", "rte_avec_chaleur_externe",
                     "energie_consommee_kwh", "energie_produite_kwh",
                     "chaleur_externe_kwh")
SORTIES_MASSE = ("masse_reservoirs_kg", "masse_cuves_kg",
                 "masse_totale_kg", "volume_reservoirs_m3",
                 "volume_cuves_m3")


@dataclass
class ResultatPoint:
    """Sorties d'une simulation en un point."""

    point: dict[str, float]
    """Valeur de chaque paramètre d'analyse (SI ou facteur)."""
    sorties: dict[str, float]
    avertissements: list[str] = field(default_factory=list)
    arret: str = ""
    erreur: str = ""

    @property
    def valide(self) -> bool:
        return not self.erreur and all(
            not math.isnan(v) for v in self.sorties.values())


def extraire_sorties(res: ResultatSimulation, inst: Installation,
                     noms: Iterable[str], pm: ParametresMasse | None,
                     p_conception_pa: float | None) -> dict[str, float]:
    """Les sorties demandées, lues dans le résultat de simulation."""
    rend = res.rendements() or {}
    ch, d = res.charge_finale, res.decharge_finale
    masses: dict[str, float] = {}
    if pm is not None and p_conception_pa is not None:
        masses = masses_installation(inst, p_conception_pa, pm)
    out: dict[str, float] = {}
    for nom in noms:
        if nom in SORTIES_RENDEMENT:
            out[nom] = float(rend.get(nom, float("nan")))
        elif nom in SORTIES_MASSE:
            out[nom] = float(masses.get(nom, float("nan")))
        elif nom.startswith("charge."):
            out[nom] = float(ch.totaux.get(nom[7:], float("nan"))
                             if ch else float("nan"))
        elif nom.startswith("decharge."):
            out[nom] = float(d.totaux.get(nom[9:], float("nan"))
                             if d else float("nan"))
        elif nom == "pertes_attente_kwh":
            c = res.dernier_cycle
            out[nom] = float(c.pertes_attente_kwh) if c else float("nan")
        elif nom == "nombre_cycles":
            out[nom] = float(len(res.cycles))
        elif nom == "converge":
            out[nom] = float(bool(res.converge))
        else:
            raise ValueError(f"sortie « {nom} » inconnue")
    return out


class Evaluateur:
    """Simule le scénario de l'analyse en un point donné."""

    def __init__(self, analyse: Analyse, registre: Registre | None = None):
        self.analyse = analyse
        self.registre = registre or Registre.charger()
        self.parametres = {p.nom: p for p in analyse.parametres}
        self.pm = ParametresMasse.depuis_bloc(analyse.masse, self.registre)
        self._bassin: ProcessPoolExecutor | None = None
        self._cache: dict[tuple[tuple[str, float], ...], ResultatPoint] = {}

    # --- évaluation en série ---------------------------------------------
    def scenario_modifie(self, point: dict[str, float]) -> Scenario:
        modifs: dict[str, float] = {}
        for nom, x in point.items():
            modifs.update(self.parametres[nom].modifications(float(x)))
        if not modifs:
            return self.analyse.scenario
        return self.analyse.scenario.avec(modifs, "analyse")

    def evaluer(self, point: dict[str, float]) -> ResultatPoint:
        cle = tuple(sorted((k, float(v)) for k, v in point.items()))
        if cle in self._cache:
            return self._cache[cle]
        r = _evaluer_point(self.analyse, self.registre, self.pm,
                           dict(point))
        self._cache[cle] = r
        return r

    # --- évaluation en parallèle -----------------------------------------
    def __enter__(self) -> Evaluateur:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.fermer()

    def ouvrir(self, procs: int | None) -> Evaluateur:
        """Ouvre un bassin de processus (``procs`` ≤ 1 : en série)."""
        if procs is not None and procs > 1:
            self._bassin = ProcessPoolExecutor(
                max_workers=procs, initializer=_initialiser_travailleur,
                initargs=(self.analyse, self.pm))
        return self

    def fermer(self) -> None:
        if self._bassin is not None:
            self._bassin.shutdown()
            self._bassin = None

    def evaluer_points(
        self, points: list[dict[str, float]],
        rappel: Callable[[int, int, ResultatPoint], None] | None = None,
    ) -> list[ResultatPoint]:
        """Évalue une liste de points (cache, puis bassin ou série)."""
        resultats: list[ResultatPoint | None] = [None] * len(points)
        a_faire: list[int] = []
        for i, pt in enumerate(points):
            cle = tuple(sorted((k, float(v)) for k, v in pt.items()))
            if cle in self._cache:
                resultats[i] = self._cache[cle]
            else:
                a_faire.append(i)
        if self._bassin is not None and a_faire:
            futs = {i: self._bassin.submit(_travail, dict(points[i]))
                    for i in a_faire}
            for n, i in enumerate(a_faire, 1):
                r = futs[i].result()
                resultats[i] = r
                self._cache[tuple(sorted(
                    (k, float(v)) for k, v in points[i].items()))] = r
                if rappel is not None:
                    rappel(n, len(a_faire), r)
        else:
            for n, i in enumerate(a_faire, 1):
                r = self.evaluer(points[i])
                resultats[i] = r
                if rappel is not None:
                    rappel(n, len(a_faire), r)
        return [r for r in resultats if r is not None]

    # --- aides -----------------------------------------------------------
    def point_nominal(self, parametres: Iterable[ParametreAnalyse]
                      ) -> dict[str, float]:
        return {p.nom: p.nominal for p in parametres}


# --- fonctions de travail (module : nécessaires au pickling) ------------
_ANALYSE: Analyse | None = None
_REGISTRE: Registre | None = None
_PM: ParametresMasse | None = None


def _initialiser_travailleur(analyse: Analyse,
                             pm: ParametresMasse | None) -> None:
    global _ANALYSE, _REGISTRE, _PM
    _ANALYSE, _PM = analyse, pm
    _REGISTRE = Registre.charger()


def _travail(point: dict[str, float]) -> ResultatPoint:
    assert _ANALYSE is not None and _REGISTRE is not None
    return _evaluer_point(_ANALYSE, _REGISTRE, _PM, point)


def _evaluer_point(analyse: Analyse, reg: Registre,
                   pm: ParametresMasse | None,
                   point: dict[str, float]) -> ResultatPoint:
    params = {p.nom: p for p in analyse.parametres}
    modifs: dict[str, float] = {}
    for nom, x in point.items():
        modifs.update(params[nom].modifications(float(x)))
    sc = analyse.scenario.avec(modifs, "analyse") if modifs \
        else analyse.scenario
    nan = {s: float("nan") for s in analyse.sorties}
    try:
        inst = construire_installation(sc, reg)
        res = inst.simuler()
        p_conc = None
        if pm is not None:
            p_conc = float(sc[pm.chemin_pression])
        sorties = extraire_sorties(res, inst, analyse.sorties, pm, p_conc)
    except (ErreurAssemblage, ErreurComposant, ErreurRegistre,
            ValueError, KeyError, ZeroDivisionError,
            FloatingPointError) as err:
        return ResultatPoint(point, nan, [], "",
                             f"{type(err).__name__} : {err}")
    arrets = []
    for cyc in res.cycles:
        arrets.append(cyc.decharge.arret)
    if res.decharge is not None:
        arrets.append(res.decharge.arret)
    arret = " ; ".join(sorted(set(a for a in arrets if a)))
    return ResultatPoint(point, sorties,
                         [str(a) for a in res.avertissements], arret)
