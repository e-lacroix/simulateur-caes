# -*- coding: utf-8 -*-
"""Analyse d'une configuration (phase 10) : sensibilité, incertitudes,
front de Pareto, masse des réservoirs, surveillance des domaines de
validité.

Une **analyse** est décrite par un fichier YAML (`scenarios/analyse/`)
qui désigne un scénario, les paramètres à faire varier (avec leur plage
et son origine : registre, hypothèse ou choix), les sorties à observer
et les réglages des méthodes. Voir `scenarios/analyse/README.md`.

* `parametres` : lecture du fichier d'analyse et des plages ;
* `evaluation` : un point de l'espace des paramètres → sorties du
  simulateur, en série ou en parallèle (processus) ;
* `sensibilite` : un paramètre à la fois (tornade) et indices de Sobol ;
* `incertitudes` : propagation des plages du registre (hypercube latin) ;
* `pareto` : NSGA-II et tri par dominance ;
* `masse` : masse des réservoirs à paroi mince (F44) et des stockages ;
* `rapport` : tableaux Markdown et figures.
"""

from caes.analyse.evaluation import Evaluateur, ResultatPoint
from caes.analyse.parametres import (
    Analyse,
    ParametreAnalyse,
    charger_analyse,
)

__all__ = [
    "Analyse",
    "Evaluateur",
    "ParametreAnalyse",
    "ResultatPoint",
    "charger_analyse",
]
