# -*- coding: utf-8 -*-
"""Tableau de bord de validation multi-sources (phase 8).

    python validation/tableau_de_bord.py

Pour chaque couple (composant ou chaîne, jeu de données), lance le
scénario correspondant (``scenarios/`` et ``scenarios/validation/``),
compare au chiffre publié (registre) et écrit
``rapports/validation/tableau_de_bord.md`` : une ligne par couple avec
l'écart relatif et le verdict (« reproduit » sous 5 %, sinon « écart
expliqué » ou « **non expliqué** »), les explications, les jeux en
attente, et ``ecarts.png``. Écrit aussi ``references.csv`` dans chaque
dossier ``data/validation/<source>/`` à partir du registre.
Durée : 2 à 4 minutes.
"""

from __future__ import annotations

import csv
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from caes.assembleur import Installation, charger_installation  # noqa: E402
from caes.composants import Contexte, EtatAir  # noqa: E402
from caes.graphiques import (  # noqa: E402
    COULEURS,
    ENCRE_2,
    GRILLE,
    nouvelle_figure,
    style_axes,
    terminer,
)
from caes.lit_gravier import Correlations, LitGravier  # noqa: E402
from caes.materiaux import charger_materiau  # noqa: E402
from caes.proprietes import air_par_defaut  # noqa: E402
from caes.registre import Registre  # noqa: E402
from caes.scenario import charger_scenario  # noqa: E402

DOSSIER = RACINE / "rapports" / "validation"
DONNEES = RACINE / "data" / "validation"
SCEN_VAL = RACINE / "scenarios" / "validation"
SEUIL = 5.0
T0C = 273.15
WH = 3.6e6

NATURES = {"mesure": "mesure", "fabricant": "fabricant",
           "simulation_publiee": "simulation publiée",
           "calcul_personnel": "calcul personnel"}


@dataclass
class Ligne:
    jeu: str
    nature: str
    composant: str
    grandeur: str
    reference: float
    simule: float
    unite: str
    scenario: str
    explication: str = ""
    """Identifiant d'un paragraphe de la section « explications »."""
    note: str = ""
    tolerance_abs: float | None = None
    """Tolérance absolue (températures : RMSE du modèle de Dormoy)."""

    @property
    def ecart_pct(self) -> float:
        if abs(self.reference) < 1e-12:
            return 0.0 if abs(self.simule) < 1e-12 else float("inf")
        return (self.simule - self.reference) / self.reference * 100.0

    @property
    def verdict(self) -> str:
        if self.tolerance_abs is not None:
            if abs(self.simule - self.reference) <= self.tolerance_abs:
                return "reproduit"
        elif abs(self.ecart_pct) <= SEUIL:
            return "reproduit"
        if self.explication and EXPLICATIONS.get(self.explication, (
                "", True))[1]:
            return "écart expliqué"
        return "**non expliqué**"


@dataclass
class Jeu:
    id: str
    nom: str
    nature: str
    ambiance: str
    etat: str
    dossier: str
    prefixes: tuple[str, ...] = ()
    lignes: list[Ligne] = field(default_factory=list)


# ----------------------------------------------------------------------
# Explications (identifiant → (texte, expliqué ?))
# ----------------------------------------------------------------------

EXPLICATIONS: dict[str, tuple[str, bool]] = {
    "cas_base": (
        "**Cas de base de Dormoy (1 étage, 3 → 1 bar, sans réchauffage) : "
        "−15 %, non expliqué depuis la phase 2.** Indépendant de la "
        "température initiale et du modèle thermique du réservoir. "
        "Diagnostics faits : le refroidissement Joule-Thomson du détendeur "
        "(190 → 3 bar) et le refroidissement de l'air dans le réservoir "
        "coûtent ≈ 1,4 kWh chacun ; sans les deux, 15,8 kWh. Dormoy "
        "modélise pourtant ces effets. Hypothèse restante : un détail du "
        "calcul de turbine non publié (travail calculé aux conditions "
        "nominales du tableau 9 ?). C'est une question ouverte du projet ; "
        "l'écart est montré, pas calibré.", False),
    "trois_etages": (
        "**Décharge à 3 étages : durée −6 %, énergie −16 % par rapport à "
        "« 16 % de 290 kWh ».** Dormoy donne 62 kW pendant 40 min, soit "
        "41,3 kWh et 14,2 % de 290 kWh, et non 16 % (qui demanderait "
        "45 min) : son texte est incohérent. Notre 39,0 kWh en 37,6 min "
        "(14,1 % de notre charge 55 → 190 bar) est entre les deux lectures. "
        "La durée plus courte vient de l'arrêt à 55 bar (consigne 40 + "
        "écart 15) et du modèle de réservoir à paroi, validé sur l'essai "
        "de décharge.", True),
    "chaleur_sup130": (
        "**Chaleur des refroidisseurs au-dessus de 130 °C : −8 %.** Elle "
        "dépend de la répartition des rapports entre les étages 3 et 4 "
        "(lois linéaires en pression, hypothèse F07) et de la température "
        "de l'air de refroidissement (20 °C supposés). Les étages 2 et 3 "
        "portent l'écart ; la chaleur totale (191,6 contre 189,2 kWh) est "
        "reproduite.", True),
    "tola_cave": (
        "**Chaîne de compression de Tola : énergie du compresseur CVHP et "
        "durée.** Tola ne décrit pas le modèle thermique de sa caverne "
        "(gaz parfait entre 15 et 55 °C) ; nous la prenons quasi isotherme "
        "à l'ambiant (15 °C), ce qui y met 7 % d'air de plus qu'à 35 °C : "
        "la charge de 6 h n'atteint pas tout à fait 10 MPa et le CVHP "
        "travaille à des rapports un peu plus bas. Les compresseurs CLP, "
        "CIP et CHP, à rapport fixe, ne dépendent pas de la caverne.", True),
    "tola_turbines": (
        "**Turbines de Tola : énergie plus haute que le tableau 9, "
        "rendement aller-retour du cas C +5 %.** Nos scénarios réchauffent "
        "l'air à une température "
        "constante (130, 150 ou 170 °C) par une source externe ; chez "
        "Tola, les cuves de gravier rendent cette température pendant "
        "environ deux tiers de la décharge, puis de l'air de plus en plus "
        "froid (jusqu'à ≈ 80 °C dans le cas A). L'écart mesure cette fin "
        "de décharge, que le lit de gravier de la phase 4 reproduit à "
        "part (ligne « cuves TES »). La répartition des rapports entre "
        "les trois turbines (« shared out ») est aussi une hypothèse "
        "(parts égales). Précision sur le tableau 10 de Tola : les "
        "tableaux 7 et 9 sont mécaniques et le rendement 0,674 applique "
        "0,97 des deux côtés (28,48 × 0,97 / (39,76 / 0,97)) ; nous "
        "faisons de même.", True),
    "shi_cycle": (
        "**Cas de Shi : bilan du cycle.** Shi impose 8 h de charge et 6 h "
        "de décharge et calcule le volume (1,18 × 10⁵ m³) qui les permet ; "
        "nous imposons le volume et laissons les durées sortir. Les "
        "écarts restants viennent du réservoir adiabatique, dont la "
        "température en fin de charge dépend de l'historique des cycles "
        "(Shi donne 2,78 → 70 °C sans dire comment il obtient 2,78 °C), et "
        "du refroidisseur du compresseur 4, qui rejette ici à l'ambiant "
        "plutôt que dans l'eau (à 80 °C, cette eau diluerait le réservoir "
        "chaud). Le réservoir froid est maintenu à 30 °C comme chez Shi "
        "(refroidissement du retour non modélisé). Prépublication non "
        "révisée : ses propres chiffres ne sont pas tous cohérents (fiche "
        "`maths-vulgarisees-secondaire5.md`).", True),
    "shi_comp4": (
        "**Cas de Shi : compresseur 4 à 7 MPa, −7 %.** La figure 7 de Shi "
        "fait sortir le compresseur 4 à 7,55 MPa quand le réservoir est à "
        "7 MPa, soit 0,55 MPa de surpression, alors que le tableau 4 n'en "
        "justifie que 0,24 (0,2 MPa à l'entrée du réservoir et 0,04 dans "
        "le dernier échangeur). Avec 0,24 MPa, le rapport de l'étage 4 "
        "vaut 1,50 au lieu de 1,57 et sa puissance est plus basse de 7 %. "
        "Les trois premiers compresseurs sont reproduits à 0,1 % près.",
        True),
    "shi_eau": (
        "**Cas de Shi : chaleur stockée dans l'eau.** Référence "
        "recalculée (calcul personnel) à partir de 4193,7 t d'eau chauffée "
        "de 30 à 190 °C ; notre stockage à deux réservoirs bien mélangés "
        "plafonne l'eau à 207 °C et prend l'air du compresseur 4 à part "
        "(refroidisseur ambiant), d'où une quantité stockée différente.",
        True),
    "tes_tola": (
        "**Cuves de gravier de Tola : +0,1 à +4 %.** Tola ne publie ni sa "
        "corrélation d'échange ni ses pertes ; Wakao et isolation parfaite "
        "ici. Avec 30 cellules et 12 cycles (phase 4 : 52 cellules, 20 "
        "cycles), l'accord est en partie une coïncidence de modèles "
        "proches ; la validation expérimentale (Cascetta, Barbour) attend "
        "les PDF.", True),
}


def pct(x: float) -> str:
    return f"{x:+.1f} %"


# ----------------------------------------------------------------------
# Outils
# ----------------------------------------------------------------------


def _scenario_modifie(nom: str, modifs: dict, suffixe: str, reg: Registre):
    """Charge un scénario brut, applique des remplacements sur le dict
    YAML et le résout (pour les changements de chaîne)."""
    base = RACINE / "scenarios" / nom
    brut = yaml.safe_load(base.read_text(encoding="utf-8"))
    for chemin, valeur in modifs.items():
        noeud = brut
        parties = chemin.split(".")
        for p in parties[:-1]:
            noeud = noeud[int(p)] if isinstance(noeud, list) else noeud[p]
        noeud[parties[-1]] = valeur
    brut["nom"] = f"{brut.get('nom', base.stem)}_{suffixe}"
    tmp = Path(tempfile.gettempdir()) / f"caes_{base.stem}_{suffixe}.yaml"
    tmp.write_text(yaml.safe_dump(brut, allow_unicode=True,
                                  sort_keys=False), encoding="utf-8")
    return charger_scenario(tmp, reg)


def _installation(nom: str, reg: Registre,
                  modifications: list[str] | None = None) -> Installation:
    chemin = SCEN_VAL / nom if (SCEN_VAL / nom).exists() else nom
    return charger_installation(chemin, reg, modifications=modifications)


def ecrire_references_csv(reg: Registre, jeu: Jeu) -> None:
    dossier = DONNEES / jeu.dossier
    dossier.mkdir(parents=True, exist_ok=True)
    with open(dossier / "references.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "grandeur", "valeur", "valeur_min", "valeur_max",
                    "unite", "localisation", "conditions", "niveau_preuve"])
        for par in reg.parametres.values():
            if any(par.id.startswith(p) for p in jeu.prefixes):
                w.writerow([par.id, par.nom, par.valeur, par.valeur_min,
                            par.valeur_max, par.unite, par.localisation,
                            par.conditions, par.niveau_preuve])


# ----------------------------------------------------------------------
# Jeux de données
# ----------------------------------------------------------------------


def cas_dormoy(reg: Registre) -> tuple[Jeu, Jeu, Jeu]:
    amb = ("20 °C, 1,013 bar, 50 % (hypothèses), air aspiré à 52 °C "
           "(déduit du débit mesuré)")
    mes = Jeu("dormoy_charge", "Dormoy 2024, essai de charge mesuré "
              "(§ 3.1, 20 réservoirs, 5,86 m³)", "mesure", amb,
              "disponible", "dormoy", ("essai_charge.",))
    mes_d = Jeu("dormoy_decharge", "Dormoy 2024, essai de décharge mesuré "
                "(§ 3.1, 8 réservoirs, 2,56 m³)", "mesure", amb,
                "disponible", "dormoy", ("essai_decharge.",))
    sim = Jeu("dormoy_simulations", "Dormoy 2024, simulations publiées et "
              "données fabricant (tableaux 5, 6, 9 ; § 3.3)",
              "simulation publiée", "mêmes hypothèses", "disponible",
              "dormoy", ("cas_base.", "cas_etages.", "charge_55_190.",
                         "refroidisseur.", "turbine.etage",
                         "dormoy_modele."))
    # --- essai de charge --------------------------------------------------
    r = _installation("dormoy_charge_1_190_aspiration_chaude.yaml",
                      reg).simuler().charge
    assert r is not None
    sc = "dormoy_charge_1_190_aspiration_chaude.yaml"
    mes.lignes += [
        Ligne(mes.nom, "mesure", "chaîne de charge (compresseur, "
              "refroidisseurs, sécheur, réservoir)", "énergie électrique "
              "1 → 190 bar", reg.si("essai_charge.energie_consommee") / WH,
              r.totaux["energie_electrique_kwh"], "kWh", sc),
        Ligne(mes.nom, "mesure", "chaîne de charge", "durée 1 → 190 bar",
              reg.si("essai_charge.duree") / 3600, r.totaux["duree_h"], "h",
              sc, note="« almost 10 h »"),
        Ligne(mes.nom, "mesure", "chaîne de charge", "puissance moyenne",
              reg.si("essai_charge.puissance_moyenne") / 1e3,
              r.totaux["puissance_moyenne_kw"], "kW", sc),
    ]
    # --- essai de décharge ------------------------------------------------
    d = _installation("dormoy_decharge_essai.yaml", reg).simuler().decharge
    assert d is not None
    mes_d.lignes.append(Ligne(
        mes_d.nom, "mesure", "réservoir (paroi) + détendeur isenthalpique",
        "durée 190 → 50 bar (2,56 m³, 0,148 kg/s)",
        reg.si("essai_decharge.duree") / 60, d.totaux["duree_min"], "min",
        "dormoy_decharge_essai.yaml"))
    d2 = _installation("dormoy_decharge_essai.yaml", reg, [
        "composants.detendeur.modele=cheayb"]).simuler().decharge
    assert d2 is not None
    mes_d.lignes.append(Ligne(
        mes_d.nom, "mesure", "réservoir (paroi) + détendeur de Cheayb",
        "durée 190 → 50 bar", reg.si("essai_decharge.duree") / 60,
        d2.totaux["duree_min"], "min", "dormoy_decharge_essai.yaml "
        "(--modifier composants.detendeur.modele=cheayb)"))
    # --- charge 55 → 190, tableau 6 ---------------------------------------
    r55 = _installation("dormoy_charge_55_190.yaml", reg, [
        "ambiance.T_aspiration=52degC"]).simuler().charge
    assert r55 is not None
    sc55 = ("dormoy_charge_55_190.yaml (--modifier "
            "ambiance.T_aspiration=52degC)")
    sim.lignes += [
        Ligne(sim.nom, "simulation publiée", "chaîne de charge",
              "durée 55 → 190 bar", reg.si("charge_55_190.duree") / 3600,
              r55.totaux["duree_h"], "h", sc55),
        Ligne(sim.nom, "simulation publiée", "refroidisseurs (efficacité)",
              "chaleur rejetée 55 → 190 bar",
              reg.si("refroidisseur.energie_chaleur_totale") / WH,
              r55.totaux["chaleur_refroidisseurs_kwh"], "kWh", sc55),
        Ligne(sim.nom, "simulation publiée", "refroidisseurs (efficacité)",
              "chaleur rejetée au-dessus de 130 °C",
              reg.si("refroidisseur.energie_chaleur_sup130_totale") / WH,
              r55.totaux["chaleur_sup_seuil_kwh"], "kWh", sc55,
              "chaleur_sup130"),
    ]
    # --- tableau 9 : turbine DEPRAG au point nominal ------------------------
    inst = _installation("dormoy_decharge_3etages.yaml", reg)
    turb = inst.composants["turbine"]
    ctx = Contexte(inst.air, inst.ambiance, 0.0, 1.0)
    m = turb.debit_massique_kg_s  # type: ignore[attr-defined]
    for i in (1, 2, 3):
        et = turb.etage(i)  # type: ignore[attr-defined]
        etat, flux = et.pas(EtatAir(et.p_entree_pa, et.T_entree_cible_K, m),
                            ctx)
        r_et = flux.resultat
        sim.lignes += [
            Ligne(sim.nom, "fabricant", f"turbine DEPRAG, étage {i}",
                  "température de sortie",
                  reg.si(f"turbine.etage{i}.temperature_sortie") - T0C,
                  r_et.T_out_K - T0C, "°C", "dormoy_decharge_3etages.yaml "
                  "(point nominal)",
                  note="tolérance : RMSE du modèle de Dormoy (2,83 °C)",
                  tolerance_abs=reg.si(
                      "dormoy_modele.charge.T_etage4.RMSE_calibre")),
            Ligne(sim.nom, "fabricant", f"turbine DEPRAG, étage {i}",
                  "puissance électrique",
                  reg.si(f"turbine.etage{i}.puissance_electrique") / 1e3,
                  flux.W_el_produit_w / 1e3, "kW",
                  "dormoy_decharge_3etages.yaml (point nominal)"),
        ]
    # --- décharge à 3 étages, tableau 5 ------------------------------------
    d3 = inst.simuler().decharge
    assert d3 is not None
    q_ref = sum(
        (reg[f"turbine.etage{i}.puissance_chaleur_requise"].valeur_si
         if not reg[f"turbine.etage{i}.puissance_chaleur_requise"].est_plage
         else 0.5 * (reg[f"turbine.etage{i}.puissance_chaleur_requise"]
                     .valeur_min_si
                     + reg[f"turbine.etage{i}.puissance_chaleur_requise"]
                     .valeur_max_si))
        for i in (1, 2, 3)) * 40 * 60 / WH
    sim.lignes += [
        Ligne(sim.nom, "simulation publiée", "réchauffage à 3 étages",
              "chaleur de réchauffage (tableau 5 : 46,2 kWh)", 46.2,
              d3.totaux["chaleur_rechauffage_kwh"], "kWh",
              "dormoy_decharge_3etages.yaml",
              note=f"puissances du tableau 5 × 40 min = {q_ref:.1f} kWh"),
        Ligne(sim.nom, "simulation publiée", "décharge à 3 étages",
              "durée 190 → 55 bar", 40.0, d3.totaux["duree_min"], "min",
              "dormoy_decharge_3etages.yaml", "trois_etages"),
        Ligne(sim.nom, "simulation publiée", "décharge à 3 étages",
              "énergie produite (16 % de 290 kWh)",
              reg.si("cas_etages.rte_3etages_prechauffe")
              * reg.si("cas_etages.energie_consommee_3etages") / WH,
              d3.totaux["energie_electrique_kwh"], "kWh",
              "dormoy_decharge_3etages.yaml", "trois_etages"),
        Ligne(sim.nom, "simulation publiée", "cycle à 3 étages",
              "rendement aller-retour sans compter la chaleur",
              reg.si("cas_etages.rte_3etages_prechauffe") * 100,
              d3.totaux["energie_electrique_kwh"]
              / r55.totaux["energie_electrique_kwh"] * 100, "%",
              "dormoy_decharge_3etages.yaml / dormoy_charge_55_190.yaml",
              "trois_etages"),
    ]
    # --- cas de base --------------------------------------------------------
    db = _installation("dormoy_decharge_base.yaml", reg).simuler().decharge
    assert db is not None
    sim.lignes.append(Ligne(
        sim.nom, "simulation publiée", "décharge à 1 étage sans réchauffage",
        "énergie produite (cas de base)",
        reg.si("cas_base.energie_produite") / WH,
        db.totaux["energie_electrique_kwh"], "kWh",
        "dormoy_decharge_base.yaml", "cas_base"))
    # --- 1 étage réchauffé à 90 °C : RTE 5,5 % -------------------------
    sc90 = _scenario_modifie("dormoy_decharge_base.yaml", {
        "composants.turbine.etages.0.T_entree_cible":
            "registre:turbine.etage3.temperature_entree",
        "composants.chaudiere": {"type": "stockage_chaleur",
                                 "modele": "source_externe"},
        "decharge.chaine": ["reservoir", "detendeur", "chaudiere",
                            "turbine.1"]}, "rechauffe90", reg)
    d90 = charger_installation(sc90, reg).simuler().decharge
    assert d90 is not None
    r18 = _installation("dormoy_charge_1_190_aspiration_chaude.yaml", reg, [
        "charge.reservoir_initial.p=18bar"]).simuler().charge
    assert r18 is not None
    sim.lignes.append(Ligne(
        sim.nom, "simulation publiée", "cycle à 1 étage réchauffé à 90 °C",
        "rendement aller-retour (fig. 16)",
        reg.si("cas_etages.rte_1etage_prechauffe") * 100,
        d90.totaux["energie_electrique_kwh"]
        / r18.totaux["energie_electrique_kwh"] * 100, "%",
        "dormoy_decharge_base.yaml (chaudière à 90 °C) / charge 18 → 190"))
    return mes, mes_d, sim


def cas_tola(reg: Registre, n_cellules: int = 30,
             n_cycles: int = 12) -> Jeu:
    jeu = Jeu("tola2022", "Tola 2022, LT-ACAES de 10 MW (tableaux 1, 6 à "
              "10)", "simulation publiée", "15 °C, 1,01 bar (tableau 1) ; "
              "humidité : hypothèse", "disponible", "tola2022",
              ("tola.", "materiau.gravier_tola."))
    # --- cuves de gravier (phase 4, réglages réduits) ------------------------
    air = air_par_defaut()
    gravier = charger_materiau("gravier_tola", reg)
    corr = Correlations(
        wakao_a=reg.si("lit.wakao.a"), wakao_b=reg.si("lit.wakao.b"),
        wakao_c=reg.si("lit.wakao.c"), wakao_Re_min=reg.si("lit.wakao.Re_min"),
        wakao_Re_max=reg.si("lit.wakao.Re_max"),
        ergun_A=reg.si("lit.ergun.A"), ergun_B=reg.si("lit.ergun.B"),
        jeffreson_facteur=reg.si("lit.jeffreson.facteur"))
    D_t = reg.si("tola.tes_lp.diametre")
    H_t = D_t * reg.si("tola.tes_lp.rapport_hauteur_diametre")
    T_amb = reg.si("tola.T_amb")
    for nom, cle in (("TES-LP", "tes_lp"), ("TES-IP", "tes_ip"),
                     ("TES-HP", "tes_hp")):
        lit = LitGravier(gravier, D_t, H_t, n_cellules=n_cellules,
                         correlations=corr)
        lit.initialiser(reg.si("tola.tes.T_entree_decharge"))
        p_c = reg.si(f"tola.{cle}.pression_charge")
        E_de = 0.0
        for _ in range(n_cycles):
            lit.simuler(air, 60.0, reg.si("tola.tes.duree_charge"),
                        reg.si("tola.tes.debit_charge"),
                        reg.si("tola.tes.T_entree_charge"), p_c, T_amb, 1)
            rd = lit.simuler(air, 60.0, reg.si("tola.tes.duree_decharge"),
                             reg.si("tola.tes.debit_decharge"),
                             reg.si("tola.tes.T_entree_decharge"), p_c,
                             T_amb, -1)
            E_de = -rd["Q_air_vers_solide_j"][0]
        jeu.lignes.append(Ligne(
            jeu.nom, "simulation publiée", f"lit de gravier (Schumann), "
            f"cuve {nom}", "chaleur rendue par cycle stable (tableau 8)",
            reg.si(f"tola.{cle}.energie_stockee") / WH / 1e3, E_de / WH / 1e3,
            "MWh", f"validation/lit_gravier.py (ici {n_cellules} cellules, "
            f"{n_cycles} cycles)", "tes_tola"))
    # --- compresseurs, tableau 7 -------------------------------------
    r = _installation("tola_charge.yaml", reg).simuler().charge
    assert r is not None
    s = r.series
    eta_mg = reg.si("tola.rendement_moteur_generateur")
    note_mec = ("tableaux 7 et 9 : grandeurs mécaniques (le tableau 10 "
                "applique 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / "
                "0,97) = 0,674)")
    for i, nom in enumerate(("CLP", "CIP", "CHP"), 1):
        P = (s[f"w_pol_{i}_j_kg"] * s["m_dot_asp_kg_s"]).mean() / 1e3
        jeu.lignes.append(Ligne(
            jeu.nom, "simulation publiée", f"compresseur polytropique "
            f"(0,88) + pincement 20 K, étage {nom}",
            "puissance mécanique moyenne (tableau 7)",
            reg.si(f"tola.compresseur.{nom}.puissance") / 1e3, P, "kW",
            "validation/tola_charge.yaml", note=note_mec))
    E4 = float((s["w_pol_4_j_kg"] * s["m_dot_asp_kg_s"]).sum()
               * r.totaux["duree_s"] / len(s) / WH / 1e3)
    E_comp_mec = r.totaux["energie_electrique_kwh"] * eta_mg / 1e3
    jeu.lignes += [
        Ligne(jeu.nom, "simulation publiée", "compresseur CVHP (6,4 → "
              "10 MPa) et caverne", "énergie mécanique sur la charge "
              "(tableau 7)",
              reg.si("tola.compresseur.CVHP.energie") / WH / 1e3,
              E4, "MWh", "validation/tola_charge.yaml", "tola_cave"),
        Ligne(jeu.nom, "simulation publiée", "chaîne de compression",
              "énergie mécanique totale (tableau 7)",
              reg.si("tola.compresseur.energie_totale") / WH / 1e3,
              E_comp_mec, "MWh", "validation/tola_charge.yaml", "tola_cave"),
        Ligne(jeu.nom, "simulation publiée", "caverne (quasi isotherme)",
              "pression en fin de charge de 6 h",
              reg.si("tola.cave.pression_max") / 1e5, r.totaux["p_finale_bar"],
              "bar", "validation/tola_charge.yaml", "tola_cave"),
    ]
    # --- turbines, tableau 9 --------------------------------------------
    E_C = 0.0
    for cas in ("A", "B", "C"):
        d = _installation(f"tola_decharge_{cas}.yaml", reg).simuler().decharge
        assert d is not None
        E_mec = d.totaux["energie_mecanique_kwh"] / 1e3
        if cas == "C":
            E_C = d.totaux["energie_electrique_kwh"] / 1e3
        jeu.lignes += [
            Ligne(jeu.nom, "simulation publiée", f"turbines polytropiques "
                  f"(0,86) en pression glissante, cas {cas}",
                  "énergie mécanique produite sur 3 h (tableau 9)",
                  reg.si(f"tola.turbine.energie_cas_{cas}") / WH / 1e3, E_mec,
                  "MWh", f"validation/tola_decharge_{cas}.yaml",
                  "tola_turbines", note=note_mec),
            Ligne(jeu.nom, "simulation publiée", f"turbines, cas {cas}",
                  "puissance mécanique maximale (début de décharge, "
                  "tableau 9)",
                  reg.si(f"tola.turbine.puissance_max_cas_{cas}") / 1e3,
                  d.series["P_mec_w"].max() / 1e3, "kW",
                  f"validation/tola_decharge_{cas}.yaml", "tola_turbines"),
        ]
    jeu.lignes.append(Ligne(
        jeu.nom, "simulation publiée", "cycle complet, cas C",
        "rendement aller-retour (tableau 10, 0,97 des deux côtés)",
        reg.si("tola.rte.cas_C") * 100,
        E_C / (r.totaux["energie_electrique_kwh"] / 1e3) * 100, "%",
        "validation/tola_charge.yaml / tola_decharge_C.yaml",
        "tola_turbines"))
    return jeu


def cas_shi(reg: Registre) -> Jeu:
    jeu = Jeu("shi2024", "Shi 2024, A-CAES de 100 MW (prépublication non "
              "révisée ; tableau 4, figure 7, tableau 5)",
              "simulation publiée", "25 °C, 0,1 MPa (tableau 4) ; eau "
              "froide 30 °C ; humidité : hypothèse", "disponible", "shi2024",
              ("shi.",))
    res = _installation("shi_100MW.yaml", reg).simuler()
    c = res.dernier_cycle
    assert c is not None
    ch, d = c.charge, c.decharge
    sc = "validation/shi_100MW.yaml (dernier cycle)"
    E_c = ch.totaux["energie_electrique_kwh"] / 1e3
    E_p = d.totaux["energie_electrique_kwh"] / 1e3
    jeu.lignes += [
        Ligne(jeu.nom, "simulation publiée", "cycle complet",
              "rendement aller-retour", reg.si("shi.rte") * 100,
              E_p / E_c * 100, "%", sc, "shi_cycle"),
        Ligne(jeu.nom, "simulation publiée", "chaîne de charge (isentropique "
              "0,86, eau sous pression, réservoir adiabatique)",
              "énergie consommée par cycle",
              reg.si("shi.energie_charge") / WH / 1e3, E_c, "MWh", sc,
              "shi_cycle"),
        Ligne(jeu.nom, "simulation publiée", "chaîne de charge",
              "durée de charge 4 → 10 MPa", reg.si("shi.duree_charge") / 3600,
              ch.totaux["duree_h"], "h", sc, "shi_cycle"),
        Ligne(jeu.nom, "simulation publiée", "chaîne de décharge "
              "(pression glissante, isentropique 0,90)",
              "énergie produite par cycle",
              reg.si("shi.energie_decharge") / WH / 1e3, E_p, "MWh", sc,
              "shi_cycle"),
        Ligne(jeu.nom, "simulation publiée", "chaîne de décharge",
              "durée de décharge 10 → 4 MPa",
              reg.si("shi.duree_decharge") / 3600, d.totaux["duree_min"] / 60,
              "h", sc, "shi_cycle"),
        Ligne(jeu.nom, "simulation publiée", "réservoir adiabatique de "
              "1,18 × 10⁵ m³", "masse d'air stockée par cycle",
              reg.si("shi.masse_air") / 1e3,
              ch.totaux["masse_stockee_kg"] / 1e3, "t", sc, "shi_cycle"),
    ]
    # puissances par étage quand le réservoir est à 7 MPa
    s = ch.series
    k = int(np.argmin(np.abs(s["p_res_pa"].to_numpy() - 70e5)))
    eta = (reg.si("shi.rendement_mecanique")
           * reg.si("shi.rendement_electrique"))
    for i in (1, 2, 3, 4):
        P = s[f"w_pol_{i}_j_kg"].iloc[k] * s["m_dot_asp_kg_s"].iloc[k] / eta
        jeu.lignes.append(Ligne(
            jeu.nom, "simulation publiée", f"compresseur {i} (isentropique "
            f"0,86)", "puissance électrique à 7 MPa",
            reg.si(f"shi.compresseur.puissance_{i}") / 1e3, P / 1e3, "kW",
            sc, "shi_comp4" if i == 4 else ""))
    sd = d.series
    k = int(np.argmin(np.abs(sd["p_res_pa"].to_numpy() - 70e5)))
    for i in (1, 2, 3):
        jeu.lignes.append(Ligne(
            jeu.nom, "simulation publiée", f"turbine {i} (isentropique "
            f"0,90)", "puissance électrique à 7 MPa",
            reg.si(f"shi.turbine.puissance_{i}") / 1e3,
            sd[f"P_el_{i}_w"].iloc[k] / 1e3, "kW", sc))
    actif = float((s["w_pol_4_j_kg"] > 1.0).mean()) * ch.totaux["duree_h"]
    jeu.lignes.append(Ligne(
        jeu.nom, "simulation publiée", "compresseur 4 (étage libre)",
        "durée de fonctionnement par charge",
        reg.si("shi.compresseur4.duree_fonctionnement") / 3600, actif, "h",
        sc, "shi_cycle"))
    Q_eau_ref = (reg.si("shi.masse_eau") * 4190.0
                 * (reg.si("shi.eau.T_chaud") - reg.si("shi.T_eau_froide"))
                 / WH / 1e3)
    jeu.lignes.append(Ligne(
        jeu.nom, "calcul personnel", "stockage d'eau sous pression",
        "chaleur stockée par charge (4193,7 t de 30 à 190 °C)", Q_eau_ref,
        ch.totaux["chaleur_cuves_kwh"] / 1e3, "MWh", sc, "shi_eau",
        note="référence recalculée, cp ≈ 4,19 kJ/kg·K"))
    jeu.note = res.resume()  # type: ignore[attr-defined]
    return jeu


def jeux_en_attente() -> list[Jeu]:
    return [
        Jeu("castellani2018", "Castellani 2018, micro-CAES de 2,2 kW "
            "(Energies 11:1921, accès libre)", "mesure", "à renseigner",
            "en attente du PDF (MDPI refuse les robots) : à déposer dans "
            "`data/sources/castellani2018/`", "castellani2018"),
        Jeu("luo", "Luo et al. (via Zhang S. 2025, § 3.3) : 3 × 90 L, "
            "tampon 50 L", "mesure", "non donnée",
            "partiel : article de Luo introuvable, courbes de Zhang non "
            "numérisées, modèle de vanne non implémenté", "luo_zhangS2025"),
        Jeu("cascetta2018", "Cascetta 2018, lit de roches mesuré "
            "(Energy Procedia, accès libre)", "mesure", "à renseigner",
            "en attente du PDF (ScienceDirect refuse les robots)",
            "cascetta2018"),
        Jeu("barbour2015", "Barbour 2015, A-CAES avec lit compact "
            "(Applied Energy, accès libre)", "mesure et modèle",
            "à renseigner", "en attente du PDF", "barbour2015"),
        Jeu("venkataramani2018", "Venkataramani 2018, petit CAES "
            "expérimental", "mesure", "non disponible",
            "non accessible légalement pour l'instant", "venkataramani2018"),
    ]


def courbes_numerisees() -> list[Path]:
    return sorted((DONNEES / "dormoy").glob("fig*.csv"))


# ----------------------------------------------------------------------
# Rapport
# ----------------------------------------------------------------------


def _valeur_figure(l: Ligne) -> tuple[float, str]:
    """Position de la barre (les températures sont ramenées à leur
    tolérance : ± 5 sur l'axe = ± tolérance) et étiquette."""
    if l.tolerance_abs:
        d = l.simule - l.reference
        return d / l.tolerance_abs * SEUIL, f"{d:+.1f} °C"
    return max(min(l.ecart_pct, 60.0), -60.0), pct(l.ecart_pct)


def figure_ecarts(lignes: list[Ligne]) -> str:
    fig, ax = nouvelle_figure(9.0, 0.32 * len(lignes) + 1.5)
    noms = [f"{l.grandeur} ({l.jeu.split(',')[0]})" for l in lignes]
    valeurs = [_valeur_figure(l) for l in lignes]
    palette = {"reproduit": COULEURS[2], "écart expliqué": COULEURS[3],
               "**non expliqué**": COULEURS[1]}
    couleurs = [palette[l.verdict] for l in lignes]
    y = np.arange(len(lignes))
    ax.barh(y, [v for v, _ in valeurs], color=couleurs, height=0.7)
    ax.axvspan(-SEUIL, SEUIL, color=GRILLE, alpha=0.6, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(noms, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(-60, 60)
    style_axes(ax, "Écart à la référence (bande : ± 5 % ; températures : "
               "± 2,83 °C)", "Écart relatif (%)", "")
    for yy, (v, txt) in zip(y, valeurs):
        ax.text(v + (1 if v >= 0 else -1), yy, txt, va="center",
                ha="left" if v >= 0 else "right", fontsize=7,
                color=ENCRE_2)
    return terminer(fig, ax, DOSSIER / "ecarts.png", None)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DOSSIER.mkdir(parents=True, exist_ok=True)
    reg = Registre.charger()
    t0 = time.perf_counter()
    jeux: list[Jeu] = []
    for fabrique in (cas_dormoy, cas_tola, cas_shi):
        t1 = time.perf_counter()
        out = fabrique(reg)
        for j in (out if isinstance(out, tuple) else (out,)):
            jeux.append(j)
            print(f"[{time.perf_counter() - t1:.0f} s] {j.nom} : "
                  f"{len(j.lignes)} lignes")
    attente = jeux_en_attente()
    for j in jeux + attente:
        if j.prefixes:
            ecrire_references_csv(reg, j)
    lignes = [l for j in jeux for l in j.lignes]
    fig = figure_ecarts(lignes)
    # CSV
    with open(DOSSIER / "tableau_de_bord.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["jeu", "nature", "composant", "grandeur", "reference",
                    "simule", "unite", "ecart_pct", "verdict", "scenario"])
        for l in lignes:
            w.writerow([l.jeu, l.nature, l.composant, l.grandeur,
                        f"{l.reference:.6g}", f"{l.simule:.6g}", l.unite,
                        f"{l.ecart_pct:.2f}", l.verdict.replace("**", ""),
                        l.scenario])
    # Markdown
    n_mes = sum(1 for j in jeux if j.nature == "mesure")
    n_ok = sum(1 for l in lignes if l.verdict == "reproduit")
    n_exp = sum(1 for l in lignes if l.verdict == "écart expliqué")
    n_non = sum(1 for l in lignes if l.verdict == "**non expliqué**")
    L = ["# Tableau de bord de validation\n",
         f"*Généré par `validation/tableau_de_bord.py` en "
         f"{time.perf_counter() - t0:.0f} s. Chaque ligne compare une "
         f"grandeur simulée par le simulateur à un chiffre publié, avec son "
         f"niveau de preuve. Verdict : « reproduit » si l'écart est sous "
         f"{SEUIL:.0f} %, sinon « écart expliqué » (paragraphe en section "
         f"4) ou **non expliqué**. Une validation faite dans les conditions "
         f"ambiantes d'un article ne vaut que pour ces conditions.*\n",
         f"**Bilan** : {len(jeux)} jeux disponibles ({n_mes} mesurés, "
         f"les deux essais de Dormoy ; {len(jeux) - n_mes} simulations "
         f"publiées), "
         f"{len(attente)} en attente ; {len(lignes)} grandeurs comparées : "
         f"{n_ok} reproduites, {n_exp} écarts expliqués, {n_non} non "
         f"expliqué(s).\n",
         "## 1. Jeux de données\n",
         "| Jeu | Nature | Ambiance | État | Provenance |",
         "|---|---|---|---|---|"]
    for j in jeux + attente:
        L.append(f"| {j.nom} | {j.nature} | {j.ambiance} | {j.etat} | "
                 f"`data/validation/{j.dossier}/provenance.md` |")
    csvs = courbes_numerisees()
    L.append(f"\nCourbes numérisées de Dormoy déposées dans "
             f"`data/validation/dormoy/` : "
             f"{', '.join(c.name for c in csvs) if csvs else 'aucune'} "
             f"(voir `A_NUMERISER.md`).\n")
    L.append("## 2. Tableau de bord\n")
    L.append("| Jeu | Nature | Composant ou chaîne | Grandeur | Référence | "
             "Simulé | Unité | Écart | Verdict | Scénario | Note |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for l in lignes:
        ref = f"{l.reference:.4g}"
        simu = f"{l.simule:.4g}"
        ecart = (f"{l.simule - l.reference:+.1f} °C" if l.unite == "°C"
                 else pct(l.ecart_pct))
        verdict = l.verdict
        if l.explication and verdict != "reproduit":
            verdict += f" ([{l.explication}](#{l.explication}))"
        L.append(f"| {l.jeu.split(',')[0]} | {l.nature} | {l.composant} | "
                 f"{l.grandeur} | {ref} | {simu} | {l.unite} | {ecart} | "
                 f"{verdict} | `{l.scenario}` | {l.note} |")
    L.append(f"\n![écarts]({fig})\n")
    L.append("## 3. Ce que chaque jeu valide, et ce qu'il ne valide pas\n")
    L.append(
        "- **Dormoy, mesures** : la seule source mesurée. Valide la chaîne "
        "de charge (énergie, durée, puissance) et le réservoir en décharge "
        "avec le détendeur. Ne valide pas la turbine (Dormoy ne l'a pas "
        "installée), ni le gravier, ni l'hiver (20 °C supposés).\n"
        "- **Dormoy, simulations** : vérification croisée avec un modèle "
        "calibré sur les mêmes mesures ; la turbine DEPRAG est une donnée "
        "fabricant au point nominal.\n"
        "- **Tola** : vérification croisée d'un modèle à 10 MW ; le lit de "
        "gravier est en plus vérifié contre la solution exacte de Schumann "
        "(phase 4). Hypothèses de notre côté : Wakao, caverne quasi "
        "isotherme, répartition égale des turbines, isolation parfaite.\n"
        "- **Shi** : cas test de changement d'échelle (100 MW) avec les "
        "hypothèses de Shi (rendements constants, réservoir adiabatique) ; "
        "prépublication non révisée.\n"
        "- Trois mots différents : **vérifier** (solution exacte), "
        "**croiser** (autre simulation), **valider** (mesure) ; voir "
        "`docs/phase-08-explication.md`.\n")
    L.append("## 4. Explications des écarts\n")
    for ident, (texte, _) in EXPLICATIONS.items():
        L.append(f"<a id=\"{ident}\"></a>\n{texte}\n")
    L.append("## 5. Régénérer\n")
    L.append("```text\n.venv\\Scripts\\python validation/tableau_de_bord.py\n"
             "```\n\nLes scripts détaillés des phases 1 à 5 restent "
             "disponibles (`validation/dormoy_charge.py`, "
             "`validation/dormoy_decharge.py`, `validation/lit_gravier.py`) "
             "avec leurs graphiques ; ce tableau en reprend les chiffres de "
             "synthèse avec les scénarios du format « composants ».\n")
    (DOSSIER / "tableau_de_bord.md").write_text("\n".join(L),
                                                encoding="utf-8")
    print(f"{len(lignes)} lignes : {n_ok} reproduites, {n_exp} expliquées, "
          f"{n_non} non expliquées ; rapport :",
          DOSSIER / "tableau_de_bord.md")


if __name__ == "__main__":
    main()
