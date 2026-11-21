"""Tests du compresseur polytropique (phase 1)."""

import pytest

from caes.compresseur import (
    Compresseur,
    comprimer_etage,
    interpoler_lineaire,
)
from caes.proprietes import AirParfait, AirReel
from caes.registre import Registre


@pytest.fixture(scope="module")
def parfait() -> AirParfait:
    return AirParfait.depuis_registre(Registre.charger())


@pytest.fixture(scope="module")
def compresseur_dormoy() -> Compresseur:
    return Compresseur(
        indices_polytropiques=(1.35, 1.38, 1.44, 1.52),
        rapports_fixes=(3.25, 3.75),
        rapport_avant_dernier_min=3.54,
        rapport_avant_dernier_max=4.44,
        p_refoulement_min_pa=66e5,
        p_refoulement_max_pa=190e5,
        rendement_mecanique_min=0.69,
        rendement_mecanique_max=0.74,
        rendement_electrique=0.945,
        debit_volumique_aspire_m3_s=172.4 / 3600.0,
        rendement_volumetrique=0.83,
    )


def test_interpolation_bornee() -> None:
    assert interpoler_lineaire(0.0, 1.0, 3.0, 10.0, 20.0) == 10.0
    assert interpoler_lineaire(2.0, 1.0, 3.0, 10.0, 20.0) == 15.0
    assert interpoler_lineaire(9.0, 1.0, 3.0, 10.0, 20.0) == 20.0
    assert interpoler_lineaire(5.0, 2.0, 2.0, 7.0, 8.0) == 7.0


def test_gaz_parfait_temperature_et_travail_analytiques(
    parfait: AirParfait,
) -> None:
    n, beta, T_in, p_in = 1.35, 3.25, 293.15, 101325.0
    et = comprimer_etage(parfait, p_in, T_in, beta, n)
    T_attendu = T_in * beta ** ((n - 1.0) / n)
    w_attendu = n / (n - 1.0) * parfait.R * (T_attendu - T_in)
    assert et.T_out_K == pytest.approx(T_attendu, rel=1e-9)
    assert et.w_pol == pytest.approx(w_attendu, rel=1e-9)
    assert et.p_out_pa == pytest.approx(p_in * beta)


def test_chaleur_rejetee_si_n_inferieur_a_gamma(parfait: AirParfait) -> None:
    gamma = parfait.cp(1e5, 300.0) / parfait.cv
    et = comprimer_etage(parfait, 1e5, 300.0, 3.0, 1.35)
    assert et.q_poly < 0.0
    et_adiab = comprimer_etage(parfait, 1e5, 300.0, 3.0, gamma)
    assert et_adiab.q_poly == pytest.approx(0.0, abs=1e-6 * et_adiab.w_pol)


def test_air_reel_proche_du_gaz_parfait_a_basse_pression(
    parfait: AirParfait,
) -> None:
    reel = AirReel()
    a = comprimer_etage(reel, 101325.0, 293.15, 3.25, 1.35)
    b = comprimer_etage(parfait, 101325.0, 293.15, 3.25, 1.35)
    assert a.T_out_K == pytest.approx(b.T_out_K, rel=2e-3)
    assert a.w_pol == pytest.approx(b.w_pol, rel=5e-3)


def test_erreurs_d_entree(parfait: AirParfait) -> None:
    with pytest.raises(ValueError):
        comprimer_etage(parfait, 1e5, 300.0, 0.5, 1.35)
    with pytest.raises(ValueError):
        comprimer_etage(parfait, 1e5, 300.0, 3.0, 0.9)


def test_cas_limite_isotherme(parfait: AirParfait) -> None:
    """n = 1 : température constante, w = p·v·ln(β) (gaz parfait)."""
    import math

    et = comprimer_etage(parfait, 1e5, 300.0, 3.0, 1.0)
    assert et.T_out_K == 300.0
    assert et.w_pol == pytest.approx(parfait.R * 300.0 * math.log(3.0))
    assert et.dh == pytest.approx(0.0)
    assert et.q_poly == pytest.approx(-et.w_pol)
    presque = comprimer_etage(parfait, 1e5, 300.0, 3.0, 1.01)
    assert presque.w_pol == pytest.approx(et.w_pol, rel=0.01)


def test_rapports_de_pression_dormoy(compresseur_dormoy: Compresseur) -> None:
    c = compresseur_dormoy
    p_amb = 1.01325e5
    for p_ref in (66e5, 100e5, 150e5, 190e5):
        betas = c.rapports_pression(p_amb, p_ref)
        produit = 1.0
        for b in betas:
            produit *= b
        assert produit == pytest.approx(p_ref / p_amb, rel=1e-12)
        assert betas[:2] == (3.25, 3.75)
        assert 3.54 <= betas[2] <= 4.44
        assert betas[3] >= 1.0
    bas = c.rapports_pression(p_amb, 66e5)
    haut = c.rapports_pression(p_amb, 190e5)
    assert bas[2] == pytest.approx(3.54)
    assert bas[3] == pytest.approx(1.52, abs=0.02)
    assert haut[2] == pytest.approx(4.44)
    assert haut[3] == pytest.approx(3.5, abs=0.05)


def test_rapport_dernier_etage_inferieur_a_1_refuse(
    compresseur_dormoy: Compresseur,
) -> None:
    with pytest.raises(ValueError):
        compresseur_dormoy.rapports_pression(1.01325e5, 30e5)


def test_p_refoulement_minimale(compresseur_dormoy: Compresseur) -> None:
    assert compresseur_dormoy.p_refoulement(10e5) == 66e5
    assert compresseur_dormoy.p_refoulement(120e5) == 120e5


def test_rendement_mecanique_dans_la_plage(
    compresseur_dormoy: Compresseur,
) -> None:
    c = compresseur_dormoy
    assert c.rendement_mecanique(10e5) == 0.69
    assert c.rendement_mecanique(190e5) == 0.74
    assert 0.69 < c.rendement_mecanique(128e5) < 0.74


def test_debit_massique_depend_de_la_densite(
    compresseur_dormoy: Compresseur, parfait: AirParfait
) -> None:
    c = compresseur_dormoy
    froid = c.debit_massique_aspire(parfait, 1.01325e5, 258.15)
    chaud = c.debit_massique_aspire(parfait, 1.01325e5, 298.15)
    assert froid > chaud
    assert froid == pytest.approx(0.065, abs=0.002)
    assert chaud == pytest.approx(0.056, abs=0.002)


def test_debit_massique_impose(parfait: AirParfait) -> None:
    c = Compresseur(
        indices_polytropiques=(1.35, 1.38, 1.44, 1.52),
        rapports_fixes=(3.25, 3.75),
        rapport_avant_dernier_min=3.54,
        rapport_avant_dernier_max=4.44,
        p_refoulement_min_pa=66e5,
        p_refoulement_max_pa=190e5,
        rendement_mecanique_min=0.69,
        rendement_mecanique_max=0.74,
        rendement_electrique=0.945,
        debit_volumique_aspire_m3_s=172.4 / 3600.0,
        rendement_volumetrique=0.83,
        debit_massique_aspire_impose_kg_s=0.052,
    )
    assert c.debit_massique_aspire(parfait, 1e5, 300.0) == 0.052


def test_puissance_electrique(compresseur_dormoy: Compresseur) -> None:
    P = compresseur_dormoy.puissance_electrique(0.052, 500e3, 190e5)
    assert P == pytest.approx(0.052 * 500e3 / (0.74 * 0.945))


def test_nombre_de_rapports_fixes_incoherent() -> None:
    with pytest.raises(ValueError):
        Compresseur(
            indices_polytropiques=(1.35, 1.38, 1.44, 1.52),
            rapports_fixes=(3.25,),
            rapport_avant_dernier_min=3.54,
            rapport_avant_dernier_max=4.44,
            p_refoulement_min_pa=66e5,
            p_refoulement_max_pa=190e5,
            rendement_mecanique_min=0.69,
            rendement_mecanique_max=0.74,
            rendement_electrique=0.945,
            debit_volumique_aspire_m3_s=0.05,
            rendement_volumetrique=0.83,
        )
