# Simulateur CAES : un banc d'essai numérique pour le stockage d'énergie par air comprimé

Simulateur Python du projet Expo-sciences 2026-2027. Il réunit les données des études publiées dans un registre scientifique traçable, modélise chaque composante d'une installation d'air comprimé (compression, refroidissement, séchage, réservoir, détente, turbine, stockage de chaleur, attente) avec plusieurs modèles au choix, valide chacune contre les mesures et simulations publiées, et calcule les performances de n'importe quelle configuration assemblée par fichier, dans les conditions ambiantes choisies (hiver québécois compris). Son cas de référence est le banc d'essai de Dormoy et al. (2024, ÉTS / Hydro-Québec, 190 bar), reproduit à quelques pour cent près.

Objectif : qu'un futur chercheur puisse tester ses propres configurations et ajouter ses propres composantes ou jeux de données. Les règles du dépôt sont dans `CLAUDE.md` ; le plan (phases 6 à 13) dans `../Études/études/plan-simulateur/plan-v2.md` ; l'état d'avancement dans `JOURNAL.md`. Licence : `LICENSE` (GPL-3.0).

## Installation

Python 3.11 ou plus.

```text
cd simulateur
python -m venv .venv
.venv\Scripts\activate          (Windows)
pip install -e ".[dev]"
pytest
```

## Organisation

| Dossier | Contenu |
|---|---|
| `caes/` | Le code du simulateur (modules en français) |
| `data/registre/` | **Registre scientifique** : `references.csv` (sources) et `parametres.csv` (chaque valeur avec sa source, son unité et son niveau de preuve). Généré par `generer_registre_phase0.py` |
| `data/sources/` | Fichiers téléchargés (données supplémentaires de Dormoy). Ne pas exécuter |
| `data/validation/` | Un dossier par jeu de données (`provenance.md`, `references.csv` généré du registre, courbes numérisées) ; `dormoy/A_NUMERISER.md` liste les figures à numériser |
| `data/materiaux/` | Propriétés du gravier, des roches, de l'huile (phase 4) |
| `scenarios/` | Fichiers YAML qui décrivent une installation (composants, chaînes, ambiance) ; `scenarios/README.md` décrit le format ; `scenarios/v1/` garde l'ancien format pour les scripts de validation |
| `validation/` | Scripts qui comparent le simulateur aux références (RMSE, MAPE) |
| `tests/` | Tests pytest : bilans, unités, cas limites |
| `rapports/` | Tableaux et graphiques générés |
| `docs/` | `formules.md` (catalogue des équations), `composants/` (une page par type de composant) et `phase-XX-explication.md` (explications pour l'élève) |
| `JOURNAL.md` | État d'avancement, écarts connus, questions ouvertes |

## Règles du projet

- Unités SI en interne (Pa, K, kg, s, J). Pressions absolues, nommées `p_abs_pa`.
- Aucun chiffre en dur dans le code : tout vient du registre ou d'un scénario.
- Le rendement global est un résultat, jamais une donnée d'entrée.
- Toute chaleur ajoutée à l'air est soit récupérée (traçable jusqu'à une cuve), soit externe et comptée.
- Chaque équation a sa fiche dans `docs/formules.md`.

## Utiliser le registre

```python
from caes.registre import Registre

reg = Registre.charger()
v = reg["reservoir.volume_total"]
print(v)              # reservoir.volume_total = 5.86 m3 [fabricant, dormoy2024, §2.1 ; §3.1 ; §3.3]
print(v.valeur_si)    # 5.86 (m3)
print(reg.si("essai_charge.pression_finale"))   # 19000000.0 (Pa)
print(reg.source("reservoir.K_global").doi_ou_url)
```

## Lancer une simulation

Tout passe par un fichier YAML qui décrit l'installation (format dans `scenarios/README.md`) :

```text
.venv\Scripts\python -m caes simuler scenarios/D.yaml --sortie resultats/D
.venv\Scripts\python -m caes simuler scenarios/D.yaml --modifier ambiance.T_amb=-20degC
.venv\Scripts\python -m caes verifier scenarios/D.yaml
```

Le dossier de résultats contient `resume.md` (installation, résultats, rendements sous les deux définitions, bilans, avertissements de domaine de validité), les séries temporelles en CSV, le tableau « 1000 unités » et sa cascade, des graphiques, et `provenance.md` (chaque paramètre avec sa source et les DOI cités).

En Python :

```python
from caes.assembleur import charger_installation

inst = charger_installation("D.yaml")        # fichier de scenarios/
res = inst.simuler()                          # charge, décharge ou cycles
print(res.resume())
c = res.dernier_cycle
c.charge.series.head()                        # séries temporelles (pandas, SI)
c.decharge.chaleur_par_source                 # kWh par source (cuve_3, externe...)
res.rendements()                              # les deux définitions du RTE
```

Scénarios d'exemple (phase 11) : `python rapports/scenarios_dormoy_gravier.py`, `scenarios_transport.py`, `scenarios_centre_urgence.py`, `scenarios_grande_echelle.py` → `rapports/scenarios/*.md` ; questions, fichiers et lecture dans `scenarios/exemples/README.md`.

Analyse d'une configuration (phase 10) : `python -m caes analyser scenarios/analyse/D.yaml --sortie rapports/phase10` → `analyse.md`, `tornade.png`, `sobol.png`, `incertitudes.png`, `pareto.png` (≈ 50 min sur dix processus ; `--rapide` pour un essai).

Humidité et sécheur (phase 9) : `python rapports/phase9_humidite.py` → `rapports/phase9/humidite.md`, `fig_givre.png` ; scénarios `scenarios/humidite/`.

Tableau de bord de validation (toutes les sources, une commande) : `python validation/tableau_de_bord.py` → `rapports/validation/tableau_de_bord.md`. Rapports détaillés : `python validation/dormoy_charge.py`, `python validation/dormoy_decharge.py`, `python validation/lit_gravier.py`, `python validation/non_regression_phase6.py` ; résultats dans `rapports/phaseN/`.

## Tout régénérer

`python generer_tout.py --liste` donne les quatorze étapes (registre, scénarios dérivés, validation, tableau de bord, rapports de phase, scénarios d'exemple, API, vérification des chiffres cités dans `docs/chiffres_cles.yaml`, tests) ; `python generer_tout.py` les lance toutes (≈ 3 h), `--sans-longs` saute la validation détaillée de Dormoy, la phase 5 et l'analyse de sensibilité. Guides pour chercheurs : `docs/demarrage.md`, `docs/ajouter-un-composant.md`, `docs/ajouter-une-etude.md`, `docs/limites-couvertes.md`, `docs/api.md`.

## Avancement

Voir `JOURNAL.md`.

| Phase | État |
|---|---|
| 0. Projet et registre | Terminée le 2 novembre 2026 |
| 1. Charge, validation sur Dormoy | Terminée le 9 novembre 2026 (écart −2,5 % sur l'énergie, −1 % sur la durée) |
| 2. Décharge, validation sur Dormoy | Terminée le 12 novembre 2026 (essai mesuré à −2 %, tableau 5 à −4 % ; cas de base à −15 %, écart non expliqué) |
| 3. Exergie et tableau « 1000 unités » | Terminée le 19 novembre 2026 (bilans fermés à 0,2 % ; le détendeur détruit 68 % de l'exergie stockée dans le cas de base) |
| 4. Lit de gravier | Terminée le 19 novembre 2026 (vérifié contre la solution exacte de Schumann ; cuves de Tola retrouvées à 0,1–3,6 % ; validation expérimentale en attente des PDF de Cascetta et Barbour) |
| 5. Système intégré Dormoy + gravier | Terminée le 21 novembre 2026 (architectures A à E ; 1,25 m³ de gravier suffisent pour que la turbine reçoive 130/90/90 °C ; D et E à 17,1 %) |
| 6. Architecture « composants », configurations YAML libres, bloc `ambiance` | Terminée le 21 novembre 2026 (huit types de composants avec interface commune ; scénarios de Dormoy et architectures A à E en YAML, reproduits à 0,00000 % ; `python -m caes simuler` ; hiver à −20 °C en changeant un nombre) |
| 7. Bibliothèque des composants et alternatives | Terminée le 21 novembre 2026 (deux à cinq modèles par fonction : isentropique, polytropique à rendement, isotherme, pincement, adiabatique, pression glissante avec Flügel, huile à deux réservoirs, eau sous pression, isolant ; 90 combinaisons testées ; 15 scénarios de variantes) |
| 8. Tableau de bord de validation multi-sources | Terminée le 21 novembre 2026 (51 grandeurs sur Dormoy, Tola, Shi ; 5 mesures reproduites à 2,5 % ; un seul écart non expliqué, le cas de base de Dormoy ; `python validation/tableau_de_bord.py`) |
| 9. Humidité et sécheur | Terminée le 21 novembre 2026 (eau suivie de l'aspiration au rejet ; séparateurs seuls jamais suffisants dans 12 climats, 0,04 à 1 kg d'eau par cycle au fond du réservoir et givre ; sécheur nécessaire mais ce qui compte est son point de rosée, pas sa purge : à −40 °C et 5 % de purge, B passe de 16,8 à 19,7 % ; `python rapports/phase9_humidite.py`) |
| 10. Sensibilité, Pareto, incertitudes | Terminée le 21 novembre 2026 (`python -m caes analyser` : tornade, indices de Sobol, propagation des plages du registre, front de Pareto NSGA-II reproductible, masse des réservoirs à paroi mince calibrée sur Dormoy ; analyse de référence sur D isolée dans `rapports/phase10/analyse.md`) |
| 11. Scénarios d'exemple (Dormoy + gravier, transport, centre d'urgence, grande échelle, solaire) | Terminée le 22 novembre 2026 (quatre scénarios dans `scenarios/exemples/` avec rapports régénérables dans `rapports/scenarios/` ; transport : la chaleur part en exponentielle, τ ≈ 3 semaines sous 20 cm ; centre d'urgence de 72 h : 192 modules et 710 t contre 76 t de batteries, résultat négatif ; solaire non fait) |
| 12. Documentation pour chercheurs et reproductibilité | Terminée le 22 novembre 2026 (guides `docs/demarrage.md`, `ajouter-un-composant.md`, `ajouter-une-etude.md`, `limites-couvertes.md`, API générée ; `generer_tout.py` régénère tout et vérifie les chiffres cités ; intégration continue ; `CITATION.cff` ; test par un tiers à faire) |
| 13. Rapport et jury | À faire |

Architectures : `python rapports/phase5_architectures.py` → `rapports/phase5/architectures.md`. En Python : `from caes.integre import simuler_cycles ; r = simuler_cycles("D.yaml") ; print(r.resume())`.

Lit de gravier : `python validation/lit_gravier.py` → `rapports/phase4/validation_lit_gravier.md`.

Tableau « 1000 unités » : `python rapports/tableau_1000_unites.py` → `rapports/phase3/exergie.md`, `tableau_1000_<cas>.md`, `cascade_<cas>.png`.

Simulation de décharge :

```python
from caes.systeme import simuler_decharge, rendements_aller_retour

d = simuler_decharge("dormoy_decharge_3etages.yaml")
print(d.resume(), d.chaleur_par_source)
```

Rapport : `python validation/dormoy_decharge.py` → `rapports/phase2/validation_decharge.md`.
