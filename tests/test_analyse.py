"""Tests du paquet d'analyse (phase 10) : masse des réservoirs (F44),
sensibilité et incertitudes (F45), NSGA-II (F46), fichier d'analyse."""

import math
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from caes.analyse import Evaluateur, charger_analyse
from caes.analyse.incertitudes import propager
from caes.analyse.masse import masse_reservoir_paroi_mince
from caes.analyse.parametres import ErreurAnalyse
from caes.analyse.pareto import (
    ReglagesNSGA2,
    distance_encombrement,
    nsga2,
    tri_non_domine,
)
from caes.analyse.sensibilite import un_parametre_a_la_fois
from caes.registre import Registre

RACINE = Path(__file__).resolve().parent.parent
ANALYSE_RAPIDE = RACINE / "scenarios" / "analyse" / "B_rapide.yaml"


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


# --- F44 : masse des réservoirs ------------------------------------------
def test_masse_paroi_mince_retrouve_les_bouteilles_de_dormoy(
        registre: Registre) -> None:
    """La résistance spécifique équivalente est calibrée sur la masse
    des deux modèles de bouteilles (tableau 8) : on doit les retrouver à
    3 % près, et la bouteille tout aluminium serait bien plus lourde."""
    p = registre.si("reservoir.pression_service")
    d = registre.si("reservoir.diametre_interieur")
    k = registre.si("reservoir.resistance_specifique_equivalente")
    S = registre.si("reservoir.coefficient_securite")
    m320 = masse_reservoir_paroi_mince(p, 0.32, d, k, S).masse_kg
    m270 = masse_reservoir_paroi_mince(p, 0.27, d, k, S).masse_kg
    assert m320 == pytest.approx(registre.si("reservoir.masse_320L"),
                                 rel=0.03)
    assert m270 == pytest.approx(registre.si("reservoir.masse_270L"),
                                 rel=0.03)
    sigma = registre.si("reservoir.alu.limite_elastique")
    rho = registre.si("reservoir.alu.masse_volumique")
    m_alu = masse_reservoir_paroi_mince(p, 0.32, d, sigma / rho, S, rho)
    assert m_alu.masse_kg > 3 * m320
    assert 0.03 < m_alu.epaisseur_equivalente_m < 0.06


def test_masse_paroi_mince_proportionnelle_et_sphere() -> None:
    a = masse_reservoir_paroi_mince(100e5, 1.0, 0.4, 4e5, 2.0)
    b = masse_reservoir_paroi_mince(200e5, 1.0, 0.4, 4e5, 2.0)
    assert b.masse_kg == pytest.approx(2 * a.masse_kg)
    # volume doublé à diamètre égal : la partie cylindrique (plus lourde
    # par m³ que les fonds) fait plus que doubler, un peu
    c = masse_reservoir_paroi_mince(100e5, 2.0, 0.4, 4e5, 2.0)
    assert 2 * a.masse_kg < c.masse_kg < 2.1 * a.masse_kg
    # volume plus petit que la sphère du diamètre donné : sphère
    s = masse_reservoir_paroi_mince(100e5, 0.01, 0.4, 4e5, 2.0)
    assert s.volume_cylindre_m3 == 0.0
    assert s.masse_kg == pytest.approx(2.0 * 100e5 / 4e5 * 1.5 * 0.01)
    assert masse_reservoir_paroi_mince(0.0, 1.0, 0.4, 4e5, 2.0).masse_kg == 0
    with pytest.raises(ValueError):
        masse_reservoir_paroi_mince(1e5, -1.0, 0.4, 4e5, 2.0)


# --- F46 : dominance et NSGA-II -------------------------------------------
def test_tri_non_domine_et_encombrement() -> None:
    F = np.array([[1.0, 2.0], [2.0, 1.0], [2.0, 2.0], [3.0, 3.0],
                  [1.5, 1.5]])
    fronts = tri_non_domine(F)
    assert sorted(fronts[0]) == [0, 1, 4]
    assert fronts[1] == [2] and fronts[2] == [3]
    d = distance_encombrement(F, fronts[0])
    assert math.isinf(d[0]) and math.isinf(d[1]) and np.isfinite(d[2])


def test_nsga2_approche_le_front_de_zdt1() -> None:
    """ZDT1 (3 variables) : front exact f2 = 1 − √f1 ; écart < 3 % après
    40 générations, résultat identique à graine égale."""
    def zdt1(U: np.ndarray) -> np.ndarray:
        f1 = U[:, 0]
        g = 1 + 9 * U[:, 1:].mean(axis=1)
        return np.column_stack([f1, g * (1 - np.sqrt(f1 / g))])

    reglages = ReglagesNSGA2(population=24, generations=40, graine=3)
    r = nsga2(zdt1, 3, reglages)
    F = r.F[r.front]
    assert len(r.front) >= 10
    assert np.all(np.diff(F[:, 0]) >= 0)
    ecart = np.abs(F[:, 1] - (1 - np.sqrt(F[:, 0])))
    assert ecart.max() < 0.03
    assert F[:, 0].min() < 0.05 and F[:, 0].max() > 0.8
    r2 = nsga2(zdt1, 3, reglages)
    assert np.array_equal(r.F, r2.F)
    assert r.evaluations == 24 * 41


def test_nsga2_penalise_les_echecs() -> None:
    def f(U: np.ndarray) -> np.ndarray:
        out = np.column_stack([U[:, 0], 1 - U[:, 0]])
        out[U[:, 0] > 0.7] = np.nan
        return out

    r = nsga2(f, 1, ReglagesNSGA2(population=8, generations=5, graine=1))
    assert r.echecs > 0
    assert not np.isnan(r.F[r.front]).any()
    assert r.F[r.front, 0].max() <= 0.7


# --- F45 : indices de Sobol sur une fonction connue -----------------------
def test_indices_de_sobol_fonction_additive() -> None:
    """y = 3 x1 + x2 : S1 = 0,9 et 0,1, troisième variable muette."""
    def f(x: np.ndarray) -> np.ndarray:
        return np.atleast_2d(3 * x[0] + x[1] + 0 * x[2])

    res = stats.sobol_indices(func=f, n=256,
                              dists=[stats.uniform(0, 1)] * 3,
                              random_state=1)
    assert res.first_order[0] == pytest.approx(0.9, abs=0.03)
    assert res.first_order[1] == pytest.approx(0.1, abs=0.03)
    assert abs(res.first_order[2]) < 0.02


# --- fichier d'analyse et évaluation ---------------------------------------
def test_fichier_d_analyse_resolu(registre: Registre) -> None:
    an = charger_analyse(ANALYSE_RAPIDE, registre)
    assert [p.nom for p in an.parametres] == ["p_max", "rendement_electrique",
                                              "T_amb"]
    p_max = an.parametre("p_max")
    assert p_max.nominal == pytest.approx(190e5)
    assert p_max.minimum == pytest.approx(120e5)
    assert p_max.affichage(p_max.maximum) == pytest.approx(220)
    rend = an.parametre("rendement_electrique")
    assert rend.origine.startswith("registre")
    assert rend.minimum == pytest.approx(0.94)
    assert rend.maximum == pytest.approx(0.95)
    assert rend.niveau == "fabricant"
    T = an.parametre("T_amb")
    assert T.minimum == pytest.approx(253.15)
    assert T.modifications(263.15) == {"ambiance.T_amb": 263.15}
    assert an.scenario.valeurs["simulation"]["nombre_max"] == 1
    with pytest.raises(ErreurAnalyse):
        an.parametre("inconnu")


def test_fichier_d_analyse_refuse_les_incoherences(
        tmp_path: Path, registre: Registre) -> None:
    texte = ANALYSE_RAPIDE.read_text(encoding="utf-8").replace(
        "scenario: ../B.yaml", f"scenario: {RACINE / 'scenarios' / 'B.yaml'}")
    base = tmp_path / "a.yaml"
    base.write_text(texte, encoding="utf-8")
    charger_analyse(base, registre)
    mauvais = tmp_path / "b.yaml"
    mauvais.write_text(texte.replace("plage: registre", "plage: hypothese")
                       .replace("sens: max", "sens: haut"), encoding="utf-8")
    with pytest.raises(ErreurAnalyse):
        charger_analyse(mauvais, registre)
    sans_plage = tmp_path / "c.yaml"
    sans_plage.write_text(texte.replace("plage: {min: 120, max: 220}",
                                        "plage: {min: 220, max: 120}"),
                          encoding="utf-8")
    with pytest.raises(ErreurAnalyse):
        charger_analyse(sans_plage, registre)


def test_evaluation_tornade_et_incertitudes_en_serie(
        registre: Registre) -> None:
    """Sur B (un cycle, pas grossiers) : la masse ne dépend que de la
    pression, l'électricité consommée baisse quand le rendement
    électrique monte, et les intervalles encadrent le nominal."""
    an = charger_analyse(ANALYSE_RAPIDE, registre)
    ev = Evaluateur(an, registre)
    params = an.selection(["p_max", "rendement_electrique"])
    tor = un_parametre_a_la_fois(ev, params, an.sorties)
    assert tor.nominal.valide and not tor.echecs
    masse = {li.parametre.nom: li for li in tor.classement("masse_totale_kg")}
    assert masse["p_max"].bas < masse["p_max"].haut
    assert masse["rendement_electrique"].balancement == 0.0
    conso = {li.parametre.nom: li
             for li in tor.classement("energie_consommee_kwh")}
    assert conso["rendement_electrique"].bas > conso["rendement_electrique"
                                                     ].haut
    assert tor.classement("energie_consommee_kwh")[0].parametre.nom == "p_max"
    inc = propager(ev, an.selection(["rendement_electrique"]), an.sorties,
                   n=4, graine=2)
    it = inc.intervalle("energie_consommee_kwh")
    assert it.n_valides == 4 and inc.echecs == 0
    assert it.minimum <= it.mediane <= it.maximum
    assert it.minimum <= it.nominal * 1.01 and it.maximum >= it.nominal * 0.99
    assert inc.spearman[an.sorties.index("energie_consommee_kwh"), 0] < 0
    # le cache évite de resimuler le nominal
    n_avant = len(ev._cache)
    ev.evaluer(ev.point_nominal(params))
    assert len(ev._cache) == n_avant


def test_point_echoue_donne_nan(registre: Registre) -> None:
    an = charger_analyse(ANALYSE_RAPIDE, registre)
    ev = Evaluateur(an, registre)
    r = ev.evaluer({"p_max": 10e5})   # sous la pression initiale : refus
    assert not r.valide and r.erreur
    assert all(math.isnan(v) for v in r.sorties.values())
