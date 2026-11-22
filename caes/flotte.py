# -*- coding: utf-8 -*-
"""Répartition d'une flotte de modules identiques sur une demande
variable, seconde par seconde (formules.md#F47).

Un **module** est une installation complète (réservoir chargé, cuves,
turbine) dont la décharge a été simulée une fois : elle donne la
puissance électrique P_module(τ) depuis son démarrage jusqu'à l'arrêt
du détendeur. La flotte est pilotée par une règle simple inspirée de
la vanne ON/OFF de Zhang S. 2025 : à chaque seconde,

* si la puissance des modules en marche ne couvre pas la demande, on
  démarre un module de plus (s'il en reste) ;
* si elle la dépasse de plus que la puissance d'un module, on met en
  pause le dernier démarré (sa vanne se ferme ; il reprend plus tard où
  il en était, sans perte) ;
* ce qui dépasse la demande entre ces deux bornes est écrêté (l'air
  passe quand même : perte comptée comme « écrêtée ») ; ce qui manque
  est de l'énergie non servie.

Les modules sont donc des « blocs » de puissance : la finesse du suivi
dépend de la taille d'un module face à la demande. Le réservoir tampon
et la régulation fine de Zhang ne sont pas modélisés ; voir la fiche.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class CourbeModule:
    """Puissance électrique d'un module en décharge, P(τ) [W] depuis le
    démarrage, à pas constant ``dt_s``."""

    dt_s: float
    P_w: np.ndarray

    @property
    def duree_s(self) -> float:
        return self.dt_s * self.P_w.size

    @property
    def energie_j(self) -> float:
        return float(self.P_w.sum() * self.dt_s)

    @property
    def P_nominale_w(self) -> float:
        return float(np.max(self.P_w)) if self.P_w.size else 0.0

    @classmethod
    def depuis_series(cls, t_s: np.ndarray, P_w: np.ndarray,
                      dt_s: float = 1.0) -> CourbeModule:
        """Rééchantillonne une série (t, P) au pas ``dt_s``."""
        t = np.asarray(t_s, dtype=float)
        P = np.asarray(P_w, dtype=float)
        if t.size < 2:
            raise ValueError("série trop courte")
        grille = np.arange(0.0, float(t[-1]), dt_s)
        return cls(dt_s, np.interp(grille, t, P))


@dataclass
class ResultatFlotte:
    nombre_modules: int
    dt_s: float
    demande_w: np.ndarray
    fournie_w: np.ndarray
    modules_en_marche: np.ndarray
    energie_demandee_j: float
    energie_fournie_j: float
    energie_non_servie_j: float
    energie_ecretee_j: float
    modules_utilises: int
    demarrages: int
    duree_couverte_s: float
    """Temps pendant lequel la demande est entièrement couverte."""
    details: dict[str, float] = field(default_factory=dict)

    @property
    def couverture(self) -> float:
        """Part de l'énergie demandée qui a été fournie."""
        return (self.energie_fournie_j / self.energie_demandee_j
                if self.energie_demandee_j > 0 else 1.0)

    @property
    def energie_restante_j(self) -> float:
        return float(self.details.get("energie_restante_j", 0.0))


def repartir(courbe: CourbeModule, demande_w: np.ndarray,
             nombre_modules: int, dt_s: float | None = None,
             marge_w: float | None = None) -> ResultatFlotte:
    """Fait suivre la demande par ``nombre_modules`` modules identiques.

    ``demande_w`` est échantillonnée au pas ``dt_s`` (par défaut celui
    de la courbe). ``marge_w`` est l'excédent toléré avant de mettre un
    module en pause (par défaut la puissance nominale d'un module).
    """
    dt = courbe.dt_s if dt_s is None else dt_s
    if dt != courbe.dt_s:
        courbe = CourbeModule(dt, np.interp(
            np.arange(0.0, courbe.duree_s, dt),
            np.arange(courbe.P_w.size) * courbe.dt_s, courbe.P_w))
    if nombre_modules < 0:
        raise ValueError("nombre de modules négatif")
    demande = np.asarray(demande_w, dtype=float)
    n = demande.size
    P = courbe.P_w
    L = P.size
    marge = courbe.P_nominale_w if marge_w is None else marge_w
    position = np.zeros(nombre_modules, dtype=int)
    """Pas déjà consommés par chaque module (τ / dt)."""
    en_marche: list[int] = []
    en_pause: list[int] = []
    """Modules mis en pause, à reprendre avant d'en démarrer un neuf."""
    prochain = 0
    fournie = np.zeros(n)
    marche = np.zeros(n, dtype=int)
    demarrages = 0
    for k in range(n):
        # retirer les modules vides
        en_marche = [i for i in en_marche if position[i] < L]
        en_pause = [i for i in en_pause if position[i] < L]
        puissance = sum(float(P[position[i]]) for i in en_marche)
        while puissance < demande[k] and (en_pause
                                          or prochain < nombre_modules):
            if en_pause:
                i = en_pause.pop()
            else:
                i = prochain
                prochain += 1
            en_marche.append(i)
            puissance += float(P[position[i]])
            demarrages += 1
        while (len(en_marche) > 1
               and puissance - float(P[position[en_marche[-1]]])
               >= demande[k] + marge):
            i = en_marche.pop()
            en_pause.append(i)
            puissance -= float(P[position[i]])
        # mettre en pause plutôt que de gaspiller quand la demande est
        # nulle
        if demande[k] <= 0 and en_marche:
            en_pause.extend(en_marche)
            en_marche = []
            puissance = 0.0
        fournie[k] = min(puissance, demande[k])
        marche[k] = len(en_marche)
        for i in en_marche:
            position[i] += 1
    E_dem = float(demande.sum() * dt)
    E_four = float(fournie.sum() * dt)
    consomme = float(sum(P[:position[i]].sum() for i in range(prochain))
                     * dt)
    E_ecr = max(consomme - E_four, 0.0)
    restante = float(sum(P[position[i]:].sum()
                         for i in range(nombre_modules)) * dt)
    couverte = float(np.sum(fournie >= demande - 1e-9) * dt)
    return ResultatFlotte(
        nombre_modules=nombre_modules, dt_s=dt, demande_w=demande,
        fournie_w=fournie, modules_en_marche=marche,
        energie_demandee_j=E_dem, energie_fournie_j=E_four,
        energie_non_servie_j=E_dem - E_four, energie_ecretee_j=E_ecr,
        modules_utilises=prochain, demarrages=demarrages,
        duree_couverte_s=couverte,
        details={"energie_restante_j": restante,
                 "energie_module_j": courbe.energie_j,
                 "P_nominale_w": courbe.P_nominale_w})


def modules_necessaires(courbe: CourbeModule, demande_w: np.ndarray,
                        dt_s: float | None = None,
                        couverture_min: float = 0.999,
                        maximum: int = 10000) -> tuple[int, ResultatFlotte]:
    """Plus petit nombre de modules qui couvre la demande (part de
    l'énergie ≥ ``couverture_min``), par recherche dichotomique à
    partir de la borne énergétique E_demandée / E_module."""
    dt = courbe.dt_s if dt_s is None else dt_s
    demande = np.asarray(demande_w, dtype=float)
    E_dem = float(demande.sum() * dt)
    bas = max(1, int(np.floor(E_dem / max(courbe.energie_j, 1e-9))))
    haut = bas
    r = repartir(courbe, demande, haut, dt)
    while r.couverture < couverture_min:
        if haut >= maximum:
            return haut, r
        haut = min(maximum, haut * 2)
        r = repartir(courbe, demande, haut, dt)
    while haut - bas > 1:
        mil = (bas + haut) // 2
        rm = repartir(courbe, demande, mil, dt)
        if rm.couverture >= couverture_min:
            haut, r = mil, rm
        else:
            bas = mil
    if bas == haut:
        return haut, r
    rb = repartir(courbe, demande, bas, dt)
    if rb.couverture >= couverture_min:
        return bas, rb
    return haut, r


def profil_jour_nuit(duree_s: float, P_moyenne_w: float,
                     facteur_jour: float, facteur_nuit: float,
                     dt_s: float = 1.0, debut_jour_h: float = 6.0,
                     fin_jour_h: float = 22.0) -> np.ndarray:
    """Demande en créneaux jour / nuit, à partir de minuit [W]."""
    t = np.arange(0.0, duree_s, dt_s)
    h = (t / 3600.0) % 24.0
    jour = (h >= debut_jour_h) & (h < fin_jour_h)
    return np.where(jour, facteur_jour, facteur_nuit) * P_moyenne_w
