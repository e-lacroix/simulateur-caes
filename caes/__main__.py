"""Point d'entrée unique du simulateur (phase 6).

    python -m caes simuler scenarios/D.yaml --sortie resultats/D
    python -m caes simuler scenarios/D.yaml --modifier ambiance.T_amb=-20degC
    python -m caes verifier scenarios/D.yaml
    python -m caes analyser scenarios/analyse/D.yaml --sortie rapports/x

``simuler`` assemble l'installation, vérifie les domaines de validité,
simule (charge, décharge ou cycles selon ``simulation.mode``) et écrit
le dossier de résultats (CSV, Markdown, graphiques, provenance).
``verifier`` s'arrête après l'assemblage et affiche les composants, les
chaînes et les avertissements statiques.

``analyser`` (phase 10) lance la sensibilité, la propagation des
incertitudes et le front de Pareto décrits par un fichier d'analyse
(``caes/analyse/rapport.py``, options ``--procs``, ``--etapes``,
``--rapide``).

``--modifier chemin=valeur[unite]`` remplace une feuille du scénario
avant l'assemblage (unités de la table ``UNITES`` du registre), par
exemple ``composants.cuve_1.volume=0.5m3``.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

from caes.assembleur import ErreurAssemblage, charger_installation
from caes.composants.base import ErreurComposant
from caes.registre import ErreurRegistre


def _parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m caes",
        description="Simulateur CAES : banc d'essai numérique assemblé "
                    "par fichier YAML.",
    )
    sous = p.add_subparsers(dest="commande", required=True)
    sous.add_parser("analyser", help="sensibilité, incertitudes et front "
                    "de Pareto d'un fichier d'analyse (phase 10) ; "
                    "options : python -m caes analyser --help")
    for nom, aide in (("simuler", "assembler, simuler et écrire les "
                                  "résultats"),
                      ("verifier", "assembler et vérifier sans simuler")):
        s = sous.add_parser(nom, help=aide)
        s.add_argument("scenario", type=Path, help="fichier YAML")
        s.add_argument("--modifier", "-m", action="append", default=[],
                       metavar="CHEMIN=VALEUR[UNITE]",
                       help="remplace une valeur du scénario "
                            "(ex. ambiance.T_amb=-20degC)")
        if nom == "simuler":
            s.add_argument("--sortie", "-s", type=Path, default=None,
                           help="dossier de résultats (défaut : "
                                "resultats/<nom du scénario>/)")
            s.add_argument("--sans-graphiques", action="store_true",
                           help="n'écrit pas les PNG (plus rapide)")
    return p


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "analyser":
        from caes.analyse.rapport import main as analyser

        return analyser(arguments[1:])
    args = _parseur().parse_args(arguments)
    try:
        inst = charger_installation(args.scenario,
                                    modifications=args.modifier)
    except (ErreurAssemblage, ErreurComposant, ErreurRegistre,
            ValueError, FileNotFoundError, yaml.YAMLError) as err:
        print(f"Erreur : {err}", file=sys.stderr)
        return 2
    avis = inst.verifier()
    print(f"{inst.nom} : {inst.description.strip()}")
    print(f"ambiance : {inst.ambiance.description()}")
    for c in inst.composants.values():
        print(f"  - {c.description()}")
    if inst.charge:
        print("charge   : " + " → ".join(e.nom for e in inst.charge.elements))
    if inst.decharge:
        print("décharge : "
              + " → ".join(e.nom for e in inst.decharge.elements))
    print(f"mode : {inst.mode}")
    for a in avis:
        print(f"  avertissement {a}")
    if args.commande == "verifier":
        print("assemblage valide")
        return 0
    from caes.sortie import ecrire_resultats

    t0 = time.perf_counter()
    res = inst.simuler()
    duree = time.perf_counter() - t0
    print(f"simulé en {duree:.1f} s : {res.resume()}")
    sortie = args.sortie or Path("resultats") / inst.nom
    commande = "python -m caes " + " ".join(argv or sys.argv[1:])
    ecrire_resultats(res, sortie, graphiques=not args.sans_graphiques,
                     commande=commande)
    for a in res.avertissements:
        print(f"  avertissement {a}")
    print(f"résultats écrits dans {sortie}/ (resume.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
