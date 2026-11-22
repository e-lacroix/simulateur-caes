"""Composant « réservoir d'air » (bilans de masse et d'énergie).

Trois modèles thermiques (phases 1, 2 et 7, formules.md#F11, #F12, #F38) :

* ``K_global`` : pertes K·A·(T − T_amb) vers l'ambiant (éq. 14) ;
* ``paroi`` : la paroi a une capacité thermique, échanges intérieur et
  extérieur (éq. 21, nécessaire en décharge) ;
* ``adiabatique`` (Shi 2024) : aucun échange avec l'extérieur ; valable
  pour une caverne, pas pour les petits réservoirs de Dormoy.

``surpression_entree`` (Shi : 0,2 MPa) est la pression que la chaîne de
compression doit fournir au-dessus de celle du réservoir.

L'air qui arrive à une pression supérieure à celle du réservoir est
laminé à enthalpie constante (le réservoir reçoit h_entrée). La
température ambiante des pertes vient du contexte.
"""

from __future__ import annotations

from typing import Any

from caes.composants.base import Composant, Contexte, EtatAir
from caes.proprietes import Air
from caes.composants.compresseur import PRECISION_CACHE_PA
from caes.composants.humidite import point_de_rosee, w_saturation
from caes.reservoir import Reservoir as ModeleReservoir

TOLERANCE_ENTREE_PA = PRECISION_CACHE_PA


class ReservoirAir(Composant):
    TYPE = "reservoir_air"
    MODELES = ("K_global", "paroi", "adiabatique")
    A_UN_ETAT = True

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        self.modele_phys = ModeleReservoir(
            volume_m3=self.nombre("volume"),
            surface_m2=self.nombre("surface"),
            modele_thermique=("K_global" if self.modele == "adiabatique"
                              else self.modele),
            K_global_w_m2k=(0.0 if self.modele == "adiabatique"
                            else self.nombre("K_global", 0.0)),
            h_int_w_m2k=self.nombre("h_int", 0.0),
            h_ext_w_m2k=self.nombre("h_ext", 0.0),
            capacite_paroi_j_k=self.nombre("capacite_thermique_paroi", 0.0),
        )
        self.p_max_pa = self.nombre("p_max", None)
        self.fuite_par_jour = self.nombre("fuite_par_jour", 0.0)
        """Fraction de la masse d'air perdue par jour pendant l'attente
        (fuite lente, F12 ; 0 par défaut)."""
        self.masse_fuite_kg = 0.0
        self.surpression_entree_pa = self.nombre("surpression_entree", 0.0)
        self.initialise = False
        self.eau_vapeur_kg = 0.0
        self.eau_liquide_kg = 0.0
        """Eau condensée au fond du réservoir (F43)."""
        self.eau_condensee_cumul_kg = 0.0
        self.eau_initiale_a_plafonner = False
        """Vrai tant que l'eau de l'air initial n'a pas été bornée par
        ce que la chaîne de charge refoule (``plafonner_eau``)."""

    # --- état ----------------------------------------------------------
    def initialiser(self, air: Air, p_abs_pa: float, T_K: float,
                    T_paroi_K: float | None = None,
                    w_kg_kg: float = 0.0) -> None:
        self.modele_phys.initialiser(air, p_abs_pa, T_K, T_paroi_K)
        self.initialise = True
        self.eau_vapeur_kg = 0.0
        self.eau_liquide_kg = 0.0
        self.eau_condensee_cumul_kg = 0.0
        self.eau_initiale_a_plafonner = w_kg_kg > 0
        if w_kg_kg > 0:
            # L'air déjà présent ne peut pas porter plus que la saturation
            # à son (T, p) : l'excès a été drainé avant l'instant initial
            # et n'est pas compté comme condensation (hypothèse, F43).
            w0 = min(w_kg_kg, w_saturation(T_K, p_abs_pa))
            self.eau_vapeur_kg = w0 * self.masse_kg

    def plafonner_eau(self, w_max_kg_kg: float) -> None:
        """Borne la vapeur de l'air initial à ``w_max`` (teneur de l'air
        que la chaîne de charge refoule) ; l'excès a été drainé avant
        l'instant initial et n'est pas compté comme condensation."""
        self.eau_vapeur_kg = min(self.eau_vapeur_kg,
                                 max(w_max_kg_kg, 0.0) * self.masse_kg)
        self.eau_initiale_a_plafonner = False

    def _equilibrer_eau(self) -> None:
        """La vapeur ne peut pas dépasser la saturation à (T, p) du
        réservoir ; l'excès se condense au fond (ou s'y évapore)."""
        total = self.eau_vapeur_kg + self.eau_liquide_kg
        if total <= 0:
            return
        cap = w_saturation(self.T_K, self.p_abs_pa) * self.masse_kg
        vap = min(total, cap)
        condense = self.eau_vapeur_kg - vap
        if condense > 1e-9:
            self.eau_condensee_cumul_kg += condense
            self.avertir(
                "condensation d'eau dans le réservoir (air plus froid que "
                "son point de rosée sous pression)")
        self.eau_vapeur_kg = vap
        self.eau_liquide_kg = total - vap

    @property
    def w_vapeur_kg_kg(self) -> float:
        return self.eau_vapeur_kg / self.masse_kg if self.masse_kg else 0.0

    @property
    def T_rosee_K(self) -> float:
        return point_de_rosee(self.p_abs_pa, self.w_vapeur_kg_kg)

    def reinitialiser(self) -> None:
        self.initialise = False

    @property
    def volume_m3(self) -> float:
        return self.modele_phys.volume_m3

    @property
    def p_abs_pa(self) -> float:
        return self.modele_phys.p_abs_pa

    @property
    def T_K(self) -> float:
        return self.modele_phys.T_K

    @property
    def T_paroi_K(self) -> float:
        return self.modele_phys.T_paroi_K

    @property
    def masse_kg(self) -> float:
        return self.modele_phys.masse_kg

    @property
    def energie_interne_j(self) -> float:
        return self.modele_phys.energie_interne_j

    def etat_sortie(self, m_dot_kg_s: float) -> EtatAir:
        """L'air qui sort : à l'état du réservoir, avec sa vapeur (l'eau
        condensée reste au fond)."""
        return EtatAir(self.p_abs_pa, self.T_K, m_dot_kg_s,
                       self.w_vapeur_kg_kg, 0.0)

    # --- un pas --------------------------------------------------------
    def remplir(self, ctx: Contexte, entree: EtatAir) -> dict[str, float]:
        """Reçoit ``entree`` pendant ``dt`` (laminage implicite, #F12)."""
        h_in = ctx.air.h(entree.p_abs_pa, entree.T_K)
        # Tolérance : les lois en pression de la chaîne sont évaluées au
        # 0,1 bar près (cache), d'où un écart possible de cet ordre.
        if entree.p_abs_pa < self.p_abs_pa - TOLERANCE_ENTREE_PA:
            self.avertir(
                "air entrant à une pression inférieure à celle du "
                "réservoir : physiquement, il ne pourrait pas entrer"
            )
        flux = self.modele_phys.pas(
            ctx.air, ctx.dt_s, entree.m_dot_kg_s, h_in, ctx.T_amb_K
        )
        self.eau_vapeur_kg += entree.w_vapeur_kg_kg * entree.m_dot_kg_s * (
            ctx.dt_s)
        self.eau_liquide_kg += (entree.w_liquide_kg_kg * entree.m_dot_kg_s
                                * ctx.dt_s)
        self._equilibrer_eau()
        self._surveiller()
        return flux

    def vider(self, ctx: Contexte, m_dot_kg_s: float) -> dict[str, float]:
        """Soutire ``m_dot`` pendant ``dt`` (#F12)."""
        w_out = self.w_vapeur_kg_kg
        flux = self.modele_phys.pas(
            ctx.air, ctx.dt_s, 0.0, 0.0, ctx.T_amb_K,
            debit_sortie_kg_s=m_dot_kg_s,
        )
        self.eau_vapeur_kg = max(
            self.eau_vapeur_kg - w_out * m_dot_kg_s * ctx.dt_s, 0.0)
        self._equilibrer_eau()
        self._surveiller()
        return flux

    def attendre(self, ctx: Contexte) -> dict[str, float]:
        """Pas sans débit : seules les pertes thermiques agissent (et
        l'eau se condense si le réservoir refroidit) ; avec
        ``fuite_par_jour``, une fraction de l'air s'échappe à l'état du
        réservoir (F12)."""
        fuite = self.fuite_par_jour / 86400.0 * self.masse_kg
        flux = self.modele_phys.pas(ctx.air, ctx.dt_s, 0.0, 0.0,
                                    ctx.T_amb_K, debit_sortie_kg_s=fuite)
        if fuite > 0:
            self.masse_fuite_kg += fuite * ctx.dt_s
            w = self.w_vapeur_kg_kg
            self.eau_vapeur_kg = max(self.eau_vapeur_kg
                                     - w * fuite * ctx.dt_s, 0.0)
        self._equilibrer_eau()
        flux["m_fuite_kg_s"] = fuite
        return flux

    def _surveiller(self) -> None:
        if self.p_max_pa is not None and self.p_abs_pa > self.p_max_pa:
            self.avertir(
                f"pression au-dessus de la pression maximale admise "
                f"({self.p_max_pa / 1e5:.0f} bar)"
            )
        if not 200.0 <= self.T_K <= 450.0:
            self.avertir(
                "température de l'air hors de la plage vérifiée "
                "(−73 à 177 °C)"
            )

    def verifier_validite(self) -> list[str]:
        avis: list[str] = []
        if self.volume_m3 <= 0 or self.modele_phys.surface_m2 <= 0:
            avis.append("volume ou surface nul")
        if not 0.0 <= self.fuite_par_jour < 1.0:
            avis.append("fuite_par_jour hors de [0, 1[")
        if self.modele == "adiabatique" and self.volume_m3 < 1000.0:
            avis.append(
                "modèle « adiabatique » sur un petit réservoir : la paroi "
                "compte (Dormoy mesure K = 8,8 W/m²K) ; valable pour une "
                "caverne")
        return avis
