# Simulateur CAES : air comprimé et gravier

Simulateur Python du projet Expo-sciences 2026-2027. Il reproduit le banc d'essai d'air comprimé de Dormoy et al. (2024, ÉTS / Hydro-Québec, 190 bar), puis l'améliore avec un stockage de chaleur dans du gravier, pour répondre à une question : combien d'électricité un module transporté par bateau peut-il livrer après 7 à 56 jours, et qu'est-ce qu'il faudrait pour que ce soit viable ?

Le plan complet (phases, priorités, règles) est dans `../Études/études/plan-simulateur/`.

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
| 5. Système intégré Dormoy + gravier | À faire |

Lit de gravier : `python validation/lit_gravier.py` → `rapports/phase4/validation_lit_gravier.md`.

Tableau « 1000 unités » : `python rapports/tableau_1000_unites.py` → `rapports/phase3/exergie.md`, `tableau_1000_<cas>.md`, `cascade_<cas>.png`.

Simulation de décharge :

```python
from caes.systeme import simuler_decharge, rendements_aller_retour

d = simuler_decharge("dormoy_decharge_3etages.yaml")
print(d.resume(), d.chaleur_par_source)
```

Rapport : `python validation/dormoy_decharge.py` → `rapports/phase2/validation_decharge.md`.
