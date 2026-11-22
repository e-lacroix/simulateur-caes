# -*- coding: utf-8 -*-
"""Régénère tout le dépôt en une commande (phase 12) : registre, scénarios
dérivés, rapports de validation, tableau de bord, rapports de phase,
scénarios d'exemple, référence de l'API ; vérifie que les chiffres cités
dans les pages d'explication correspondent aux rapports ; lance les tests.

    python generer_tout.py           # tout (≈ 3 h, étapes longues comprises)
    python generer_tout.py --sans-longs         # sans les étapes > 10 min
    python generer_tout.py --etapes registre,scenarios,verifier
    python generer_tout.py --sauf tests
    python generer_tout.py --liste              # les étapes et leurs durées

Chaque étape est un script du dépôt lancé dans un sous-processus avec
l'interpréteur courant ; la sortie va dans ``rapports/generer_tout.log``.
L'exécution s'arrête à la première erreur (``--continuer`` pour aller au
bout quand même) et imprime un tableau des durées.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent
JOURNAL = RACINE / "rapports" / "generer_tout.log"
CHIFFRES = RACINE / "docs" / "chiffres_cles.yaml"


@dataclass(frozen=True)
class Etape:
    nom: str
    commandes: tuple[tuple[str, ...], ...]
    duree: str
    longue: bool = False
    description: str = ""


def _py(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


ETAPES: tuple[Etape, ...] = (
    Etape("registre", (_py("-I", "data/registre/generer_registre_phase0.py"),),
          "5 s", description="registre scientifique (CSV)"),
    Etape("scenarios", (_py("scenarios/variantes/generer_variantes.py"),
                        _py("scenarios/humidite/generer_humidite.py"),
                        _py("scenarios/exemples/generer_exemples.py")),
          "10 s", description="scénarios dérivés et profils"),
    Etape("validation", (_py("validation/dormoy_charge.py"),
                         _py("validation/dormoy_decharge.py"),
                         _py("validation/lit_gravier.py")),
          "55 min", longue=True,
          description="rapports de validation des phases 1, 2, 4"),
    Etape("non_regression", (_py("validation/non_regression_phase6.py"),),
          "4 min", description="phases 1 à 5 contre le format composants"),
    Etape("tableau_de_bord", (_py("validation/tableau_de_bord.py"),),
          "3 min", description="tableau de bord de validation (phase 8)"),
    Etape("tableau_1000", (_py("rapports/tableau_1000_unites.py"),),
          "2 min", description="exergie et 1000 unités (phase 3)"),
    Etape("phase5", (_py("rapports/phase5_architectures.py"),),
          "15 min", longue=True, description="architectures A à E (phase 5)"),
    Etape("phase7", (_py("rapports/phase7_variantes.py"),),
          "3 min", description="variantes de la bibliothèque (phase 7)"),
    Etape("phase9", (_py("rapports/phase9_humidite.py"),),
          "2 min", description="humidité et sécheur (phase 9)"),
    Etape("analyse", (_py("-m", "caes", "analyser", "scenarios/analyse/D.yaml",
                          "--sortie", "rapports/phase10"),),
          "50 min", longue=True,
          description="sensibilité, incertitudes, Pareto (phase 10)"),
    Etape("exemples", (_py("rapports/scenarios_dormoy_gravier.py"),
                       _py("rapports/scenarios_transport.py"),
                       _py("rapports/scenarios_centre_urgence.py"),
                       _py("rapports/scenarios_grande_echelle.py")),
          "8 min", description="scénarios d'exemple (phase 11)"),
    Etape("api", (_py("docs/generer_api.py"),), "5 s",
          description="référence de l'API depuis les docstrings"),
    Etape("verifier", (), "1 s",
          description="chiffres des pages d'explication contre les "
                      "rapports (docs/chiffres_cles.yaml)"),
    Etape("tests", (_py("-m", "pytest", "-q", "-p", "no:cacheprovider"),),
          "6 min", description="suite de tests"),
)


# --- vérification des chiffres cités --------------------------------------
@dataclass
class Verification:
    description: str
    page: str
    rapport: str
    attendu: str
    trouve: bool
    erreur: str = ""


def _formater(valeur: float, fmt: str, facteur: float,
              decimale: str) -> str:
    texte = fmt.format(valeur * facteur)
    return texte.replace(".", decimale) if decimale != "." else texte


def verifier_chiffres(chemin: Path = CHIFFRES,
                      racine: Path = RACINE) -> list[Verification]:
    """Pour chaque entrée de ``docs/chiffres_cles.yaml`` : lit la valeur
    dans le rapport (expression régulière, groupe 1), la met en forme
    (``format``, ``facteur``, ``decimale``) et vérifie que le texte
    obtenu figure dans la page d'explication."""
    entrees = yaml.safe_load(chemin.read_text(encoding="utf-8")) or []
    out: list[Verification] = []
    for e in entrees:
        page = racine / e["page"]
        rapport = racine / e["rapport"]
        desc = str(e.get("description", e["motif"]))
        try:
            texte_rapport = rapport.read_text(encoding="utf-8")
            m = re.search(e["motif"], texte_rapport, re.S)
            if m is None:
                out.append(Verification(desc, e["page"], e["rapport"], "",
                                        False, "motif introuvable dans le "
                                        "rapport"))
                continue
            attendu = _formater(float(m.group(1)), e.get("format", "{}"),
                                float(e.get("facteur", 1.0)),
                                str(e.get("decimale", ",")))
            texte_page = page.read_text(encoding="utf-8")
            out.append(Verification(desc, e["page"], e["rapport"], attendu,
                                    attendu in texte_page,
                                    "" if attendu in texte_page else
                                    f"« {attendu} » absent de la page"))
        except (OSError, ValueError, KeyError) as err:
            out.append(Verification(desc, e.get("page", "?"),
                                    e.get("rapport", "?"), "", False,
                                    f"{type(err).__name__} : {err}"))
    return out


# --- exécution ------------------------------------------------------------
@dataclass
class Resultat:
    etape: str
    duree_s: float
    ok: bool
    message: str = ""
    details: list[str] = field(default_factory=list)


def _lancer(cmd: tuple[str, ...], journal) -> tuple[bool, str]:
    journal.write(f"\n$ {' '.join(cmd)}\n")
    journal.flush()
    proc = subprocess.run(cmd, cwd=RACINE, stdout=journal,
                          stderr=subprocess.STDOUT,
                          env={**__import__("os").environ,
                               "PYTHONIOENCODING": "utf-8"})
    return proc.returncode == 0, f"code de retour {proc.returncode}"


def executer(noms: list[str], continuer: bool = False) -> list[Resultat]:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    resultats: list[Resultat] = []
    par_nom = {e.nom: e for e in ETAPES}
    with open(JOURNAL, "a", encoding="utf-8") as journal:
        journal.write(f"\n===== generer_tout {time.strftime('%Y-%m-%d %H:%M')}"
                      f" : {', '.join(noms)} =====\n")
        for nom in noms:
            e = par_nom[nom]
            t0 = time.perf_counter()
            print(f"[{nom}] {e.description} (≈ {e.duree})", flush=True)
            if nom == "verifier":
                verifs = verifier_chiffres()
                mauvais = [v for v in verifs if not v.trouve]
                r = Resultat(nom, time.perf_counter() - t0, not mauvais,
                             f"{len(verifs) - len(mauvais)}/{len(verifs)} "
                             f"chiffres retrouvés",
                             [f"{v.description} ({v.page}) : {v.erreur}"
                              for v in mauvais])
                for v in verifs:
                    journal.write(f"  {'ok ' if v.trouve else 'NON'} "
                                  f"{v.description} → {v.attendu or v.erreur}"
                                  f"\n")
            else:
                ok, msg = True, ""
                for cmd in e.commandes:
                    ok, msg = _lancer(cmd, journal)
                    if not ok:
                        break
                r = Resultat(nom, time.perf_counter() - t0, ok, msg)
            resultats.append(r)
            etat = "ok" if r.ok else "ÉCHEC"
            print(f"  {etat} en {r.duree_s:.0f} s {r.message}", flush=True)
            for d in r.details:
                print(f"    - {d}", flush=True)
            if not r.ok and not continuer:
                break
    return resultats


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(
        description="Régénère le dépôt (registre, scénarios, rapports, "
                    "API), vérifie les chiffres cités, lance les tests.")
    p.add_argument("--etapes", default=None,
                   help="étapes à lancer, séparées par des virgules")
    p.add_argument("--sauf", default="", help="étapes à sauter")
    p.add_argument("--sans-longs", action="store_true",
                   help="saute les étapes de plus de dix minutes")
    p.add_argument("--continuer", action="store_true",
                   help="ne s'arrête pas à la première erreur")
    p.add_argument("--liste", action="store_true", help="liste les étapes")
    args = p.parse_args(argv)
    if args.liste:
        for e in ETAPES:
            longue = "(longue) " if e.longue else ""
            print(f"{e.nom:16s} ≈ {e.duree:7s} {longue}{e.description}")
        return 0
    noms = ([n.strip() for n in args.etapes.split(",") if n.strip()]
            if args.etapes else [e.nom for e in ETAPES])
    sauf = {n.strip() for n in args.sauf.split(",") if n.strip()}
    connus = {e.nom for e in ETAPES}
    inconnus = [n for n in noms + sorted(sauf) if n not in connus]
    if inconnus:
        print(f"étapes inconnues : {inconnus} ; connues : {sorted(connus)}",
              file=sys.stderr)
        return 2
    par_nom = {e.nom: e for e in ETAPES}
    noms = [n for n in noms if n not in sauf
            and not (args.sans_longs and par_nom[n].longue)]
    t0 = time.perf_counter()
    res = executer(noms, args.continuer)
    print("\n| Étape | Durée | État |\n|---|---|---|")
    for r in res:
        print(f"| {r.etape} | {r.duree_s / 60:.1f} min | "
              f"{'ok' if r.ok else 'ÉCHEC : ' + r.message} |")
    print(f"\nTotal : {(time.perf_counter() - t0) / 60:.1f} min ; journal : "
          f"{JOURNAL}")
    return 0 if all(r.ok for r in res) and len(res) == len(noms) else 1


if __name__ == "__main__":
    sys.exit(main())
