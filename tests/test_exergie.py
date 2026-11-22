"""Tests du bilan d'exergie (phase 3)."""

import math

import pytest

from caes.compresseur import comprimer_etage
from caes.exergie import (
    Exergie,
    bilan_exergie_charge,
    bilan_exergie_decharge,
    exergie_etage_compression,
    temperature_log_moyenne,
)
from caes.proprietes import AirParfait, AirReel
from caes.registre import Registre
from caes.scenario import charger_scenario
from caes.systeme import simuler_charge, simuler_decharge

T0 = 293.15
P0 = 101325.0


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def reel() -> AirReel:
    return AirReel()


@pytest.fixture(scope="module")
def parfait(registre: Registre) -> AirParfait:
    return AirParfait.depuis_registre(registre)


def test_exergie_nulle_a_l_etat_mort(reel: AirReel) -> None:
    ex = Exergie(reel, T0, P0)
    assert ex.flux(P0, T0) == pytest.approx(0.0, abs=1e-6)
    assert ex.fermee_massique(P0, T0) == pytest.approx(0.0, abs=1e-6)
    assert ex.chaleur(1000.0, T0) == 0.0


def test_exergie_positive_hors_etat_mort(reel: AirReel) -> None:
    ex = Exergie(reel, T0, P0)
    assert ex.flux(190e5, T0) > 0.0
    assert ex.flux(P0, 400.0) > 0.0
    assert ex.flux(P0, 250.0) > 0.0  # le froid aussi a de l'exergie
    assert ex.fermee_massique(190e5, T0) > 0.0
    assert ex.chaleur(1000.0, 400.0) == pytest.approx(1000.0 * (1 - T0 / 400))
    assert ex.chaleur(1000.0, 250.0) < 0.0


def test_eq_22_baniamerian_egale_exergie_fermee_gaz_parfait(
    parfait: AirParfait,
) -> None:
    ex = Exergie(parfait, T0, P0)
    V, p = 5.86, 190e5
    m = parfait.rho(p, T0) * V
    assert ex.fermee(m, p, T0) == pytest.approx(
        ex.air_comprime_gaz_parfait(V, p), rel=1e-9
    )
    # 132 kWh dans la fiche Dormoy (gaz parfait, 15 °C)
    ex15 = Exergie(parfait, 288.15, P0)
    assert ex15.air_comprime_gaz_parfait(V, p) / 3.6e6 == pytest.approx(
        131.1, abs=1.0
    )


def test_air_reel_contient_un_peu_moins_d_exergie(
    reel: AirReel, parfait: AirParfait
) -> None:
    exr = Exergie(reel, T0, P0)
    exp = Exergie(parfait, T0, P0)
    V, p = 5.86, 190e5
    reelle = exr.fermee(reel.rho(p, T0) * V, p, T0)
    ideale = exp.fermee(parfait.rho(p, T0) * V, p, T0)
    assert 0.9 < reelle / ideale < 1.0


def test_temperature_log_moyenne() -> None:
    assert temperature_log_moyenne(300.0, 300.0) == 300.0
    tlm = temperature_log_moyenne(300.0, 400.0)
    assert 300.0 < tlm < 350.0
    assert tlm == pytest.approx(100.0 / math.log(400.0 / 300.0))


def test_compresseur_isotherme_reversible_ne_detruit_rien(
    parfait: AirParfait,
) -> None:
    """Cas limite : n = 1 à T0, chaleur rejetée à T0 → D = 0, Ex_q = 0."""
    ex = Exergie(parfait, T0, P0)
    et = comprimer_etage(parfait, P0, T0, 3.25, 1.0)
    D, Exq = exergie_etage_compression(
        ex, P0, T0, et.p_out_pa, et.T_out_K, et.q_poly
    )
    assert D == pytest.approx(0.0, abs=1e-6 * et.w_pol)
    assert Exq == pytest.approx(0.0, abs=1e-6 * et.w_pol)
    # et le travail fourni se retrouve intégralement en exergie
    gain = ex.flux(et.p_out_pa, et.T_out_K) - ex.flux(P0, T0)
    assert gain == pytest.approx(et.w_pol, rel=1e-9)


def test_compression_polytropique_bilan_d_etage(parfait: AirParfait) -> None:
    """w + ex_in − ex_out = D + Ex_q pour une polytropique (gaz parfait)."""
    ex = Exergie(parfait, T0, P0)
    et = comprimer_etage(parfait, P0, 325.0, 3.25, 1.35)
    D, Exq = exergie_etage_compression(
        ex, P0, 325.0, et.p_out_pa, et.T_out_K, et.q_poly
    )
    gauche = et.w_pol + ex.flux(P0, 325.0) - ex.flux(et.p_out_pa, et.T_out_K)
    assert gauche == pytest.approx(D + Exq, rel=1e-6)
    assert D >= -1e-9  # intérieurement réversible : D ≈ 0


@pytest.fixture(scope="module")
def chaine(registre: Registre):
    sc_c = charger_scenario(
        "v1/dormoy_charge_1_190_aspiration_chaude.yaml", registre
    ).avec({"reservoir.p_initiale": registre.si("cas_base.pression_arret")},
           "depuis18")
    ch = simuler_charge(sc_c)
    sc_d = charger_scenario("v1/dormoy_decharge_base.yaml", registre).avec(
        {"reservoir.p_initiale": ch.series["p_res_pa"].iloc[-1],
         "reservoir.T_initiale": ch.series["T_res_K"].iloc[-1],
         "reservoir.T_paroi_initiale": ch.series["T_paroi_K"].iloc[-1]},
        "chaine",
    )
    return ch, simuler_decharge(sc_d)


def test_bilan_charge_ferme_a_1_pourcent(chaine) -> None:
    ch, _ = chaine
    b = bilan_exergie_charge(ch)
    assert abs(b.residu_relatif) < 0.01
    assert b.entree_j == pytest.approx(ch.bilan["E_el_j"], rel=1e-6)


def test_bilan_decharge_ferme_a_1_pourcent(chaine) -> None:
    _, d = chaine
    b = bilan_exergie_decharge(d)
    assert abs(b.residu_relatif) < 0.01
    assert b.sorties_utiles_j["électricité produite"] == pytest.approx(
        d.bilan["E_electrique_j"], rel=1e-6
    )


def test_exergies_detruites_positives(chaine) -> None:
    """Toute destruction est >= 0, à deux exceptions près, petites et
    expliquées : la chaleur « absorbée » par le modèle polytropique quand
    n > γ, et l'air rejeté sous la pression atmosphérique (1,0 bar contre
    1,013 bar chez DEPRAG), dont l'exergie de flux est négative."""
    ch, d = chaine
    bc, bd = bilan_exergie_charge(ch), bilan_exergie_decharge(d)
    for b in (bc, bd):
        for nom, val in b.postes.items():
            assert val > -0.01 * b.entree_j, nom
    for nom in ("moteur et mécanique", "refroidisseur 1 (chaleur rejetée)",
                "air rejeté (sécheur)", "laminage vers le réservoir"):
        assert bc.postes[nom] > 0.0, nom
    for nom in ("détendeur (laminage)", "turbine étage 1 (irréversibilité)",
                "génératrice étage 1"):
        assert bd.postes[nom] > 0.0, nom


def test_stock_charge_egale_exergie_initiale_decharge(chaine) -> None:
    ch, d = chaine
    bc = bilan_exergie_charge(ch)
    bd = bilan_exergie_decharge(d)
    stock_fin = bc.exergie_initiale_j + bc.sorties_utiles_j[
        "exergie stockée dans les réservoirs"]
    assert bd.exergie_initiale_j == pytest.approx(stock_fin, rel=1e-6)


def test_detendeur_domine_les_pertes_du_cas_de_base(chaine) -> None:
    _, d = chaine
    b = bilan_exergie_decharge(d)
    assert b.postes["détendeur (laminage)"] > 0.5 * b.entree_j


def test_regle_du_bilan_de_chaleur_3_etages(registre: Registre) -> None:
    d = simuler_decharge(charger_scenario("v1/dormoy_decharge_3etages.yaml",
                                          registre))
    b = bilan_exergie_decharge(d)
    assert b.exergie_rechauffage_j > 0.0
    chaleur = sum(v for k, v in b.chaleurs_j.items() if "réchauffage" in k)
    assert chaleur == pytest.approx(d.bilan["Q_rechauffage_j"], rel=1e-6)
    assert set(d.chaleur_par_source) == {"externe"}
    # l'exergie apportée est inférieure à la chaleur (facteur de Carnot)
    assert b.exergie_rechauffage_j < chaleur
