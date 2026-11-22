"""Composant « compresseur » : une machine à plusieurs étages.

Quatre modèles (phase 7, voir ``docs/composants/compresseur.md``) :

* ``polytropique_dormoy`` (phase 1, formules.md#F04 à #F08) : chaque
  étage suit p·vⁿ = constante ; rapports fixes des premiers étages,
  avant-dernier linéaire en pression de refoulement, dernier prend le
  reste ; rendement mécanique calibré linéaire en pression.
* ``isentropique`` (Shi 2024, #F34) : rendement isentropique constant,
  compression adiabatique.
* ``polytropique_rendement`` (Tola 2022, #F35) : rendement polytropique
  constant, compression adiabatique.
* ``isotherme`` (Baniamerian 2025, éq. 8, #F36) : borne inférieure du
  travail, température constante.

Pour les trois modèles génériques, chaque étage déclare soit un
``rapport_pression`` fixe, soit une ``T_sortie`` visée (le rapport en
découle, règle de Tola et de Shi), soit rien : les étages sans consigne
se partagent à parts égales le rapport restant jusqu'à la pression de
refoulement. Dans une chaîne, chaque étage est un maillon
(``compresseur.1``, ``compresseur.2``, ...) ; la machine est préparée
une fois par pas (:meth:`Compresseur.preparer`).
"""

from __future__ import annotations

from typing import Any

from caes.compresseur import Compresseur as ModelePolytropique
from caes.compresseur import comprimer_etage
from caes.composants.base import (
    Composant,
    Contexte,
    ErreurComposant,
    EtatAir,
    Flux,
)
from caes.composants.compresseur.isotherme import comprimer_isotherme
from caes.composants.humidite import mettre_a_l_equilibre
from caes.composants.compresseur.rendement import (
    comprimer_isentropique,
    comprimer_polytropique_rendement,
)

PRECISION_CACHE_PA = 1.0e4
"""Les lois en pression sont évaluées au 0,1 bar près (cache, phase 1)."""
BETA_MAX_RECHERCHE = 50.0
"""Borne de la recherche du rapport qui donne une température visée."""


class EtageCompresseur:
    """Vue « maillon » de l'étage ``numero`` d'une machine."""

    def __init__(self, machine: Compresseur, numero: int,
                 spec: dict[str, Any] | None = None) -> None:
        self.machine = machine
        self.numero = numero
        self.spec = spec or {}
        self.actif = True

    @property
    def nom(self) -> str:
        return f"{self.machine.nom}.{self.numero}"

    def _comprimer(self, ctx: Contexte, p_in: float, T_in: float,
                   beta: float):
        m = self.machine
        if m.modele == "polytropique_dormoy":
            n = m.modele_phys.indices_polytropiques[self.numero - 1]
            return comprimer_etage(ctx.air, p_in, T_in, beta, n)
        if m.modele == "isentropique":
            return comprimer_isentropique(ctx.air, p_in, T_in, beta,
                                          m.rendement_etage(self.numero))
        if m.modele == "polytropique_rendement":
            return comprimer_polytropique_rendement(
                ctx.air, p_in, T_in, beta, m.rendement_etage(self.numero))
        return comprimer_isotherme(ctx.air, p_in, T_in, beta)

    def _beta_pour_T(self, ctx: Contexte, p_in: float, T_in: float,
                     T_cible: float, beta_max: float) -> float:
        """Rapport de pression qui donne T_sortie = T_cible (bissection)."""
        if T_cible <= T_in:
            self.machine.avertir(
                f"étage {self.numero} : température de sortie visée sous "
                f"la température d'entrée ; rapport 1 (étage inactif)")
            return 1.0
        bas, haut = 1.0, min(beta_max, BETA_MAX_RECHERCHE)
        if self._comprimer(ctx, p_in, T_in, haut).T_out_K < T_cible:
            self.machine.avertir(
                f"étage {self.numero} : température visée inatteignable "
                f"avec le rapport restant ; rapport maximal appliqué")
            return haut
        for _ in range(60):
            mil = 0.5 * (bas + haut)
            if self._comprimer(ctx, p_in, T_in, mil).T_out_K < T_cible:
                bas = mil
            else:
                haut = mil
            if haut - bas < 1e-6:
                break
        return 0.5 * (bas + haut)

    def rapport(self, ctx: Contexte, p_in: float, T_in: float) -> float:
        """Rapport de pression de l'étage pour ce pas (formules.md#F33)."""
        m = self.machine
        if m.modele == "polytropique_dormoy":
            assert m.rapports is not None
            return m.rapports[self.numero - 1]
        restant = m.p_chaine_pa / p_in
        if restant <= 1.0 + 1e-9:
            self.actif = False
            m.avertir(
                f"étage {self.numero} : pression déjà atteinte en amont, "
                f"étage inactif (rapport 1)")
            return 1.0
        self.actif = True
        if self.spec.get("rapport_pression") is not None:
            return float(self.spec["rapport_pression"])
        if self.spec.get("T_sortie") is not None:
            return self._beta_pour_T(ctx, p_in, T_in,
                                     float(self.spec["T_sortie"]), restant)
        n_libres = m.nb_etages_libres_depuis(self.numero)
        return restant ** (1.0 / n_libres)

    def pas(self, etat: EtatAir, ctx: Contexte) -> tuple[EtatAir, Flux]:
        """Compression d'un étage selon le modèle de la machine."""
        beta = self.rapport(ctx, etat.p_abs_pa, etat.T_K)
        r = self._comprimer(ctx, etat.p_abs_pa, etat.T_K, beta)
        m_dot = etat.m_dot_kg_s
        flux = Flux(
            W_pol_w=m_dot * r.w_pol,
            Q_retire_w=max(-m_dot * r.q_poly, 0.0),
            destination="ambiant",
            resultat=r,
        )
        if r.q_poly > 0:
            # n > γ : le modèle polytropique « absorbe » un peu de
            # chaleur ; artefact signalé en phase 3.
            flux.Q_ajoute_w = m_dot * r.q_poly
            flux.source = "modele_polytropique"
        sortie = EtatAir(r.p_out_pa, r.T_out_K, m_dot,
                         etat.w_vapeur_kg_kg, etat.w_liquide_kg_kg)
        # l'eau entraînée s'évapore dans l'air chaud comprimé
        sortie = mettre_a_l_equilibre(sortie, flux, self.machine,
                                      f"étage {self.numero} : ")
        return sortie, flux


class Compresseur(Composant):
    TYPE = "compresseur"
    MODELES = ("polytropique_dormoy", "isentropique",
               "polytropique_rendement", "isotherme")

    def __init__(self, nom: str, parametres: dict[str, Any],
                 provenance: dict[str, str] | None = None) -> None:
        super().__init__(nom, parametres, provenance)
        etages = self.param("etages")
        if not isinstance(etages, list) or not etages:
            raise ErreurComposant(f"{nom} : il faut au moins un étage")
        self.rendement_electrique = self.nombre("rendement_electrique")
        self.debit_volumique = self.nombre("debit_volumique_aspire", None)
        self.debit_massique_impose = self.nombre("debit_massique_aspire",
                                                 None)
        if self.debit_volumique is None and self.debit_massique_impose is None:
            raise ErreurComposant(
                f"{nom} : donner debit_volumique_aspire ou "
                f"debit_massique_aspire")
        self.modele_phys: ModelePolytropique | None = None
        self.rapports: tuple[float, ...] | None = None
        self.p_refoulement_pa = 0.0
        self.p_chaine_pa = 0.0
        if self.modele == "polytropique_dormoy":
            if len(etages) < 2:
                raise ErreurComposant(f"{nom} : il faut au moins deux étages")
            self._construire_dormoy(etages)
            self.p_refoulement_min_pa = self.modele_phys.p_refoulement_min_pa
        else:
            self.rendement_mecanique_cst = self.nombre("rendement_mecanique")
            self.p_refoulement_min_pa = self.nombre(
                "pression_refoulement_min", 0.0)
            cle = ("rendement_isentropique" if self.modele == "isentropique"
                   else "rendement_polytropique")
            self.rendement_machine = (self.nombre(cle)
                                      if self.modele != "isotherme" else 1.0)
            self.rendements_etages: list[float] = []
            for e in etages:
                if not isinstance(e, dict):
                    e = {}
                self.rendements_etages.append(
                    float(e[cle]) if e.get(cle) is not None
                    else self.rendement_machine)
            self.etages = [EtageCompresseur(self, i + 1,
                                            e if isinstance(e, dict) else {})
                           for i, e in enumerate(etages)]

    def _construire_dormoy(self, etages: list[dict[str, Any]]) -> None:
        indices = tuple(float(e["indice_polytropique"]) for e in etages)
        fixes = tuple(
            float(e["rapport_pression"]) for e in etages
            if e.get("rapport_pression") is not None
        )
        avant_dernier = etages[-2]
        if (avant_dernier.get("rapport_pression_min") is None
                or avant_dernier.get("rapport_pression_max") is None):
            raise ErreurComposant(
                f"{self.nom} : l'avant-dernier étage doit donner "
                f"rapport_pression_min et rapport_pression_max")
        self.modele_phys = ModelePolytropique(
            indices_polytropiques=indices,
            rapports_fixes=fixes,
            rapport_avant_dernier_min=float(
                avant_dernier["rapport_pression_min"]),
            rapport_avant_dernier_max=float(
                avant_dernier["rapport_pression_max"]),
            p_refoulement_min_pa=self.nombre("pression_refoulement_min"),
            p_refoulement_max_pa=self.nombre("pression_refoulement_max"),
            rendement_mecanique_min=self.nombre("rendement_mecanique_min"),
            rendement_mecanique_max=self.nombre("rendement_mecanique_max"),
            rendement_electrique=self.rendement_electrique,
            debit_volumique_aspire_m3_s=self.debit_volumique or 0.0,
            rendement_volumetrique=1.0,
            debit_massique_aspire_impose_kg_s=self.debit_massique_impose,
        )
        self.etages = [EtageCompresseur(self, i + 1)
                       for i in range(len(indices))]

    # --- accès ---------------------------------------------------------
    @property
    def nb_etages(self) -> int:
        return len(self.etages)

    def etage(self, numero: int) -> EtageCompresseur:
        if not 1 <= numero <= self.nb_etages:
            raise ErreurComposant(
                f"{self.nom} : pas d'étage {numero} (1 à {self.nb_etages})")
        return self.etages[numero - 1]

    def rendement_etage(self, numero: int) -> float:
        return self.rendements_etages[numero - 1]

    def nb_etages_libres_depuis(self, numero: int) -> int:
        """Étages sans consigne (ni rapport ni T_sortie) de ``numero`` à
        la fin, l'étage ``numero`` compris."""
        n = 0
        for e in self.etages[numero - 1:]:
            if (e.spec.get("rapport_pression") is None
                    and e.spec.get("T_sortie") is None):
                n += 1
        return max(n, 1)

    # --- un pas --------------------------------------------------------
    def preparer(self, p_reservoir_pa: float, p_aspiration_pa: float,
                 surpression_pa: float = 0.0) -> None:
        """Fixe la pression de refoulement du pas (et les rapports pour
        le modèle de Dormoy).

        p_ref = max(p_réservoir + surpression, p_min) ; les lois en
        pression sont évaluées au 0,1 bar près (clé de cache).
        """
        self.p_refoulement_pa = max(p_reservoir_pa + surpression_pa,
                                    self.p_refoulement_min_pa)
        self.p_chaine_pa = (
            round(self.p_refoulement_pa / PRECISION_CACHE_PA)
            * PRECISION_CACHE_PA
        )
        if self.modele_phys is not None:
            self.rapports = self.modele_phys.rapports_pression(
                p_aspiration_pa, self.p_chaine_pa)
            if self.p_refoulement_pa > self.modele_phys.p_refoulement_max_pa:
                self.avertir(
                    f"refoulement au-dessus de la plage calibrée "
                    f"({self.modele_phys.p_refoulement_max_pa / 1e5:.0f} "
                    f"bar) : lois en pression bloquées à la borne")
        elif self.p_chaine_pa <= p_aspiration_pa:
            self.p_chaine_pa = p_aspiration_pa * (1.0 + 1e-6)

    @property
    def cle_cache(self) -> int:
        return int(round(self.p_chaine_pa / PRECISION_CACHE_PA))

    def debit_aspire(self, ctx: Contexte) -> float:
        """Débit massique aspiré [kg/s] (formules.md#F06)."""
        if self.debit_massique_impose is not None:
            return self.debit_massique_impose
        rho = ctx.air.rho(ctx.p_amb_pa, ctx.T_aspiration_K)
        return rho * float(self.debit_volumique)

    def rendement_mecanique(self) -> float:
        if self.modele_phys is not None:
            return self.modele_phys.rendement_mecanique(self.p_chaine_pa)
        return self.rendement_mecanique_cst

    def puissance_electrique_depuis_travail(self, W_pol_w: float) -> float:
        """Puissance électrique [W] pour un travail polytropique total
        [W] fourni à l'air par tous les étages (formules.md#F08)."""
        if self.modele_phys is not None:
            eta = self.modele_phys.rendement_mecanique(self.p_refoulement_pa)
        else:
            eta = self.rendement_mecanique_cst
        return W_pol_w / (eta * self.rendement_electrique)

    def verifier_validite(self) -> list[str]:
        avis: list[str] = []
        if not 0.0 < self.rendement_electrique <= 1.0:
            avis.append("rendement électrique hors de ]0, 1]")
        if self.modele_phys is not None:
            m = self.modele_phys
            for i, n in enumerate(m.indices_polytropiques, 1):
                if not 1.0 <= n <= 1.6:
                    avis.append(
                        f"indice polytropique de l'étage {i} = {n} hors de "
                        f"[1 ; 1,6]")
            if m.p_refoulement_min_pa >= m.p_refoulement_max_pa:
                avis.append(
                    "pression_refoulement_min >= pression_refoulement_max")
        else:
            if not 0.0 < self.rendement_mecanique_cst <= 1.0:
                avis.append("rendement mécanique hors de ]0, 1]")
            for i, r in enumerate(self.rendements_etages, 1):
                if not 0.0 < r <= 1.0:
                    avis.append(f"rendement de l'étage {i} hors de ]0, 1]")
            if self.modele == "isotherme":
                avis.append(
                    "modèle « isotherme » : borne inférieure du travail "
                    "(Baniamerian, éq. 8), pas une machine réelle")
        return avis
