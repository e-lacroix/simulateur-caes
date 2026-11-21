"""Tests des refroidisseurs NTU et du sécheur (phase 1)."""

import pytest

from caes.proprietes import AirParfait, AirReel
from caes.refroidisseur import Refroidisseur, refroidir
from caes.registre import Registre
from caes.secheur import EtatDebit, Secheur

T_SEUIL = 403.15  # 130 °C


@pytest.fixture(scope="module")
def parfait() -> AirParfait:
    return AirParfait.depuis_registre(Registre.charger())


def test_temperature_de_sortie_ntu(parfait: AirParfait) -> None:
    r = refroidir(parfait, 3e5, 450.0, 293.15, 0.82, T_SEUIL)
    assert r.T_out_K == pytest.approx(450.0 - 0.82 * (450.0 - 293.15))
    assert r.q == pytest.approx(parfait.cp(3e5, 400.0) * (450.0 - r.T_out_K))


def test_efficacite_nulle_et_totale(parfait: AirParfait) -> None:
    aucun = refroidir(parfait, 3e5, 450.0, 293.15, 0.0, T_SEUIL)
    assert aucun.T_out_K == 450.0
    assert aucun.q == 0.0
    total = refroidir(parfait, 3e5, 450.0, 293.15, 1.0, T_SEUIL)
    assert total.T_out_K == pytest.approx(293.15)


def test_chaleur_au_dessus_du_seuil(parfait: AirParfait) -> None:
    r = refroidir(parfait, 3e5, 450.0, 293.15, 0.82, T_SEUIL)
    assert 0.0 < r.q_sup_seuil < r.q
    assert r.q_sup_seuil == pytest.approx(
        parfait.cp(3e5, 420.0) * (450.0 - T_SEUIL)
    )
    froid = refroidir(parfait, 3e5, 390.0, 293.15, 0.82, T_SEUIL)
    assert froid.q_sup_seuil == 0.0
    peu = refroidir(parfait, 3e5, 450.0, 440.0, 0.5, T_SEUIL)
    # la sortie (445 K) reste au-dessus du seuil : tout est « utile »
    assert peu.q_sup_seuil == pytest.approx(peu.q)


def test_efficacite_hors_bornes(parfait: AirParfait) -> None:
    with pytest.raises(ValueError):
        refroidir(parfait, 3e5, 450.0, 293.15, 1.2, T_SEUIL)


def test_air_reel_coherent(parfait: AirParfait) -> None:
    reel = AirReel()
    a = refroidir(reel, 3e5, 450.0, 293.15, 0.82, T_SEUIL)
    b = refroidir(parfait, 3e5, 450.0, 293.15, 0.82, T_SEUIL)
    assert a.q == pytest.approx(b.q, rel=1e-2)


def test_refroidisseur_a_efficacite_variable() -> None:
    r = Refroidisseur(
        efficacite=0.74, efficacite_max=0.85, p_min_pa=66e5, p_max_pa=190e5
    )
    assert r.efficacite_a(10e5) == 0.74
    assert r.efficacite_a(190e5) == 0.85
    assert 0.74 < r.efficacite_a(128e5) < 0.85
    fixe = Refroidisseur(efficacite=0.82)
    assert fixe.efficacite_a(150e5) == 0.82


def test_secheur() -> None:
    s = Secheur(efficacite=0.81)
    assert s.debit_sortie(0.052) == pytest.approx(0.04212)
    assert s.debit_rejete(0.052) + s.debit_sortie(0.052) == pytest.approx(
        0.052
    )
    sortie = s.traiter(EtatDebit(66e5, 320.0, 0.043))
    assert sortie.p_abs_pa == 66e5
    assert sortie.T_K == 320.0
    assert sortie.debit_massique_kg_s == pytest.approx(0.043 * 0.81)


def test_secheur_efficacite_invalide() -> None:
    with pytest.raises(ValueError):
        Secheur(efficacite=0.0)
    with pytest.raises(ValueError):
        Secheur(efficacite=1.3)
