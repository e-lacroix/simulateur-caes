"""Tests de la simulation de décharge (phase 2)."""

import numpy as np
import pytest

from caes.registre import Registre
from caes.scenario import Scenario, charger_scenario
from caes.systeme import (
    ResultatDecharge,
    rendements_aller_retour,
    simuler_charge,
    simuler_decharge,
)


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def essai(registre: Registre) -> ResultatDecharge:
    return simuler_decharge(
        charger_scenario("dormoy_decharge_essai.yaml", registre)
    )


@pytest.fixture(scope="module")
def base(registre: Registre) -> ResultatDecharge:
    return simuler_decharge(
        charger_scenario("dormoy_decharge_base.yaml", registre)
    )


@pytest.fixture(scope="module")
def trois(registre: Registre) -> ResultatDecharge:
    return simuler_decharge(
        charger_scenario("dormoy_decharge_3etages.yaml", registre)
    )


def test_essai_mesure_duree_proche_de_38_min(essai: ResultatDecharge) -> None:
    assert essai.arret == "pression d'arrêt du détendeur atteinte"
    assert essai.totaux["p_finale_bar"] == pytest.approx(50.0, abs=0.1)
    assert 33.0 < essai.totaux["duree_min"] < 43.0


def test_pression_et_masse_decroissantes(essai: ResultatDecharge) -> None:
    assert np.all(np.diff(essai.series["p_res_pa"].to_numpy()) < 0)
    assert np.all(np.diff(essai.series["m_res_kg"].to_numpy()) < 0)


def test_conservation_de_la_masse_en_decharge(
    essai: ResultatDecharge,
) -> None:
    b = essai.bilan
    assert b["masse_soutiree_kg"] == pytest.approx(
        b["masse_sortie_kg"], rel=1e-6
    )


def test_bilans_fermes(
    essai: ResultatDecharge, base: ResultatDecharge, trois: ResultatDecharge
) -> None:
    for r in (essai, base, trois):
        assert abs(r.bilan["residu_relatif"]) < 0.01
        ref = abs(r.bilan["E_sortie_reservoir_j"])
        assert abs(r.bilan["residu_reservoir_j"]) < 0.01 * ref


def test_air_se_refroidit_dans_le_reservoir(essai: ResultatDecharge) -> None:
    s = essai.series
    assert s["T_res_K"].iloc[-1] < s["T_res_K"].iloc[0]
    assert s["T_res_K"].between(200.0, 340.0).all()
    # la paroi, plus chaude, réchauffe l'air : elle se refroidit aussi
    assert s["T_paroi_K"].iloc[-1] < s["T_paroi_K"].iloc[0]
    assert (s["T_paroi_K"] > s["T_res_K"]).iloc[-1]


def test_cheayb_proche_de_l_isenthalpique(
    registre: Registre, essai: ResultatDecharge
) -> None:
    sc = charger_scenario("dormoy_decharge_essai.yaml", registre)
    ch = simuler_decharge(sc.avec({"detendeur.modele": "cheayb"}, "cheayb"))
    assert abs(ch.totaux["duree_min"] - essai.totaux["duree_min"]) < 0.5
    ecart = abs(
        ch.totaux["T_sortie_detendeur_moyenne_degC"]
        - essai.totaux["T_sortie_detendeur_moyenne_degC"]
    )
    assert ecart < 8.0


def test_cas_de_base_ordre_de_grandeur_de_dormoy(
    base: ResultatDecharge,
) -> None:
    """Dormoy : 16,93 kWh. Le modèle donne ≈ 14,3 kWh (écart connu de
    −15 %, analysé dans rapports/phase2/validation_decharge.md)."""
    assert base.totaux["p_finale_bar"] == pytest.approx(18.0, abs=0.1)
    assert base.totaux["chaleur_rechauffage_kwh"] == 0.0
    assert base.chaleur_par_source == {}
    assert 13.0 <= base.totaux["energie_electrique_kwh"] <= 18.0
    # détente de 3 à 1 bar sans réchauffage : sortie très froide (givre)
    assert base.totaux["T_rejet_min_degC"] < 0.0


def test_trois_etages_chaleur_et_energie(trois: ResultatDecharge) -> None:
    """Dormoy, tableau 5 : 46,2 kWh (24,8 / 6,4 / 15,0) sur 40 min."""
    t = trois.totaux
    assert t["p_finale_bar"] == pytest.approx(55.0, abs=0.1)
    assert trois.chaleur_par_source.keys() == {"externe"}
    assert t["chaleur_rechauffage_kwh"] == pytest.approx(
        trois.chaleur_par_source["externe"]
    )
    somme = sum(t[f"chaleur_rechauffage_{i}_kwh"] for i in (1, 2, 3))
    assert somme == pytest.approx(t["chaleur_rechauffage_kwh"], rel=1e-9)
    assert 34.0 < t["duree_min"] < 46.0
    assert 36.0 < t["energie_electrique_kwh"] < 50.0
    assert t["chaleur_rechauffage_kwh"] == pytest.approx(46.2, rel=0.08)
    assert t["chaleur_rechauffage_1_kwh"] == pytest.approx(24.8, rel=0.08)
    assert t["chaleur_rechauffage_2_kwh"] == pytest.approx(6.4, rel=0.12)
    assert t["chaleur_rechauffage_3_kwh"] == pytest.approx(15.0, rel=0.10)


def test_regle_du_bilan_de_chaleur(trois: ResultatDecharge) -> None:
    """Toute chaleur ajoutée a une source déclarée."""
    total = sum(trois.chaleur_par_source.values())
    assert total == pytest.approx(trois.totaux["chaleur_rechauffage_kwh"])
    assert all(s in ("externe",) or s.startswith("cuve_")
               for s in trois.chaleur_par_source)


def test_rendements_aller_retour(
    registre: Registre, trois: ResultatDecharge
) -> None:
    charge = simuler_charge(
        charger_scenario("dormoy_charge_55_190.yaml", registre)
    )
    r = rendements_aller_retour(charge, trois)
    assert 0.12 < r["rte_sans_chaleur"] < 0.20
    assert r["rte_avec_chaleur_externe"] < r["rte_sans_chaleur"]
    assert r["chaleur_externe_kwh"] > 0


def test_convergence_dt(registre: Registre, trois: ResultatDecharge) -> None:
    sc = charger_scenario("dormoy_decharge_3etages.yaml", registre)
    gros = simuler_decharge(sc.avec({"simulation.dt": 10.0}, "dt10"))
    e1 = trois.totaux["energie_electrique_kwh"]
    e10 = gros.totaux["energie_electrique_kwh"]
    assert abs(e1 - e10) / e1 < 5e-3


def test_mode_inconnu_refuse(registre: Registre) -> None:
    sc = charger_scenario("dormoy_decharge_essai.yaml", registre)
    with pytest.raises(ValueError):
        simuler_decharge(sc.avec({"decharge.mode": "x"}, "x"))
