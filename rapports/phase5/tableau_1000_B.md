# Tableau « 1000 unités » : B : 3 étages, chaleur externe (Dormoy)

*Cas `B` : charge `dormoy_charge_1_190_aspiration_chaude_cycle` (243.2 kWh = 1000 unités, 1 unité = 243.241 Wh), puis décharge `dormoy_decharge_3etages_cycle` enchaînée (40.96 kWh produits). État mort : 20 °C, 1.013 bar. Généré par `rapports/tableau_1000_unites.py`.*

| # | Étape | Exergie perdue | Exergie restante | Chaleur (énergie) | Remarque |
|---|---|---|---|---|---|
| 0 | Électricité tirée du réseau |  | 1000 |  | charge |
| 1 | moteur et mécanique | 326 | 674 |  |  |
| 2 | compression étage 1 (chaleur échangée en comprimant) | 3 | 671 | 15 rejetées |  |
| 3 | compression étage 2 (chaleur échangée en comprimant) | 2 | 669 | 8 rejetées |  |
| 4 | compression étage 3 (chaleur échangée en comprimant) | -1 | 670 | -4 rejetées | n > γ : le modèle absorbe un peu de chaleur |
| 5 | compression étage 4 (chaleur échangée en comprimant) | 1 | 669 | 0 rejetées |  |
| 6 | refroidisseur 1 (chaleur rejetée) | 35 | 634 | 159 rejetées, dont 50 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 7 | refroidisseur 2 (chaleur rejetée) | 44 | 590 | 185 rejetées, dont 73 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 8 | refroidisseur 3 (chaleur rejetée) | 54 | 537 | 217 rejetées, dont 97 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 9 | refroidisseur 4 (chaleur rejetée) | 25 | 511 | 132 rejetées, dont 21 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 10 | air rejeté (rendement volumétrique) | 87 | 424 |  | dans le modèle, l'air non refoulé a été comprimé : à lire avec « moteur et mécanique » |
| 11 | air rejeté (sécheur) | 81 | 343 |  |  |
| 12 | laminage vers le réservoir | 0 | 343 |  |  |
| 13 | remplissage du réservoir (mélange) | 1 | 342 |  |  |
| 14 | chaleur perdue par les parois | 3 | 339 | 84 perdues | chaleur tiède : beaucoup d'énergie, peu d'exergie |
| 15 | **Exergie stockée dans les réservoirs** |  | 342 |  | résidu du bilan de charge -0.21 % |
| 16 | Exergie disponible (stock + coussin initial) |  | 473 |  | coussin initial 131 |
| 17 | Réchauffage avant les turbines (source externe ou huile idéale) | -24 | 497 | +211 fournies | exergie apportée = gain de l'air ; à compter si la source est externe |
| 18 | réservoir (détente interne) | -0 | 497 |  |  |
| 19 | chaleur reçue des parois (exergie de froid perdue) | 3 | 494 | 56 reçues des parois | l'air se refroidit en se détendant ; la paroi le réchauffe |
| 20 | détendeur (laminage) | 70 | 424 |  |  |
| 21 | turbine étage 1 (irréversibilité) | 42 | 382 |  |  |
| 22 | génératrice étage 1 | 6 | 376 |  |  |
| 23 | chute de pression avant l'étage 2 | 3 | 372 |  |  |
| 24 | turbine étage 2 (irréversibilité) | 30 | 342 |  |  |
| 25 | génératrice étage 2 | 5 | 337 |  |  |
| 26 | chute de pression avant l'étage 3 | 11 | 326 |  |  |
| 27 | turbine étage 3 (irréversibilité) | 22 | 304 |  |  |
| 28 | génératrice étage 3 | 5 | 299 |  |  |
| 29 | air rejeté à l'atmosphère | -1 | 300 |  |  |
| 30 | Exergie restant dans les réservoirs (coussin) | 131 | 169 |  | pas une perte : reste pour le cycle suivant (plus froid et plus lourd que le coussin initial, d'où une exergie un peu plus grande) |
| 31 | **Électricité rendue au réseau** |  | 168 |  | résidu du bilan de décharge +0.00 % |

Les colonnes « exergie » comptent l'énergie **utile** (travail maximal récupérable) ; la colonne « chaleur » compte de l'**énergie** thermique, dans la même unité. Les deux ne s'additionnent pas : 100 unités de chaleur à 45 °C ne valent que 8 unités d'exergie.
