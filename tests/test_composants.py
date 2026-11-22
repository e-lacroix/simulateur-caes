"""Tests de l'interface commune des composants (phase 6)."""

import pytest

from caes.ambiance import Ambiance
from caes.composants import (
    FABRIQUES,
    Attente,
    Contexte,
    ErreurComposant,
    EtatAir,
    Refroidisseur,
    ReservoirAir,
    Secheur,
    StockageChaleur,
)
from caes.composants.secheur import PerteDebit
from caes.proprietes import air_par_defaut
from caes.registre import Registre


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def ctx() -> Contexte:
    amb = Ambiance(T_amb_K=293.15, p_amb_pa=101325.0, humidite_relative=0.5,
                   T_aspiration_K=293.15)
    return Contexte(air_par_defaut(), amb, 0.0, 10.0, p_refoulement_pa=100e5)


def test_fabriques_couvrent_les_huit_fonctions() -> None:
    attendu = {"compresseur", "refroidisseur", "secheur", "perte_debit",
               "reservoir_air", "stockage_chaleur", "detente", "turbine",
               "attente"}
    assert set(FABRIQUES) == attendu
    for cls in FABRIQUES.values():
        assert cls.MODELES, cls


def test_modele_inconnu_et_parametre_manquant() -> None:
    with pytest.raises(ErreurComposant):
        Secheur("s", {"modele": "inconnu", "efficacite": 0.8})
    with pytest.raises(ErreurComposant):
        Secheur("s", {})


def test_etat_air_est_immuable_et_remplacable() -> None:
    e = EtatAir(1e5, 300.0, 0.05)
    e2 = e.remplacer(T_K=310.0)
    assert e.T_K == 300.0 and e2.T_K == 310.0
    with pytest.raises(AttributeError):
        e.T_K = 1.0  # type: ignore[misc]


def test_refroidisseur_puise_son_froid_dans_l_ambiance(
    ctx: Contexte,
) -> None:
    r = Refroidisseur("r", {"efficacite": 0.9})
    e_in = EtatAir(3e5, 450.0, 0.05)
    e_out, flux = r.pas(e_in, ctx)
    assert e_out.T_K == pytest.approx(450.0 - 0.9 * (450.0 - 293.15))
    assert flux.Q_retire_w > 0 and flux.destination == "ambiant"
    assert e_out.m_dot_kg_s == e_in.m_dot_kg_s
    froid = Contexte(ctx.air, Ambiance(253.15, 101325.0, 0.5, 253.15), 0.0,
                     10.0, p_refoulement_pa=100e5)
    e_hiver, _ = r.pas(e_in, froid)
    assert e_hiver.T_K < e_out.T_K


def test_secheur_et_perte_debit_conservent_p_et_T(ctx: Contexte) -> None:
    s = Secheur("s", {"efficacite": 0.81})
    p = PerteDebit("p", {"fraction_conservee": 0.83})
    e = EtatAir(190e5, 320.0, 0.052)
    e1, f1 = p.pas(e, ctx)
    e2, f2 = s.pas(e1, ctx)
    assert e2.m_dot_kg_s == pytest.approx(0.052 * 0.83 * 0.81)
    assert (e2.p_abs_pa, e2.T_K) == (e.p_abs_pa, e.T_K)
    assert f1.m_dot_perdu_kg_s + f2.m_dot_perdu_kg_s == pytest.approx(
        0.052 - e2.m_dot_kg_s)
    with pytest.raises(ErreurComposant):
        PerteDebit("p", {"fraction_conservee": 1.5})


def test_reservoir_bilan_de_masse(ctx: Contexte) -> None:
    res = ReservoirAir("res", {"modele": "K_global", "volume": 1.0,
                               "surface": 5.0, "K_global": 0.0})
    res.initialiser(ctx.air, 10e5, 293.15)
    m0 = res.masse_kg
    for _ in range(10):
        res.remplir(ctx, EtatAir(50e5, 300.0, 0.01))
    assert res.masse_kg == pytest.approx(m0 + 10 * 10.0 * 0.01)
    assert res.p_abs_pa > 10e5
    res.vider(ctx, 0.5)
    assert res.masse_kg == pytest.approx(m0 + 1.0 - 5.0)
    assert res.etat_sortie(0.1).p_abs_pa == res.p_abs_pa


def test_stockage_gravier_charge_et_rechauffe(ctx: Contexte,
                                              registre: Registre) -> None:
    st = StockageChaleur("cuve", {"modele": "gravier",
                                  "materiau": "gravier_tola", "volume": 0.2,
                                  "rapport_hauteur_diametre": 2,
                                  "n_cellules": 10}, registre=registre)
    st.initialiser(293.15)
    assert st.a_un_etat
    e = EtatAir(12e5, 450.0, 0.05)
    Q = 0.0
    for _ in range(200):
        e_out, flux = st.charger_air(e, ctx)
        Q += flux.Q_retire_w * ctx.dt_s
        assert e_out.T_K <= e.T_K
    assert st.energie_stockee_j(293.15) == pytest.approx(Q, rel=1e-6)
    assert st.exergie_j(293.15) > 0
    froid = EtatAir(11e5, 270.0, 0.05)
    e_r, flux_r = st.rechauffer(froid, ctx, 363.15)
    assert 363.15 - 0.5 <= e_r.T_K <= 363.15 + 1e-6
    assert flux_r.source == "cuve" and flux_r.Q_ajoute_w > 0
    with pytest.raises(ErreurComposant):
        st.deposer(1.0)


def test_source_externe_et_huile_ideale(ctx: Contexte) -> None:
    ext = StockageChaleur("chaudiere", {"modele": "source_externe"})
    assert not ext.a_un_etat
    e, f = ext.rechauffer(EtatAir(40e5, 280.0, 0.3), ctx, 403.15)
    assert e.T_K == 403.15 and f.source == "externe"
    e2, f2 = ext.rechauffer(EtatAir(40e5, 410.0, 0.3), ctx, 403.15)
    assert e2.T_K == 410.0 and f2.Q_ajoute_w == 0.0
    huile = StockageChaleur("huile", {"modele": "huile_ideale",
                                      "appoint_externe": True})
    huile.initialiser(293.15)
    huile.deposer(4e5)  # un pas de 10 s à 0,3 kg/s en demande ≈ 3,7e5 J
    e3, f3 = huile.rechauffer(EtatAir(40e5, 280.0, 0.3), ctx, 403.15)
    assert f3.source == "huile" and huile.reserve_j < 4e5
    e4, f4 = huile.rechauffer(EtatAir(40e5, 280.0, 0.3), ctx, 403.15)
    assert f4.source == "externe"
    assert any("épuisée" in a.message for a in huile.avertissements)


def test_attente_fait_passer_le_temps(ctx: Contexte,
                                      registre: Registre) -> None:
    att = Attente("att", {"duree": 7200.0, "dt": 600.0})
    res = ReservoirAir("res", {"modele": "K_global", "volume": 1.0,
                               "surface": 5.0, "K_global": 2.0})
    res.initialiser(ctx.air, 100e5, 330.0)
    st = StockageChaleur("cuve", {"modele": "gravier",
                                  "materiau": "gravier_tola", "volume": 0.2,
                                  "rapport_hauteur_diametre": 2,
                                  "n_cellules": 5, "coefficient_perte": 1.0},
                         registre=registre)
    st.initialiser(400.0)
    E0 = st.energie_stockee_j(293.15)
    c = Contexte(ctx.air, ctx.ambiance, 100.0, 0.0)
    pertes = att.executer(c, res, [st])
    assert c.t_s == pytest.approx(7300.0)
    assert pertes["Q_perte_cuves_j"] > 0
    assert res.T_K < 330.0
    assert st.energie_stockee_j(293.15) == pytest.approx(
        E0 - pertes["Q_perte_cuves_j"], rel=1e-9)
