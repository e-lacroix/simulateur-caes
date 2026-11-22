"""Tests de l'air humide, du séparateur et du sécheur (phase 9)."""

import math

import pytest

from caes.ambiance import Ambiance
from caes.composants import (
    Contexte,
    EtatAir,
    Flux,
    Refroidisseur,
    ReservoirAir,
    Secheur,
    Turbine,
)
from caes.composants.humidite import (
    P_MAX_VALIDITE_PA,
    enthalpie_condensation,
    equilibrer,
    mettre_a_l_equilibre,
    point_de_rosee,
    w_de_humidite_relative,
    w_saturation,
)
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


def test_saturation_et_point_de_rosee() -> None:
    w20 = w_saturation(293.15, 101325.0)
    assert 0.0140 < w20 < 0.0155          # ≈ 14,7 g/kg à 20 °C, 1 bar
    assert w_saturation(303.15, 101325.0) > w20
    assert w_saturation(293.15, 10e5) < w20 / 8    # la pression assèche
    w_moitie = w_de_humidite_relative(293.15, 101325.0, 0.5)
    assert 0.45 * w20 < w_moitie < 0.55 * w20
    assert w_de_humidite_relative(293.15, 101325.0, 0.0) == 0.0
    assert point_de_rosee(101325.0, w20) == pytest.approx(293.15, abs=0.05)
    assert point_de_rosee(101325.0, w_moitie) < 293.15
    assert point_de_rosee(101325.0, 0.0) == float("-inf")
    # l'eau ne peut plus condenser quand p_sat(T) dépasse la pression
    assert w_saturation(450.0, 3e5) == float("inf")
    # sous 0 °C : saturation sur la glace, plus basse
    assert w_saturation(253.15, 101325.0) < 1e-3


def test_extrapolation_au_dela_de_10_MPa() -> None:
    w10 = w_saturation(318.15, P_MAX_VALIDITE_PA)
    w19 = w_saturation(318.15, 190e5)
    assert w19 == pytest.approx(w10 * P_MAX_VALIDITE_PA / 190e5, rel=1e-6)
    # calcul personnel du plan : air saturé à 45 °C et 190 bar, point de
    # givre à 1 bar autour de −27 °C
    T_givre = point_de_rosee(101325.0, w19)
    assert -35.0 < T_givre - 273.15 < -20.0


def test_equilibre_conserve_l_eau() -> None:
    eq = equilibrer(283.15, 101325.0, 0.012, 0.001)
    assert eq.w_vapeur + eq.w_liquide == pytest.approx(0.013)
    assert eq.w_vapeur == pytest.approx(w_saturation(283.15, 101325.0))
    assert eq.condense > 0 and not eq.givre
    eq2 = equilibrer(303.15, 101325.0, 0.005, 0.003)   # tout s'évapore
    assert eq2.w_liquide == 0.0 and eq2.condense == pytest.approx(-0.003)
    eq3 = equilibrer(253.15, 101325.0, 0.005, 0.0)
    assert eq3.givre and eq3.w_liquide > 0
    assert enthalpie_condensation(293.15) > 2.4e6
    assert enthalpie_condensation(253.15) > enthalpie_condensation(293.15)


def test_refroidisseur_condense_et_separateur_retire(ctx: Contexte) -> None:
    r = Refroidisseur("r", {"efficacite": 0.95})
    e = EtatAir(3e5, 450.0, 0.05, w_vapeur_kg_kg=0.01)
    e_out, flux = r.pas(e, ctx)
    assert e_out.w_liquide_kg_kg > 0 and e_out.w_vapeur_kg_kg < 0.01
    assert e_out.w_total_kg_kg == pytest.approx(0.01)
    assert flux.eau_condensee_kg_s > 0 and flux.Q_latente_w > 0
    sep = Secheur("sep", {"modele": "separateur",
                          "efficacite_separation": 0.98})
    e_sep, f_sep = sep.pas(e_out, ctx)
    assert e_sep.w_liquide_kg_kg == pytest.approx(
        0.02 * e_out.w_liquide_kg_kg)
    assert f_sep.eau_separee_kg_s == pytest.approx(
        0.98 * e_out.w_liquide_kg_kg * 0.05)
    assert e_sep.m_dot_kg_s == e_out.m_dot_kg_s


def test_secheur_adsorption_seche_au_point_de_rosee(ctx: Contexte) -> None:
    s = Secheur("s", {"efficacite": 0.81, "point_de_rosee_sortie": 233.15})
    e = EtatAir(190e5, 318.15, 0.05, w_vapeur_kg_kg=1e-4,
                w_liquide_kg_kg=5e-4)
    e_out, flux = s.pas(e, ctx)
    assert e_out.w_liquide_kg_kg == 0.0
    assert e_out.w_vapeur_kg_kg == pytest.approx(
        min(1e-4, w_saturation(233.15, 190e5)))
    assert flux.eau_separee_kg_s > 0 and e_out.m_dot_kg_s == pytest.approx(
        0.05 * 0.81)
    assert point_de_rosee(190e5, e_out.w_vapeur_kg_kg) <= 233.15 + 0.1
    # modèle historique sans point de rosée : l'eau n'est pas touchée
    s0 = Secheur("s", {"efficacite": 0.81})
    e0, _ = s0.pas(e, ctx)
    assert e0.w_vapeur_kg_kg == 1e-4 and e0.w_liquide_kg_kg == 5e-4


def test_reservoir_condense_quand_il_refroidit(ctx: Contexte) -> None:
    res = ReservoirAir("res", {"modele": "K_global", "volume": 1.0,
                               "surface": 5.0, "K_global": 50.0})
    res.initialiser(ctx.air, 150e5, 318.15)
    w_sat = w_saturation(318.15, 150e5)
    for _ in range(50):
        res.remplir(ctx, EtatAir(160e5, 318.15, 0.02,
                                 w_vapeur_kg_kg=w_sat))
    assert res.eau_liquide_kg == pytest.approx(0.0, abs=1e-6)
    froid = Contexte(ctx.air, Ambiance(253.15, 101325.0, 0.5, 253.15), 0.0,
                     600.0)
    for _ in range(100):
        res.attendre(froid)
    assert res.T_K < 280.0
    assert res.eau_liquide_kg > 0.0
    assert any("condensation" in a.message for a in res.avertissements)
    e = res.etat_sortie(0.1)
    assert e.w_vapeur_kg_kg == pytest.approx(res.w_vapeur_kg_kg)
    assert e.w_vapeur_kg_kg <= w_saturation(res.T_K, res.p_abs_pa) * 1.001


def test_turbine_givre_a_la_sortie(ctx: Contexte, registre: Registre) -> None:
    t = Turbine("t", {
        "modele": "polytropique_deprag", "debit_massique": 0.321,
        "etages": [{"p_entree": 3e5, "p_sortie": 1.0e5,
                    "indice_polytropique": 1.27, "rendement_mecanique": 0.73,
                    "rendement_electrique": 0.92}]})
    w = w_saturation(318.15, 190e5)   # air du réservoir de Dormoy (45 °C)
    e_out, flux = t.etage(1).pas(EtatAir(3e5, 275.0, 0.321,
                                         w_vapeur_kg_kg=w), ctx)
    assert e_out.T_K < 240.0
    assert flux.givre and flux.eau_condensee_kg_s > 0
    assert any("givre" in a.message for a in t.avertissements)
    # réchauffé à 90 °C avant la détente : plus de givre
    t.effacer_avertissements()
    e2, f2 = t.etage(1).pas(EtatAir(3e5, 363.15, 0.321, w_vapeur_kg_kg=w),
                            ctx)
    assert not f2.givre and f2.eau_condensee_kg_s == 0.0


def test_mise_a_l_equilibre_sans_eau_ne_change_rien() -> None:
    e = EtatAir(1e5, 250.0, 1.0)
    f = Flux()
    assert mettre_a_l_equilibre(e, f) is e and not f.givre
    assert math.isinf(f.T_rosee_K)


def test_sous_130_K_toute_l_eau_gele() -> None:
    """Sous le domaine RP-1485 (130 K), la saturation est nulle : l'air
    d'une détente très froide garde son eau sous forme de glace, avec un
    avertissement, sans arrêter la simulation."""
    assert w_saturation(115.0, 3e5) == 0.0
    eq = equilibrer(115.0, 3e5, 1e-4, 0.0)
    assert eq.w_vapeur == 0.0 and eq.w_liquide == pytest.approx(1e-4)
    assert eq.givre
    t = Turbine("t", {
        "modele": "isentropique", "debit_massique": 0.3,
        "rendement_isentropique": 0.8, "rendement_mecanique": 0.9,
        "rendement_electrique": 0.9,
        "etages": [{"p_entree": 3e5, "p_sortie": 1.0e5}]})
    f = Flux()
    e = mettre_a_l_equilibre(EtatAir(3e5, 115.0, 0.3, w_vapeur_kg_kg=1e-4),
                             f, t)
    assert e.w_liquide_kg_kg == pytest.approx(1e-4) and f.givre
    assert any("130 K" in a.message for a in t.avertissements)


def test_eau_initiale_du_reservoir_plafonnee(ctx: Contexte) -> None:
    """L'air déjà dans le réservoir porte au plus la saturation à son
    (T, p), puis au plus ce que la chaîne de charge refoule ; rien de
    cela n'est compté comme condensation (F43)."""
    res = ReservoirAir("res", {"modele": "K_global", "volume": 1.0,
                               "surface": 5.0, "K_global": 50.0})
    res.initialiser(ctx.air, 55e5, 293.15, w_kg_kg=0.0073)
    assert res.eau_initiale_a_plafonner
    assert res.w_vapeur_kg_kg == pytest.approx(w_saturation(293.15, 55e5))
    assert res.eau_liquide_kg == 0.0 and res.eau_condensee_cumul_kg == 0.0
    w_chaine = w_saturation(233.15, 55e5)
    res.plafonner_eau(w_chaine)
    assert not res.eau_initiale_a_plafonner
    assert res.w_vapeur_kg_kg == pytest.approx(w_chaine)
    assert res.eau_condensee_cumul_kg == 0.0
    assert not res.avertissements
