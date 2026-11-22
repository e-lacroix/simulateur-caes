# -*- coding: utf-8 -*-
"""Phase 7 : comparaison des modèles de la bibliothèque sur le banc de
Dormoy.

    python rapports/phase7_variantes.py

Fait tourner les scénarios de ``scenarios/variantes/`` (un par modèle
nouveau) et les références correspondantes de ``scenarios/``, puis écrit
``rapports/phase7/variantes.md`` : pour chaque fonction, un tableau qui
compare les modèles (énergie, chaleur, températures, avertissements).
Durée : environ 2 minutes.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from caes.assembleur import ResultatSimulation  # noqa: E402
from caes.assembleur import charger_installation  # noqa: E402
from caes.registre import Registre  # noqa: E402

DOSSIER = RACINE / "rapports" / "phase7"
VARIANTES = RACINE / "scenarios" / "variantes"
T0C = 273.15


def simuler(nom: str, reg: Registre) -> tuple[ResultatSimulation, float]:
    chemin = VARIANTES / nom if (VARIANTES / nom).exists() else nom
    t0 = time.perf_counter()
    r = charger_installation(chemin, reg).simuler()
    return r, time.perf_counter() - t0


def avis_txt(r: ResultatSimulation, n: int = 3) -> str:
    avis = r.avertissements
    if not avis:
        return "aucun"
    txt = " ; ".join(a.message.split(" :")[0][:70] for a in avis[:n])
    if len(avis) > n:
        txt += f" ; (+{len(avis) - n})"
    return txt


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    L = ["# Phase 7 : les modèles de la bibliothèque comparés sur le banc "
         "de Dormoy\n",
         "*Généré par `rapports/phase7_variantes.py`. Chaque ligne est un "
         "scénario de `scenarios/` ou `scenarios/variantes/` ; seul le "
         "composant nommé change par rapport à la référence. Les "
         "avertissements sont ceux du simulateur (domaine de validité).*\n"]

    # --- charge --------------------------------------------------------
    L.append("## 1. Charge 1 → 190 bar (référence : aspiration chaude, "
             "386 kWh)\n")
    L.append("| Scénario | Modèle changé | Électricité (kWh) | Durée (h) | "
             "Chaleur des refroidisseurs (kWh) | dont > 130 °C | T sortie "
             "étage 3 (°C, moy.) | T finale réservoir (°C) | Avertissements |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    charges = [
        ("dormoy_charge_1_190_aspiration_chaude.yaml", "référence (Dormoy)"),
        ("charge_compresseur_isentropique.yaml",
         "compresseur isentropique η_s = 0,86 (Shi)"),
        ("charge_compresseur_polytropique_rendement.yaml",
         "compresseur polytropique η_p = 0,88 (Tola)"),
        ("charge_compresseur_isotherme.yaml",
         "compresseur isotherme (borne, Baniamerian)"),
        ("charge_refroidisseur_pincement.yaml",
         "refroidisseurs à pincement 20 K (Tola)"),
        ("charge_refroidisseur_perte_de_charge.yaml",
         "isentropique + pincement 10 K + Δp 0,04 MPa (Shi)"),
        ("charge_secheur_aucun.yaml", "sans sécheur"),
        ("charge_reservoir_adiabatique.yaml",
         "réservoir adiabatique + 0,2 MPa (Shi)"),
    ]
    for nom, modele in charges:
        r, dt = simuler(nom, reg)
        ch = r.charge
        assert ch is not None
        s = ch.series
        print(f"[{dt:.0f} s] {r.resume()}")
        L.append(
            f"| `{nom}` | {modele} | "
            f"{ch.totaux['energie_electrique_kwh']:.1f} | "
            f"{ch.totaux['duree_h']:.2f} | "
            f"{ch.totaux['chaleur_refroidisseurs_kwh']:.1f} | "
            f"{ch.totaux['chaleur_sup_seuil_kwh']:.1f} | "
            f"{s['T_out_comp_3_K'].mean() - T0C:.0f} | "
            f"{ch.totaux['T_finale_degC']:.0f} | {avis_txt(r)} |")

    # --- décharge ------------------------------------------------------
    L.append("\n## 2. Décharge 190 → 55 bar, 3 étages (référence : DEPRAG, "
             "réchauffage externe)\n")
    L.append("| Scénario | Modèle changé | Électricité (kWh) | Durée (min) | "
             "Débit moyen (kg/s) | Chaleur externe (kWh) | T rejet min (°C) "
             "| p entrée étage 1 (bar, début → fin) | Avertissements |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    decharges = [
        ("dormoy_decharge_3etages.yaml", "référence (DEPRAG, détendeur)"),
        ("decharge_turbine_isentropique.yaml",
         "turbine isentropique η_s = 0,90 (Shi)"),
        ("decharge_turbine_polytropique_rendement.yaml",
         "turbine polytropique η_p = 0,86 (Tola)"),
        ("decharge_pression_glissante.yaml",
         "pression glissante, η_s constant (Shi)"),
        ("decharge_flugel.yaml", "pression glissante + Flügel (Zhang S.)"),
    ]
    for nom, modele in decharges:
        r, dt = simuler(nom, reg)
        d = r.decharge
        assert d is not None
        s = d.series
        print(f"[{dt:.0f} s] {r.resume()}")
        L.append(
            f"| `{nom}` | {modele} | "
            f"{d.totaux['energie_electrique_kwh']:.2f} | "
            f"{d.totaux['duree_min']:.1f} | {d.totaux['debit_kg_s']:.3f} | "
            f"{d.chaleur_par_source.get('externe', 0.0):.1f} | "
            f"{d.totaux['T_rejet_min_degC']:.0f} | "
            f"{s['p_in_turb_1_pa'].iloc[0] / 1e5:.0f} → "
            f"{s['p_in_turb_1_pa'].iloc[-1] / 1e5:.0f} | {avis_txt(r)} |")

    # --- cycles --------------------------------------------------------
    L.append("\n## 3. Cycles avec stockage de chaleur (référence : D, "
             "gravier direct, attente 1 h)\n")
    L.append("| Scénario | Stockage / attente | Cycles | Charge (kWh) | "
             "Produit (kWh) | RTE | Chaleur rendue (kWh) | Chaleur restante "
             "(kWh) | Pertes pendant l'attente (kWh) | T entrée turbines "
             "(°C, moy.) | Avertissements |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    cycles = [
        ("D.yaml", "gravier direct, attente 1 h sans pertes (phase 5)"),
        ("cycles_huile_deux_reservoirs.yaml",
         "huile à deux réservoirs (Tola, Wolf et Budt)"),
        ("cycles_eau_sous_pression.yaml", "eau sous pression 18 bar (Shi)"),
        ("cycles_attente_sans_pertes_14j.yaml",
         "gravier, 14 j sans pertes (borne)"),
        ("cycles_gravier_isolant_14j.yaml",
         "gravier, 14 j, 20 cm de laine minérale"),
    ]
    for nom, modele in cycles:
        r, dt = simuler(nom, reg)
        c = r.dernier_cycle
        assert c is not None
        s = c.decharge.series
        E_c = c.charge.totaux["energie_electrique_kwh"]
        E_p = c.decharge.totaux["energie_electrique_kwh"]
        T_in = " / ".join(f"{s[f'T_in_turb_{i}_K'].mean() - T0C:.0f}"
                          for i in (1, 2, 3) if f"T_in_turb_{i}_K" in s)
        print(f"[{dt:.0f} s] {r.resume()}")
        L.append(
            f"| `{nom}` | {modele} | {len(r.cycles)}"
            f"{'' if r.converge else ' (non stab.)'} | {E_c:.1f} | {E_p:.2f} "
            f"| {E_p / E_c * 100:.1f} % | "
            f"{c.decharge.totaux['chaleur_rechauffage_kwh']:.1f} | "
            f"{c.chaleur_cuves_fin_kwh:.1f} | {c.pertes_attente_kwh:.1f} | "
            f"{T_in} | {avis_txt(r)} |")
    L.append(
        "\n## 4. Lecture\n\n"
        "- Les modèles génériques (isentropique, polytropique à rendement) "
        "avec les rendements de Tola et de Shi ne reproduisent pas le banc "
        "de Dormoy : ce sont des rendements de grosses turbomachines "
        "appliqués à un compresseur à pistons de 45 kW. Ils servent au "
        "changement d'échelle (phase 8, cas de Shi), pas à la validation.\n"
        "- La borne isotherme dit ce qu'aucun compresseur ne peut battre ; "
        "l'écart avec Dormoy mesure la chaleur de compression.\n"
        "- La pression glissante supprime la perte du détendeur ; avec la "
        "formule de Flügel, le débit suit la pression et la turbine DEPRAG "
        "se retrouve très loin de son point nominal : le gain n'est réel "
        "qu'avec une turbine conçue pour cette plage.\n"
        "- Les deux réservoirs d'huile ou d'eau alimentent les turbines "
        "comme le gravier au volume de base ; l'eau est plafonnée par son "
        "ébullition (18 bar : 202 °C) alors que les compresseurs de Dormoy "
        "sortent jusqu'à 195 °C en moyenne.\n"
        "- Après 14 jours derrière 20 cm de laine minérale, les cuves de "
        "base perdent une part de leur chaleur et les turbines reçoivent "
        "de l'air plus froid ; c'est le point de départ du scénario de "
        "transport (phase 11).\n")
    (DOSSIER / "variantes.md").write_text("\n".join(L), encoding="utf-8")
    print("rapport écrit :", DOSSIER / "variantes.md")


if __name__ == "__main__":
    main()
