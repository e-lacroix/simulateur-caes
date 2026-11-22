# -*- coding: utf-8 -*-
"""Génère ``phases_1_5.yaml`` : les chiffres validés des phases 1 à 5,
calculés par les modules d'origine (``caes.systeme``, ``caes.integre``)
sur les scénarios ``scenarios/v1/``. Le test ``test_non_regression.py``
compare la nouvelle architecture (phase 6) à ce fichier à 0,1 % près.

    python tests/reference/generer_reference_phases_1_5.py [--complet]

Section ``rapide`` : réglages réduits pour D et E (2 cycles, 15 cellules),
utilisée par le test. Section ``complet`` (option ``--complet``, 3 min) :
réglages de la phase 5, utilisée par ``validation/non_regression_phase6.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from caes.exergie import bilan_exergie_charge, bilan_exergie_decharge  # noqa
from caes.integre import simuler_cycles  # noqa: E402
from caes.registre import Registre  # noqa: E402
from caes.scenario import charger_scenario  # noqa: E402
from caes.systeme import simuler_charge, simuler_decharge  # noqa: E402

SORTIE = Path(__file__).resolve().parent / "phases_1_5.yaml"
CLES_CHARGE = ("energie_electrique_kwh", "duree_h", "puissance_moyenne_kw",
               "chaleur_refroidisseurs_kwh", "chaleur_sup_seuil_kwh",
               "chaleur_paroi_reservoir_kwh", "T_finale_degC",
               "masse_stockee_kg")
CLES_DECHARGE = ("energie_electrique_kwh", "duree_min",
                 "chaleur_rechauffage_kwh", "p_finale_bar", "T_finale_degC",
                 "T_rejet_min_degC", "masse_soutiree_kg")


def _tot(res, cles) -> dict[str, float]:
    return {k: float(res.totaux[k]) for k in cles if k in res.totaux}


def _cycle(r) -> dict:
    c = r.dernier
    bc = bilan_exergie_charge(c.charge)
    bd = bilan_exergie_decharge(c.decharge)
    unite = bc.entree_j / 1000.0
    return {
        "cycles": len(r.cycles),
        "converge": bool(r.converge),
        "charge": _tot(c.charge, CLES_CHARGE),
        "decharge": _tot(c.decharge, CLES_DECHARGE),
        "chaleur_par_source": {
            k: float(v) for k, v in c.decharge.chaleur_par_source.items()},
        "chaleur_cuves_fin_kwh": float(c.chaleur_cuves_fin_kwh),
        "chaleur_cuves_charge_kwh": float(
            c.charge.totaux["chaleur_cuves_kwh"]),
        "unites_1000": {
            "stock_reservoirs": float(bc.sorties_utiles_j[
                "exergie stockée dans les réservoirs"] / unite),
            "electricite_rendue": float(bd.sorties_utiles_j[
                "électricité produite"] / unite),
            "detendeur": float(bd.postes["détendeur (laminage)"] / unite),
            "residu_charge": float(bc.residu_relatif),
            "residu_decharge": float(bd.residu_relatif),
        },
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    complet = "--complet" in sys.argv
    reg = Registre.charger()
    ref: dict = {}
    if SORTIE.exists():
        ref = yaml.safe_load(SORTIE.read_text(encoding="utf-8")) or {}
    rapide: dict = {"charge": {}, "decharge": {}, "cycles": {}}
    for nom in ("dormoy_charge_1_190", "dormoy_charge_1_190_aspiration_chaude",
                "dormoy_charge_55_190"):
        r = simuler_charge(charger_scenario(f"v1/{nom}.yaml", reg))
        rapide["charge"][nom] = _tot(r, CLES_CHARGE)
        print(nom, r.resume())
    for nom in ("dormoy_decharge_essai", "dormoy_decharge_base",
                "dormoy_decharge_3etages"):
        r = simuler_decharge(charger_scenario(f"v1/{nom}.yaml", reg))
        d = _tot(r, CLES_DECHARGE)
        for i in (1, 2, 3):
            k = f"chaleur_rechauffage_{i}_kwh"
            if k in r.totaux:
                d[k] = float(r.totaux[k])
        d["chaleur_par_source"] = {k: float(v) for k, v in
                                   r.chaleur_par_source.items()}
        rapide["decharge"][nom] = d
        print(nom, r.resume())
    for code in ("A", "B", "C", "D", "E"):
        sc = charger_scenario(f"v1/{code}.yaml", reg)
        mods = {"cycles.nombre_max": 2}
        if code in ("D", "E"):
            mods["cuves.n_cellules"] = 15
        r = simuler_cycles(sc.avec(mods, "court"), reg)
        rapide["cycles"][code] = _cycle(r)
        print(code, r.resume())
    ref["rapide"] = rapide
    ref["reglages_rapide"] = ("A à E : 2 cycles au plus ; D et E : 15 "
                              "cellules par cuve")
    if complet:
        complet_d: dict = {}
        for code in ("A", "B", "C", "D", "E"):
            r = simuler_cycles(f"v1/{code}.yaml", reg)
            complet_d[code] = _cycle(r)
            print("complet", code, r.resume())
        ref["complet"] = complet_d
        ref["reglages_complet"] = "réglages de la phase 5 (scenarios/v1)"
    ref["origine"] = ("généré par tests/reference/"
                      "generer_reference_phases_1_5.py avec caes.systeme et "
                      "caes.integre (modules des phases 1 à 5)")
    SORTIE.write_text(yaml.safe_dump(ref, allow_unicode=True,
                                     sort_keys=False), encoding="utf-8")
    print("écrit :", SORTIE)


if __name__ == "__main__":
    main()
