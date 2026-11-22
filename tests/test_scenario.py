"""Tests du chargeur de scénarios (phase 1)."""

from pathlib import Path

import pytest

from caes.registre import ErreurRegistre, Registre
from caes.scenario import charger_scenario


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


def test_scenario_dormoy_se_charge_en_si(registre: Registre) -> None:
    sc = charger_scenario("v1/dormoy_charge_1_190.yaml", registre)
    assert sc.nom == "dormoy_charge_1_190"
    assert sc["simulation.p_cible"] == pytest.approx(190e5)
    assert sc["ambiance.T_amb"] == pytest.approx(293.15)
    assert sc["reservoir.volume"] == pytest.approx(5.86)
    assert sc["simulation.dt"] == 10.0
    assert sc["compresseur.etages.0.rapport_pression"] == 3.25
    assert sc["compresseur.rendement_electrique"] == pytest.approx(0.945)
    assert sc.get("secheur.debit_massique_reservoir_impose") is None


def test_provenance_est_tracee(registre: Registre) -> None:
    sc = charger_scenario("v1/dormoy_charge_1_190.yaml", registre)
    prov = sc.provenance["reservoir.volume"]
    assert "reservoir.volume_total" in prov
    assert "fabricant" in prov
    assert "scénario" in sc.provenance["simulation.dt"]
    assert "hypothèse" in sc.provenance["compresseur.rendement_electrique"]


def test_avec_modifie_une_copie(registre: Registre) -> None:
    sc = charger_scenario("v1/dormoy_charge_1_190.yaml", registre)
    sc2 = sc.avec({"ambiance.T_aspiration": 325.15}, "chaud")
    assert sc2["ambiance.T_aspiration"] == 325.15
    assert sc["ambiance.T_aspiration"] == pytest.approx(293.15)
    assert sc2.nom.endswith("_chaud")
    assert "modifié" in sc2.provenance["ambiance.T_aspiration"]


def test_erreurs_de_resolution(tmp_path: Path, registre: Registre) -> None:
    f = tmp_path / "mauvais.yaml"
    f.write_text(
        "x: registre:reservoir.volume_total#median\n", encoding="utf-8"
    )
    with pytest.raises(ErreurRegistre):
        charger_scenario(f, registre)
    f.write_text(
        "x: {valeur: 1, unite: furlong, source: test}\n", encoding="utf-8"
    )
    with pytest.raises(ErreurRegistre):
        charger_scenario(f, registre)
    f.write_text("x: registre:inexistant.id\n", encoding="utf-8")
    with pytest.raises(ErreurRegistre):
        charger_scenario(f, registre)
