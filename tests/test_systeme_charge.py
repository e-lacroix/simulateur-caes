"""Tests de la simulation de charge complète (phase 1)."""

import numpy as np
import pytest

from caes.registre import Registre
from caes.scenario import Scenario, charger_scenario
from caes.systeme import ResultatCharge, simuler_charge


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def scenario(registre: Registre) -> Scenario:
    return charger_scenario("v1/dormoy_charge_1_190.yaml", registre)


@pytest.fixture(scope="module")
def resultat(scenario: Scenario) -> ResultatCharge:
    return simuler_charge(scenario)


def test_la_charge_atteint_la_cible(resultat: ResultatCharge) -> None:
    assert resultat.arret == "pression cible atteinte"
    assert resultat.totaux["p_finale_bar"] == pytest.approx(190.0, abs=0.2)


def test_pression_strictement_croissante(resultat: ResultatCharge) -> None:
    p = resultat.series["p_res_pa"].to_numpy()
    assert np.all(np.diff(p) > 0)


def test_temperatures_physiques(resultat: ResultatCharge) -> None:
    s = resultat.series
    assert s["T_res_K"].between(250.0, 500.0).all()
    for i in range(1, 5):
        assert s[f"T_out_comp_{i}_K"].between(300.0, 600.0).all()
        assert (s[f"T_out_ref_{i}_K"] < s[f"T_out_comp_{i}_K"]).all()
        assert (s[f"T_out_ref_{i}_K"] > 293.0).all()


def test_conservation_de_la_masse(resultat: ResultatCharge) -> None:
    b = resultat.bilan
    assert b["masse_stockee_kg"] == pytest.approx(
        b["masse_entree_kg"], rel=1e-3
    )


def test_bilan_d_energie_ferme_a_1_pourcent(resultat: ResultatCharge) -> None:
    b = resultat.bilan
    assert abs(b["residu_relatif"]) < 0.01
    # chaque poste est positif sauf le stock relatif, qui peut être < 0
    for cle in (
        "pertes_mec_el_j",
        "Q_poly_rejete_j",
        "Q_refroidisseurs_j",
        "E_air_perdu_j",
        "Q_paroi_reservoir_j",
    ):
        assert b[cle] >= 0.0, cle


def test_ordres_de_grandeur_de_dormoy(resultat: ResultatCharge) -> None:
    t = resultat.totaux
    assert 8.0 < t["duree_h"] < 12.0
    assert 330.0 < t["energie_electrique_kwh"] < 430.0
    assert 33.0 < t["puissance_moyenne_kw"] < 45.0


def test_chaleur_utile_inferieure_a_la_chaleur_totale(
    resultat: ResultatCharge,
) -> None:
    t = resultat.totaux
    assert 0.0 < t["chaleur_sup_seuil_kwh"] < t["chaleur_refroidisseurs_kwh"]
    somme = sum(t[f"chaleur_refroidisseur_{i}_kwh"] for i in range(1, 5))
    assert somme == pytest.approx(t["chaleur_refroidisseurs_kwh"], rel=1e-9)


def test_convergence_en_pas_de_temps(
    scenario: Scenario, resultat: ResultatCharge
) -> None:
    fin = simuler_charge(scenario.avec({"simulation.dt": 2.0}, "dt2"))
    e10 = resultat.totaux["energie_electrique_kwh"]
    e2 = fin.totaux["energie_electrique_kwh"]
    assert abs(e10 - e2) / e2 < 2e-3
    assert abs(resultat.totaux["duree_h"] - fin.totaux["duree_h"]) < 0.02


def test_charge_partielle_plus_courte(
    registre: Registre, resultat: ResultatCharge
) -> None:
    partiel = simuler_charge(
        charger_scenario("v1/dormoy_charge_55_190.yaml", registre)
    )
    assert partiel.totaux["duree_h"] < resultat.totaux["duree_h"]
    assert partiel.totaux["chaleur_refroidisseurs_kwh"] < (
        resultat.totaux["chaleur_refroidisseurs_kwh"]
    )


def test_arret_sur_duree_maximale(scenario: Scenario) -> None:
    court = simuler_charge(
        scenario.avec({"simulation.duree_max": 600.0}, "court")
    )
    assert court.arret == "durée maximale atteinte"
    assert court.totaux["duree_s"] == pytest.approx(600.0)


def test_debit_reservoir_impose(scenario: Scenario) -> None:
    r = simuler_charge(
        scenario.avec(
            {"secheur.debit_massique_reservoir_impose": 0.032}, "mesure"
        )
    )
    assert r.totaux["debit_reservoir_kg_s"] == 0.032
    assert r.totaux["debit_aspire_kg_s"] == pytest.approx(0.052)
