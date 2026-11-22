# Fichiers d'analyse (phase 10)

Un fichier d'analyse décrit **ce qu'on fait varier** dans un scénario et **ce qu'on regarde**. Il se lance avec :

```
python -m caes analyser scenarios/analyse/D.yaml --sortie rapports/phase10 [--procs 10] [--etapes tornade,sobol,incertitudes,pareto] [--rapide]
```

et produit `analyse.md` (tableaux), `evaluations.csv` (toutes les simulations) et quatre figures (`tornade.png`, `sobol.png`, `incertitudes.png`, `pareto.png`). Les simulations tournent en parallèle (`--procs`, défaut : cœurs − 2). `--rapide` réduit les échantillons à presque rien : il sert à vérifier le format, pas à produire un résultat. `--rendu` réécrit le rapport depuis le `resultats.pkl` du dossier de sortie, sans resimuler (utile après un changement de mise en forme).

| Fichier | Scénario | Usage |
|---|---|---|
| `D.yaml` | `variantes/cycles_gravier_isolant_14j.yaml` (D avec isolant, attente ramenée à un jour) | analyse de référence de la phase 10 (`rapports/phase10/analyse.md`), dix paramètres, ≈ 50 min sur dix processus |
| `B_rapide.yaml` | `B.yaml`, un cycle, pas grossiers | démonstration du format et tests (`tests/test_analyse.py`) |

## Format

```yaml
nom: D_isolee
description: ...
scenario: ../variantes/cycles_gravier_isolant_14j.yaml   # relatif au fichier, à scenarios/ ou absolu
modifications_de_base:            # mêmes « chemin=valeur[unite] » que --modifier
  - composants.attente.duree=1j
  - simulation.nombre_max=2

sorties:                          # ce qu'on observe (la première sert aux figures)
  - rte_sans_chaleur
  - energie_produite_kwh
  - masse_totale_kg
  - decharge.T_rejet_min_degC

parametres:
  - nom: p_max                    # identifiant court
    chemin: charge.p_cible        # feuille du scénario (valeur SI)
    etiquette: Pression maximale du réservoir
    unite: bar                    # unité d'affichage et des bornes
    plage: {min: 120, max: 250}   # choix de l'analyse
  - nom: rendement_electrique
    chemin: composants.compresseur.rendement_electrique
    plage: registre               # bornes valeur_min / valeur_max du registre
  - nom: volume_cuves
    chemins: [composants.cuve_1.volume, composants.cuve_2.volume]
    facteur: {min: 0.5, max: 2}   # plusieurs feuilles multipliées ensemble
  - nom: T_paroi
    chemin: ...
    plage: hypothese              # ± ecart_hypothese (20 % par défaut)

sobol: {n: 32, graine: 1}                       # n puissance de 2 ; n·(d+2) simulations
incertitudes: {n: 48, graine: 1, parametres: [rendement_electrique, ...]}
pareto:
  objectifs:
    - {sortie: energie_produite_kwh, sens: max}
    - {sortie: masse_totale_kg, sens: min}
  variables: [p_max, volume_cuves]
  population: 16
  generations: 12
  p_croisement: 0.9
  eta_croisement: 15
  eta_mutation: 20
  graine: 1
masse:                                          # F44, pour les sorties masse_*
  pression: charge.p_cible                      # chemin de la pression de conception
  diametre: registre:reservoir.diametre_interieur
  resistance_specifique: registre:reservoir.resistance_specifique_equivalente
  coefficient_securite: registre:reservoir.coefficient_securite
```

## Sorties disponibles

| Clé | Sens |
|---|---|
| `rte_sans_chaleur`, `rte_avec_chaleur_externe`, `energie_consommee_kwh`, `energie_produite_kwh`, `chaleur_externe_kwh` | rendements du dernier cycle (F20) |
| `charge.<total>`, `decharge.<total>` | tout total du dernier cycle (`charge.duree_h`, `decharge.givre_total_kg`, `decharge.T_rejet_min_degC`, …) |
| `pertes_attente_kwh`, `nombre_cycles`, `converge` | attente et convergence des cycles |
| `masse_reservoirs_kg`, `masse_cuves_kg`, `masse_totale_kg`, `volume_reservoirs_m3`, `volume_cuves_m3` | masse des réservoirs à paroi mince (F44) et des stockages (gravier : volume × (1 − ε) × ρ ; liquides : masse déclarée) |

## Méthodes

- **Tornade** (un paramètre à la fois, F45) : 2d + 1 simulations ; lisible, sans interactions.
- **Sobol** (F45) : `scipy.stats.sobol_indices`, estimateur de Saltelli, intervalle bootstrap ; n·(d + 2) simulations.
- **Incertitudes** (F45) : hypercube latin dans les plages du registre ; intervalles 5–95 % et corrélations de rang.
- **Pareto** (F46) : NSGA-II (tri non dominé, encombrement, SBX, mutation polynomiale), tous les réglages dans le rapport ; une simulation échouée est pénalisée.
- **Domaine de validité** : tous les avertissements émis pendant les balayages sont comptés (section 7 du rapport).

Une simulation qui échoue (assemblage refusé, par exemple pression cible sous la pression initiale) donne `nan` et est comptée, jamais masquée.
