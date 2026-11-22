"""Tests du système intégré Dormoy + cuves (phase 5)."""

import pytest

from caes.exergie import bilan_exergie_charge, bilan_exergie_decharge
from caes.integre import ResultatIntegre, simuler_cycles
from caes.registre import Registre
from caes.scenario import charger_scenario


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def res_B(registre: Registre) -> ResultatIntegre:
    sc = charger_scenario("v1/B.yaml", registre).avec(
        {"cycles.nombre_max": 2}, "court")
    return simuler_cycles(sc, registre)


@pytest.fixture(scope="module")
def res_C(registre: Registre) -> ResultatIntegre:
    sc = charger_scenario("v1/C.yaml", registre).avec(
        {"cycles.nombre_max": 2}, "court")
    return simuler_cycles(sc, registre)


@pytest.fixture(scope="module")
def res_D(registre: Registre) -> ResultatIntegre:
    sc = charger_scenario("v1/D.yaml", registre).avec(
        {"cycles.nombre_max": 2, "cuves.n_cellules": 15}, "court")
    return simuler_cycles(sc, registre)


@pytest.fixture(scope="module")
def res_E(registre: Registre) -> ResultatIntegre:
    sc = charger_scenario("v1/E.yaml", registre).avec(
        {"cycles.nombre_max": 2, "cuves.n_cellules": 15}, "court")
    return simuler_cycles(sc, registre)


def test_B_source_externe(res_B: ResultatIntegre) -> None:
    d = res_B.dernier.decharge
    assert set(d.chaleur_par_source) == {"externe"}
    assert 35.0 < d.totaux["energie_electrique_kwh"] < 50.0
    assert res_B.dernier.charge.totaux["p_initiale_bar"] == pytest.approx(
        55.0, abs=0.5)


def test_C_huile_ideale_sans_appoint(res_C: ResultatIntegre) -> None:
    d = res_C.dernier.decharge
    assert set(d.chaleur_par_source) == {"huile_ideale"}
    assert res_C.huile_reserve_kwh > 0.0  # type: ignore[attr-defined]
    # même électricité que B : la chaleur est seulement étiquetée autrement
    assert d.totaux["energie_electrique_kwh"] == pytest.approx(
        res_B_energie(res_C), rel=0.05)


def res_B_energie(res: ResultatIntegre) -> float:
    return res.dernier.decharge.totaux["energie_electrique_kwh"]


def test_D_cuves_alimentent_les_turbines(res_D: ResultatIntegre) -> None:
    c = res_D.dernier
    d = c.decharge
    assert set(d.chaleur_par_source) <= {"cuve_1", "cuve_2", "cuve_3"}
    assert "externe" not in d.chaleur_par_source
    s = d.series
    for i, cible in ((1, 403.15), (2, 363.15), (3, 363.15)):
        assert (s[f"T_in_turb_{i}_K"] <= cible + 0.5).all()
        assert (s[f"T_in_turb_{i}_K"] >= s[f"T_avant_rech_{i}_K"] - 1e-6).all()
    assert c.charge.totaux["chaleur_cuves_kwh"] > 0.0
    assert c.chaleur_cuves_fin_kwh > 0.0


def test_D_bilan_de_charge_ferme_avec_cuves(res_D: ResultatIntegre) -> None:
    ch = res_D.dernier.charge
    assert abs(ch.bilan["residu_relatif"]) < 0.01
    assert ch.bilan["Q_cuves_j"] > 0.0
    # avec cuves, les refroidisseurs rejettent moins qu'en B
    assert ch.totaux["chaleur_refroidisseurs_kwh"] < 170.0


def test_D_bilan_d_exergie_ferme(res_D: ResultatIntegre) -> None:
    c = res_D.dernier
    bc = bilan_exergie_charge(c.charge)
    bd = bilan_exergie_decharge(c.decharge)
    assert abs(bc.residu_relatif) < 0.01
    assert abs(bd.residu_relatif) < 0.02
    assert bd.exergie_puisee_cuves_j > 0.0
    assert any("cuve" in k for k in bc.sorties_utiles_j)
    assert any("restitution" in k for k in bd.postes)


def test_E_pincement_reduit_la_temperature(
    res_D: ResultatIntegre, res_E: ResultatIntegre
) -> None:
    # au premier cycle, la cuve 3 de E (chargée 20 K plus froid et rendant
    # 20 K plus froid) chauffe moins la turbine 1 que celle de D
    d1_D = res_D.cycles[0].decharge.series["T_in_turb_1_K"].mean()
    d1_E = res_E.cycles[0].decharge.series["T_in_turb_1_K"].mean()
    assert d1_E <= d1_D + 1e-6
    assert res_E.cuves is not None
    assert max(l.T_s_K.max() for l in res_E.cuves) < max(
        l.T_s_K.max() for l in res_D.cuves)  # type: ignore[union-attr]


def test_cuves_trop_petites_ne_suffisent_pas(registre: Registre) -> None:
    sc = charger_scenario("v1/D.yaml", registre).avec(
        {"cycles.nombre_max": 1, "cuves.n_cellules": 10}, "mini")
    r = simuler_cycles(sc, registre, volumes_m3=[0.05, 0.05, 0.05])
    s = r.dernier.decharge.series
    assert s["T_in_turb_1_K"].min() < 403.15 - 5.0
    assert r.dernier.decharge.totaux["energie_electrique_kwh"] < (
        res_B_energie(r) + 1e-9)


def test_architecture_inconnue(registre: Registre) -> None:
    sc = charger_scenario("v1/A.yaml", registre).avec(
        {"architecture": "Z"}, "z")
    with pytest.raises(ValueError):
        simuler_cycles(sc, registre)
