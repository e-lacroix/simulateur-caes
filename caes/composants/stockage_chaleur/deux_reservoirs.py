"""Stockage de chaleur à deux réservoirs de liquide (formules.md#F40).

Un réservoir froid et un réservoir chaud ; le liquide passe de l'un à
l'autre à travers un échangeur à pincement δ :

* **charge** : l'air chaud (T_in) chauffe le liquide froid (T_f) jusqu'à
  T_in − δ (au plus T_max) et ressort lui-même à T_f + δ ; la masse de
  liquide déplacée vers le réservoir chaud est Q / (c·(T_chaud,in −
  T_f)) ; le réservoir chaud est bien mélangé ;
* **décharge** : le liquide chaud (T_c) réchauffe l'air froid (T_a)
  jusqu'à min(cible, T_c − δ) et ressort à T_a + δ vers le réservoir
  froid ;
* **attente** : chaque réservoir perd U·A·(T − T_amb) (relaxation
  exacte sur le pas).

Deux fluides : l'huile thermique de Tola 2022 (Therminol 66, c = 1494
J/kg·K, δ = 10 K ; concept LTA-CAES de Wolf et Budt 2014) et l'eau sous
pression de Shi 2024 (c de l'eau liquide par CoolProp, IAPWS-95, à la
pression de la cuve ; la température du réservoir chaud est plafonnée
par l'ébullition, T_sat(p) − marge). C'est ce plafond qui limite les
stockages à eau quand les compresseurs sortent plus chaud que 200 °C.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from caes.proprietes import Air


@dataclass
class Fluide:
    nom: str
    cp_j_kgk: float
    T_max_K: float | None = None
    """Température maximale admise (ébullition pour l'eau sous pression)."""


def fluide_eau(p_cuve_pa: float, marge_K: float, T_calcul_K: float) -> Fluide:
    """Eau liquide à la pression de la cuve (CoolProp, IAPWS-95)."""
    import CoolProp.CoolProp as CP

    T_sat = CP.PropsSI("T", "P", p_cuve_pa, "Q", 0.0, "Water")
    T_cp = min(T_calcul_K, T_sat - 1.0)
    cp = CP.PropsSI("C", "P", p_cuve_pa, "T", T_cp, "Water")
    return Fluide(nom=f"eau à {p_cuve_pa / 1e5:.0f} bar", cp_j_kgk=cp,
                  T_max_K=T_sat - marge_K)


@dataclass
class DeuxReservoirs:
    fluide: Fluide
    masse_totale_kg: float
    pincement_K: float
    coefficient_perte_w_m2k: float = 0.0
    surface_par_reservoir_m2: float = 0.0
    T_froid_maintenue_K: float | None = None
    """Si donnée, le réservoir froid est maintenu à cette température : le
    liquide qui y revient plus chaud est refroidi par un moyen non
    modélisé (hypothèse de Shi 2024 : eau froide à 30 °C). La chaleur
    ainsi rejetée est comptée dans ``Q_rejetee_j``."""
    Q_rejetee_j: float = field(init=False, default=0.0)
    m_chaud_kg: float = field(init=False, default=0.0)
    T_chaud_K: float = field(init=False, default=293.15)
    m_froid_kg: float = field(init=False, default=0.0)
    T_froid_K: float = field(init=False, default=293.15)

    def initialiser(self, T_K: float) -> None:
        self.m_chaud_kg = 0.0
        self.T_chaud_K = T_K
        self.m_froid_kg = self.masse_totale_kg
        self.T_froid_K = (self.T_froid_maintenue_K
                          if self.T_froid_maintenue_K is not None else T_K)
        self.Q_rejetee_j = 0.0

    # --- bilans ----------------------------------------------------------
    def energie_stockee_j(self, T_ref_K: float) -> float:
        c = self.fluide.cp_j_kgk
        return c * (self.m_chaud_kg * (self.T_chaud_K - T_ref_K)
                    + self.m_froid_kg * (self.T_froid_K - T_ref_K))

    def exergie_j(self, T0_K: float) -> float:
        c = self.fluide.cp_j_kgk
        ex = 0.0
        for m, T in ((self.m_chaud_kg, self.T_chaud_K),
                     (self.m_froid_kg, self.T_froid_K)):
            if m > 0:
                ex += m * c * ((T - T0_K) - T0_K * math.log(T / T0_K))
        return ex

    @property
    def T_plafond_K(self) -> float:
        return (self.fluide.T_max_K if self.fluide.T_max_K is not None
                else float("inf"))

    # --- charge ----------------------------------------------------------
    def charger(self, air: Air, p_pa: float, T_in_K: float, m_dot_kg_s: float,
                dt_s: float) -> tuple[float, float, bool]:
        """Retourne (T_air_out, Q_j stockée, plafond atteint)."""
        d = self.pincement_K
        T_liquide = min(T_in_K - d, self.T_plafond_K)
        plafond = T_in_K - d > self.T_plafond_K
        if self.m_froid_kg <= 0 or T_liquide <= self.T_froid_K + 1e-6:
            return T_in_K, 0.0, plafond
        T_air_out = min(T_in_K, self.T_froid_K + d)
        q = air.h(p_pa, T_in_K) - air.h(p_pa, T_air_out)
        Q = m_dot_kg_s * q * dt_s
        c = self.fluide.cp_j_kgk
        dm = Q / (c * (T_liquide - self.T_froid_K))
        if dm > self.m_froid_kg:
            dm = self.m_froid_kg
            Q = dm * c * (T_liquide - self.T_froid_K)
            h_out = air.h(p_pa, T_in_K) - Q / (m_dot_kg_s * dt_s)
            T_air_out = air.T_de_p_h(p_pa, h_out)
        self.T_chaud_K = (
            (self.m_chaud_kg * self.T_chaud_K + dm * T_liquide)
            / (self.m_chaud_kg + dm))
        self.m_chaud_kg += dm
        self.m_froid_kg -= dm
        return T_air_out, Q, plafond

    # --- décharge --------------------------------------------------------
    def rechauffer(self, air: Air, p_pa: float, T_avant_K: float,
                   m_dot_kg_s: float, dt_s: float,
                   T_cible_K: float | None) -> tuple[float, float]:
        """Retourne (T_air_out, Q_j fournie)."""
        d = self.pincement_K
        T_max_air = self.T_chaud_K - d
        if self.m_chaud_kg <= 0 or T_max_air <= T_avant_K + 1e-6:
            return T_avant_K, 0.0
        T_out = T_max_air if T_cible_K is None else min(T_cible_K, T_max_air)
        if T_out <= T_avant_K:
            return T_avant_K, 0.0
        q = air.h(p_pa, T_out) - air.h(p_pa, T_avant_K)
        Q = m_dot_kg_s * q * dt_s
        c = self.fluide.cp_j_kgk
        T_liquide_out = T_avant_K + d
        dm = Q / (c * (self.T_chaud_K - T_liquide_out))
        if dm > self.m_chaud_kg:
            dm = self.m_chaud_kg
            Q = dm * c * (self.T_chaud_K - T_liquide_out)
            h_out = air.h(p_pa, T_avant_K) + Q / (m_dot_kg_s * dt_s)
            T_out = air.T_de_p_h(p_pa, h_out)
        if self.T_froid_maintenue_K is not None:
            T_retour = self.T_froid_maintenue_K
            self.Q_rejetee_j += dm * c * max(T_liquide_out - T_retour, 0.0)
        else:
            T_retour = T_liquide_out
        self.T_froid_K = (
            (self.m_froid_kg * self.T_froid_K + dm * T_retour)
            / (self.m_froid_kg + dm))
        self.m_froid_kg += dm
        self.m_chaud_kg -= dm
        return T_out, Q

    # --- attente ---------------------------------------------------------
    def attendre(self, dt_s: float, T_amb_K: float) -> float:
        """Pertes des deux réservoirs [J] (relaxation exacte, #F41)."""
        UA = self.coefficient_perte_w_m2k * self.surface_par_reservoir_m2
        if UA <= 0:
            return 0.0
        c = self.fluide.cp_j_kgk
        Q = 0.0
        if self.m_chaud_kg > 0:
            f = 1.0 - math.exp(-UA * dt_s / (self.m_chaud_kg * c))
            dT = (self.T_chaud_K - T_amb_K) * f
            Q += self.m_chaud_kg * c * dT
            self.T_chaud_K -= dT
        if self.m_froid_kg > 0:
            f = 1.0 - math.exp(-UA * dt_s / (self.m_froid_kg * c))
            dT = (self.T_froid_K - T_amb_K) * f
            Q += self.m_froid_kg * c * dT
            self.T_froid_K -= dT
        return Q
