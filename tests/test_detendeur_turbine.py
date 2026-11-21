"""Tests du détendeur et de la turbine (phase 2)."""

import pytest

from caes.detendeur import (
    CoefficientsCheayb,
    Detendeur,
    detente_cheayb,
    detente_isenthalpique,
)
from caes.proprietes import AirParfait, AirReel
from caes.registre import Registre
from caes.turbine import EtageTurbine, Turbine, detendre_etage


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def reel() -> AirReel:
    return AirReel()


@pytest.fixture(scope="module")
def parfait(registre: Registre) -> AirParfait:
    return AirParfait.depuis_registre(registre)


@pytest.fixture(scope="module")
def cheayb(registre: Registre) -> CoefficientsCheayb:
    r = registre
    return CoefficientsCheayb(
        a1=r.si("detendeur.cheayb.a1"), a2=r.si("detendeur.cheayb.a2"),
        a3=r.si("detendeur.cheayb.a3"), a4=r.si("detendeur.cheayb.a4"),
        b1=r.si("detendeur.cheayb.b1"), b2=r.si("detendeur.cheayb.b2"),
        b3=r.si("detendeur.cheayb.b3"), b4=r.si("detendeur.cheayb.b4"),
    )


@pytest.fixture(scope="module")
def deprag(registre: Registre) -> Turbine:
    etages = []
    for i in (1, 2, 3):
        pre = f"turbine.etage{i}."
        etages.append(
            EtageTurbine(
                p_entree_pa=registre.si(pre + "pression_entree"),
                p_sortie_pa=registre.si(pre + "pression_sortie"),
                indice_polytropique=registre.si(pre + "indice_polytropique"),
                rendement_mecanique=registre.si(pre + "rendement_mecanique"),
                rendement_electrique=registre.si(
                    pre + "rendement_electrique"
                ),
                T_entree_cible_K=registre.si(pre + "temperature_entree"),
            )
        )
    return Turbine(
        etages=tuple(etages),
        debit_massique_kg_s=registre.si("turbine.etage1.debit_massique"),
    )


# --- Détendeur ---------------------------------------------------------


def test_isenthalpique_gaz_parfait_ne_change_pas_T(
    parfait: AirParfait,
) -> None:
    r = detente_isenthalpique(parfait, 190e5, 328.15, 35e5)
    assert r.T_out_K == pytest.approx(328.15)
    assert r.dh == pytest.approx(0.0)


def test_isenthalpique_air_reel_refroidit(reel: AirReel) -> None:
    r = detente_isenthalpique(reel, 190e5, 328.15, 35e5)
    assert r.dh == pytest.approx(0.0, abs=1e-6 * abs(r.h_in))
    # effet Joule-Thomson : l'air se refroidit de quelques dizaines de K
    assert 5.0 < 328.15 - r.T_out_K < 60.0


def test_cheayb_coherent_avec_isenthalpique(
    reel: AirReel, cheayb: CoefficientsCheayb
) -> None:
    """Les deux modèles ont un MAPE < 0,4 % chez Dormoy : ils doivent
    rester à quelques kelvins l'un de l'autre."""
    for p_in, T_in in [(100e5, 300.0), (150e5, 320.0), (190e5, 328.15)]:
        iso = detente_isenthalpique(reel, p_in, T_in, 35e5)
        ch = detente_cheayb(reel, cheayb, p_in, T_in, 35e5)
        assert ch.T_out_K < T_in
        assert abs(ch.T_out_K - iso.T_out_K) < 8.0


def test_cheayb_signale_hors_validite(
    reel: AirReel, cheayb: CoefficientsCheayb
) -> None:
    assert detente_cheayb(reel, cheayb, 190e5, 328.0, 35e5).hors_validite
    assert not detente_cheayb(reel, cheayb, 100e5, 328.0, 35e5).hors_validite


def test_detendeur_arret_et_consigne(reel: AirReel) -> None:
    d = Detendeur(p_consigne_pa=35e5, ecart_min_pa=15e5)
    assert d.p_arret_pa == 50e5
    assert d.peut_fonctionner(50e5)
    assert not d.peut_fonctionner(49.9e5)
    r = d.detendre(reel, 120e5, 320.0)
    assert r.p_out_pa == 35e5
    with pytest.raises(ValueError):
        d.detendre(reel, 30e5, 320.0)
    with pytest.raises(ValueError):
        Detendeur(p_consigne_pa=35e5, ecart_min_pa=15e5, modele="cheayb")
    with pytest.raises(ValueError):
        Detendeur(p_consigne_pa=35e5, ecart_min_pa=15e5, modele="x")


# --- Turbine -----------------------------------------------------------


def test_detente_gaz_parfait_analytique(parfait: AirParfait) -> None:
    n = 1.27
    T_out, w, dh = detendre_etage(parfait, 3e5, 363.15, 1e5, n)
    T_att = 363.15 * (1.0 / 3.0) ** ((n - 1.0) / n)
    assert T_out == pytest.approx(T_att, rel=1e-9)
    assert w == pytest.approx(n / (n - 1.0) * parfait.R * (363.15 - T_out))
    assert dh < 0.0
    assert w > -dh  # n < gamma : la détente « reçoit » de la chaleur


def test_tableau_9_deprag_reproduit(reel: AirReel, deprag: Turbine) -> None:
    """Avec un air arrivant à 130 °C, retrouver les sorties du tableau 9."""
    res = deprag.produire(reel, 403.15)
    T_out_att = (59.2, 20.7, 16.0)
    P_mec_att = (22.1e3, 22.0e3, 23.7e3)
    P_el_att = (20.0e3, 20.1e3, 21.8e3)
    m = deprag.debit_massique_kg_s
    for e, T_a, Pm_a, Pe_a in zip(res, T_out_att, P_mec_att, P_el_att):
        assert e.T_out_K - 273.15 == pytest.approx(T_a, abs=2.5)
        assert m * e.w_mec == pytest.approx(Pm_a, rel=0.03)
        assert m * e.w_el == pytest.approx(Pe_a, rel=0.03)
    assert deprag.puissance_electrique(res) == pytest.approx(61.9e3, rel=0.03)


def test_rechauffage_suivi(reel: AirReel, deprag: Turbine) -> None:
    res = deprag.produire(reel, 293.15)
    assert res[0].q_rechauffage > 0
    assert res[0].source_chaleur == "externe"
    assert res[0].T_in_K == pytest.approx(403.15)
    # étage 2 : sortie étage 1 ≈ 59 °C < 90 °C → réchauffage aussi
    assert res[1].q_rechauffage > 0
    assert res[1].T_in_K == pytest.approx(363.15)
    # pas de réchauffage si l'air arrive déjà plus chaud que la cible
    chaud = deprag.produire(reel, 450.0)
    assert chaud[0].q_rechauffage == 0.0
    assert chaud[0].source_chaleur == ""
    assert chaud[0].T_in_K == 450.0


def test_puissance_thermique_tableau_5(reel: AirReel, deprag: Turbine) -> None:
    """Étages 2 et 3 : 9,6 et 22,5 kW chez Dormoy."""
    res = deprag.produire(reel, 403.15)
    m = deprag.debit_massique_kg_s
    assert m * res[1].q_rechauffage == pytest.approx(9.6e3, rel=0.12)
    assert m * res[2].q_rechauffage == pytest.approx(22.5e3, rel=0.08)


def test_chaleur_residuelle_petite(reel: AirReel, deprag: Turbine) -> None:
    """Le travail à l'arbre vaut à peu près la chute d'enthalpie."""
    for e in deprag.produire(reel, 403.15):
        assert abs(e.q_residuel) < 0.1 * e.w_mec


def test_erreurs_turbine() -> None:
    with pytest.raises(ValueError):
        EtageTurbine(1e5, 3e5, 1.2, 0.5, 0.9)
    with pytest.raises(ValueError):
        EtageTurbine(3e5, 1e5, 1.0, 0.5, 0.9)
    with pytest.raises(ValueError):
        EtageTurbine(3e5, 1e5, 1.2, 1.5, 0.9)
    with pytest.raises(ValueError):
        Turbine(etages=(), debit_massique_kg_s=0.3)
