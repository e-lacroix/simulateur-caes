# -*- coding: utf-8 -*-
"""Simuler un lot de variantes d'un scénario, en parallèle, et n'en
garder qu'un résumé transportable (totaux, cycles, avertissements).

    from caes.analyse.lot import simuler_lot
    resumes = simuler_lot("scenarios/exemples/transport/transport.yaml",
                          [["composants.attente.duree=7j"],
                           ["composants.attente.duree=14j"]], procs=6)

Chaque élément du lot est une liste de modifications « chemin=valeur
[unite] » (comme ``--modifier``). Le résumé rendu est un
:class:`ResumeSimulation` : rendements du dernier cycle, totaux de la
charge et de la décharge, chaleur des cuves avant et après l'attente,
pertes de l'attente, avertissements, et au besoin les séries de la
décharge (``series_decharge``) pour les scénarios qui en ont besoin
(répartition d'une flotte, phase 11).
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

from caes.assembleur import ResultatSimulation, charger_installation
from caes.registre import Registre


@dataclass
class ResumeSimulation:
    modifications: list[str]
    rendements: dict[str, float]
    charge: dict[str, float]
    decharge: dict[str, float]
    attente_h: float = 0.0
    chaleur_cuves_debut_kwh: float = 0.0
    chaleur_cuves_fin_kwh: float = 0.0
    pertes_attente_kwh: float = 0.0
    nombre_cycles: int = 0
    converge: bool | None = None
    avertissements: list[str] = field(default_factory=list)
    erreur: str = ""
    series_decharge: pd.DataFrame | None = None
    masse_fuite_kg: float = 0.0

    @property
    def valide(self) -> bool:
        return not self.erreur


def resumer(res: ResultatSimulation, modifs: list[str],
            series: bool = False) -> ResumeSimulation:
    ch, d = res.charge_finale, res.decharge_finale
    c = res.dernier_cycle
    r = ResumeSimulation(
        modifications=list(modifs), rendements=res.rendements() or {},
        charge=dict(ch.totaux) if ch else {},
        decharge=dict(d.totaux) if d else {},
        nombre_cycles=len(res.cycles), converge=res.converge,
        avertissements=[str(a) for a in res.avertissements])
    if c is not None:
        r.attente_h = c.attente_h
        r.chaleur_cuves_debut_kwh = c.chaleur_cuves_debut_kwh
        r.chaleur_cuves_fin_kwh = c.chaleur_cuves_fin_kwh
        r.pertes_attente_kwh = c.pertes_attente_kwh
    if series and d is not None:
        r.series_decharge = d.series.copy()
    inst = res.installation
    if inst.charge is not None:
        r.masse_fuite_kg = float(getattr(inst.charge.reservoir,
                                         "masse_fuite_kg", 0.0))
    return r


_CHEMIN: Path | None = None
_REGISTRE: Registre | None = None
_SERIES = False


def _init(chemin: Path, series: bool) -> None:
    global _CHEMIN, _REGISTRE, _SERIES
    _CHEMIN, _SERIES = chemin, series
    _REGISTRE = Registre.charger()


def _un(modifs: list[str]) -> ResumeSimulation:
    assert _CHEMIN is not None
    return simuler_un(_CHEMIN, modifs, _REGISTRE, _SERIES)


def simuler_un(chemin: Path | str, modifs: list[str],
               registre: Registre | None = None,
               series: bool = False) -> ResumeSimulation:
    """Une variante, en série, résumée ; une erreur d'assemblage ou de
    simulation est rendue dans ``erreur`` plutôt que levée."""
    try:
        res = charger_installation(chemin, registre,
                                   modifications=list(modifs)).simuler()
        return resumer(res, modifs, series)
    except Exception as err:  # noqa: BLE001 : résumé, jamais masqué
        return ResumeSimulation(list(modifs), {}, {}, {},
                                erreur=f"{type(err).__name__} : {err}")


def simuler_lot(
    chemin: Path | str, lot: list[list[str]], procs: int | None = None,
    series: bool = False,
    rappel: Callable[[int, int, ResumeSimulation], None] | None = None,
) -> list[ResumeSimulation]:
    """Toutes les variantes du lot (bassin de processus si ``procs`` > 1),
    dans l'ordre du lot."""
    chemin = Path(chemin)
    if not lot:
        return []
    if procs is None or procs <= 1 or len(lot) == 1:
        reg = Registre.charger()
        out = []
        for i, m in enumerate(lot, 1):
            r = simuler_un(chemin, m, reg, series)
            out.append(r)
            if rappel is not None:
                rappel(i, len(lot), r)
        return out
    out = []
    with ProcessPoolExecutor(max_workers=min(procs, len(lot)),
                             initializer=_init,
                             initargs=(chemin, series)) as bassin:
        for i, r in enumerate(bassin.map(_un, lot), 1):
            out.append(r)
            if rappel is not None:
                rappel(i, len(lot), r)
    return out


def _un_scenario(tache: tuple[str, list[str], bool]) -> ResumeSimulation:
    chemin, modifs, series = tache
    return simuler_un(chemin, modifs, _REGISTRE, series)


def simuler_scenarios(
    taches: list[tuple[Path | str, list[str]]], procs: int | None = None,
    series: bool = False,
    rappel: Callable[[int, int, ResumeSimulation], None] | None = None,
) -> list[ResumeSimulation]:
    """Comme :func:`simuler_lot`, mais chaque tâche porte son propre
    scénario : ``[(chemin, modifications), ...]``."""
    if not taches:
        return []
    args = [(str(c), list(m), series) for c, m in taches]
    if procs is None or procs <= 1 or len(taches) == 1:
        reg = Registre.charger()
        out = []
        for i, (c, m, s) in enumerate(args, 1):
            r = simuler_un(c, m, reg, s)
            out.append(r)
            if rappel is not None:
                rappel(i, len(args), r)
        return out
    out = []
    with ProcessPoolExecutor(max_workers=min(procs, len(args)),
                             initializer=_init,
                             initargs=(Path(args[0][0]), series)) as bassin:
        for i, r in enumerate(bassin.map(_un_scenario, args), 1):
            out.append(r)
            if rappel is not None:
                rappel(i, len(args), r)
    return out
