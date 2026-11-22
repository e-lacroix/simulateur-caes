"""Tests des modèles de la bibliothèque (phase 7) : bilans, cas limites,
avertissements hors du domaine de validité."""

import math

import pytest

from caes.ambiance import Ambiance
from caes.composants import (
    Attente,
    Compresseur,
    Contexte,
    Detente,
    EtatAir,
    Refroidisseur,
    ReservoirAir,
    Secheur,
    StockageChaleur,
    Turbine,
)
from caes.composants.compresseur.rendement import (
    comprimer_isentropique,
    comprimer_polytropique_rendement,
)
from caes.composants.isolation import Isolant
from caes.composants.turbine.flugel import (
    PointNominal,
    debit_stodola,
    p_entree_pour_debit,
    rendement_relatif,
    resoudre_debit_glissant,
)
from caes.composants.turbine.rendement import (
    detendre_isentropique,
    detendre_polytropique_rendement,
)
from caes.proprietes import AirParfait, air_par_defaut
from caes.registre import Registre


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


@pytest.fixture(scope="module")
def ctx() -> Contexte:
    amb = Ambiance(T_amb_K=293.15, p_amb_pa=101325.0, humidite_relative=0.5,
                   T_aspiration_K=293.15)
    return Contexte(air_par_defaut(), amb, 0.0, 10.0, p_refoulement_pa=100e5)


# --- compression -----------------------------------------------------------


def test_isentropique_rendement_1_est_reversible(registre: Registre) -> None:
    air = AirParfait.depuis_registre(registre)
    r = comprimer_isentropique(air, 1e5, 293.15, 4.0, 1.0)
    gamma = air.gamma(1e5, 293.15)
    assert r.T_out_K == pytest.approx(293.15 * 4.0 ** ((gamma - 1) / gamma),
                                      rel=1e-6)
    assert r.q_poly == 0.0 and r.w_pol == pytest.approx(r.dh)
    r2 = comprimer_isentropique(air, 1e5, 293.15, 4.0, 0.86)
    assert r2.w_pol == pytest.approx(r.w_pol / 0.86, rel=1e-9)
    assert r2.T_out_K > r.T_out_K


def test_polytropique_rendement_coincide_avec_isentropique_a_1(
    registre: Registre,
) -> None:
    air = AirParfait.depuis_registre(registre)
    a = comprimer_isentropique(air, 1e5, 300.0, 3.0, 1.0)
    b = comprimer_polytropique_rendement(air, 1e5, 300.0, 3.0, 1.0)
    assert a.T_out_K == pytest.approx(b.T_out_K, rel=1e-9)
    c = comprimer_polytropique_rendement(air, 1e5, 300.0, 3.0, 0.88)
    assert c.T_out_K > a.T_out_K and c.w_pol > a.w_pol
    with pytest.raises(ValueError):
        comprimer_polytropique_rendement(air, 1e5, 300.0, 3.0, 1.2)


def test_isotherme_est_la_borne_inferieure(ctx: Contexte) -> None:
    base = {"debit_massique_aspire": 0.05, "rendement_electrique": 1.0,
            "rendement_mecanique": 1.0,
            "etages": [{"rapport_pression": 3.0}, {}, {}]}
    iso = Compresseur("c", {**base, "modele": "isotherme"})
    isen = Compresseur("c", {**base, "modele": "isentropique",
                             "rendement_isentropique": 1.0})
    poly = Compresseur("c", {**base, "modele": "polytropique_rendement",
                             "rendement_polytropique": 0.88})
    travaux = []
    for comp in (iso, isen, poly):
        comp.preparer(50e5, ctx.p_amb_pa)
        ctx.p_refoulement_pa = comp.p_chaine_pa
        etat = EtatAir(ctx.p_amb_pa, 293.15, 0.05)
        W = 0.0
        for e in comp.etages:
            etat, flux = e.pas(etat, ctx)
            W += flux.W_pol_w
        assert etat.p_abs_pa == pytest.approx(comp.p_chaine_pa, rel=1e-6)
        travaux.append(W)
    assert travaux[0] < travaux[1] < travaux[2]
    assert any("borne" in m for m in iso.verifier_validite())


def test_etage_a_T_sortie_visee_et_etage_inactif(ctx: Contexte) -> None:
    comp = Compresseur("c", {
        "modele": "isentropique", "debit_massique_aspire": 0.05,
        "rendement_electrique": 0.98, "rendement_mecanique": 0.99,
        "rendement_isentropique": 0.86,
        "etages": [{"T_sortie": 473.15}, {"T_sortie": 473.15}, {}]})
    comp.preparer(60e5, ctx.p_amb_pa)
    ctx.p_refoulement_pa = comp.p_chaine_pa
    etat = EtatAir(ctx.p_amb_pa, 308.15, 0.05)
    etat, _ = comp.etage(1).pas(etat, ctx)
    assert etat.T_K == pytest.approx(473.15, abs=0.01)
    etat = etat.remplacer(T_K=308.15)
    etat, _ = comp.etage(2).pas(etat, ctx)
    assert etat.T_K == pytest.approx(473.15, abs=0.01)
    etat, _ = comp.etage(3).pas(etat.remplacer(T_K=308.15), ctx)
    assert etat.p_abs_pa == pytest.approx(comp.p_chaine_pa, rel=1e-6)
    # pression déjà atteinte : le dernier étage ne fait rien
    comp.preparer(2e5, ctx.p_amb_pa)
    e3 = comp.etage(3)
    etat, flux = e3.pas(EtatAir(5e5, 320.0, 0.05), ctx)
    assert not e3.actif and abs(flux.W_pol_w) < 1e-6
    assert any("inactif" in a.message for a in comp.avertissements)


# --- refroidissement, séchage, réservoir -----------------------------------


def test_refroidisseur_pincement_et_perte_de_charge(ctx: Contexte) -> None:
    r = Refroidisseur("r", {"modele": "pincement", "pincement": 20.0,
                            "perte_de_charge": 0.4e5,
                            "T_seuil_chaleur_utile": 403.15})
    e_out, flux = r.pas(EtatAir(10e5, 450.0, 0.05), ctx)
    assert e_out.T_K == pytest.approx(293.15 + 20.0, abs=0.2)
    assert e_out.p_abs_pa == pytest.approx(9.6e5)
    assert flux.Q_retire_w > 0 and 0 < flux.resultat.q_sup_seuil < (
        flux.resultat.q)
    # air déjà froid : rien ne change (pas de réchauffage symétrique)
    e2, f2 = r.pas(EtatAir(10e5, 300.0, 0.05), ctx)
    assert e2.T_K == pytest.approx(300.0, abs=0.2) and f2.Q_retire_w == 0.0
    mauvais = Refroidisseur("r", {"modele": "pincement", "pincement": -1.0})
    assert any("négatif" in m for m in mauvais.verifier_validite())


def test_secheur_aucun_et_reservoir_adiabatique(ctx: Contexte) -> None:
    s = Secheur("s", {"modele": "aucun"})
    e = EtatAir(190e5, 320.0, 0.052)
    assert s.pas(e, ctx)[0] == e
    res = ReservoirAir("res", {"modele": "adiabatique", "volume": 1.0,
                               "surface": 5.0, "surpression_entree": 2e5})
    assert res.surpression_entree_pa == 2e5
    assert any("caverne" in m for m in res.verifier_validite())
    res.initialiser(ctx.air, 10e5, 293.15)
    U0 = res.energie_interne_j
    H = 0.0
    froid = Contexte(ctx.air, Ambiance(250.0, 101325.0, 0.5, 250.0), 0.0,
                     10.0)
    for _ in range(20):
        entree = EtatAir(50e5, 400.0, 0.01)
        H += 0.01 * 10.0 * ctx.air.h(50e5, 400.0)
        f = res.remplir(froid, entree)
        assert f["q_perte_w"] == 0.0
    assert res.energie_interne_j - U0 == pytest.approx(H, rel=1e-9)


# --- détente et turbine ----------------------------------------------------


def test_detente_isentropique_et_polytropique(registre: Registre) -> None:
    air = AirParfait.depuis_registre(registre)
    T1, w1, dh1 = detendre_isentropique(air, 40e5, 403.15, 11.5e5, 1.0)
    T2, w2, _ = detendre_polytropique_rendement(air, 40e5, 403.15, 11.5e5,
                                                1.0)
    assert T1 == pytest.approx(T2, rel=1e-9) and dh1 == pytest.approx(-w1)
    T3, w3, _ = detendre_isentropique(air, 40e5, 403.15, 11.5e5, 0.9)
    assert w3 == pytest.approx(0.9 * w1, rel=1e-9) and T3 > T1
    with pytest.raises(ValueError):
        detendre_isentropique(air, 10e5, 400.0, 20e5, 0.9)


def test_stodola_et_flugel() -> None:
    pn = PointNominal(40e5, 11.5e5, 403.15, 0.321)
    assert debit_stodola(pn, 40e5, 11.5e5, 403.15) == pytest.approx(0.321)
    G = debit_stodola(pn, 80e5, 11.5e5, 403.15)
    assert 1.9 * 0.321 < G < 2.1 * 0.321
    assert p_entree_pour_debit(pn, G, 11.5e5, 403.15) == pytest.approx(80e5)
    assert debit_stodola(pn, 40e5, 11.5e5, 500.0) < 0.321
    assert rendement_relatif(1.0, 1.0, 0.3) == pytest.approx(1.0)
    assert rendement_relatif(0.5, 1.0, 0.3) < 1.0
    assert rendement_relatif(3.0, 1.0, 0.3) < 1.0
    assert rendement_relatif(1e-3, 1.0, 0.3) >= 0.05
    pts = [PointNominal(40e5, 11.5e5, 403.15, 0.321),
           PointNominal(11e5, 3.5e5, 363.15, 0.321),
           PointNominal(3e5, 1e5, 363.15, 0.321)]
    G, p_ins = resoudre_debit_glissant(pts, [403.15, 363.15, 363.15], 40e5,
                                       1e5)
    assert p_ins[0] == pytest.approx(40e5, rel=1e-6)
    assert G == pytest.approx(0.321, rel=0.05)
    G2, p2 = resoudre_debit_glissant(pts, [403.15, 363.15, 363.15], 190e5,
                                     1e5)
    assert G2 > 3 * 0.321 and p2[1] > 11e5


def test_turbine_isentropique_accepte_pression_variable(
    ctx: Contexte,
) -> None:
    t = Turbine("t", {
        "modele": "isentropique", "debit_massique": 0.3,
        "rendement_isentropique": 0.9, "rendement_mecanique": 0.99,
        "rendement_electrique": 0.98,
        "etages": [{"p_sortie": 11.5e5, "T_entree_cible": 403.15},
                   {"p_entree": 11e5, "p_sortie": 3.5e5}]})
    assert t.pression_entree_variable and not t.debit_variable
    e_bas, f_bas = t.etage(1).pas(EtatAir(40e5, 403.15, 0.3), ctx)
    e_haut, f_haut = t.etage(1).pas(EtatAir(80e5, 403.15, 0.3), ctx)
    assert f_haut.W_el_produit_w > f_bas.W_el_produit_w
    assert e_haut.T_K < e_bas.T_K
    # étage inactif si la pression est déjà au niveau de la sortie
    e_in, f_in = t.etage(1).pas(EtatAir(11.5e5, 403.15, 0.3), ctx)
    assert f_in.W_el_produit_w == 0.0


def test_detente_pression_glissante(ctx: Contexte) -> None:
    d = Detente("d", {"modele": "pression_glissante", "p_min": 55e5})
    assert d.glissante and d.p_arret_pa == 55e5 and d.peut_fonctionner(60e5)
    assert not d.peut_fonctionner(50e5)
    e = EtatAir(150e5, 300.0, 0.3)
    e2, f = d.pas(e, ctx)
    assert e2 == e and f.resultat.dh == 0.0
    assert d.p_sortie_pour(123e5) == 123e5


# --- stockage à deux réservoirs, isolation, attente -------------------------


def test_deux_reservoirs_huile_bilan(ctx: Contexte) -> None:
    st = StockageChaleur("huile", {"modele": "huile_deux_reservoirs",
                                   "masse": 500.0, "cp": 1494.0,
                                   "pincement": 10.0})
    st.initialiser(293.15)
    assert st.physique and st.energie_stockee_j(293.15) == 0.0
    Q_in = 0.0
    for _ in range(100):
        e_out, flux = st.charger_air(EtatAir(12e5, 450.0, 0.05), ctx)
        Q_in += flux.Q_retire_w * ctx.dt_s
        assert e_out.T_K == pytest.approx(293.15 + 10.0, abs=1e-6)
    assert st.energie_stockee_j(293.15) == pytest.approx(Q_in, rel=1e-9)
    assert st.reservoirs is not None
    assert st.reservoirs.T_chaud_K == pytest.approx(440.0)
    assert st.exergie_j(293.15) > 0
    Q_out = 0.0
    for _ in range(50):
        e_r, f_r = st.rechauffer(EtatAir(11e5, 270.0, 0.05), ctx, 363.15)
        Q_out += f_r.Q_ajoute_w * ctx.dt_s
        assert e_r.T_K == pytest.approx(363.15, abs=1e-6)
        assert f_r.source == "huile"
    assert st.energie_stockee_j(293.15) == pytest.approx(Q_in - Q_out,
                                                         rel=1e-9)
    # vider le réservoir chaud : la cible n'est plus atteinte
    for _ in range(2000):
        e_r, f_r = st.rechauffer(EtatAir(11e5, 270.0, 0.05), ctx, 363.15)
    assert e_r.T_K < 363.15
    assert any("vide" in a.message for a in st.avertissements)
    assert st.reservoirs.m_chaud_kg == pytest.approx(0.0, abs=1e-9)


def test_eau_sous_pression_plafonnee_par_l_ebullition(ctx: Contexte) -> None:
    st = StockageChaleur("eau", {"modele": "eau_sous_pression",
                                 "masse": 300.0, "pression_cuve": 18e5,
                                 "pincement": 10.0, "marge_ebullition": 5.0})
    st.initialiser(293.15)
    T_max = st.fluide.T_max_K
    assert 470.0 < T_max < 485.0  # T_sat(18 bar) ≈ 207 °C, moins 5 K
    assert 4000.0 < st.fluide.cp_j_kgk < 4600.0
    for _ in range(20):
        st.charger_air(EtatAir(12e5, 500.0, 0.05), ctx)
    assert st.reservoirs is not None
    assert st.reservoirs.T_chaud_K == pytest.approx(T_max)
    assert any("plafonn" in a.message for a in st.avertissements)
    assert any("ébullition" in m for m in st.verifier_validite())


def test_isolant_et_pertes_pendant_l_attente(ctx: Contexte,
                                             registre: Registre) -> None:
    iso = Isolant("laine_minerale", 0.2, 0.036, 2.5)
    assert iso.coefficient_global_w_m2k == pytest.approx(
        1.0 / (0.2 / 0.036 + 1.0 / 2.5))
    st = StockageChaleur("cuve", {
        "modele": "gravier", "materiau": "gravier_tola", "volume": 0.2,
        "rapport_hauteur_diametre": 2, "n_cellules": 5,
        "isolation": {"materiau": "laine_minerale", "epaisseur": 0.2}},
        registre=registre)
    assert st.coefficient_perte == pytest.approx(
        iso.coefficient_global_w_m2k, rel=1e-9)
    st.initialiser(450.0)
    E0 = st.energie_stockee_j(293.15)
    att = Attente("a", {"duree": 14 * 86400.0, "dt": 3600.0})
    c = Contexte(ctx.air, ctx.ambiance, 0.0, 0.0)
    pertes = att.executer(c, None, [st])
    assert 0 < pertes["Q_perte_cuves_j"] < E0
    assert st.energie_stockee_j(293.15) == pytest.approx(
        E0 - pertes["Q_perte_cuves_j"], rel=1e-9)
    # constante de temps : 0,2 m³ de gravier isolé perd beaucoup en 14 j
    assert st.energie_stockee_j(293.15) / E0 < 0.7
    sans = Attente("b", {"modele": "sans_pertes", "duree": 14 * 86400.0})
    st.initialiser(450.0)
    c = Contexte(ctx.air, ctx.ambiance, 0.0, 0.0)
    p2 = sans.executer(c, None, [st])
    assert p2["Q_perte_cuves_j"] == 0.0 and c.t_s == 14 * 86400.0
    assert st.energie_stockee_j(293.15) == pytest.approx(E0)
    assert any("optimiste" in m for m in sans.verifier_validite())
    assert math.isfinite(st.exergie_j(293.15))
