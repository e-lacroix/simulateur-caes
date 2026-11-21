# Phase 3 : bilan d'exergie et tableau « 1000 unités »

*Généré par `rapports/tableau_1000_unites.py`. Un tableau détaillé et une cascade par cas.*

## 1. Résumé des cas

| Cas | Charge | 1000 unités = | Stocké | Électricité rendue | Chaleur externe (énergie) | RTE | Résidus (charge / décharge) |
|---|---|---|---|---|---|---|---|
| base | dormoy_charge_1_190_aspiration_chaude_depuis18 | 351.8 kWh | 329 | 40 | 0 | 4.0 % | -0.22 % / +0.00 % |
| 3etages | dormoy_charge_1_190_aspiration_chaude_depuis55 | 276.3 kWh | 341 | 155 | 204 | 15.5 % | -0.21 % / -0.00 % |
| base_chargeA | dormoy_charge_1_190_depuis18 | 339.9 kWh | 341 | 41 | 0 | 4.1 % | +0.00 % / -0.00 % |

## 2. Comparaison avec le calcul à la main de la fiche Dormoy (cas de base)

Le calcul à la main (fiche `dormoy-2024-caes-hors-sol.md`, section 2) supposait un gaz parfait à 15 °C, un détendeur réglé à 35 bar et un arrêt à 50 bar. Le simulateur montre (phase 2) que le cas de base de Dormoy utilise l'étage 3 seul, donc un détendeur à 3 bar et un arrêt à 18 bar : la répartition des pertes change beaucoup.

| Étape | Calcul à la main (fiche) | Simulateur | Explication |
|---|---|---|---|
| Moteur et mécanique | 285 | 331 (+ 87 d'air non refoulé) | la fiche prenait 69-74 % sans le rendement électrique (94,5 %) ; le modèle applique le travail au débit aspiré, d'où la ligne « air non refoulé » à lire avec celle-ci |
| Compression « chaude » | 271 | 5 + 156 (refroidisseurs) | la fiche comptait l'excès de travail par rapport à l'isotherme ; l'exergie compte la valeur de la chaleur rejetée, plus faible parce qu'une partie est tiède |
| Sécheur | 84 | 81 | même logique (19 % de l'air à l'état de sortie) ; exergie réelle au lieu du gaz parfait |
| Réservoir (laminage, remplissage, parois) | 0 | 14 | non compté dans la fiche |
| **Stocké** | **360** | **329** | |
| Masse morte / coussin | 65 (arrêt à 50 bar) | 22 (arrêt à 18 bar) | pas une perte par cycle : l'air reste |
| Détendeur | 74 (190 → 35 bar) | 234 (190 → 3 bar) | **la vraie perte dominante du cas de base** |
| Réservoir en décharge | 0 | 7 | détente interne et chaleur reçue des parois |
| Turbine (et génératrice) | 175 | 25 | avec le détendeur à 3 bar, il reste peu d'exergie à détruire dans la turbine |
| Air rejeté froid | 0 | 19 | l'air sort à −60 °C : son « froid » est une exergie perdue |
| **Électricité rendue** | **46** | **40** | Dormoy : 43-46 ; écart de −15 % connu depuis la phase 2 |

### Ce que le simulateur change dans l'histoire

- La recharge coûte toujours les deux tiers : moteur, air non refoulé, chaleur rejetée et sécheur. Les refroidisseurs rejettent 689 unités de **chaleur**, mais seulement 156 unités d'**exergie** : la chaleur tiède vaut peu, c'est la part au-dessus de 130 °C qui compte pour la turbine.
- Dans le cas de base, le détendeur n'est pas une perte parmi d'autres : il détruit 68 % de l'exergie disponible, parce qu'il fait chuter la pression de 190 à 3 bar sans rien produire. La turbine à 3 étages (détendeur à 40 bar) est d'abord un moyen de réduire cette perte.
- La « masse morte » du cas de base est petite (arrêt à 18 bar) et n'est pas une perte par cycle.


## 3. Cas à 3 étages : où va l'exergie du réchauffage

| Poste | Unités |
|---|---|
| Exergie stockée par la charge (55 → 190 bar) | 341 |
| Coussin initial (55 bar) | 99 |
| Réchauffage externe : chaleur fournie (énergie) | 204 |
| Réchauffage externe : exergie apportée à l'air | 21 |
| Détendeur (190 → 40 bar) | 64 |
| Turbines (3 étages) et génératrices | 102 |
| Air rejeté | -1 |
| Coussin final (55 bar) | 123 |
| **Électricité rendue** | **155** |

La chaleur de réchauffage apporte beaucoup d'énergie mais nettement moins d'exergie (facteur de Carnot à 130 °C : 27 %). Si elle vient des refroidisseurs du compresseur (phases 4 et 5), elle ne coûte rien ; si elle vient d'une source externe, il faut l'ajouter à la consommation (phase 2, deux définitions du rendement).


## 4. Fichiers

- `tableau_1000_base.md`, `cascade_base.png`

![cascade base](cascade_base.png)

- `tableau_1000_3etages.md`, `cascade_3etages.png`

![cascade 3etages](cascade_3etages.png)

- `tableau_1000_base_chargeA.md`, `cascade_base_chargeA.png`

![cascade base_chargeA](cascade_base_chargeA.png)
