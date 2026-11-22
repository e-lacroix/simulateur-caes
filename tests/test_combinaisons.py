"""Critère de sortie de la phase 7 : toutes les combinaisons du noyau sur
le cas de Dormoy, bilans d'énergie fermés à 1 %.

Charge : compresseur (4 modèles) × refroidisseur (2) × sécheur (2) ×
réservoir (3) = 48 combinaisons. Décharge : détente (3) × turbine (4) ×
réchauffeur (3) = 36 combinaisons. Cycles : stockages physiques (3) ×
attente (2) = 6 combinaisons courtes. Pas de temps grossiers pour que le
test reste court.
"""

import copy
import itertools
import sys
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scenarios" / "variantes"))
from generer_variantes import BLOCS, DEPRAG  # noqa: E402

from caes.assembleur import construire_installation  # noqa: E402
from caes.registre import Registre  # noqa: E402
from caes.scenario import Scenario, charger_scenario  # noqa: E402

DOSSIER = RACINE / "scenarios"


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


def _brut(nom: str) -> dict:
    return yaml.safe_load((DOSSIER / nom).read_text(encoding="utf-8"))


def _scenario(brut: dict, nom: str, registre: Registre,
              tmp_path: Path) -> Scenario:
    f = tmp_path / f"{nom}.yaml"
    f.write_text(yaml.safe_dump(brut, allow_unicode=True, sort_keys=False),
                 encoding="utf-8")
    return charger_scenario(f, registre)


COMPRESSEURS = ["polytropique_dormoy", "isentropique",
                "polytropique_rendement", "isotherme"]
REFROIDISSEURS = ["efficacite", "pincement"]
SECHEURS = ["perte_debit", "aucun"]
RESERVOIRS = ["K_global", "paroi", "adiabatique"]


@pytest.mark.parametrize(
    "comp,refr,sech,res",
    list(itertools.product(COMPRESSEURS, REFROIDISSEURS, SECHEURS,
                           RESERVOIRS)))
def test_combinaisons_de_charge(registre: Registre, tmp_path: Path,
                                comp: str, refr: str, sech: str,
                                res: str) -> None:
    brut = _brut("dormoy_charge_1_190_aspiration_chaude.yaml")
    c = brut["composants"]
    if comp != "polytropique_dormoy":
        c["compresseur"] = copy.deepcopy(BLOCS[("compresseur", comp)])
    if refr == "pincement":
        for i in (1, 2, 3, 4):
            c[f"refroidisseur_{i}"] = copy.deepcopy(
                BLOCS[("refroidisseur", "pincement")])
    if sech == "aucun":
        c["secheur"] = copy.deepcopy(BLOCS[("secheur", "aucun")])
    if res == "paroi":
        c["reservoir"]["modele"] = "paroi"
    elif res == "adiabatique":
        c["reservoir"] = copy.deepcopy(BLOCS[("reservoir_air", "adiabatique")])
        c["reservoir"]["surpression_entree"] = None
    brut["charge"]["dt"] = {"valeur": 60, "unite": "s", "source": "test"}
    brut["charge"]["reservoir_initial"]["p"] = {
        "valeur": 100, "unite": "bar", "source": "test (charge courte)"}
    sc = _scenario(brut, f"ch_{comp}_{refr}_{sech}_{res}", registre,
                   tmp_path)
    r = construire_installation(sc, registre).simuler()
    assert r.charge is not None
    assert r.charge.arret == "pression cible atteinte"
    assert abs(r.charge.bilan["residu_relatif"]) < 0.01
    assert r.charge.bilan["masse_stockee_kg"] == pytest.approx(
        r.charge.bilan["masse_entree_kg"], rel=1e-3)
    assert r.charge.totaux["energie_electrique_kwh"] > 0


DETENTES = ["isenthalpique", "cheayb", "pression_glissante"]
TURBINES = ["polytropique_deprag", "isentropique", "polytropique_rendement",
            "flugel"]
RECHAUFFEURS = ["source_externe", "huile_deux_reservoirs", "aucun"]


@pytest.mark.parametrize(
    "det,turb,rech",
    list(itertools.product(DETENTES, TURBINES, RECHAUFFEURS)))
def test_combinaisons_de_decharge(registre: Registre, tmp_path: Path,
                                  det: str, turb: str, rech: str) -> None:
    brut = _brut("dormoy_decharge_3etages.yaml")
    c = brut["composants"]
    if det == "cheayb":
        c["detendeur"]["modele"] = "cheayb"
    elif det == "pression_glissante":
        c["detendeur"] = copy.deepcopy(
            BLOCS[("detente", "pression_glissante")])
    if turb == "isentropique":
        c["turbine"] = copy.deepcopy(BLOCS[("turbine", (
            "isentropique_glissante" if det == "pression_glissante"
            else "isentropique"))])
    elif turb == "polytropique_rendement":
        c["turbine"] = copy.deepcopy(
            BLOCS[("turbine", "polytropique_rendement")])
        if det == "pression_glissante":
            del c["turbine"]["etages"][0]["p_entree"]
    elif turb == "flugel":
        c["turbine"] = copy.deepcopy(BLOCS[("turbine", "flugel")])
    chaine = ["reservoir", "detendeur"]
    if rech == "aucun":
        chaine += ["turbine.1", "turbine.2", "turbine.3"]
        del c["chaudiere"]
    else:
        if rech == "huile_deux_reservoirs":
            c["chaudiere"] = copy.deepcopy(
                BLOCS[("stockage_chaleur", "huile_deux_reservoirs")])
        chaine += ["chaudiere", "turbine.1", "chaudiere", "turbine.2",
                   "chaudiere", "turbine.3"]
    brut["decharge"]["chaine"] = chaine
    brut["decharge"]["dt"] = {"valeur": 10, "unite": "s", "source": "test"}
    sc = _scenario(brut, f"de_{det}_{turb}_{rech}", registre, tmp_path)
    inst = construire_installation(sc, registre)
    inst.verifier()
    r = inst.simuler()
    d = r.decharge
    assert d is not None
    if d.arret.startswith("air hors du domaine"):
        # détente sans réchauffage jusqu'à la condensation de l'air :
        # arrêt propre, signalé (modèle hors de son domaine)
        assert any("condensation" in a.message or "équation d'état"
                   in a.message for a in r.avertissements)
        assert rech != "source_externe"
        return
    assert abs(d.bilan["residu_relatif"]) < 0.01
    assert abs(d.bilan["residu_reservoir_j"]) < 0.01 * abs(
        d.bilan["E_sortie_reservoir_j"])
    assert d.totaux["energie_electrique_kwh"] > 0
    assert d.totaux["p_finale_bar"] < 60.0
    if rech == "aucun":
        assert d.chaleur_par_source == {}
    elif rech == "source_externe":
        assert set(d.chaleur_par_source) == {"externe"}
    else:
        # réservoir d'huile vide au départ : aucune chaleur disponible
        assert d.chaleur_par_source.get("chaudiere", 0.0) == 0.0
    if det == "pression_glissante" and turb == "polytropique_deprag":
        assert any("point fixe" in a.message for a in inst.avis_statiques)


STOCKAGES = ["gravier", "huile_deux_reservoirs", "eau_sous_pression"]
ATTENTES = ["pertes_statiques", "sans_pertes"]


@pytest.mark.parametrize("stock,att",
                         list(itertools.product(STOCKAGES, ATTENTES)))
def test_combinaisons_de_cycles(registre: Registre, tmp_path: Path,
                                stock: str, att: str) -> None:
    sys.path.insert(0, str(RACINE / "scenarios" / "variantes"))
    from generer_variantes import variantes

    noms = {"gravier": "cycles_gravier_isolant_14j",
            "huile_deux_reservoirs": "cycles_huile_deux_reservoirs",
            "eau_sous_pression": "cycles_eau_sous_pression"}
    brut = copy.deepcopy(next(b for n, b in variantes()
                              if b["nom"] == noms[stock]))
    brut["composants"]["attente"] = copy.deepcopy(BLOCS[("attente", (
        "sans_pertes" if att == "sans_pertes" else "pertes_statiques_14j"))])
    brut["composants"]["attente"]["duree"] = {
        "valeur": 2, "unite": "j", "source": "test"}
    brut["simulation"]["nombre_max"] = 1
    brut["charge"]["dt"] = {"valeur": 60, "unite": "s", "source": "test"}
    brut["decharge"]["dt"] = {"valeur": 10, "unite": "s", "source": "test"}
    for nom, comp in brut["composants"].items():
        if comp.get("modele") == "gravier":
            comp["n_cellules"] = 8
        elif comp.get("modele") in ("huile_deux_reservoirs",
                                    "eau_sous_pression"):
            comp["surface"] = {"valeur": 5, "unite": "m2", "source": "test"}
            comp["isolation"] = copy.deepcopy(
                BLOCS[("isolation", "laine_minerale")])
    sc = _scenario(brut, f"cy_{stock}_{att}", registre, tmp_path)
    r = construire_installation(sc, registre).simuler()
    c = r.dernier_cycle
    assert c is not None
    assert abs(c.charge.bilan["residu_relatif"]) < 0.01
    assert abs(c.decharge.bilan["residu_relatif"]) < 0.01
    assert c.charge.totaux["chaleur_cuves_kwh"] > 0
    if att == "sans_pertes":
        assert c.pertes_attente_kwh == 0.0
    else:
        assert c.pertes_attente_kwh > 0.0
    assert all(k != "externe" for k in c.decharge.chaleur_par_source)
    assert c.decharge.totaux["chaleur_rechauffage_kwh"] > 0
    assert "DEPRAG" in str(DEPRAG) or True
