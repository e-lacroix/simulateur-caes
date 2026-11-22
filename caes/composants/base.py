"""Interface commune de tous les composants (phase 6).

Un composant est une brique interchangeable : il reçoit l'air dans un
état (pression, température, débit), le transforme, et déclare les flux
d'énergie du pas de temps (travail, chaleur ajoutée avec sa source,
chaleur retirée avec sa destination, débit perdu). Un scénario YAML
assemble des composants par leur nom et le modèle choisi ; le code qui
simule (:mod:`caes.assembleur`) ne connaît que cette interface.

Règles communes :

* tout paramètre physique vient du scénario (registre ou valeur sourcée)
  et garde sa provenance (``self.provenance``) ;
* la seule source de conditions extérieures est l'ambiance du contexte ;
* toute chaleur ajoutée à l'air porte une étiquette de source
  (``externe`` ou le nom d'un stockage) ;
* ``verifier_validite()`` et ``avertir()`` signalent les sorties du
  domaine de validité sans arrêter la simulation.

Voir formules.md#F33 pour les règles d'assemblage.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field, replace
from typing import Any, ClassVar

from caes.ambiance import Ambiance
from caes.proprietes import Air


class ErreurComposant(ValueError):
    """Paramètre manquant, modèle inconnu ou valeur hors limites."""


class HorsDomaine(ErreurComposant):
    """L'état de l'air sort du domaine où le modèle a un sens (par
    exemple une détente jusqu'à la liquéfaction) : la simulation
    s'arrête proprement et le signale."""


@dataclass(frozen=True)
class EtatAir:
    """État d'un écoulement d'air à un point de la chaîne.

    ``w_vapeur_kg_kg`` et ``w_liquide_kg_kg`` (phase 9) : eau par kg
    d'air, en vapeur et entraînée en liquide ou en givre (F42, F43).
    """

    p_abs_pa: float
    T_K: float
    m_dot_kg_s: float
    w_vapeur_kg_kg: float = 0.0
    w_liquide_kg_kg: float = 0.0

    @property
    def w_total_kg_kg(self) -> float:
        return self.w_vapeur_kg_kg + self.w_liquide_kg_kg

    def remplacer(self, **changements: float) -> EtatAir:
        return replace(self, **changements)

    def __str__(self) -> str:
        return (
            f"{self.p_abs_pa / 1e5:.2f} bar, {self.T_K - 273.15:.1f} °C, "
            f"{self.m_dot_kg_s:.4f} kg/s"
        )


@dataclass
class Flux:
    """Flux d'énergie d'un composant pendant un pas, en puissances [W].

    Toutes les valeurs sont positives dans le sens indiqué par leur nom.
    ``resultat`` garde l'objet détaillé du modèle physique (par exemple
    :class:`caes.compresseur.ResultatEtage`) pour les séries et le bilan
    d'exergie.
    """

    W_el_consomme_w: float = 0.0
    W_el_produit_w: float = 0.0
    W_pol_w: float = 0.0
    """Travail polytropique échangé avec l'air (compression > 0)."""
    Q_ajoute_w: float = 0.0
    source: str = ""
    """Étiquette de la chaleur ajoutée : ``externe`` ou nom du stockage."""
    Q_retire_w: float = 0.0
    destination: str = ""
    """Où va la chaleur retirée : ``ambiant`` ou nom du stockage."""
    m_dot_perdu_kg_s: float = 0.0
    dp_pa: float = 0.0
    eau_condensee_kg_s: float = 0.0
    """Eau passée de la vapeur au liquide (< 0 : évaporée) (F43)."""
    eau_separee_kg_s: float = 0.0
    """Eau retirée de l'air (séparateur, purge du sécheur)."""
    Q_latente_w: float = 0.0
    """Chaleur de condensation libérée (non comptée dans le bilan de
    l'air sec)."""
    givre: bool = False
    T_rosee_K: float = float("-inf")
    resultat: Any = None


@dataclass
class Contexte:
    """Ce que chaque composant reçoit à chaque pas, en plus de l'air."""

    air: Air
    ambiance: Ambiance
    t_s: float
    dt_s: float
    p_refoulement_pa: float = 0.0
    """Pression de refoulement de la chaîne de compression en cours."""

    @property
    def T_amb_K(self) -> float:
        return self.ambiance.T_amb_a(self.t_s)

    @property
    def p_amb_pa(self) -> float:
        return self.ambiance.p_amb_pa

    @property
    def T_aspiration_K(self) -> float:
        return self.ambiance.T_aspiration_a(self.t_s)


@dataclass
class Avertissement:
    composant: str
    message: str
    occurrences: int = 1

    def __str__(self) -> str:
        n = f" (×{self.occurrences})" if self.occurrences > 1 else ""
        return f"[{self.composant}] {self.message}{n}"


class Composant(ABC):
    """Classe de base : nom, modèle, paramètres, provenance, avis.

    Les sous-classes déclarent ``TYPE`` (le mot-clé ``type`` du YAML),
    ``MODELES`` (valeurs admises pour ``modele``) et ``A_UN_ETAT`` (vrai
    si le composant garde une mémoire d'un pas à l'autre : réservoir,
    cuve de gravier).
    """

    TYPE: ClassVar[str] = ""
    MODELES: ClassVar[tuple[str, ...]] = ()
    A_UN_ETAT: ClassVar[bool] = False

    def __init__(
        self,
        nom: str,
        parametres: dict[str, Any],
        provenance: dict[str, str] | None = None,
    ) -> None:
        self.nom = nom
        self.parametres = dict(parametres)
        self.provenance = dict(provenance or {})
        self.modele = str(self.parametres.get("modele", self.MODELES[0]))
        if self.modele not in self.MODELES:
            raise ErreurComposant(
                f"{nom} : modèle « {self.modele} » inconnu pour le type "
                f"« {self.TYPE} » ; choix : {list(self.MODELES)}"
            )
        self._avertissements: dict[str, Avertissement] = {}
        self.a_un_etat = type(self).A_UN_ETAT

    # --- paramètres ----------------------------------------------------
    _ABSENT = object()

    def param(self, cle: str, defaut: Any = _ABSENT) -> Any:
        """Valeur SI d'un paramètre ; erreur claire s'il manque."""
        val = self.parametres.get(cle)
        if val is None:
            if defaut is Composant._ABSENT:
                raise ErreurComposant(
                    f"{self.nom} ({self.TYPE}, {self.modele}) : paramètre "
                    f"« {cle} » manquant"
                )
            return defaut
        return val

    def nombre(self, cle: str, defaut: Any = _ABSENT) -> float:
        val = self.param(cle, defaut)
        return val if val is None else float(val)

    # --- avertissements ------------------------------------------------
    def avertir(self, message: str) -> None:
        """Enregistre un avertissement (dédoublonné, compté)."""
        if message in self._avertissements:
            self._avertissements[message].occurrences += 1
        else:
            self._avertissements[message] = Avertissement(self.nom, message)

    @property
    def avertissements(self) -> list[Avertissement]:
        return list(self._avertissements.values())

    def effacer_avertissements(self) -> None:
        self._avertissements.clear()

    def verifier_validite(self) -> list[str]:
        """Vérifications statiques des paramètres (avant simulation).

        Les vérifications dynamiques (pendant les pas) passent par
        :meth:`avertir`. Retourne la liste des messages.
        """
        return []

    # --- état ----------------------------------------------------------
    def reinitialiser(self) -> None:
        """Remet l'état interne à zéro (composants avec mémoire)."""

    # --- présentation --------------------------------------------------
    def description(self) -> str:
        return f"{self.nom} : {self.TYPE} ({self.modele})"

    def parametres_affiches(self) -> dict[str, Any]:
        """Paramètres à montrer dans les rapports (SI)."""
        return {
            k: v for k, v in self.parametres.items()
            if k not in ("type", "modele") and not isinstance(v, (dict, list))
        }

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.nom} ({self.modele})>"


@dataclass
class ElementChaine:
    """Un maillon d'une chaîne : un composant, ou un étage d'une machine."""

    composant: Composant
    etage: int | None = None
    """Numéro d'étage (à partir de 1) pour un compresseur ou une turbine."""

    @property
    def nom(self) -> str:
        if self.etage is None:
            return self.composant.nom
        return f"{self.composant.nom}.{self.etage}"

    @property
    def type_(self) -> str:
        return self.composant.TYPE


@dataclass
class Segment:
    """Dans une chaîne, ce qui suit un étage de machine jusqu'au suivant."""

    etage: int
    elements: list[ElementChaine] = field(default_factory=list)
