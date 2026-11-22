"""Tests de la phase 12 : référence de l'API, vérification des chiffres
cités, liste des étapes de generer_tout, fichiers de publication."""

import importlib.util
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent


def _charger_module(chemin: Path, nom: str):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nom] = mod
    spec.loader.exec_module(mod)
    return mod


def test_reference_api_se_genere(tmp_path: Path) -> None:
    mod = _charger_module(RACINE / "docs" / "generer_api.py", "generer_api")
    lignes = mod.documenter_module("caes.flotte")
    texte = "\n".join(lignes)
    assert "classe `CourbeModule`" in texte
    assert "`repartir(" in texte
    assert "Répartition d'une flotte" in texte
    lignes = mod.documenter_module("caes.analyse.pareto")
    assert "`nsga2(" in "\n".join(lignes)


def test_verification_des_chiffres_cles(tmp_path: Path) -> None:
    """Le mécanisme : une page et un rapport factices ; puis les vraies
    entrées sur les rapports du dépôt (quand ils sont présents)."""
    gt = _charger_module(RACINE / "generer_tout.py", "generer_tout")
    (tmp_path / "rapport.md").write_text(
        "| **D** | x | 17.13 % |\n", encoding="utf-8")
    (tmp_path / "page.md").write_text("D rend 17,1 % ; 0,17.",
                                      encoding="utf-8")
    entrees = [
        {"description": "ok", "page": "page.md", "rapport": "rapport.md",
         "motif": r"\| \*\*D\*\* \| x \| ([0-9.]+) %", "format": "{:.1f} %"},
        {"description": "facteur", "page": "page.md",
         "rapport": "rapport.md", "motif": r"([0-9.]+) %",
         "format": "{:.2f}", "facteur": 0.01},
        {"description": "absent", "page": "page.md",
         "rapport": "rapport.md", "motif": r"([0-9.]+) %",
         "format": "{:.0f} %"},
        {"description": "motif", "page": "page.md",
         "rapport": "rapport.md", "motif": r"zzz ([0-9]+)"},
    ]
    chemin = tmp_path / "chiffres.yaml"
    chemin.write_text(yaml.safe_dump(entrees, allow_unicode=True),
                      encoding="utf-8")
    v = gt.verifier_chiffres(chemin, tmp_path)
    assert [x.trouve for x in v] == [True, True, False, False]
    assert v[0].attendu == "17,1 %" and v[1].attendu == "0,17"
    assert "absent" in v[2].erreur and "introuvable" in v[3].erreur
    # les vraies entrées, si les rapports sont là
    reel = yaml.safe_load((RACINE / "docs" / "chiffres_cles.yaml")
                          .read_text(encoding="utf-8"))
    assert len(reel) >= 8
    if all((RACINE / e["rapport"]).exists() for e in reel):
        verifs = gt.verifier_chiffres()
        rates = [x for x in verifs if not x.trouve]
        assert not rates, [f"{x.description} : {x.erreur}" for x in rates]


def test_etapes_de_generer_tout() -> None:
    gt = _charger_module(RACINE / "generer_tout.py", "generer_tout")
    noms = [e.nom for e in gt.ETAPES]
    assert noms[0] == "registre" and "tests" in noms and "verifier" in noms
    assert len(noms) == len(set(noms))
    for e in gt.ETAPES:
        for cmd in e.commandes:
            script = cmd[-1] if cmd[1] != "-m" else None
            if script and script.endswith(".py"):
                assert (RACINE / script).exists(), script
    assert gt.main(["--liste"]) == 0
    assert gt.main(["--etapes", "inconnue"]) == 2


def test_fichiers_de_publication() -> None:
    cff = yaml.safe_load((RACINE / "CITATION.cff").read_text(
        encoding="utf-8"))
    assert cff["license"] == "GPL-3.0-or-later"
    assert cff["authors"] and cff["version"]
    pyproject = (RACINE / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "GPL-3.0-or-later"' in pyproject
    assert f'version = "{cff["version"]}"' in pyproject
    assert (RACINE / "LICENSE").read_text(encoding="utf-8").startswith(
        "                    GNU GENERAL PUBLIC LICENSE")
    assert (RACINE / ".github" / "workflows" / "tests.yml").exists()
    for nom in ("demarrage.md", "ajouter-un-composant.md",
                "ajouter-une-etude.md", "limites-couvertes.md", "api.md"):
        assert (RACINE / "docs" / nom).exists(), nom
