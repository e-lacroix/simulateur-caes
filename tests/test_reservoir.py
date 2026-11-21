"""Tests du réservoir équivalent (phase 1)."""

import math

import pytest

from caes.proprietes import AirParfait, AirReel
from caes.registre import Registre
from caes.reservoir import Reservoir


@pytest.fixture(scope="module")
def parfait() -> AirParfait:
    return AirParfait.depuis_registre(Registre.charger())


def test_conservation_de_la_masse(parfait: AirParfait) -> None:
    res = Reservoir(volume_m3=5.86, surface_m2=65.5, K_global_w_m2k=8.8)
    res.initialiser(parfait, 1.01325e5, 293.15)
    m0 = res.masse_kg
    h_in = parfait.h(66e5, 320.0)
    entree = 0.0
    for _ in range(600):
        res.pas(parfait, 10.0, 0.035, h_in, 293.15, debit_sortie_kg_s=0.005)
        entree += (0.035 - 0.005) * 10.0
    assert res.masse_kg - m0 == pytest.approx(entree, rel=1e-9)
    assert res.p_abs_pa == pytest.approx(
        parfait.p_de_rho_T(res.rho, res.T_K)
    )


def test_remplissage_adiabatique_tend_vers_gamma_T_in(
    parfait: AirParfait,
) -> None:
    """Remplir un réservoir vide sans pertes : T → γ·T_in (gaz parfait)."""
    res = Reservoir(volume_m3=1.0, surface_m2=10.0, K_global_w_m2k=0.0)
    res.initialiser(parfait, 100.0, 300.0)  # presque vide
    h_in = parfait.h(1e6, 300.0)
    while res.p_abs_pa < 50e5:
        res.pas(parfait, 1.0, 0.1, h_in, 300.0)
    gamma = parfait.cp(1e5, 300.0) / parfait.cv
    assert res.T_K == pytest.approx(gamma * 300.0, rel=2e-3)


def test_refroidissement_exponentiel_sans_debit(parfait: AirParfait) -> None:
    res = Reservoir(volume_m3=5.86, surface_m2=65.5, K_global_w_m2k=8.8)
    res.initialiser(parfait, 190e5, 353.15)
    tau = res.masse_kg * parfait.cv / (8.8 * 65.5)
    T_amb = 293.15
    t = 0.0
    while t < 2 * tau:
        res.pas(parfait, 60.0, 0.0, 0.0, T_amb)
        t += 60.0
    attendu = T_amb + (353.15 - T_amb) * math.exp(-t / tau)
    assert res.T_K == pytest.approx(attendu, abs=0.2)


def test_stable_quand_dt_depasse_la_constante_de_temps(
    parfait: AirParfait,
) -> None:
    """Début de charge : masse minuscule, τ ≈ 10 s, dt = 60 s."""
    res = Reservoir(volume_m3=5.86, surface_m2=65.5, K_global_w_m2k=8.8)
    res.initialiser(parfait, 1.01325e5, 330.0)
    for _ in range(50):
        res.pas(parfait, 60.0, 0.0, 0.0, 293.15)
        assert res.T_K >= 293.15 - 1e-6
    assert res.T_K == pytest.approx(293.15, abs=0.01)


def test_modele_paroi_conserve_l_energie(parfait: AirParfait) -> None:
    """Sans échange extérieur, air + paroi conservent l'énergie entrée."""
    res = Reservoir(
        volume_m3=5.86,
        surface_m2=65.5,
        modele_thermique="paroi",
        h_int_w_m2k=25.42,
        h_ext_w_m2k=0.0,
        capacite_paroi_j_k=1.767e6,
    )
    res.initialiser(parfait, 50e5, 293.15)
    U0 = res.energie_interne_j
    Tp0 = res.T_paroi_K
    h_in = parfait.h(66e5, 320.0)
    E_in = 0.0
    for _ in range(360):
        res.pas(parfait, 10.0, 0.035, h_in, 293.15)
        E_in += 0.035 * h_in * 10.0
    dU_air = res.energie_interne_j - U0
    dU_paroi = 1.767e6 * (res.T_paroi_K - Tp0)
    assert dU_air + dU_paroi == pytest.approx(E_in, rel=1e-6)
    assert res.T_paroi_K > Tp0


def test_air_reel_remplissage_coherent() -> None:
    reel = AirReel()
    res = Reservoir(volume_m3=5.86, surface_m2=65.5, K_global_w_m2k=8.8)
    res.initialiser(reel, 1.01325e5, 293.15)
    h_in = reel.h(66e5, 316.0)
    for _ in range(360):
        res.pas(reel, 10.0, 0.035, h_in, 293.15)
    assert res.p_abs_pa > 1.01325e5
    assert 280.0 < res.T_K < 400.0
    assert res.p_abs_pa == pytest.approx(reel.p_de_rho_T(res.rho, res.T_K))


def test_erreurs_de_configuration() -> None:
    with pytest.raises(ValueError):
        Reservoir(volume_m3=1.0, surface_m2=1.0, modele_thermique="x")
    with pytest.raises(ValueError):
        Reservoir(volume_m3=1.0, surface_m2=1.0, modele_thermique="paroi")
