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
| `data/validation/` | Courbes numérisées des articles ; `A_NUMERISER.md` liste ce qui reste à faire |
| `data/materiaux/` | Propriétés du gravier, des roches, de l'huile (phase 4) |
| `scenarios/` | Fichiers YAML qui décrivent un cas à simuler |
| `validation/` | Scripts qui comparent le simulateur aux références (RMSE, MAPE) |
| `tests/` | Tests pytest : bilans, unités, cas limites |
| `rapports/` | Tableaux et graphiques générés |
| `docs/` | `formules.md` (catalogue des équations) et `phase-XX-explication.md` (explications pour l'élève) |
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

## Lancer une simulation de charge

```python
from caes.systeme import simuler_charge

r = simuler_charge("dormoy_charge_1_190.yaml")   # fichier de scenarios/
print(r.resume())
r.series.head()        # séries temporelles (pandas, unités SI)
r.totaux, r.bilan      # totaux en kWh, bilan d'énergie
```

Rapport de validation sur Dormoy : `python validation/dormoy_charge.py`, puis lire `rapports/phase1/validation_charge.md`.

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
| 6. Architecture « composants », configurations YAML libres, bloc `ambiance` | À faire (plan v2) |
| 7. Bibliothèque des composants et alternatives | À faire |
| 8. Tableau de bord de validation multi-sources | À faire |
| 9. Humidité et sécheur | Souhaitable |
| 10. Sensibilité, Pareto, incertitudes | Souhaitable |
| 11. Scénarios d'exemple (Dormoy + gravier, transport, centre d'urgence, grande échelle, solaire) | À faire |
| 12. Documentation pour chercheurs et reproductibilité | À faire |
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
