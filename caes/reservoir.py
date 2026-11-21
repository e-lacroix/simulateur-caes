"""Réservoir d'air comprimé équivalent : bilans de masse et d'énergie.

Équations 11 à 14 et 21 de Dormoy (2024), voir formules.md#F11 et #F12.
Hypothèses de Dormoy : température uniforme, volume constant, pas de
rayonnement, un seul réservoir équivalent (volume et surface sommés).

Deux modèles thermiques :

* ``"K_global"`` : pertes K·A·(T − T_amb) vers l'ambiant (éq. 14, charge) ;
* ``"paroi"`` : la paroi a une capacité thermique ; échange intérieur
  h_int·A·(T − T_paroi) et extérieur h_ext·A·(T_paroi − T_amb) (éq. 21,
  utilisé par Dormoy pour la décharge).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from caes.proprietes import Air


@dataclass
class Reservoir:
    """Réservoir équivalent (état mutable : masse et énergie interne)."""

    volume_m3: float
    surface_m2: float
    modele_thermique: str = "K_global"
    K_global_w_m2k: float = 0.0
    h_int_w_m2k: float = 0.0
    h_ext_w_m2k: float = 0.0
    capacite_paroi_j_k: float = 0.0

    masse_kg: float = field(init=False, default=0.0)
    energie_interne_j: float = field(init=False, default=0.0)
    T_K: float = field(init=False, default=0.0)
    p_abs_pa: float = field(init=False, default=0.0)
    T_paroi_K: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        if self.modele_thermique not in ("K_global", "paroi"):
            raise ValueError(
                f"modèle thermique inconnu : {self.modele_thermique}"
            )
        if self.modele_thermique == "paroi" and self.capacite_paroi_j_k <= 0:
            raise ValueError("le modèle « paroi » exige une capacité > 0")

    def initialiser(
        self,
        air: Air,
        p_abs_pa: float,
        T_K: float,
        T_paroi_K: float | None = None,
    ) -> None:
        """Fixe l'état initial à (p, T) ; la paroi est à T_paroi ou T."""
        rho = air.rho(p_abs_pa, T_K)
        self.masse_kg = rho * self.volume_m3
        self.energie_interne_j = self.masse_kg * air.u_de_rho_T(rho, T_K)
        self.T_K = T_K
        self.p_abs_pa = p_abs_pa
        self.T_paroi_K = T_K if T_paroi_K is None else T_paroi_K

    @property
    def rho(self) -> float:
        return self.masse_kg / self.volume_m3

    def _conductance_interne(self) -> float:
        """Conductance [W/K] entre l'air et son premier puits de chaleur."""
        if self.modele_thermique == "K_global":
            return self.K_global_w_m2k * self.surface_m2
        return self.h_int_w_m2k * self.surface_m2

    def _T_puits(self, T_amb_K: float) -> float:
        if self.modele_thermique == "K_global":
            return T_amb_K
        return self.T_paroi_K

    def pas(
        self,
        air: Air,
        dt_s: float,
        debit_entree_kg_s: float,
        h_entree_j_kg: float,
        T_amb_K: float,
        debit_sortie_kg_s: float = 0.0,
    ) -> dict[str, float]:
        """Avance d'un pas de temps (formules.md#F11, #F12).

        ΔU = ṁ_in·h_in·Δt − ṁ_out·h_out·Δt − Q_perte   (éq. 14)

        La perte thermique est intégrée exactement sur le pas pour une
        température de puits constante, ce qui reste stable quand la
        masse d'air est petite (début de charge) et Δt grand.

        Retourne les flux du pas : ``q_perte_w`` (chaleur cédée par
        l'air), ``q_ext_w`` (chaleur cédée par la paroi à l'ambiant, en
        mode paroi) et ``h_sortie_j_kg``.
        """
        if dt_s <= 0:
            raise ValueError("dt doit être > 0")
        rho = self.rho
        h_sortie = air.h(self.p_abs_pa, self.T_K)
        cv = air.cv_de_rho_T(rho, self.T_K)
        UA = self._conductance_interne()
        T_puits = self._T_puits(T_amb_K)
        if UA > 0 and self.masse_kg > 0:
            tau = self.masse_kg * cv / UA
            facteur = tau / dt_s * (1.0 - math.exp(-dt_s / tau))
        else:
            facteur = 1.0
        q_perte_w = UA * (self.T_K - T_puits) * facteur

        q_ext_w = 0.0
        if self.modele_thermique == "paroi":
            UA_ext = self.h_ext_w_m2k * self.surface_m2
            q_ext_w = UA_ext * (self.T_paroi_K - T_amb_K)
            self.T_paroi_K += dt_s * (q_perte_w - q_ext_w) / (
                self.capacite_paroi_j_k
            )

        dm = (debit_entree_kg_s - debit_sortie_kg_s) * dt_s
        dU = (
            debit_entree_kg_s * h_entree_j_kg
            - debit_sortie_kg_s * h_sortie
            - q_perte_w
        ) * dt_s
        self.masse_kg += dm
        self.energie_interne_j += dU
        if self.masse_kg <= 0:
            raise ValueError("masse du réservoir négative ou nulle")
        rho_new = self.rho
        u_new = self.energie_interne_j / self.masse_kg
        self.T_K = air.T_de_rho_u(rho_new, u_new, self.T_K)
        self.p_abs_pa = air.p_de_rho_T(rho_new, self.T_K)
        return {
            "q_perte_w": q_perte_w,
            "q_ext_w": q_ext_w,
            "h_sortie_j_kg": h_sortie,
        }
