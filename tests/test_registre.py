"""Tests du registre scientifique (phase 0)."""

import csv
from pathlib import Path

import pytest

from caes.registre import (
    DOSSIER_REGISTRE_DEFAUT,
    NIVEAUX_PREUVE,
    UNITES,
    ErreurRegistre,
    Registre,
)


@pytest.fixture(scope="module")
def registre() -> Registre:
    return Registre.charger()


def _lignes(nom: str) -> list[dict[str, str]]:
    chemin = DOSSIER_REGISTRE_DEFAUT / nom
    with open(chemin, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_le_registre_se_charge(registre: Registre) -> None:
    assert len(registre) > 100
    assert "dormoy2024" in registre.references


def test_aucun_identifiant_en_double() -> None:
    ids = [ligne["id"] for ligne in _lignes("parametres.csv")]
    doublons = {i for i in ids if ids.count(i) > 1}
    assert doublons == set()
    refs = [ligne["id"] for ligne in _lignes("references.csv")]
    assert len(refs) == len(set(refs))


def test_toutes_les_unites_sont_connues(registre: Registre) -> None:
    unites = {p.unite for p in registre.parametres.values()}
    assert unites - set(UNITES) == set()


def test_chaque_parametre_a_une_source_connue(registre: Registre) -> None:
    for par in registre.parametres.values():
        assert par.source_id in registre.references, par.id
        assert par.localisation.strip() != "", par.id


def test_chaque_parametre_a_un_niveau_de_preuve(registre: Registre) -> None:
    for par in registre.parametres.values():
        assert par.niveau_preuve in NIVEAUX_PREUVE, par.id


def test_chaque_reference_a_un_doi_ou_une_url(registre: Registre) -> None:
    for ref in registre.references.values():
        assert ref.doi_ou_url.startswith("http"), ref.id


def test_conversion_si_bar_degc_kwh(registre: Registre) -> None:
    p_max = registre["essai_charge.pression_finale"]
    assert p_max.unite_si == "Pa"
    assert p_max.valeur_si == pytest.approx(190e5)
    t0 = registre["essai_decharge.temperature_initiale"]
    assert t0.valeur_si == pytest.approx(328.15)
    e = registre.si("essai_charge.energie_consommee")
    assert e == pytest.approx(396 * 3.6e6)


def test_une_plage_n_a_pas_de_valeur_unique(registre: Registre) -> None:
    eta = registre["compresseur.rendement_mecanique"]
    assert eta.est_plage
    assert eta.valeur_min_si == pytest.approx(0.69)
    assert eta.valeur_max_si == pytest.approx(0.74)
    with pytest.raises(ErreurRegistre):
        _ = eta.valeur_si


def test_parametre_absent_leve_une_erreur(registre: Registre) -> None:
    with pytest.raises(ErreurRegistre):
        registre["n.existe.pas"]


def test_registre_incoherent_est_refuse(tmp_path: Path) -> None:
    (tmp_path / "references.csv").write_text(
        "id,auteurs,annee,titre,revue,doi_ou_url,type,acces,"
        "fichier_local,notes\n"
        "src,A,2020,T,R,https://x,article_revise,libre,,\n",
        encoding="utf-8",
    )
    (tmp_path / "parametres.csv").write_text(
        "id,nom,valeur,valeur_min,valeur_max,unite,source_id,localisation,"
        "conditions,niveau_preuve,notes\n"
        "x,X,1,,,furlong,src,p. 1,,mesure,\n",
        encoding="utf-8",
    )
    with pytest.raises(ErreurRegistre, match="unité inconnue"):
        Registre.charger(tmp_path)


def test_parametres_cles_de_dormoy_presents(registre: Registre) -> None:
    for id_ in [
        "compresseur.indice_polytropique_etage1",
        "compresseur.indice_polytropique_etage4",
        "compresseur.rendement_electrique",
        "refroidisseur.efficacite_etage1",
        "secheur.efficacite",
        "reservoir.volume_total",
        "reservoir.K_global",
        "reservoir.h_conv_int",
        "reservoir.h_conv_ext",
        "detendeur.ecart_pression_min",
        "essai_charge.energie_consommee",
        "essai_decharge.debit_massique",
        "turbine.etage1.pression_entree",
        "turbine.etage3.rendement_mecanique",
        "cas_base.energie_produite",
    ]:
        assert id_ in registre, id_


def test_le_total_des_puissances_turbine_est_coherent(
    registre: Registre,
) -> None:
    somme = sum(
        registre.si(f"turbine.etage{i}.puissance_electrique")
        for i in (1, 2, 3)
    )
    assert somme == pytest.approx(
        registre.si("turbine.puissance_electrique_totale"), rel=0.01
    )
