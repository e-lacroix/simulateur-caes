"""Tests du lit de gravier (phase 4)."""

import math

import numpy as np
import pytest

from caes.lit_gravier import (
    Correlations,
    LitGravier,
    coefficient_echange,
    perte_de_charge_ergun,
    solution_schumann,
)
from caes.materiaux import Materiau, charger_materiau
from caes.proprietes import AirParfait, AirReel
from caes.registre import Registre

T0 = 293.15


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def gravier(registre: Registre) -> Materiau:
    return charger_materiau("gravier_tola", registre)


@pytest.fixture(scope="module")
def parfait(registre: Registre) -> AirParfait:
    return AirParfait.depuis_registre(registre)


@pytest.fixture(scope="module")
def reel() -> AirReel:
    return AirReel()


def test_materiau(gravier: Materiau) -> None:
    assert gravier.capacite_volumique_lit_j_m3k == pytest.approx(
        0.7 * 2750 * 900
    )
    assert gravier.surface_specifique_m2_m3 == pytest.approx(6 * 0.7 / 0.03)
    with pytest.raises(ValueError):
        gravier.avec(porosite=1.2)
    fin = gravier.avec(diametre_particule_m=0.01)
    assert fin.surface_specifique_m2_m3 == pytest.approx(
        3 * gravier.surface_specifique_m2_m3
    )


def test_wakao_et_jeffreson(reel: AirReel, gravier: Materiau) -> None:
    corr = Correlations()
    h, Re, Bi = coefficient_echange(reel, gravier, corr, 3e5, 400.0, 0.1)
    assert corr.dans_validite(Re)
    assert 10.0 < h < 200.0
    assert Bi > 0.0
    # Nu augmente avec Re ; Nu(Re → 0) = 2
    assert corr.nusselt(0.0, 0.71) == 2.0
    assert corr.nusselt(1000.0, 0.71) > corr.nusselt(100.0, 0.71)
    h2, Re2, _ = coefficient_echange(reel, gravier, corr, 3e5, 400.0, 0.2)
    assert Re2 == pytest.approx(2 * Re, rel=1e-9)
    assert h2 > h


def test_ergun_croit_avec_la_vitesse_et_decroit_avec_d(
    reel: AirReel, gravier: Materiau
) -> None:
    corr = Correlations()
    dp1 = perte_de_charge_ergun(reel, gravier, corr, 3e5, 400.0, 0.1, 2.0)
    dp2 = perte_de_charge_ergun(reel, gravier, corr, 3e5, 400.0, 0.2, 2.0)
    assert 2.0 < dp2 / dp1 < 4.0  # entre linéaire et quadratique
    gros = gravier.avec(diametre_particule_m=0.06)
    assert perte_de_charge_ergun(reel, gros, corr, 3e5, 400.0, 0.1, 2.0) < dp1
    dp_long = perte_de_charge_ergun(reel, gravier, corr, 3e5, 400.0, 0.1, 4.0)
    assert dp_long == pytest.approx(2 * dp1)


def test_conservation_de_l_energie(reel: AirReel, gravier: Materiau) -> None:
    """Chaleur cédée par l'air = chaleur stockée + pertes (à 1 % près)."""
    lit = LitGravier(gravier, 0.5, 2.0, n_cellules=30,
                     coefficient_perte_w_m2k=0.5)
    lit.initialiser(T0)
    r = lit.simuler(reel, 10.0, 2 * 3600, 0.05, 443.15, 3e5, T0)
    Q_in = r["Q_air_vers_solide_j"][0]
    assert Q_in > 0
    assert Q_in == pytest.approx(r["dE_stock_j"][0] + r["Q_perte_j"][0],
                                 rel=1e-6)


def test_debit_nul_isolation_parfaite_temperature_constante(
    reel: AirReel, gravier: Materiau
) -> None:
    lit = LitGravier(gravier, 0.5, 2.0, n_cellules=20)
    lit.initialiser(400.0)
    for _ in range(100):
        r = lit.pas(reel, 600.0, 0.0, 300.0, 3e5, T0)
        assert r["Q_air_vers_solide_j"] == 0.0
        assert r["Q_perte_j"] == 0.0
    assert np.allclose(lit.T_s_K, 400.0)


def test_pertes_relaxent_vers_l_ambiant(
    reel: AirReel, gravier: Materiau
) -> None:
    lit = LitGravier(gravier, 0.5, 2.0, n_cellules=10,
                     coefficient_perte_w_m2k=2.0)
    lit.initialiser(400.0)
    E0 = lit.energie_stockee_j(T0)
    for _ in range(200):
        lit.pas(reel, 3600.0, 0.0, 300.0, 3e5, T0)
    assert np.all(lit.T_s_K < 400.0)
    assert np.all(lit.T_s_K > T0)
    assert lit.energie_stockee_j(T0) < 0.5 * E0


def test_conduction_lisse_un_profil(reel: AirReel, gravier: Materiau) -> None:
    lit = LitGravier(gravier, 0.5, 2.0, n_cellules=20)
    profil = np.full(20, T0)
    profil[:10] = 400.0
    lit.initialiser(profil)
    E0 = lit.energie_stockee_j(T0)
    for _ in range(50):
        lit.pas(reel, 3600.0 * 24, 0.0, 300.0, 3e5, T0)
    assert lit.energie_stockee_j(T0) == pytest.approx(E0, rel=1e-9)
    assert lit.T_s_K[0] < 400.0
    assert lit.T_s_K[-1] > T0
    assert np.all(np.diff(lit.T_s_K) <= 1e-9)


def test_convergence_vers_schumann(
    parfait: AirParfait, gravier: Materiau
) -> None:
    """Le maillage raffiné converge vers la solution analytique."""
    h, D, H, m_dot, p, Tin = 50.0, 0.5, 2.0, 0.05, 3e5, 443.15
    cp = parfait.cp(p, 350.0)
    erreurs = []
    for n in (20, 80):
        lit = LitGravier(gravier, D, H, n_cellules=n, h_impose_w_m2k=h,
                         conduction_axiale=False)
        lit.initialiser(T0)
        r = lit.simuler(parfait, 10.0, 4 * 3600, m_dot, Tin, p, T0)
        xi = h * gravier.surface_specifique_m2_m3 * lit.section_m2 * H / (
            m_dot * cp)
        eta = (h * gravier.surface_specifique_m2_m3 * r["t_s"][::40]
               / gravier.capacite_volumique_lit_j_m3k)
        th_num = (r["T_sortie_K"][::40] - T0) / (Tin - T0)
        th_an, _ = solution_schumann(xi, eta)
        erreurs.append(float(np.max(np.abs(th_num - th_an))))
    assert erreurs[1] < 0.01
    assert erreurs[1] < 0.3 * erreurs[0]


def test_convergence_en_maillage(reel: AirReel, gravier: Materiau) -> None:
    """Énergie stockée : moins de 1 % d'écart entre 40 et 80 cellules."""
    E = []
    for n in (40, 80):
        lit = LitGravier(gravier, 0.5, 2.0, n_cellules=n)
        lit.initialiser(T0)
        r = lit.simuler(reel, 20.0, 2 * 3600, 0.05, 443.15, 3e5, T0)
        E.append(r["dE_stock_j"][0])
    assert abs(E[1] - E[0]) / E[1] < 0.01


def test_cuve_bien_melangee_une_cellule(
    reel: AirReel, gravier: Materiau
) -> None:
    lit = LitGravier(gravier, 0.5, 2.0, n_cellules=1)
    lit.initialiser(T0)
    r = lit.simuler(reel, 10.0, 2 * 3600, 0.05, 443.15, 3e5, T0)
    # une seule température : la sortie suit le solide de près
    assert abs(r["T_sortie_K"][-1] - lit.T_s_K[0]) < 1.0
    assert r["dE_stock_j"][0] > 0


def test_front_thermique_plus_net_avec_plus_de_cellules(
    reel: AirReel, gravier: Materiau
) -> None:
    """Avec 1 cellule la sortie monte tout de suite ; avec 40, elle reste
    froide pendant une bonne partie de la charge (front thermique)."""
    sorties = {}
    for n in (1, 40):
        lit = LitGravier(gravier, 0.5, 2.0, n_cellules=n)
        lit.initialiser(T0)
        r = lit.simuler(reel, 10.0, 1800.0, 0.05, 443.15, 3e5, T0)
        sorties[n] = r["T_sortie_K"]
    assert sorties[1][-1] > sorties[40][-1] + 10.0
    assert sorties[40][0] < T0 + 1.0
    assert sorties[40][-1] < T0 + 1.0  # le front n'a pas encore percé


def test_schumann_bornes() -> None:
    th_f, th_s = solution_schumann(0.0, np.array([0.5, 2.0]))
    assert np.allclose(th_f, 1.0)
    th_f, th_s = solution_schumann(5.0, np.array([0.0]))
    assert th_s[0] == pytest.approx(0.0, abs=1e-9)
    th_f, th_s = solution_schumann(2.0, np.array([50.0]))
    assert th_f[0] == pytest.approx(1.0, abs=1e-3)
    assert th_s[0] == pytest.approx(1.0, abs=1e-3)
    assert math.isfinite(th_f[0])
