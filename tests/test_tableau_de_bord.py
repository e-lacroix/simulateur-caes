"""Tests du tableau de bord de validation (phase 8)."""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "validation"))
import tableau_de_bord as tb  # noqa: E402

from caes.assembleur import charger_installation  # noqa: E402
from caes.registre import Registre  # noqa: E402


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


def test_verdicts() -> None:
    ok = tb.Ligne("j", "mesure", "c", "g", 100.0, 103.0, "kWh", "s")
    assert ok.verdict == "reproduit" and ok.ecart_pct == pytest.approx(3.0)
    expl = tb.Ligne("j", "mesure", "c", "g", 100.0, 110.0, "kWh", "s",
                    "trois_etages")
    assert expl.verdict == "écart expliqué"
    non = tb.Ligne("j", "mesure", "c", "g", 100.0, 85.0, "kWh", "s",
                   "cas_base")
    assert non.verdict == "**non expliqué**"
    sans = tb.Ligne("j", "mesure", "c", "g", 100.0, 85.0, "kWh", "s")
    assert sans.verdict == "**non expliqué**"
    temp = tb.Ligne("j", "fabricant", "c", "T", 16.0, 14.5, "°C", "s",
                    tolerance_abs=2.83)
    assert temp.verdict == "reproduit"


def test_jeux_en_attente_ont_une_provenance() -> None:
    for jeu in tb.jeux_en_attente():
        assert (tb.DONNEES / jeu.dossier / "provenance.md").exists(), jeu.id
    for d in ("dormoy", "shi2024", "tola2022"):
        assert (tb.DONNEES / d / "provenance.md").exists()


def test_scenarios_de_validation_s_assemblent(registre: Registre) -> None:
    for nom in ("shi_100MW.yaml", "tola_charge.yaml", "tola_decharge_A.yaml",
                "tola_decharge_B.yaml", "tola_decharge_C.yaml"):
        inst = charger_installation(tb.SCEN_VAL / nom, registre)
        inst.verifier()
        assert inst.ambiance.T_amb_K > 250.0


def test_dormoy_mesures_reproduites(registre: Registre) -> None:
    mes, mes_d, sim = tb.cas_dormoy(registre)
    assert mes.nature == "mesure" and mes_d.nature == "mesure"
    assert len(mes.lignes) + len(mes_d.lignes) >= 4
    assert all(l.verdict == "reproduit"
               for l in mes.lignes + mes_d.lignes), [
        (l.grandeur, l.ecart_pct) for l in mes.lignes + mes_d.lignes]
    cas_base = [l for l in sim.lignes if l.explication == "cas_base"]
    assert cas_base and cas_base[0].verdict == "**non expliqué**"
    assert -17.0 < cas_base[0].ecart_pct < -13.0
    deprag = [l for l in sim.lignes if "DEPRAG" in l.composant]
    assert len(deprag) == 6 and all(l.verdict == "reproduit"
                                    for l in deprag)
