"""Tests de la phase 11 : fuite du réservoir (F12), répartition d'une
flotte (F47), profils météo et de demande, scénarios d'exemple."""

from pathlib import Path

import numpy as np
import pytest

from caes.ambiance import Ambiance, charger_profil
from caes.analyse.lot import simuler_lot, simuler_scenarios
from caes.assembleur import charger_installation
from caes.composants import Contexte, ReservoirAir
from caes.flotte import (
    CourbeModule,
    modules_necessaires,
    profil_jour_nuit,
    repartir,
)
from caes.proprietes import air_par_defaut
from caes.registre import Registre

RACINE = Path(__file__).resolve().parent.parent
EXEMPLES = RACINE / "scenarios" / "exemples"


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


# --- F12 : fuite -------------------------------------------------------------
def test_fuite_du_reservoir_pendant_l_attente() -> None:
    air = air_par_defaut()
    amb = Ambiance(293.15, 101325.0, 0.5, 293.15)
    res = ReservoirAir("res", {"modele": "K_global", "volume": 1.0,
                               "surface": 5.0, "K_global": 0.0,
                               "fuite_par_jour": 0.01})
    res.initialiser(air, 100e5, 293.15)
    m0 = res.masse_kg
    for _ in range(144):
        res.attendre(Contexte(air, amb, 0.0, 600.0))
    # un jour à 1 %/j : exp(−0,01) de la masse
    assert res.masse_kg == pytest.approx(m0 * np.exp(-0.01), rel=2e-4)
    assert res.masse_fuite_kg == pytest.approx(m0 - res.masse_kg, rel=1e-6)
    assert res.p_abs_pa < 100e5
    sans = ReservoirAir("res", {"modele": "K_global", "volume": 1.0,
                                "surface": 5.0, "K_global": 0.0})
    sans.initialiser(air, 100e5, 293.15)
    sans.attendre(Contexte(air, amb, 0.0, 600.0))
    assert sans.masse_kg == pytest.approx(m0) and sans.masse_fuite_kg == 0
    mauvais = ReservoirAir("res", {"modele": "K_global", "volume": 1.0,
                                   "surface": 5.0, "K_global": 0.0,
                                   "fuite_par_jour": 1.5})
    assert any("fuite" in a for a in mauvais.verifier_validite())


# --- F47 : flotte ------------------------------------------------------------
def _courbe(P_w: float = 60e3, duree_s: float = 2400.0) -> CourbeModule:
    return CourbeModule(1.0, np.full(int(duree_s), P_w))


def test_repartition_demande_constante() -> None:
    """Demande constante de 100 kW pendant 10 h avec des modules de 60 kW
    × 40 min (40 kWh) : au moins 1000 / 40 = 25 modules ; avec deux en
    marche (120 kW) l'écrêtage demande un peu plus, et tout est servi."""
    c = _courbe()
    demande = np.full(36000, 100e3)
    n, r = modules_necessaires(c, demande)
    assert 25 <= n <= 32
    assert r.couverture >= 0.999
    assert r.energie_non_servie_j <= 0.001 * r.energie_demandee_j
    assert r.energie_ecretee_j > 0
    assert r.modules_en_marche.max() == 2
    assert r.modules_utilises == n
    # moins de modules : énergie non servie
    r2 = repartir(c, demande, 10)
    assert r2.couverture < 0.5 and r2.energie_restante_j == 0.0
    # aucun module : rien de fourni
    r0 = repartir(c, demande, 0)
    assert r0.energie_fournie_j == 0.0 and r0.couverture == 0.0


def test_repartition_pause_et_reprise() -> None:
    """Demande nulle au milieu : les modules se mettent en pause et
    reprennent sans perdre leur air."""
    c = _courbe(P_w=50e3, duree_s=1000.0)
    demande = np.concatenate([np.full(500, 50e3), np.zeros(500),
                              np.full(500, 50e3)])
    r = repartir(c, demande, 2)
    assert r.couverture == pytest.approx(1.0)
    assert r.modules_en_marche[600] == 0
    assert r.modules_utilises == 1
    assert r.energie_restante_j == pytest.approx(50e3 * 1000.0)


def test_courbe_depuis_series_et_profil() -> None:
    t = np.array([0.0, 10.0, 20.0, 30.0])
    P = np.array([0.0, 100.0, 100.0, 0.0])
    c = CourbeModule.depuis_series(t, P, 5.0)
    assert c.P_w.size == 6 and c.P_w[1] == pytest.approx(50.0)
    assert c.P_nominale_w == 100.0
    prof = profil_jour_nuit(86400.0, 100e3, 1.2, 0.6, dt_s=3600.0)
    assert prof.size == 24
    assert prof[:6].max() == pytest.approx(60e3)
    assert prof[12] == pytest.approx(120e3)
    assert prof.mean() == pytest.approx(100e3)


# --- profils et scénarios d'exemple ------------------------------------------
def test_profils_generes_et_scenarios_s_assemblent(registre: Registre
                                                   ) -> None:
    t, T = charger_profil(EXEMPLES / "transport" / "meteo_hiver.csv")
    assert t[-1] >= 56 * 86400 and T.min() < 253.15 < T.max()
    assert abs(T.mean() - 253.15) < 0.5
    for nom in ("transport/transport.yaml", "transport/transport_appoint.yaml",
                "centre_urgence/module.yaml"):
        inst = charger_installation(EXEMPLES / nom, registre)
        assert inst.mode == "cycles"
    inst = charger_installation(
        EXEMPLES / "transport" / "transport.yaml", registre,
        modifications=["ambiance.profil=meteo_ete.csv"])
    assert inst.ambiance.a_un_profil
    assert inst.ambiance.T_amb_a(12 * 3600.0) > 300.0
    app = charger_installation(EXEMPLES / "transport"
                               / "transport_appoint.yaml", registre)
    assert app.decharge is not None
    assert sum(1 for e in app.decharge.elements
               if e.type_ == "stockage_chaleur") == 6


def test_lot_de_simulations_resume(registre: Registre) -> None:
    """Un lot de deux variantes de B (rapide) : résumés complets, erreur
    rendue (pas levée) pour une variante impossible."""
    chemin = RACINE / "scenarios" / "B.yaml"
    base = ["simulation.nombre_max=1", "charge.dt=120s", "decharge.dt=20s"]
    res = simuler_lot(chemin, [base, base + ["charge.p_cible=10bar"]],
                      procs=1, series=True)
    assert res[0].valide and res[0].series_decharge is not None
    assert "P_el_w" in res[0].series_decharge.columns
    assert res[0].rendements["energie_produite_kwh"] > 30
    assert not res[1].valide and res[1].erreur
    r2 = simuler_scenarios([(chemin, base)], procs=1)
    assert r2[0].rendements == pytest.approx(res[0].rendements)
