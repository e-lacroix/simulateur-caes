# -*- coding: utf-8 -*-
"""Non-régression de la phase 6 aux réglages complets de la phase 5.

    python validation/non_regression_phase6.py

Simule les scénarios de Dormoy et les architectures A à E avec la
nouvelle architecture « composants » (``caes.assembleur``), aux mêmes
réglages que la phase 5, et les compare aux chiffres de référence
calculés par les modules d'origine (``tests/reference/phases_1_5.yaml``,
sections ``rapide`` et ``complet``). Écrit
``rapports/phase6/non_regression.md``. Durée : 3 à 4 minutes.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from caes.assembleur import charger_installation  # noqa: E402
from caes.exergie import bilan_exergie_charge  # noqa: E402
from caes.exergie import bilan_exergie_decharge  # noqa: E402
from caes.registre import Registre  # noqa: E402

DOSSIER = RACINE / "rapports" / "phase6"
REF = yaml.safe_load((RACINE / "tests" / "reference" /
                      "phases_1_5.yaml").read_text(encoding="utf-8"))


def ecart(a: float, b: float) -> str:
    if abs(b) < 1e-9:
        return f"{a:.4g} / {b:.4g}"
    return f"{(a - b) / b * 100:+.4f} %"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    L = ["# Phase 6 : non-régression de l'architecture « composants »\n",
         "*Généré par `validation/non_regression_phase6.py`. Chaque ligne "
         "compare la nouvelle architecture (scénarios `scenarios/*.yaml`, "
         "assemblés par `caes.assembleur`) aux chiffres calculés par les "
         "modules des phases 1 à 5 (`caes.systeme`, `caes.integre`, "
         "scénarios `scenarios/v1/`), enregistrés dans "
         "`tests/reference/phases_1_5.yaml`. Critère du plan : 0,1 %.*\n"]
    pire = 0.0

    L.append("## 1. Scénarios de validation de Dormoy (phases 1 et 2)\n")
    L.append("| Scénario | Grandeur | Phase 6 | Référence | Écart |")
    L.append("|---|---|---|---|---|")
    for nom, att in REF["rapide"]["charge"].items():
        r = charger_installation(f"{nom}.yaml", reg).simuler().charge
        for k, v in att.items():
            e = ecart(r.totaux[k], v)
            pire = max(pire, abs(r.totaux[k] - v) / max(abs(v), 1e-9))
            L.append(f"| {nom} | {k} | {r.totaux[k]:.6g} | {v:.6g} | {e} |")
    for nom, att in REF["rapide"]["decharge"].items():
        r = charger_installation(f"{nom}.yaml", reg).simuler().decharge
        for k, v in att.items():
            if k == "chaleur_par_source":
                for src, q in v.items():
                    e = ecart(r.chaleur_par_source.get(src, 0.0), q)
                    L.append(f"| {nom} | chaleur {src} | "
                             f"{r.chaleur_par_source.get(src, 0.0):.6g} | "
                             f"{q:.6g} | {e} |")
                continue
            e = ecart(r.totaux[k], v)
            pire = max(pire, abs(r.totaux[k] - v) / max(abs(v), 1e-9))
            L.append(f"| {nom} | {k} | {r.totaux[k]:.6g} | {v:.6g} | {e} |")

    L.append("\n## 2. Architectures A à E, réglages de la phase 5\n")
    L.append("| Arch. | Cycles | Charge (kWh) | Produit (kWh) | Réf. produit "
             "| Écart | Chaleur par source (kWh) | Réf. | Cuves fin (kWh) | "
             "Réf. | Unités rendues | Réf. | Résidus exergie | Durée |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    complet = REF.get("complet", {})
    for code in ("A", "B", "C", "D", "E"):
        att = complet.get(code)
        t0 = time.perf_counter()
        r = charger_installation(f"{code}.yaml", reg).simuler()
        duree = time.perf_counter() - t0
        c = r.dernier_cycle
        assert c is not None
        bc = bilan_exergie_charge(c.charge)
        bd = bilan_exergie_decharge(c.decharge)
        unite = bc.entree_j / 1000.0
        rendu = bd.sorties_utiles_j["électricité produite"] / unite
        E_p = c.decharge.totaux["energie_electrique_kwh"]
        src = ", ".join(f"{k} {v:.2f}" for k, v in
                        c.decharge.chaleur_par_source.items()) or "–"
        if att:
            ref_p = att["decharge"]["energie_electrique_kwh"]
            pire = max(pire, abs(E_p - ref_p) / ref_p)
            ref_src = ", ".join(
                f"{k.replace('huile_ideale', 'huile')} {v:.2f}"
                for k, v in att["chaleur_par_source"].items()) or "–"
            ref_cuves = f"{att['chaleur_cuves_fin_kwh']:.2f}"
            ref_rendu = f"{att['unites_1000']['electricite_rendue']:.1f}"
            e = ecart(E_p, ref_p)
            ref_p_txt = f"{ref_p:.4f}"
        else:
            ref_p_txt = ref_src = ref_cuves = ref_rendu = "(absent)"
            e = "–"
        print(f"[{duree:.0f} s] {r.resume()}")
        L.append(
            f"| {code} | {len(r.cycles)}{'' if r.converge else ' (non stab.)'}"
            f" | {c.charge.totaux['energie_electrique_kwh']:.2f} | {E_p:.4f} "
            f"| {ref_p_txt} | {e} | {src} | {ref_src} | "
            f"{c.chaleur_cuves_fin_kwh:.2f} | {ref_cuves} | {rendu:.1f} | "
            f"{ref_rendu} | {bc.residu_relatif * 100:+.2f} % / "
            f"{bd.residu_relatif * 100:+.2f} % | {duree:.0f} s |")
    L.append(f"\n**Pire écart relatif sur l'ensemble : {pire * 100:.5f} %** "
             f"(critère : 0,1 %). Les écarts nuls à la précision affichée "
             f"sont attendus : la nouvelle architecture appelle les mêmes "
             f"fonctions physiques dans le même ordre ; seule la façon de "
             f"les assembler a changé.\n")
    L.append("## 3. Ce que la phase 6 ajoute sans changer les chiffres\n")
    L.append(
        "- Bloc `ambiance` unique (F32) : source froide, pertes, air aspiré "
        "et état mort viennent du même endroit ; profil météo optionnel.\n"
        "- Chaînes de composants (F33) : la chaîne de Dormoy et les "
        "architectures A à E sont décrites par des fichiers YAML sans code "
        "spécifique ; `python -m caes simuler` écrit les résultats.\n"
        "- Avertissements de domaine de validité (Wakao, Cheayb, givrage, "
        "cuve trop froide, lois en pression extrapolées).\n"
        "- Étiquettes de chaleur : le nom du composant (`cuve_3`, `huile`) "
        "ou `externe` ; `huile_ideale` de la phase 5 est devenu `huile` "
        "(le nom du composant dans `C.yaml`).\n")
    (DOSSIER / "non_regression.md").write_text("\n".join(L),
                                               encoding="utf-8")
    print("rapport écrit :", DOSSIER / "non_regression.md")


if __name__ == "__main__":
    main()
