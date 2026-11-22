# Tableau « 1000 unités » : A : base Dormoy, 1 étage, sans réchauffage

*Cas `A` : charge `dormoy_charge_1_190_aspiration_chaude_cycle` (324.5 kWh = 1000 unités, 1 unité = 324.488 Wh), puis décharge `dormoy_decharge_base_cycle` enchaînée (14.05 kWh produits). État mort : 20 °C, 1.013 bar. Généré par `rapports/tableau_1000_unites.py`.*

| # | Étape | Exergie perdue | Exergie restante | Chaleur (énergie) | Remarque |
|---|---|---|---|---|---|
| 0 | Électricité tirée du réseau |  | 1000 |  | charge |
| 1 | moteur et mécanique | 331 | 669 |  |  |
| 2 | compression étage 1 (chaleur échangée en comprimant) | 3 | 666 | 15 rejetées |  |
| 3 | compression étage 2 (chaleur échangée en comprimant) | 2 | 664 | 8 rejetées |  |
| 4 | compression étage 3 (chaleur échangée en comprimant) | -1 | 664 | -4 rejetées | n > γ : le modèle absorbe un peu de chaleur |
| 5 | compression étage 4 (chaleur échangée en comprimant) | 0 | 664 | -1 rejetées | n > γ : le modèle absorbe un peu de chaleur |
| 6 | refroidisseur 1 (chaleur rejetée) | 36 | 628 | 163 rejetées, dont 51 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 7 | refroidisseur 2 (chaleur rejetée) | 45 | 583 | 190 rejetées, dont 75 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 8 | refroidisseur 3 (chaleur rejetée) | 53 | 530 | 218 rejetées, dont 94 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 9 | refroidisseur 4 (chaleur rejetée) | 21 | 508 | 118 rejetées, dont 16 au-dessus du seuil | récupérable dans un stockage de chaleur |
| 10 | air rejeté (rendement volumétrique) | 87 | 422 |  | dans le modèle, l'air non refoulé a été comprimé : à lire avec « moteur et mécanique » |
| 11 | air rejeté (sécheur) | 81 | 341 |  |  |
| 12 | laminage vers le réservoir | 11 | 330 |  |  |
| 13 | remplissage du réservoir (mélange) | 0 | 329 |  |  |
| 14 | chaleur perdue par les parois | 3 | 326 | 90 perdues | chaleur tiède : beaucoup d'énergie, peu d'exergie |
| 15 | **Exergie stockée dans les réservoirs** |  | 329 |  | résidu du bilan de charge -0.22 % |
| 16 | Exergie disponible (stock + coussin initial) |  | 350 |  | coussin initial 21 |
| 17 | réservoir (détente interne) | -0 | 350 |  |  |
| 18 | chaleur reçue des parois (exergie de froid perdue) | 4 | 346 | 60 reçues des parois | l'air se refroidit en se détendant ; la paroi le réchauffe |
| 19 | détendeur (laminage) | 241 | 105 |  |  |
| 20 | turbine étage 1 (irréversibilité) | 22 | 83 |  |  |
| 21 | génératrice étage 1 | 4 | 79 |  |  |
| 22 | air rejeté à l'atmosphère | 14 | 65 |  |  |
| 23 | Exergie restant dans les réservoirs (coussin) | 22 | 44 |  | pas une perte : reste pour le cycle suivant (plus froid et plus lourd que le coussin initial, d'où une exergie un peu plus grande) |
| 24 | **Électricité rendue au réseau** |  | 43 |  | résidu du bilan de décharge +0.00 % |

Les colonnes « exergie » comptent l'énergie **utile** (travail maximal récupérable) ; la colonne « chaleur » compte de l'**énergie** thermique, dans la même unité. Les deux ne s'additionnent pas : 100 unités de chaleur à 45 °C ne valent que 8 unités d'exergie.
