"""Détendeur (régulateur de pression) en sortie des réservoirs.

Deux modèles de Dormoy (2024), §2.2.5 :

* **isenthalpique** : h_out = h_in (voir formules.md#F15) ;
* **Cheayb et al.** : relation semi-empirique T(P) = a·P² + b·P + c
  (éq. 15, voir formules.md#F16), validée de 25 à 150 bar.

Le détendeur s'arrête quand l'écart entre la pression du réservoir et la
pression de consigne passe sous un seuil (15 bar chez Dormoy).
"""

from __future__ import annotations

from dataclasses import dataclass

from caes.proprietes import Air

MODELES = ("isenthalpique", "cheayb", "isotherme")
"""``isotherme`` (T_out = T_in) n'est pas physique : il sert seulement de
diagnostic pour mesurer l'effet du refroidissement Joule-Thomson."""


@dataclass(frozen=True)
class CoefficientsCheayb:
    """Coefficients de l'éq. 15 (registre ``detendeur.cheayb.*``)."""

    a1: float
    a2: float
    a3: float
    a4: float
    b1: float
    b2: float
    b3: float
    b4: float
    p_min_validite_pa: float = 25e5
    p_max_validite_pa: float = 150e5

    def a(self, T_in_K: float) -> float:
        T = T_in_K
        return 0.5 * (
            self.a1 / T - self.a2 / T**2 - self.a3 / T**3 + self.a4
        )

    def b(self, T_in_K: float) -> float:
        T = T_in_K
        return self.b1 / T + self.b2 / T**2 + self.b3 / T**3 - self.b4


@dataclass(frozen=True)
class ResultatDetente:
    """État avant et après le détendeur."""

    p_in_pa: float
    T_in_K: float
    p_out_pa: float
    T_out_K: float
    h_in: float
    h_out: float
    modele: str
    hors_validite: bool = False

    @property
    def dh(self) -> float:
        """Écart d'enthalpie massique [J/kg] (0 pour l'isenthalpique)."""
        return self.h_out - self.h_in


def detente_isenthalpique(
    air: Air, p_in_pa: float, T_in_K: float, p_out_pa: float
) -> ResultatDetente:
    """Laminage adiabatique sans travail : h constante (formules.md#F15)."""
    h_in = air.h(p_in_pa, T_in_K)
    T_out = air.T_de_p_h(p_out_pa, h_in)
    return ResultatDetente(
        p_in_pa=p_in_pa,
        T_in_K=T_in_K,
        p_out_pa=p_out_pa,
        T_out_K=T_out,
        h_in=h_in,
        h_out=air.h(p_out_pa, T_out),
        modele="isenthalpique",
    )


def temperature_cheayb(
    coef: CoefficientsCheayb, T_in_K: float, p_in_pa: float, p_out_pa: float
) -> float:
    """Température de sortie [K] selon l'éq. 15 (pression en bar)."""
    P_in = p_in_pa / 1e5
    P_out = p_out_pa / 1e5
    a = coef.a(T_in_K)
    b = coef.b(T_in_K)
    c = T_in_K - a * P_in**2 - b * P_in
    return a * P_out**2 + b * P_out + c


def detente_cheayb(
    air: Air,
    coef: CoefficientsCheayb,
    p_in_pa: float,
    T_in_K: float,
    p_out_pa: float,
) -> ResultatDetente:
    """Détente selon Cheayb et al. (formules.md#F16)."""
    T_out = temperature_cheayb(coef, T_in_K, p_in_pa, p_out_pa)
    hors = not (coef.p_min_validite_pa <= p_in_pa <= coef.p_max_validite_pa)
    return ResultatDetente(
        p_in_pa=p_in_pa,
        T_in_K=T_in_K,
        p_out_pa=p_out_pa,
        T_out_K=T_out,
        h_in=air.h(p_in_pa, T_in_K),
        h_out=air.h(p_out_pa, T_out),
        modele="cheayb",
        hors_validite=hors,
    )


@dataclass(frozen=True)
class Detendeur:
    """Régulateur de pression à consigne fixe."""

    p_consigne_pa: float
    ecart_min_pa: float
    modele: str = "isenthalpique"
    cheayb: CoefficientsCheayb | None = None

    def __post_init__(self) -> None:
        if self.modele not in MODELES:
            raise ValueError(f"modèle de détendeur inconnu : {self.modele}")
        if self.modele == "cheayb" and self.cheayb is None:
            raise ValueError("le modèle de Cheayb exige ses coefficients")

    @property
    def p_arret_pa(self) -> float:
        """Pression de réservoir sous laquelle le détendeur s'arrête."""
        return self.p_consigne_pa + self.ecart_min_pa

    def peut_fonctionner(self, p_reservoir_pa: float) -> bool:
        return p_reservoir_pa >= self.p_arret_pa

    def detendre(
        self, air: Air, p_reservoir_pa: float, T_reservoir_K: float
    ) -> ResultatDetente:
        if p_reservoir_pa < self.p_consigne_pa:
            raise ValueError(
                f"pression du réservoir ({p_reservoir_pa / 1e5:.1f} bar) "
                f"sous la consigne ({self.p_consigne_pa / 1e5:.1f} bar)"
            )
        if self.modele == "cheayb":
            assert self.cheayb is not None
            return detente_cheayb(
                air, self.cheayb, p_reservoir_pa, T_reservoir_K,
                self.p_consigne_pa,
            )
        if self.modele == "isotherme":
            return ResultatDetente(
                p_in_pa=p_reservoir_pa,
                T_in_K=T_reservoir_K,
                p_out_pa=self.p_consigne_pa,
                T_out_K=T_reservoir_K,
                h_in=air.h(p_reservoir_pa, T_reservoir_K),
                h_out=air.h(self.p_consigne_pa, T_reservoir_K),
                modele="isotherme",
            )
        return detente_isenthalpique(
            air, p_reservoir_pa, T_reservoir_K, self.p_consigne_pa
        )
