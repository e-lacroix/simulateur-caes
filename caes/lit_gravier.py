"""Lit de gravier traversé par de l'air : modèle de Schumann 1D.

Deux équations (air et solide), discrétisées en cellules le long de
l'axe de la cuve (voir formules.md#F25 à #F29) :

* l'air est quasi stationnaire (sa capacité thermique est négligeable
  devant celle du gravier) : dans chaque cellule, il se rapproche de la
  température du solide selon T_out = T_s + (T_in − T_s)·e^(−NTU) ;
* le solide reçoit la chaleur cédée par l'air, échange par conduction
  avec ses voisins et perd de la chaleur à travers l'isolant.

Le schéma est exact cellule par cellule pour un pas de temps (relaxation
exponentielle), donc stable quel que soit le pas, et conserve l'énergie
par construction. Avec ``n_cellules = 1`` on retrouve le modèle « cuve
bien mélangée ».

Corrélations : Wakao (coefficient d'échange, #F27), Jeffreson
(gradient interne, #F27), Ergun (perte de charge, #F28).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from caes.materiaux import Materiau
from caes.proprietes import Air


@dataclass(frozen=True)
class Correlations:
    """Constantes des corrélations (registre ``lit.*``)."""

    wakao_a: float = 2.0
    wakao_b: float = 1.1
    wakao_c: float = 0.6
    wakao_Re_min: float = 15.0
    wakao_Re_max: float = 8500.0
    ergun_A: float = 150.0
    ergun_B: float = 1.75
    jeffreson_facteur: float = 5.0

    def nusselt(self, Re: float, Pr: float) -> float:
        """Nu = a + b·Re^c·Pr^(1/3) (Wakao et al. 1979, formules.md#F27)."""
        return self.wakao_a + self.wakao_b * Re**self.wakao_c * Pr ** (1.0 / 3)

    def dans_validite(self, Re: float) -> bool:
        return self.wakao_Re_min <= Re <= self.wakao_Re_max


def coefficient_echange(
    air: Air,
    materiau: Materiau,
    corr: Correlations,
    p_abs_pa: float,
    T_K: float,
    vitesse_superficielle_m_s: float,
) -> tuple[float, float, float]:
    """Coefficient d'échange air-particule h [W/m²K] (formules.md#F27).

    Retourne (h_eff, Re, Bi). h_eff inclut la correction de Jeffreson
    pour le gradient de température à l'intérieur des particules.
    """
    d = materiau.diametre_particule_m
    rho = air.rho(p_abs_pa, T_K)
    mu = air.mu(p_abs_pa, T_K)
    k_f = air.k(p_abs_pa, T_K)
    Pr = air.prandtl(p_abs_pa, T_K)
    Re = rho * vitesse_superficielle_m_s * d / mu
    Nu = corr.nusselt(Re, Pr)
    h = Nu * k_f / d
    Bi = h * d / (2.0 * materiau.conductivite_w_mk)
    h_eff = h / (1.0 + Bi / corr.jeffreson_facteur)
    return h_eff, Re, Bi


def perte_de_charge_ergun(
    air: Air,
    materiau: Materiau,
    corr: Correlations,
    p_abs_pa: float,
    T_K: float,
    vitesse_superficielle_m_s: float,
    longueur_m: float,
) -> float:
    """Perte de charge d'Ergun [Pa] (formules.md#F28).

    Δp/L = A·μ·(1−ε)²·u/(ε³·d²) + B·ρ·(1−ε)·u²/(ε³·d)
    """
    eps = materiau.porosite
    d = materiau.diametre_particule_m
    u = vitesse_superficielle_m_s
    rho = air.rho(p_abs_pa, T_K)
    mu = air.mu(p_abs_pa, T_K)
    visqueux = corr.ergun_A * mu * (1.0 - eps) ** 2 * u / (eps**3 * d**2)
    inertiel = corr.ergun_B * rho * (1.0 - eps) * u**2 / (eps**3 * d)
    return (visqueux + inertiel) * longueur_m


@dataclass
class LitGravier:
    """Cuve cylindrique remplie de gravier, discrétisée en cellules.

    La cellule 0 est en haut (entrée de l'air chaud en charge, sortie en
    décharge). ``coefficient_perte_w_m2k`` est le coefficient global de
    perte à travers la paroi latérale isolée (interface du futur module
    ``isolation``) ; 0 = isolation parfaite.
    """

    materiau: Materiau
    diametre_m: float
    hauteur_m: float
    n_cellules: int = 40
    coefficient_perte_w_m2k: float = 0.0
    correlations: Correlations = field(default_factory=Correlations)
    conduction_axiale: bool = True
    h_impose_w_m2k: float | None = None
    """Si donné, remplace la corrélation (tests analytiques)."""

    T_s_K: np.ndarray = field(init=False, repr=False)
    Re_dernier: float = field(init=False, default=0.0)
    Bi_dernier: float = field(init=False, default=0.0)
    h_dernier: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        if self.n_cellules < 1:
            raise ValueError("au moins une cellule")
        self.T_s_K = np.full(self.n_cellules, 293.15)

    # --- géométrie -----------------------------------------------------
    @property
    def section_m2(self) -> float:
        return math.pi * self.diametre_m**2 / 4.0

    @property
    def volume_m3(self) -> float:
        return self.section_m2 * self.hauteur_m

    @property
    def dx_m(self) -> float:
        return self.hauteur_m / self.n_cellules

    @property
    def masse_gravier_kg(self) -> float:
        return (
            (1.0 - self.materiau.porosite)
            * self.materiau.masse_volumique_kg_m3
            * self.volume_m3
        )

    @property
    def capacite_cellule_j_k(self) -> float:
        """Capacité thermique du solide d'une cellule [J/K]."""
        return self.materiau.capacite_volumique_lit_j_m3k * (
            self.section_m2 * self.dx_m
        )

    @property
    def surface_laterale_cellule_m2(self) -> float:
        return math.pi * self.diametre_m * self.dx_m

    def initialiser(self, T_K: float | np.ndarray) -> None:
        """Température initiale uniforme ou profil (haut → bas)."""
        self.T_s_K = np.full(self.n_cellules, float(T_K)) if np.isscalar(
            T_K
        ) else np.array(T_K, dtype=float).copy()

    def energie_stockee_j(self, T_ref_K: float) -> float:
        """Chaleur du gravier au-dessus de T_ref [J]."""
        return float(self.capacite_cellule_j_k * np.sum(self.T_s_K - T_ref_K))

    def energie_utile_j(self, T_seuil_K: float) -> float:
        """Chaleur du gravier au-dessus d'un seuil (par exemple 130 °C)."""
        return float(
            self.capacite_cellule_j_k
            * np.sum(np.maximum(self.T_s_K - T_seuil_K, 0.0))
        )

    # --- un pas de temps -------------------------------------------------
    def pas(
        self,
        air: Air,
        dt_s: float,
        debit_massique_kg_s: float,
        T_entree_K: float,
        p_abs_pa: float,
        T_amb_K: float,
        sens: int = 1,
    ) -> dict[str, float]:
        """Avance d'un pas (formules.md#F25, #F26, #F29).

        ``sens = +1`` : l'air entre en haut (cellule 0), charge ;
        ``sens = -1`` : l'air entre en bas, décharge. Débit nul : attente
        (conduction et pertes seulement).

        Retourne la température de sortie de l'air, la perte de charge,
        la chaleur cédée par l'air au gravier, la chaleur perdue et le
        bilan des cellules.
        """
        if dt_s <= 0:
            raise ValueError("dt doit être > 0")
        n = self.n_cellules
        C = self.capacite_cellule_j_k
        T_s = self.T_s_K
        Q_air_solide = 0.0
        T_sortie = T_entree_K
        dp = 0.0
        if debit_massique_kg_s > 0:
            ordre = range(n) if sens >= 0 else range(n - 1, -1, -1)
            m_dot = debit_massique_kg_s
            T_in = T_entree_K
            dT_s_conv = np.zeros(n)
            for i in ordre:
                T_film = 0.5 * (T_in + T_s[i])
                cp = air.cp(p_abs_pa, T_film)
                rho = air.rho(p_abs_pa, T_film)
                u = m_dot / (rho * self.section_m2)
                if self.h_impose_w_m2k is not None:
                    h = self.h_impose_w_m2k
                else:
                    h, Re, Bi = coefficient_echange(
                        air, self.materiau, self.correlations, p_abs_pa,
                        T_film, u,
                    )
                    self.Re_dernier, self.Bi_dernier = Re, Bi
                self.h_dernier = h
                a_v = self.materiau.surface_specifique_m2_m3
                NTU = h * a_v * self.section_m2 * self.dx_m / (m_dot * cp)
                eff = 1.0 - math.exp(-NTU)
                # relaxation exacte du solide vers T_in sur dt
                tau = C / (m_dot * cp * eff)
                dT = (T_in - T_s[i]) * (1.0 - math.exp(-dt_s / tau))
                dT_s_conv[i] = dT
                Q = C * dT
                Q_air_solide += Q
                T_out = T_in - Q / (m_dot * cp * dt_s)
                T_in = T_out
            T_sortie = T_in
            T_s = T_s + dT_s_conv
            T_moy = float(np.mean(T_s))
            u_moy = m_dot / (air.rho(p_abs_pa, T_moy) * self.section_m2)
            dp = perte_de_charge_ergun(
                air, self.materiau, self.correlations, p_abs_pa, T_moy,
                u_moy, self.hauteur_m,
            )

        # conduction axiale dans le solide (explicite, sous-cyclée)
        if self.conduction_axiale and n > 1:
            k = self.materiau.conductivite_w_mk * (
                1.0 - self.materiau.porosite
            )
            alpha = k / self.materiau.capacite_volumique_lit_j_m3k
            dt_max = 0.4 * self.dx_m**2 / alpha
            n_sub = max(1, int(math.ceil(dt_s / dt_max)))
            ddt = dt_s / n_sub
            r = alpha * ddt / self.dx_m**2
            for _ in range(n_sub):
                lap = np.zeros(n)
                lap[1:-1] = T_s[2:] - 2.0 * T_s[1:-1] + T_s[:-2]
                lap[0] = T_s[1] - T_s[0]
                lap[-1] = T_s[-2] - T_s[-1]
                T_s = T_s + r * lap

        # pertes latérales à travers l'isolant (relaxation exacte)
        Q_perte = 0.0
        UA = self.coefficient_perte_w_m2k * self.surface_laterale_cellule_m2
        if UA > 0:
            facteur = 1.0 - math.exp(-UA * dt_s / C)
            dT_perte = (T_s - T_amb_K) * facteur
            Q_perte = float(C * np.sum(dT_perte))
            T_s = T_s - dT_perte
        self.T_s_K = T_s
        return {
            "T_sortie_K": T_sortie,
            "dp_pa": dp,
            "Q_air_vers_solide_j": Q_air_solide,
            "Q_perte_j": Q_perte,
        }

    def simuler(
        self,
        air: Air,
        dt_s: float,
        duree_s: float,
        debit_massique_kg_s: float,
        T_entree_K: float,
        p_abs_pa: float,
        T_amb_K: float,
        sens: int = 1,
    ) -> dict[str, np.ndarray]:
        """Enchaîne des pas à conditions constantes ; renvoie les séries."""
        n = int(round(duree_s / dt_s))
        t = np.zeros(n)
        T_out = np.zeros(n)
        Q_in = 0.0
        Q_perte = 0.0
        E0 = self.energie_stockee_j(T_amb_K)
        for k in range(n):
            r = self.pas(
                air, dt_s, debit_massique_kg_s, T_entree_K, p_abs_pa,
                T_amb_K, sens,
            )
            t[k] = (k + 1) * dt_s
            T_out[k] = r["T_sortie_K"]
            Q_in += r["Q_air_vers_solide_j"]
            Q_perte += r["Q_perte_j"]
        return {
            "t_s": t,
            "T_sortie_K": T_out,
            "Q_air_vers_solide_j": np.array([Q_in]),
            "Q_perte_j": np.array([Q_perte]),
            "dE_stock_j": np.array([self.energie_stockee_j(T_amb_K) - E0]),
            "dp_pa": np.array([r["dp_pa"]]) if n else np.array([0.0]),
        }


def solution_schumann(
    xi: float, eta: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Solution analytique de Schumann (1929) pour un échelon d'entrée.

    Variables réduites : ξ = h·a_v·A·x/(ṁ·c_f), η = h·a_v·t/((1−ε)·ρ_s·c_s).
    Retourne (θ_f, θ_s) : températures réduites de l'air et du solide,
    (T − T_initial)/(T_entrée − T_initial). Capacité de l'air négligée.
    Voir formules.md#F25.
    """
    from scipy.integrate import quad
    from scipy.special import i0e

    def J(x: float, y: float) -> float:
        # J(x, y) = 1 − e^(−y) ∫₀ˣ e^(−τ) I₀(2√(yτ)) dτ, avec I₀ = i0e·e^z
        def f(tau: float) -> float:
            z = 2.0 * math.sqrt(y * tau)
            return math.exp(-tau - y + z) * i0e(z)

        val, _ = quad(f, 0.0, x, limit=200)
        return 1.0 - val

    th_f = np.array([J(xi, e) for e in eta])
    th_s = np.array([1.0 - J(e, xi) for e in eta])
    return th_f, th_s
