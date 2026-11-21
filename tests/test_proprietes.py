"""Tests des propriétés de l'air (phase 1)."""

import pytest

from caes.proprietes import AirParfait, AirReel
from caes.registre import Registre

P_ATM = 101325.0
T_20 = 293.15


@pytest.fixture(scope="module")
def reel() -> AirReel:
    return AirReel()


@pytest.fixture(scope="module")
def parfait() -> AirParfait:
    return AirParfait.depuis_registre(Registre.charger())


def test_masse_volumique_1bar_20C_concorde_a_0_1_pourcent(
    reel: AirReel, parfait: AirParfait
) -> None:
    rho_r = reel.rho(P_ATM, T_20)
    rho_p = parfait.rho(P_ATM, T_20)
    assert rho_r == pytest.approx(1.204, rel=1e-3)
    assert abs(rho_r - rho_p) / rho_r < 1e-3


def test_variation_enthalpie_concorde_a_0_5_pourcent(
    reel: AirReel, parfait: AirParfait
) -> None:
    dh_r = reel.h(P_ATM, T_20 + 80) - reel.h(P_ATM, T_20)
    dh_p = parfait.h(P_ATM, T_20 + 80) - parfait.h(P_ATM, T_20)
    assert abs(dh_r - dh_p) / dh_r < 5e-3


def test_air_reel_n_est_pas_parfait_a_190_bar(
    reel: AirReel, parfait: AirParfait
) -> None:
    rho_r = reel.rho(190e5, 303.15)
    rho_p = parfait.rho(190e5, 303.15)
    ecart = abs(rho_r - rho_p) / rho_r
    assert 0.01 < ecart < 0.10


@pytest.mark.parametrize("modele", ["reel", "parfait"])
def test_aller_retour_T_de_rho_u(
    modele: str, reel: AirReel, parfait: AirParfait
) -> None:
    air = reel if modele == "reel" else parfait
    for p, T in [(P_ATM, T_20), (50e5, 330.0), (190e5, 300.0)]:
        rho = air.rho(p, T)
        u = air.u_de_rho_T(rho, T)
        assert air.T_de_rho_u(rho, u, T + 40.0) == pytest.approx(T, abs=1e-3)
        assert air.p_de_rho_T(rho, T) == pytest.approx(p, rel=1e-6)
        assert air.T_de_p_rho(p, rho) == pytest.approx(T, rel=1e-6)


@pytest.mark.parametrize("modele", ["reel", "parfait"])
def test_aller_retour_T_de_p_h(
    modele: str, reel: AirReel, parfait: AirParfait
) -> None:
    air = reel if modele == "reel" else parfait
    h = air.h(35e5, 400.0)
    assert air.T_de_p_h(35e5, h) == pytest.approx(400.0, rel=1e-6)


def test_etat_complet(reel: AirReel) -> None:
    e = reel.etat(P_ATM, T_20)
    assert e.rho == pytest.approx(reel.rho(P_ATM, T_20))
    assert e.h == pytest.approx(reel.h(P_ATM, T_20))


def test_gaz_parfait_cp_moins_cv_egale_R(parfait: AirParfait) -> None:
    assert parfait.cp(P_ATM, T_20) - parfait.cv == pytest.approx(parfait.R)
