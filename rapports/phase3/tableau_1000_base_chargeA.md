# Tableau « 1000 unités » : cas de base, charge A (air aspiré à 20 °C)

*Cas `base_chargeA` : charge `dormoy_charge_1_190_depuis18` (339.9 kWh = 1000 unités, 1 unité = 339.889 Wh), puis décharge `dormoy_decharge_base_enchaine` enchaînée (14.04 kWh produits). État mort : 20 °C, 1.013 bar. Généré par `rapports/tableau_1000_unites.py`.*

| # | Étape | Exergie perdue | Exergie restante | Chaleur (énergie) | Remarque |
|---|---|---|---|---|---|
| 0 | Électricité tirée du réseau |  | 1000 |  | charge |
| 1 | moteur et mécanique | 331 | 669 |  |  |
| 2 | compression étage 1 (chaleur échangée en comprimant) | 2 | 667 | 15 rejetées |  |
| 3 | compression étage 2 (chaleur échangée en comprimant) | 2 | 665 | 9 rejetées |  |
| 4 | compression étage 3 (chaleur échangée en comprimant) | -1 | 666 | -4 rejetées | n > γ : le modèle absorbe un peu de chaleur |
| 5 | compression étage 4 (chaleur échangée en comprimant) | 0 | 666 | -0 rejetées | n > γ : le modèle absorbe un peu de chaleur |
| 6 | refroidisseur 1 (chaleur rejetée) | 20 | 646 | 119 rejetées, dont 0 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 7 | refroidisseur 2 (chaleur rejetée) | 41 | 605 | 183 rejetées, dont 62 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 8 | refroidisseur 3 (chaleur rejetée) | 54 | 551 | 223 rejetées, dont 94 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 9 | refroidisseur 4 (chaleur rejetée) | 22 | 529 | 123 rejetées, dont 17 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 10 | air rejeté (rendement volumétrique) | 90 | 439 |  | dans le modèle, l'air non refoulé a été comprimé : à lire avec « moteur et mécanique » |
| 11 | air rejeté (sécheur) | 83 | 355 |  |  |
| 12 | laminage vers le réservoir | 11 | 344 |  |  |
| 13 | remplissage du réservoir (mélange) | 0 | 344 |  |  |
| 14 | chaleur perdue par les parois | 3 | 341 | 109 perdues | chaleur tiède : beaucoup d'énergie, peu d'exergie |
| 15 | **Exergie stockée dans les réservoirs** |  | 341 |  | résidu du bilan de charge +0.00 % |
| 16 | Exergie disponible (stock + coussin initial) |  | 358 |  | coussin initial 17 |
| 17 | réservoir (détente interne) | -0 | 358 |  |  |
| 18 | chaleur reçue des parois (exergie de froid perdue) | 7 | 351 | 56 reçues des parois | l'air se refroidit en se détendant ; la paroi le réchauffe |
| 19 | détendeur (laminage) | 242 | 109 |  |  |
| 20 | turbine étage 1 (irréversibilité) | 22 | 87 |  |  |
| 21 | génératrice étage 1 | 4 | 83 |  |  |
| 22 | air rejeté à l'atmosphère | 19 | 64 |  |  |
| 23 | Exergie restant dans les réservoirs (coussin) | 23 | 41 |  | pas une perte : reste pour le cycle suivant (plus froid et plus lourd que le coussin initial, d'où une exergie un peu plus grande) |
| 24 | **Électricité rendue au réseau** |  | 41 |  | résidu du bilan de décharge -0.00 % |

Les colonnes « exergie » comptent l'énergie **utile** (travail maximal récupérable) ; la colonne « chaleur » compte de l'**énergie** thermique, dans la même unité. Les deux ne s'additionnent pas : 100 unités de chaleur à 45 °C ne valent que 8 unités d'exergie.
