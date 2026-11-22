"""Chargeur du registre scientifique.

Le registre est formé de deux fichiers CSV dans ``data/registre/`` :

* ``references.csv`` : les sources (articles, données supplémentaires) ;
* ``parametres.csv`` : chaque valeur chiffrée, avec sa source, son
  unité, ses conditions et son niveau de preuve.

Règle du projet : aucun chiffre en dur dans le code. Tout paramètre
physique est lu ici, et le code reçoit un :class:`Parametre` qui porte
sa source avec lui.

Les valeurs sont conservées dans l'unité de la source (bar, °C, kWh)
pour rester vérifiables à l'œil. La conversion en unités SI se fait à
la demande avec :attr:`Parametre.valeur_si`.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

NIVEAUX_PREUVE: frozenset[str] = frozenset(
    {
        "mesure",
        "fabricant",
        "calibration",
        "simulation_publiee",
        "calcul_personnel",
        "hypothese",
    }
)
"""Niveaux de preuve admis, du plus solide au plus fragile."""

# unité source -> (unité SI, facteur multiplicatif, décalage additif)
# valeur_si = valeur * facteur + decalage
UNITES: dict[str, tuple[str, float, float]] = {
    "-": ("-", 1.0, 0.0),
    "%": ("-", 0.01, 0.0),
    "texte": ("texte", 1.0, 0.0),
    "Pa": ("Pa", 1.0, 0.0),
    "MPa": ("Pa", 1e6, 0.0),
    "bar": ("Pa", 1.0e5, 0.0),
    "K": ("K", 1.0, 0.0),
    "degC": ("K", 1.0, 273.15),
    "kg": ("kg", 1.0, 0.0),
    "t": ("kg", 1.0e3, 0.0),
    "kg/s": ("kg/s", 1.0, 0.0),
    "kg/m3": ("kg/m3", 1.0, 0.0),
    "m": ("m", 1.0, 0.0),
    "m2": ("m2", 1.0, 0.0),
    "m3": ("m3", 1.0, 0.0),
    "L": ("m3", 1.0e-3, 0.0),
    "m3/h": ("m3/s", 1.0 / 3600.0, 0.0),
    "m3/s": ("m3/s", 1.0, 0.0),
    "m3/tr": ("m3/tr", 1.0, 0.0),
    "rpm": ("tr/s", 1.0 / 60.0, 0.0),
    "s": ("s", 1.0, 0.0),
    "min": ("s", 60.0, 0.0),
    "h": ("s", 3600.0, 0.0),
    "j": ("s", 86400.0, 0.0),
    "W": ("W", 1.0, 0.0),
    "kW": ("W", 1.0e3, 0.0),
    "MW": ("W", 1.0e6, 0.0),
    "J": ("J", 1.0, 0.0),
    "kWh": ("J", 3.6e6, 0.0),
    "kJ/kg": ("J/kg", 1.0e3, 0.0),
    "MJ/kg": ("J/kg", 1.0e6, 0.0),
    "L/h": ("m3/s", 1.0e-3 / 3600.0, 0.0),
    "$/kWh": ("$/J", 1.0 / 3.6e6, 0.0),
    "J/kg": ("J/kg", 1.0, 0.0),
    "W/m2K": ("W/m2K", 1.0, 0.0),
    "W/mK": ("W/mK", 1.0, 0.0),
    "J/kgK": ("J/kgK", 1.0, 0.0),
    "J/K": ("J/K", 1.0, 0.0),
    "Pa.s": ("Pa.s", 1.0, 0.0),
    "MWh": ("J", 3.6e9, 0.0),
}
"""Unités connues du registre et leur conversion vers le SI."""

DOSSIER_REGISTRE_DEFAUT = (
    Path(__file__).resolve().parent.parent / "data" / "registre"
)


class ErreurRegistre(ValueError):
    """Le registre est incohérent (identifiant, unité ou source)."""


@dataclass(frozen=True)
class Reference:
    """Une source du registre (ligne de ``references.csv``)."""

    id: str
    auteurs: str
    annee: int
    titre: str
    revue: str
    doi_ou_url: str
    type: str
    acces: str
    fichier_local: str
    notes: str

    def citation(self) -> str:
        """Citation courte, par exemple « Dormoy E. et al. (2024), ... »."""
        return f"{self.auteurs} ({self.annee}), {self.revue}"


@dataclass(frozen=True)
class Parametre:
    """Une valeur du registre, avec sa source et son unité.

    ``valeur`` vaut ``None`` quand la source ne donne qu'une plage
    (``valeur_min`` et ``valeur_max``). Dans ce cas, le code appelant
    doit choisir une loi et la déclarer comme hypothèse.
    """

    id: str
    nom: str
    valeur: float | str | None
    valeur_min: float | None
    valeur_max: float | None
    unite: str
    source_id: str
    localisation: str
    conditions: str
    niveau_preuve: str
    notes: str

    @property
    def unite_si(self) -> str:
        """Unité SI correspondante."""
        return UNITES[self.unite][0]

    def _vers_si(self, x: float | str | None) -> float | None:
        if x is None or isinstance(x, str):
            return None
        facteur, decalage = UNITES[self.unite][1:]
        return x * facteur + decalage

    @property
    def valeur_si(self) -> float:
        """Valeur convertie en SI. Erreur si seule une plage existe."""
        v = self._vers_si(self.valeur)
        if v is None:
            raise ErreurRegistre(
                f"{self.id} : pas de valeur unique (plage "
                f"{self.valeur_min}-{self.valeur_max} {self.unite})"
            )
        return v

    @property
    def valeur_min_si(self) -> float | None:
        """Borne basse convertie en SI, ou ``None``."""
        return self._vers_si(self.valeur_min)

    @property
    def valeur_max_si(self) -> float | None:
        """Borne haute convertie en SI, ou ``None``."""
        return self._vers_si(self.valeur_max)

    @property
    def est_plage(self) -> bool:
        """Vrai si la source ne donne qu'une plage."""
        return self.valeur is None and self.valeur_min is not None

    def __str__(self) -> str:
        if self.est_plage:
            v = f"{self.valeur_min}-{self.valeur_max}"
        else:
            v = str(self.valeur)
        return (
            f"{self.id} = {v} {self.unite} "
            f"[{self.niveau_preuve}, {self.source_id}, {self.localisation}]"
        )


def _nombre(texte: str) -> float | str | None:
    texte = texte.strip()
    if texte == "":
        return None
    try:
        return float(texte)
    except ValueError:
        return texte


class Registre:
    """Registre scientifique chargé en mémoire.

    >>> reg = Registre.charger()
    >>> reg["reservoir.volume_total"].valeur_si
    5.86
    """

    def __init__(
        self,
        references: dict[str, Reference],
        parametres: dict[str, Parametre],
    ) -> None:
        self.references = references
        self.parametres = parametres
        self.verifier()

    @classmethod
    def charger(cls, dossier: Path | str | None = None) -> Registre:
        """Lit ``references.csv`` et ``parametres.csv`` dans ``dossier``."""
        dossier = Path(dossier) if dossier else DOSSIER_REGISTRE_DEFAUT
        references: dict[str, Reference] = {}
        chemin_refs = dossier / "references.csv"
        with open(chemin_refs, encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                ref = Reference(
                    id=ligne["id"],
                    auteurs=ligne["auteurs"],
                    annee=int(ligne["annee"]),
                    titre=ligne["titre"],
                    revue=ligne["revue"],
                    doi_ou_url=ligne["doi_ou_url"],
                    type=ligne["type"],
                    acces=ligne["acces"],
                    fichier_local=ligne["fichier_local"],
                    notes=ligne["notes"],
                )
                if ref.id in references:
                    raise ErreurRegistre(f"référence en double : {ref.id}")
                references[ref.id] = ref

        parametres: dict[str, Parametre] = {}
        chemin_pars = dossier / "parametres.csv"
        with open(chemin_pars, encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f):
                vmin = _nombre(ligne["valeur_min"])
                vmax = _nombre(ligne["valeur_max"])
                par = Parametre(
                    id=ligne["id"],
                    nom=ligne["nom"],
                    valeur=_nombre(ligne["valeur"]),
                    valeur_min=vmin if isinstance(vmin, float) else None,
                    valeur_max=vmax if isinstance(vmax, float) else None,
                    unite=ligne["unite"].strip(),
                    source_id=ligne["source_id"].strip(),
                    localisation=ligne["localisation"],
                    conditions=ligne["conditions"],
                    niveau_preuve=ligne["niveau_preuve"].strip(),
                    notes=ligne["notes"],
                )
                if par.id in parametres:
                    raise ErreurRegistre(f"paramètre en double : {par.id}")
                parametres[par.id] = par
        return cls(references, parametres)

    def verifier(self) -> None:
        """Lève :class:`ErreurRegistre` si le registre est incohérent."""
        for par in self.parametres.values():
            if par.unite not in UNITES:
                raise ErreurRegistre(
                    f"{par.id} : unité inconnue « {par.unite} »"
                )
            if par.source_id not in self.references:
                raise ErreurRegistre(
                    f"{par.id} : source inconnue « {par.source_id} »"
                )
            if par.niveau_preuve not in NIVEAUX_PREUVE:
                raise ErreurRegistre(
                    f"{par.id} : niveau de preuve inconnu "
                    f"« {par.niveau_preuve} »"
                )
            if par.valeur is None and par.valeur_min is None:
                raise ErreurRegistre(f"{par.id} : ni valeur ni plage")
            if (par.valeur_min is None) != (par.valeur_max is None):
                raise ErreurRegistre(f"{par.id} : plage incomplète")
            if par.unite != "texte" and isinstance(par.valeur, str):
                raise ErreurRegistre(f"{par.id} : valeur non numérique")

    def __getitem__(self, id_: str) -> Parametre:
        try:
            return self.parametres[id_]
        except KeyError:
            raise ErreurRegistre(
                f"paramètre absent du registre : {id_}"
            ) from None

    def __contains__(self, id_: str) -> bool:
        return id_ in self.parametres

    def __len__(self) -> int:
        return len(self.parametres)

    def si(self, id_: str) -> float:
        """Raccourci : valeur SI du paramètre ``id_``."""
        return self[id_].valeur_si

    def source(self, id_: str) -> Reference:
        """La référence d'où vient le paramètre ``id_``."""
        return self.references[self[id_].source_id]

    def par_niveau(self, niveau: str) -> list[Parametre]:
        """Tous les paramètres d'un niveau de preuve donné."""
        return [
            p for p in self.parametres.values() if p.niveau_preuve == niveau
        ]

    def par_prefixe(self, prefixe: str) -> list[Parametre]:
        """Tous les paramètres dont l'identifiant commence par ``prefixe``."""
        return [
            p for p in self.parametres.values() if p.id.startswith(prefixe)
        ]
