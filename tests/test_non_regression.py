"""Non-régression (phase 6) : la nouvelle architecture « composants »
reproduit les chiffres validés des phases 1 à 5 à 0,1 % près.

La référence ``tests/reference/phases_1_5.yaml`` a été calculée par les
modules d'origine (``caes.systeme``, ``caes.integre``) sur les scénarios
``scenarios/v1/`` ; voir ``generer_reference_phases_1_5.py``.
"""

from pathlib import Path

import pytest
import yaml

from caes.assembleur import ResultatSimulation, charger_installation
from caes.exergie import bilan_exergie_charge, bilan_exergie_decharge
from caes.registre import Registre

TOL = 1e-3
REF = yaml.safe_load(
    (Path(__file__).parent / "reference" / "phases_1_5.yaml").read_text(
        encoding="utf-8"))["rapide"]


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


def _comparer(obtenu: dict, attendu: dict, contexte: str) -> None:
    for k, v in attendu.items():
        assert k in obtenu, f"{contexte} : {k} absent"
        if abs(v) < 1e-9:
            assert abs(obtenu[k]) < 1e-6, f"{contexte} : {k}"
        else:
            assert obtenu[k] == pytest.approx(v, rel=TOL), f"{contexte} : {k}"


@pytest.mark.parametrize("nom", list(REF["charge"]))
def test_charges_dormoy(registre: Registre, nom: str) -> None:
    r = charger_installation(f"{nom}.yaml", registre).simuler()
    assert r.charge is not None
    _comparer(r.charge.totaux, REF["charge"][nom], nom)
    assert abs(r.charge.bilan["residu_relatif"]) < 1e-6


@pytest.mark.parametrize("nom", list(REF["decharge"]))
def test_decharges_dormoy(registre: Registre, nom: str) -> None:
    r = charger_installation(f"{nom}.yaml", registre).simuler()
    assert r.decharge is not None
    attendu = dict(REF["decharge"][nom])
    sources = attendu.pop("chaleur_par_source")
    _comparer(r.decharge.totaux, attendu, nom)
    _comparer(r.decharge.chaleur_par_source, sources, nom + " sources")
    assert abs(r.decharge.bilan["residu_relatif"]) < 1e-6


def _simuler_cycle(registre: Registre, code: str) -> ResultatSimulation:
    mods = ["simulation.nombre_max=2"]
    if code in ("D", "E"):
        mods += [f"composants.cuve_{i}.n_cellules=15" for i in (1, 2, 3)]
    return charger_installation(f"{code}.yaml", registre,
                                modifications=mods).simuler()


@pytest.fixture(scope="module")
def cycles(registre: Registre) -> dict[str, ResultatSimulation]:
    return {code: _simuler_cycle(registre, code) for code in REF["cycles"]}


@pytest.mark.parametrize("code", list(REF["cycles"]))
def test_architectures_A_a_E(cycles: dict[str, ResultatSimulation],
                             code: str) -> None:
    r = cycles[code]
    att = REF["cycles"][code]
    c = r.dernier_cycle
    assert c is not None
    assert len(r.cycles) == att["cycles"]
    _comparer(c.charge.totaux, att["charge"], f"{code} charge")
    _comparer(c.decharge.totaux, att["decharge"], f"{code} décharge")
    # étiquettes : « huile_ideale » (phase 5) est devenu le nom du composant
    sources = {k.replace("huile_ideale", "huile"): v
               for k, v in att["chaleur_par_source"].items()}
    _comparer(c.decharge.chaleur_par_source, sources, f"{code} sources")
    assert c.chaleur_cuves_fin_kwh == pytest.approx(
        att["chaleur_cuves_fin_kwh"], rel=TOL, abs=1e-6)
    assert c.charge.totaux["chaleur_cuves_kwh"] == pytest.approx(
        att["chaleur_cuves_charge_kwh"], rel=TOL, abs=1e-6)


@pytest.mark.parametrize("code", list(REF["cycles"]))
def test_tableau_1000_unites(cycles: dict[str, ResultatSimulation],
                             code: str) -> None:
    c = cycles[code].dernier_cycle
    assert c is not None
    bc = bilan_exergie_charge(c.charge)
    bd = bilan_exergie_decharge(c.decharge)
    unite = bc.entree_j / 1000.0
    att = REF["cycles"][code]["unites_1000"]
    assert bc.sorties_utiles_j["exergie stockée dans les réservoirs"] / unite \
        == pytest.approx(att["stock_reservoirs"], rel=TOL)
    assert bd.sorties_utiles_j["électricité produite"] / unite \
        == pytest.approx(att["electricite_rendue"], rel=TOL)
    assert bd.postes["détendeur (laminage)"] / unite == pytest.approx(
        att["detendeur"], rel=TOL)
    assert abs(bc.residu_relatif) < 0.01
    assert abs(bd.residu_relatif) < 0.02
