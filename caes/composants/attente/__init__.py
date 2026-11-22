"""Composant « attente » : le temps qui passe entre charge et décharge.

Deux modèles (phases 6 et 7) :

* ``pertes_statiques`` : pendant ``duree``, le réservoir d'air et les
  stockages de chaleur restent au repos ; seules leurs pertes
  thermiques vers l'ambiant agissent (formules.md#F12 pour le
  réservoir, #F29 et #F41 pour les cuves), avec la température
  extérieure du profil météo s'il y en a un. Les pertes dépendent du
  ``coefficient_perte`` ou du bloc ``isolation`` de chaque stockage.
* ``sans_pertes`` : le temps passe, rien ne change (isolation parfaite
  et réservoir sans échange) : l'hypothèse de la phase 5, utile comme
  borne.

L'air comprimé ne perd pas son énergie utile en refroidissant (seule la
chaleur stockée se perd) : c'est ce que les scénarios de transport
(phase 11) mesurent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from caes.composants.base import Composant, Contexte, ErreurComposant

if TYPE_CHECKING:
    from caes.composants.reservoir_air import ReservoirAir
    from caes.composants.stockage_chaleur import StockageChaleur


class Attente(Composant):
    TYPE = "attente"
    MODELES = ("pertes_statiques", "sans_pertes")

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        self.duree_s = self.nombre("duree")
        if self.duree_s < 0:
            raise ErreurComposant(f"{nom} : durée négative")
        self.dt_s = self.nombre("dt", None)

    def pas_de_temps(self) -> float:
        if self.dt_s is not None:
            return min(self.dt_s, self.duree_s) if self.duree_s > 0 else 1.0
        return min(600.0, self.duree_s) if self.duree_s > 0 else 1.0

    def executer(
        self,
        ctx: Contexte,
        reservoir: ReservoirAir | None,
        stockages: list[StockageChaleur],
    ) -> dict[str, float]:
        """Fait passer le temps ; retourne les pertes [J] et la durée.

        ``ctx.t_s`` est avancé de la durée de l'attente.
        """
        if self.duree_s <= 0 or self.modele == "sans_pertes":
            ctx.t_s += self.duree_s
            return {"duree_s": self.duree_s, "Q_perte_cuves_j": 0.0,
                    "Q_perte_reservoir_j": 0.0}
        dt = self.pas_de_temps()
        n = max(1, int(round(self.duree_s / dt)))
        dt = self.duree_s / n
        pertes_cuves = 0.0
        pertes_res = 0.0
        for k in range(n):
            pas = Contexte(ctx.air, ctx.ambiance, ctx.t_s + k * dt, dt)
            if reservoir is not None:
                f = reservoir.attendre(pas)
                pertes_res += f["q_perte_w"] * dt
            for st in stockages:
                pertes_cuves += st.attendre(pas)
        ctx.t_s += self.duree_s
        return {
            "duree_s": self.duree_s,
            "Q_perte_cuves_j": pertes_cuves,
            "Q_perte_reservoir_j": pertes_res,
        }

    def verifier_validite(self) -> list[str]:
        avis: list[str] = []
        if self.dt_s is not None and self.dt_s <= 0:
            avis.append("dt <= 0")
        if self.modele == "sans_pertes" and self.duree_s > 86400.0:
            avis.append(
                "modèle « sans_pertes » sur plus d'un jour : borne "
                "optimiste, les pertes réelles sont l'objet du modèle "
                "« pertes_statiques » avec un isolant")
        return avis
