"""Tests de l'assembleur et des configurations libres (phase 6)."""

from pathlib import Path

import pytest
import yaml

from caes.ambiance import ErreurAmbiance
from caes.assembleur import (
    ErreurAssemblage,
    appliquer_modifications,
    charger_installation,
)
from caes.registre import Registre
from caes.scenario import charger_scenario

DOSSIER = Path(__file__).resolve().parent.parent / "scenarios"


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


def _brut(nom: str) -> dict:
    return yaml.safe_load((DOSSIER / nom).read_text(encoding="utf-8"))


def _ecrire(tmp_path: Path, brut: dict, nom: str = "s.yaml") -> Path:
    f = tmp_path / nom
    f.write_text(yaml.safe_dump(brut, allow_unicode=True, sort_keys=False),
                 encoding="utf-8")
    return f


# --- assemblage ----------------------------------------------------------


def test_les_scenarios_d_exemple_s_assemblent(registre: Registre) -> None:
    for f in sorted(DOSSIER.glob("*.yaml")):
        inst = charger_installation(f, registre)
        inst.verifier()
        assert inst.mode in ("charge", "decharge", "cycles")
        assert inst.ambiance.p_amb_pa > 0


def test_ambiance_obligatoire(tmp_path: Path, registre: Registre) -> None:
    brut = _brut("dormoy_decharge_essai.yaml")
    del brut["ambiance"]["humidite_relative"]
    with pytest.raises(ErreurAmbiance):
        charger_installation(_ecrire(tmp_path, brut), registre)
    del brut["ambiance"]
    with pytest.raises(ErreurAmbiance):
        charger_installation(_ecrire(tmp_path, brut), registre)


def test_type_et_modele_inconnus(tmp_path: Path, registre: Registre) -> None:
    brut = _brut("dormoy_decharge_essai.yaml")
    brut["composants"]["detendeur"]["type"] = "robinet"
    with pytest.raises(ErreurAssemblage):
        charger_installation(_ecrire(tmp_path, brut), registre)
    brut = _brut("dormoy_decharge_essai.yaml")
    brut["composants"]["detendeur"]["modele"] = "magique"
    with pytest.raises(ValueError):
        charger_installation(_ecrire(tmp_path, brut), registre)


def test_cle_inconnue_refusee(tmp_path: Path, registre: Registre) -> None:
    brut = _brut("dormoy_decharge_essai.yaml")
    brut["decharges"] = brut["decharge"]
    with pytest.raises(ErreurAssemblage):
        charger_installation(_ecrire(tmp_path, brut), registre)


def test_ordre_des_etages_verifie(tmp_path: Path, registre: Registre) -> None:
    brut = _brut("dormoy_charge_1_190.yaml")
    chaine = brut["charge"]["chaine"]
    chaine[0], chaine[2] = chaine[2], chaine[0]  # compresseur.2 avant .1
    with pytest.raises(ErreurAssemblage):
        charger_installation(_ecrire(tmp_path, brut), registre)
    brut = _brut("dormoy_charge_1_190.yaml")
    brut["charge"]["chaine"].remove("reservoir")
    with pytest.raises(ErreurAssemblage):
        charger_installation(_ecrire(tmp_path, brut), registre)


def test_pressions_incompatibles_refusees(tmp_path: Path,
                                          registre: Registre) -> None:
    brut = _brut("dormoy_decharge_3etages.yaml")
    brut["composants"]["detendeur"]["p_consigne"] = {
        "valeur": 30, "unite": "bar", "source": "test"}
    with pytest.raises(ErreurAssemblage):
        charger_installation(_ecrire(tmp_path, brut), registre)
    brut = _brut("dormoy_decharge_3etages.yaml")
    et = brut["composants"]["turbine"]["etages"]
    et[0], et[1] = et[1], et[0]  # l'étage 2 (11 bar) avant l'étage 1 (40)
    with pytest.raises(ErreurAssemblage):
        charger_installation(_ecrire(tmp_path, brut), registre)


def test_rechauffeur_sans_turbine_refuse(tmp_path: Path,
                                         registre: Registre) -> None:
    brut = _brut("dormoy_decharge_3etages.yaml")
    brut["decharge"]["chaine"].append("chaudiere")
    with pytest.raises(ErreurAssemblage):
        charger_installation(_ecrire(tmp_path, brut), registre)


def test_developpement_turbine_entiere(tmp_path: Path,
                                       registre: Registre) -> None:
    """« turbine » seul dans la chaîne = tous ses étages, sans réchauffage."""
    brut = _brut("dormoy_decharge_3etages.yaml")
    brut["decharge"]["chaine"] = ["reservoir", "detendeur", "turbine"]
    inst = charger_installation(_ecrire(tmp_path, brut), registre)
    assert [e.nom for e in inst.decharge.elements] == [
        "reservoir", "detendeur", "turbine.1", "turbine.2", "turbine.3"]
    r = inst.simuler()
    assert r.decharge is not None
    assert r.decharge.chaleur_par_source == {}
    # sans réchauffage, moins d'électricité qu'avec la chaudière
    assert r.decharge.totaux["energie_electrique_kwh"] < 30.0


def test_modifications_en_ligne_de_commande(registre: Registre) -> None:
    sc = charger_scenario("D.yaml", registre)
    sc2 = appliquer_modifications(
        sc, ["ambiance.T_amb=-20degC", "composants.cuve_1.volume=0.5m3",
             "simulation.nombre_max=3", "composants.cuve_1.bypass=false"])
    assert sc2["ambiance.T_amb"] == pytest.approx(253.15)
    assert sc2["composants.cuve_1.volume"] == 0.5
    assert sc2["simulation.nombre_max"] == 3
    assert sc2["composants.cuve_1.bypass"] is False
    with pytest.raises(ErreurAssemblage):
        appliquer_modifications(sc, ["ambiance.T_amb=-20furlong"])
    with pytest.raises(ErreurAssemblage):
        appliquer_modifications(sc, ["pas_de_signe_egal"])


# --- ambiance ------------------------------------------------------------


def test_hiver_change_les_resultats(registre: Registre) -> None:
    """Changer T_amb de 20 à −20 °C suffit : l'air aspiré est plus dense,
    les refroidisseurs plus efficaces, le réservoir plus froid."""
    ete = charger_installation("dormoy_charge_1_190_aspiration_chaude.yaml",
                               registre).simuler().charge
    hiver = charger_installation(
        "dormoy_charge_1_190_aspiration_chaude.yaml", registre,
        modifications=["ambiance.T_amb=-20degC",
                       "ambiance.T_aspiration=-20degC"]).simuler().charge
    assert ete is not None and hiver is not None
    assert hiver.parametres["T0_K"] == pytest.approx(253.15)
    assert hiver.series["T_in_comp_1_K"].iloc[0] == pytest.approx(253.15)
    assert hiver.totaux["debit_aspire_kg_s"] > ete.totaux["debit_aspire_kg_s"]
    assert hiver.totaux["T_finale_degC"] < ete.totaux["T_finale_degC"]
    assert hiver.totaux["chaleur_refroidisseurs_kwh"] != pytest.approx(
        ete.totaux["chaleur_refroidisseurs_kwh"], rel=0.01)


def test_profil_meteo(tmp_path: Path, registre: Registre) -> None:
    csv = tmp_path / "meteo.csv"
    csv.write_text("t_h,T_amb_degC\n0,20\n5,-10\n10,-10\n", encoding="utf-8")
    brut = _brut("dormoy_charge_1_190.yaml")
    brut["ambiance"]["profil"] = "meteo.csv"
    inst = charger_installation(_ecrire(tmp_path, brut), registre)
    amb = inst.ambiance
    assert amb.a_un_profil
    assert amb.T_amb_a(0.0) == pytest.approx(293.15)
    assert amb.T_amb_a(2.5 * 3600) == pytest.approx(278.15)
    assert amb.T_amb_a(20 * 3600) == pytest.approx(263.15)
    r = inst.simuler().charge
    assert r is not None
    assert r.series["T_amb_K"].iloc[0] > r.series["T_amb_K"].iloc[-1]
    assert abs(r.bilan["residu_relatif"]) < 1e-3


# --- cycles, attente, validité --------------------------------------------


def test_attente_avec_pertes_refroidit_les_cuves(registre: Registre) -> None:
    inst = charger_installation(
        "D.yaml", registre,
        modifications=["simulation.nombre_max=1",
                       "composants.cuve_3.coefficient_perte=5W/m2K",
                       "composants.attente.duree=48h"]
        + [f"composants.cuve_{i}.n_cellules=10" for i in (1, 2, 3)])
    r = inst.simuler()
    c = r.dernier_cycle
    assert c is not None
    assert c.attente_h == pytest.approx(48.0)
    assert c.pertes_attente_kwh > 1.0
    # la cuve 3 a perdu de la chaleur : moins de chaleur pour la turbine 1
    assert c.decharge.chaleur_par_source["cuve_3"] < 30.0


def test_avertissements_hors_domaine(registre: Registre) -> None:
    inst = charger_installation(
        "dormoy_decharge_essai.yaml", registre,
        modifications=["composants.detendeur.modele=cheayb"])
    avis = inst.verifier()
    assert not avis
    r = inst.simuler()
    textes = [a.message for a in r.avertissements]
    assert any("Cheayb" in t for t in textes)  # 190 bar > 150 bar


def test_sortie_ecrit_les_fichiers(tmp_path: Path, registre: Registre) -> None:
    from caes.sortie import ecrire_resultats

    r = charger_installation("A.yaml", registre,
                             modifications=["simulation.nombre_max=1"]
                             ).simuler()
    dossier = ecrire_resultats(r, tmp_path / "A", graphiques=False)
    for nom in ("resume.md", "provenance.md", "tableau_1000.md",
                "charge_series.csv", "decharge_series.csv", "cycles.csv"):
        assert (dossier / nom).exists(), nom
    texte = (dossier / "resume.md").read_text(encoding="utf-8")
    assert "RTE sans compter la chaleur" in texte
    prov = (dossier / "provenance.md").read_text(encoding="utf-8")
    assert "doi.org" in prov


def test_ligne_de_commande(tmp_path: Path) -> None:
    from caes.__main__ import main

    code = main(["verifier", str(DOSSIER / "B.yaml")])
    assert code == 0
    code = main(["simuler", str(DOSSIER / "dormoy_decharge_base.yaml"),
                 "--sortie", str(tmp_path / "base"), "--sans-graphiques"])
    assert code == 0
    assert (tmp_path / "base" / "resume.md").exists()
    assert main(["verifier", str(tmp_path / "inexistant.yaml")]) == 2
