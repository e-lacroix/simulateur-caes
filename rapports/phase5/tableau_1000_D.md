# Tableau « 1000 unités » : D : 3 étages, gravier direct (3 cuves sous pression)

*Cas `D` : charge `dormoy_charge_1_190_aspiration_chaude_cycle` (239.5 kWh = 1000 unités, 1 unité = 239.463 Wh), puis décharge `dormoy_decharge_3etages_cycle` enchaînée (41.05 kWh produits). État mort : 20 °C, 1.013 bar. Généré par `rapports/tableau_1000_unites.py`.*

| # | Étape | Exergie perdue | Exergie restante | Chaleur (énergie) | Remarque |
|---|---|---|---|---|---|
| 0 | Électricité tirée du réseau |  | 1000 |  | charge |
| 1 | moteur et mécanique | 326 | 674 |  |  |
| 2 | compression étage 1 (chaleur échangée en comprimant) | 3 | 671 | 15 rejetées |  |
| 3 | compression étage 2 (chaleur échangée en comprimant) | 2 | 669 | 8 rejetées |  |
| 4 | compression étage 3 (chaleur échangée en comprimant) | -1 | 670 | -4 rejetées | n > γ : le modèle absorbe un peu de chaleur |
| 5 | compression étage 4 (chaleur échangée en comprimant) | 1 | 669 | 1 rejetées |  |
| 6 | refroidisseur 1 (chaleur rejetée) | 21 | 648 | 110 rejetées, dont 22 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 7 | refroidisseur 2 (chaleur rejetée) | 32 | 616 | 152 rejetées, dont 39 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 8 | refroidisseur 3 (chaleur rejetée) | 19 | 597 | 102 rejetées, dont 19 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 9 | refroidisseur 4 (chaleur rejetée) | 21 | 576 | 118 rejetées, dont 14 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 10 | air rejeté (rendement volumétrique) | 89 | 487 |  | dans le modèle, l'air non refoulé a été comprimé : à lire avec « moteur et mécanique » |
| 11 | air rejeté (sécheur) | 82 | 405 |  |  |
| 12 | laminage vers le réservoir | 0 | 404 |  |  |
| 13 | remplissage du réservoir (mélange) | 0 | 404 |  |  |
| 14 | chaleur perdue par les parois | 3 | 401 | 83 perdues | chaleur tiède : beaucoup d'énergie, peu d'exergie |
| 15 | cuve 1 (échange air-gravier en charge) | 1 | 401 |  |  |
| 16 | cuve 2 (échange air-gravier en charge) | 0 | 400 |  |  |
| 17 | cuve 3 (échange air-gravier en charge) | 2 | 398 |  |  |
| 18 | **Exergie stockée dans les réservoirs** |  | 348 |  | résidu du bilan de charge -0.22 % |
| 19 | Exergie disponible (stock + coussin initial) |  | 481 |  | coussin initial 133 |
| 20 | Exergie puisée dans les cuves de gravier | -52 | 534 | +215 fournies à l'air | chaleur de compression stockée pendant la charge |
| 21 | réservoir (détente interne) | -0 | 534 |  |  |
| 22 | chaleur reçue des parois (exergie de froid perdue) | 3 | 531 | 57 reçues des parois | l'air se refroidit en se détendant ; la paroi le réchauffe |
| 23 | détendeur (laminage) | 71 | 459 |  |  |
| 24 | turbine étage 1 (irréversibilité) | 43 | 416 |  |  |
| 25 | génératrice étage 1 | 6 | 410 |  |  |
| 26 | chute de pression avant l'étage 2 | 3 | 407 |  |  |
| 27 | turbine étage 2 (irréversibilité) | 31 | 376 |  |  |
| 28 | génératrice étage 2 | 5 | 371 |  |  |
| 29 | chute de pression avant l'étage 3 | 11 | 359 |  |  |
| 30 | turbine étage 3 (irréversibilité) | 22 | 337 |  |  |
| 31 | génératrice étage 3 | 5 | 332 |  |  |
| 32 | air rejeté à l'atmosphère | -1 | 333 |  |  |
| 33 | cuve 3 (restitution gravier → air) | 16 | 317 |  |  |
| 34 | cuve 2 (restitution gravier → air) | 3 | 313 |  |  |
| 35 | cuve 1 (restitution gravier → air) | 8 | 305 |  |  |
| 36 | Exergie restant dans les réservoirs (coussin) | 134 | 172 |  | pas une perte : reste pour le cycle suivant (plus froid et plus lourd que le coussin initial, d'où une exergie un peu plus grande) |
| 37 | **Électricité rendue au réseau** |  | 171 |  | résidu du bilan de décharge +0.00 % |

Les colonnes « exergie » comptent l'énergie **utile** (travail maximal récupérable) ; la colonne « chaleur » compte de l'**énergie** thermique, dans la même unité. Les deux ne s'additionnent pas : 100 unités de chaleur à 45 °C ne valent que 8 unités d'exergie.
