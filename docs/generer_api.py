# -*- coding: utf-8 -*-
"""Référence de l'API générée depuis les docstrings (phase 12), sans
dépendance : parcourt le paquet ``caes``, liste chaque module avec son
résumé, ses classes (et leurs méthodes publiques) et ses fonctions
publiques, avec la première ligne de leur docstring et leur signature.

    python docs/generer_api.py      # → docs/api.md
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import caes  # noqa: E402

SORTIE = RACINE / "docs" / "api.md"


def _resume(obj: object) -> str:
    doc = inspect.getdoc(obj) or ""
    premier = doc.strip().split("\n\n")[0].replace("\n", " ")
    return premier.strip()


def _signature(obj: object) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(...)"


def _membres_publics(classe: type) -> list[tuple[str, object]]:
    out = []
    for nom, membre in classe.__dict__.items():
        if nom.startswith("_") or not callable(membre) and not isinstance(
                membre, property):
            continue
        out.append((nom, membre))
    return out


def documenter_module(nom: str) -> list[str]:
    try:
        mod = importlib.import_module(nom)
    except Exception as err:  # noqa: BLE001 : un module cassé ne doit
        return [f"## `{nom}`\n", f"*Import impossible : {err}*\n"]
    L = [f"## `{nom}`\n"]
    resume = _resume(mod)
    if resume:
        L.append(resume + "\n")
    classes = [(n, o) for n, o in inspect.getmembers(mod, inspect.isclass)
               if o.__module__ == nom and not n.startswith("_")]
    fonctions = [(n, o) for n, o in inspect.getmembers(mod,
                                                        inspect.isfunction)
                 if o.__module__ == nom and not n.startswith("_")]
    for n, c in classes:
        L.append(f"### classe `{n}`\n")
        r = _resume(c)
        if r:
            L.append(r + "\n")
        membres = []
        for mn, m in _membres_publics(c):
            if isinstance(m, property):
                membres.append(f"- propriété `{mn}` : {_resume(m.fget)}"
                               if m.fget else f"- propriété `{mn}`")
            elif inspect.isfunction(m):
                membres.append(f"- `{mn}{_signature(m)}` : {_resume(m)}")
        if membres:
            L.extend(membres)
            L.append("")
    for n, f in fonctions:
        L.append(f"### `{n}{_signature(f)}`\n")
        r = _resume(f)
        if r:
            L.append(r + "\n")
    return L


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    noms = ["caes"]
    for info in pkgutil.walk_packages(caes.__path__, "caes."):
        noms.append(info.name)
    L = ["# Référence de l'API du paquet `caes`\n",
         "*Générée par `python docs/generer_api.py` depuis les docstrings "
         "(premier paragraphe de chaque objet). Les modules des phases 1 "
         "à 5 (`systeme`, `integre`, `compresseur`, `turbine`, "
         "`reservoir`, `lit_gravier`, `exergie`) restent l'implémentation "
         "physique ; les composants de la phase 6 les enveloppent. Le "
         "point d'entrée est `python -m caes` (`caes/__main__.py`). Les "
         "équations sont dans `formules.md` (le code y renvoie par "
         "`#Fnn`).*\n",
         "## Modules\n"]
    L += [f"- `{n}`" for n in noms]
    L.append("")
    for n in noms:
        L += documenter_module(n)
    SORTIE.write_text("\n".join(L), encoding="utf-8")
    print(f"écrit : {SORTIE} ({len(noms)} modules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
