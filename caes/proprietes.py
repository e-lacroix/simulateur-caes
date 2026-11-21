"""Propriétés thermodynamiques de l'air sec.

Deux modèles interchangeables :

* :class:`AirReel` : équation d'état de Lemmon et al. (2000) via CoolProp,
  comme Dormoy (2024). C'est le modèle par défaut (voir formules.md#F02).
* :class:`AirParfait` : gaz parfait à chaleur massique constante, pour
  comparer et pour les exemples à la main (voir formules.md#F03).

Toutes les grandeurs sont en SI : Pa, K, kg/m3, J/kg, J/(kg·K).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

import CoolProp.CoolProp as CP

from caes.registre import Registre


@dataclass(frozen=True)
class Etat:
    """État thermodynamique d'une masse d'air."""

    p_abs_pa: float
    T_K: float
    rho: float
    h: float


class Air(ABC):
    """Interface commune aux modèles d'air."""

    nom: str = "air"

    @abstractmethod
    def rho(self, p_abs_pa: float, T_K: float) -> float:
        """Masse volumique [kg/m3]."""

    @abstractmethod
    def T_de_p_rho(self, p_abs_pa: float, rho: float) -> float:
        """Température [K] à partir de la pression et de la masse volumique."""

    @abstractmethod
    def p_de_rho_T(self, rho: float, T_K: float) -> float:
        """Pression absolue [Pa] à partir de la masse volumique et de T."""

    @abstractmethod
    def h(self, p_abs_pa: float, T_K: float) -> float:
        """Enthalpie massique [J/kg]."""

    @abstractmethod
    def u_de_rho_T(self, rho: float, T_K: float) -> float:
        """Énergie interne massique [J/kg]."""

    @abstractmethod
    def cv_de_rho_T(self, rho: float, T_K: float) -> float:
        """Chaleur massique à volume constant [J/(kg·K)]."""

    @abstractmethod
    def cp(self, p_abs_pa: float, T_K: float) -> float:
        """Chaleur massique à pression constante [J/(kg·K)]."""

    @abstractmethod
    def s(self, p_abs_pa: float, T_K: float) -> float:
        """Entropie massique [J/(kg·K)]."""

    @abstractmethod
    def T_de_p_h(self, p_abs_pa: float, h: float) -> float:
        """Température [K] à partir de la pression et de l'enthalpie."""

    @abstractmethod
    def mu(self, p_abs_pa: float, T_K: float) -> float:
        """Viscosité dynamique [Pa·s]."""

    @abstractmethod
    def k(self, p_abs_pa: float, T_K: float) -> float:
        """Conductivité thermique [W/(m·K)]."""

    def prandtl(self, p_abs_pa: float, T_K: float) -> float:
        """Nombre de Prandtl Pr = μ·cp/k [-]."""
        return self.mu(p_abs_pa, T_K) * self.cp(p_abs_pa, T_K) / self.k(
            p_abs_pa, T_K
        )

    def etat(self, p_abs_pa: float, T_K: float) -> Etat:
        """État complet à (p, T)."""
        return Etat(
            p_abs_pa=p_abs_pa,
            T_K=T_K,
            rho=self.rho(p_abs_pa, T_K),
            h=self.h(p_abs_pa, T_K),
        )

    def T_de_rho_u(
        self,
        rho: float,
        u: float,
        T_depart: float,
        tolerance_K: float = 1e-4,
        iterations_max: int = 50,
    ) -> float:
        """Température [K] telle que u(rho, T) = u, par la méthode de Newton.

        Utilisé par le réservoir : on connaît sa masse (donc rho) et son
        énergie interne, on cherche sa température. La dérivée de u par
        rapport à T à volume constant est cv, ce qui rend Newton très
        rapide (2 ou 3 itérations).
        """
        T = T_depart
        for _ in range(iterations_max):
            f = self.u_de_rho_T(rho, T) - u
            cv = self.cv_de_rho_T(rho, T)
            dT = -f / cv
            T += dT
            if abs(dT) < tolerance_K:
                return T
        raise RuntimeError(
            f"T_de_rho_u : pas de convergence (rho={rho}, u={u})"
        )


class AirReel(Air):
    """Air réel (CoolProp, fluide « Air », équation de Lemmon 2000).

    Domaine de validité de l'équation d'état : 60 à 2000 K, jusqu'à
    2000 MPa, bien au-delà des besoins du simulateur.
    """

    nom = "air réel (CoolProp)"

    def __init__(self) -> None:
        self._etat = CP.AbstractState("HEOS", "Air")

    def rho(self, p_abs_pa: float, T_K: float) -> float:
        self._etat.update(CP.PT_INPUTS, p_abs_pa, T_K)
        return self._etat.rhomass()

    def T_de_p_rho(self, p_abs_pa: float, rho: float) -> float:
        self._etat.update(CP.DmassP_INPUTS, rho, p_abs_pa)
        return self._etat.T()

    def p_de_rho_T(self, rho: float, T_K: float) -> float:
        self._etat.update(CP.DmassT_INPUTS, rho, T_K)
        return self._etat.p()

    def h(self, p_abs_pa: float, T_K: float) -> float:
        self._etat.update(CP.PT_INPUTS, p_abs_pa, T_K)
        return self._etat.hmass()

    def u_de_rho_T(self, rho: float, T_K: float) -> float:
        self._etat.update(CP.DmassT_INPUTS, rho, T_K)
        return self._etat.umass()

    def cv_de_rho_T(self, rho: float, T_K: float) -> float:
        self._etat.update(CP.DmassT_INPUTS, rho, T_K)
        return self._etat.cvmass()

    def cp(self, p_abs_pa: float, T_K: float) -> float:
        self._etat.update(CP.PT_INPUTS, p_abs_pa, T_K)
        return self._etat.cpmass()

    def s(self, p_abs_pa: float, T_K: float) -> float:
        self._etat.update(CP.PT_INPUTS, p_abs_pa, T_K)
        return self._etat.smass()

    def T_de_p_h(self, p_abs_pa: float, h: float) -> float:
        self._etat.update(CP.HmassP_INPUTS, h, p_abs_pa)
        return self._etat.T()

    def mu(self, p_abs_pa: float, T_K: float) -> float:
        self._etat.update(CP.PT_INPUTS, p_abs_pa, T_K)
        return self._etat.viscosity()

    def k(self, p_abs_pa: float, T_K: float) -> float:
        self._etat.update(CP.PT_INPUTS, p_abs_pa, T_K)
        return self._etat.conductivity()


class AirParfait(Air):
    """Gaz parfait à chaleurs massiques constantes (voir formules.md#F03).

    ``R`` et ``cp`` viennent du registre (``air.R_specifique`` et
    ``air.cp_1bar_20C``). L'enthalpie et l'énergie interne sont comptées
    à partir de 0 K (h = cp·T, u = cv·T) : seules les différences ont un
    sens physique.
    """

    nom = "gaz parfait"

    def __init__(
        self,
        R: float,
        cp: float,
        mu_ref: float = 1.716e-5,
        T_ref_mu: float = 273.15,
        S_sutherland: float = 110.4,
        prandtl: float = 0.71,
    ) -> None:
        self.R = R
        self._cp = cp
        self.cv = cp - R
        self._mu_ref = mu_ref
        self._T_ref_mu = T_ref_mu
        self._S = S_sutherland
        self._Pr = prandtl

    @classmethod
    def depuis_registre(cls, registre: Registre | None = None) -> AirParfait:
        """Construit le modèle avec les constantes du registre."""
        reg = registre or Registre.charger()
        return cls(
            R=reg.si("air.R_specifique"),
            cp=reg.si("air.cp_1bar_20C"),
            mu_ref=reg.si("air.sutherland.mu_ref"),
            T_ref_mu=reg.si("air.sutherland.T_ref"),
            S_sutherland=reg.si("air.sutherland.S"),
            prandtl=reg.si("air.prandtl"),
        )

    def mu(self, p_abs_pa: float, T_K: float) -> float:
        """Loi de Sutherland (formules.md#F26)."""
        T0, S = self._T_ref_mu, self._S
        return self._mu_ref * (T_K / T0) ** 1.5 * (T0 + S) / (T_K + S)

    def k(self, p_abs_pa: float, T_K: float) -> float:
        return self.mu(p_abs_pa, T_K) * self._cp / self._Pr

    def rho(self, p_abs_pa: float, T_K: float) -> float:
        return p_abs_pa / (self.R * T_K)

    def T_de_p_rho(self, p_abs_pa: float, rho: float) -> float:
        return p_abs_pa / (self.R * rho)

    def p_de_rho_T(self, rho: float, T_K: float) -> float:
        return rho * self.R * T_K

    def h(self, p_abs_pa: float, T_K: float) -> float:
        return self._cp * T_K

    def u_de_rho_T(self, rho: float, T_K: float) -> float:
        return self.cv * T_K

    def cv_de_rho_T(self, rho: float, T_K: float) -> float:
        return self.cv

    def cp(self, p_abs_pa: float, T_K: float) -> float:
        return self._cp

    def s(self, p_abs_pa: float, T_K: float) -> float:
        # Référence arbitraire : s = 0 à 1 Pa et 1 K (seules les
        # différences comptent).
        return self._cp * math.log(T_K) - self.R * math.log(p_abs_pa)

    def T_de_p_h(self, p_abs_pa: float, h: float) -> float:
        return h / self._cp


def air_par_defaut() -> Air:
    """Le modèle d'air utilisé par le simulateur : l'air réel."""
    return AirReel()
