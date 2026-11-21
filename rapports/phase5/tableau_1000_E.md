# Tableau « 1000 unités » : E : 3 étages, gravier + boucle d'air (cuves à 1 bar, 2 × 20 K)

*Cas `E` : charge `dormoy_charge_1_190_aspiration_chaude_cycle` (239.4 kWh = 1000 unités, 1 unité = 239.426 Wh), puis décharge `dormoy_decharge_3etages_cycle` enchaînée (41.01 kWh produits). État mort : 20 °C, 1.013 bar. Généré par `rapports/tableau_1000_unites.py`.*

| # | Étape | Exergie perdue | Exergie restante | Chaleur (énergie) | Remarque |
|---|---|---|---|---|---|
| 0 | Électricité tirée du réseau |  | 1000 |  | charge |
| 1 | moteur et mécanique | 326 | 674 |  |  |
| 2 | compression étage 1 (chaleur échangée en comprimant) | 3 | 671 | 15 rejetées |  |
| 3 | compression étage 2 (chaleur échangée en comprimant) | 2 | 669 | 8 rejetées |  |
| 4 | compression étage 3 (chaleur échangée en comprimant) | -1 | 670 | -4 rejetées | n > γ : le modèle absorbe un peu de chaleur |
| 5 | compression étage 4 (chaleur échangée en comprimant) | 1 | 669 | 1 rejetées |  |
| 6 | refroidisseur 1 (chaleur rejetée) | 20 | 649 | 111 rejetées, dont 19 au-dessus de 130 °C | récupérable dans une cuve (phases 4-5) |
| 7 | refroidisseur 2 (chaleur rejetée) | 31 | 618 | 152 rejetées, dont 36 au-dessus de 130 °C | récupérable dans une cuve (phases 4-5) |
| 8 | refroidisseur 3 (chaleur rejetée) | 17 | 601 | 102 rejetées, dont 12 au-dessus de 130 °C | récupérable dans une cuve (phases 4-5) |
| 9 | refroidisseur 4 (chaleur rejetée) | 21 | 580 | 118 rejetées, dont 13 au-dessus de 130 °C | récupérable dans une cuve (phases 4-5) |
| 10 | air rejeté (rendement volumétrique) | 89 | 491 |  | dans le modèle, l'air non refoulé a été comprimé : à lire avec « moteur et mécanique » |
| 11 | air rejeté (sécheur) | 82 | 409 |  |  |
| 12 | laminage vers le réservoir | 0 | 409 |  |  |
| 13 | remplissage du réservoir (mélange) | 0 | 408 |  |  |
| 14 | chaleur perdue par les parois | 3 | 406 | 83 perdues | chaleur tiède : beaucoup d'énergie, peu d'exergie |
| 15 | cuve 1 (échange air-gravier en charge) | 3 | 403 |  |  |
| 16 | cuve 2 (échange air-gravier en charge) | 1 | 401 |  |  |
| 17 | cuve 3 (échange air-gravier en charge) | 7 | 394 |  |  |
| 18 | **Exergie stockée dans les réservoirs** |  | 348 |  | résidu du bilan de charge -0.22 % |
| 19 | Exergie disponible (stock + coussin initial) |  | 482 |  | coussin initial 134 |
| 20 | Exergie puisée dans les cuves de gravier | -48 | 530 | +214 fournies à l'air | chaleur de compression stockée pendant la charge |
| 21 | réservoir (détente interne) | -0 | 530 |  |  |
| 22 | chaleur reçue des parois (exergie de froid perdue) | 3 | 527 | 57 reçues des parois | l'air se refroidit en se détendant ; la paroi le réchauffe |
| 23 | détendeur (laminage) | 72 | 456 |  |  |
| 24 | turbine étage 1 (irréversibilité) | 43 | 412 |  |  |
| 25 | génératrice étage 1 | 6 | 406 |  |  |
| 26 | chute de pression avant l'étage 2 | 3 | 403 |  |  |
| 27 | turbine étage 2 (irréversibilité) | 31 | 372 |  |  |
| 28 | génératrice étage 2 | 5 | 367 |  |  |
| 29 | chute de pression avant l'étage 3 | 11 | 355 |  |  |
| 30 | turbine étage 3 (irréversibilité) | 22 | 333 |  |  |
| 31 | génératrice étage 3 | 5 | 328 |  |  |
| 32 | air rejeté à l'atmosphère | -1 | 329 |  |  |
| 33 | cuve 3 (restitution gravier → air) | 14 | 315 |  |  |
| 34 | cuve 2 (restitution gravier → air) | 3 | 312 |  |  |
| 35 | cuve 1 (restitution gravier → air) | 7 | 305 |  |  |
| 36 | Exergie restant dans les réservoirs (coussin) | 134 | 172 |  | pas une perte : reste pour le cycle suivant (plus froid et plus lourd que le coussin initial, d'où une exergie un peu plus grande) |
| 37 | **Électricité rendue au réseau** |  | 171 |  | résidu du bilan de décharge +0.00 % |

Les colonnes « exergie » comptent l'énergie **utile** (travail maximal récupérable) ; la colonne « chaleur » compte de l'**énergie** thermique, dans la même unité. Les deux ne s'additionnent pas : 100 unités de chaleur à 45 °C ne valent que 8 unités d'exergie.
