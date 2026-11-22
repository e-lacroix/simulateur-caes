# Analyse « D_isolee » : sensibilité, incertitudes, Pareto

*Architecture D (gravier direct, cas C de Tola) avec isolant de laine minérale et un jour d'attente ; dix paramètres, Sobol, incertitudes du registre, Pareto électricité livrée contre masse.*

*Généré par `python -m caes analyser scenarios/analyse/D.yaml --sortie rapports/phase10` (10 processus) ; fichier d'analyse `scenarios\analyse\D.yaml` ; méthodes : formules F44 à F46 de `docs/formules.md`.*

## 1. Configuration analysée

Scénario : `scenarios\analyse\..\variantes\cycles_gravier_isolant_14j.yaml` ; modifications de base : `composants.attente.duree=1j`, `simulation.nombre_max=2`, `charge.dt=60s`, `decharge.dt=10s`.

| Paramètre | Chemin(s) | Nominal | Plage | Origine de la plage | Niveau de preuve |
|---|---|---|---|---|---|
| Pression maximale du réservoir (`p_max`) | `charge.p_cible` | 190 bar | 120 à 250 bar | plage (choix de l'analyse) | mesure |
| Volume des trois cuves (facteur) (`volume_cuves`) | `composants.cuve_1.volume`, `composants.cuve_2.volume`, `composants.cuve_3.volume` | × 1 (valeurs : 0.35, 0.2, 0.7 SI) | × 0.5 à × 2 | facteur (choix de l'analyse) | scénario |
| Diamètre des particules de gravier (`diametre_particule`) | `composants.cuve_1.diametre_particule`, `composants.cuve_2.diametre_particule`, `composants.cuve_3.diametre_particule` | 0.03 m | 0.01 à 0.05 m | plage (choix de l'analyse) | simulation_publiee |
| Épaisseur de laine minérale (`epaisseur_isolant`) | `composants.cuve_1.isolation.epaisseur`, `composants.cuve_2.isolation.epaisseur`, `composants.cuve_3.isolation.epaisseur` | 0.2 m | 0.05 à 0.3 m | plage (choix de l'analyse) | scénario |
| Durée d'attente entre charge et décharge (`duree_attente`) | `composants.attente.duree` | 24 h | 1 à 168 h | plage (choix de l'analyse) | scénario |
| Température ambiante (`T_amb`) | `ambiance.T_amb` | 20 degC | -20 à 30 degC | plage (choix de l'analyse) | hypothese |
| Humidité relative ambiante (`humidite`) | `ambiance.humidite_relative` | 0.5 | 0.3 à 0.9 | plage (choix de l'analyse) | hypothese |
| Rendement électrique du compresseur (`rendement_electrique`) | `composants.compresseur.rendement_electrique` | 94.5 % | 94 à 95 % | registre (plage publiée) | fabricant |
| Rendement mécanique du compresseur (facteur) (`rendement_mecanique`) | `composants.compresseur.rendement_mecanique_min`, `composants.compresseur.rendement_mecanique_max` | × 1 (valeurs : 0.69, 0.74 SI) | × 0.93 à × 1.07 | facteur (choix de l'analyse) | calibration |
| Efficacité des refroidisseurs (facteur) (`efficacite_refroidisseurs`) | `composants.refroidisseur_1.efficacite`, `composants.refroidisseur_2.efficacite`, `composants.refroidisseur_3.efficacite`, `composants.refroidisseur_4.efficacite_min`, `composants.refroidisseur_4.efficacite_max` | × 1 (valeurs : 0.82, 0.85, 0.88, 0.74, 0.85 SI) | × 0.9 à × 1.05 | facteur (choix de l'analyse) | calibration |

## 2. Point nominal

| Sortie | Valeur |
|---|---|
| Rendement aller-retour (sans chaleur externe) | 0.172 |
| Électricité produite (kWh) | 40.53 |
| Électricité consommée (kWh) | 235.3 |
| Masse réservoirs + stockages (kg) | 3 699 |
| Pertes pendant l'attente (kWh) | 4.772 |
| decharge.T_rejet_min_degC | 14.54 |

Arrêt : pression d'arrêt du détendeur atteinte.

Avertissements du point nominal : [compresseur] air humide au-delà de 10 MPa : teneur à saturation extrapolée (formulation RP-1485 valable jusqu'à 10 MPa) ; [refroidisseur_3] air entrant plus froid que l'ambiant (le gravier amont a gardé du froid de la décharge) : le modèle à efficacité le réchauffe ; le modèle à pincement le laisse tel quel ; [refroidisseur_4] air humide au-delà de 10 MPa : teneur à saturation extrapolée (formulation RP-1485 valable jusqu'à 10 MPa) ; [cuve_1] en charge, condensation d'eau (air refroidi sous son point de rosée) ; [cuve_2] en charge, condensation d'eau (air refroidi sous son point de rosée) ; [cuve_3] en charge, condensation d'eau (air refroidi sous son point de rosée) ; [cuve_3] en charge, givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre).

## 3. Sensibilité « un paramètre à la fois » (tornade)

21 simulations (nominal, puis chaque paramètre à sa borne basse et à sa borne haute, les autres au nominal), 50.3 s. Le balancement est l'écart entre les deux bornes ; il classe les paramètres mais ignore les interactions (voir Sobol).

### Rendement aller-retour (sans chaleur externe)

| Rang | Paramètre | À la borne basse | À la borne haute | Balancement | Balancement relatif |
|---|---|---|---|---|---|
| 1 | Rendement mécanique du compresseur (facteur) | 0.16 | 0.184 | 0.0241 | 14.0 % |
| 2 | Température ambiante | 0.187 | 0.168 | 0.0193 | 11.2 % |
| 3 | Pression maximale du réservoir | 0.182 | 0.166 | 0.0161 | 9.3 % |
| 4 | Volume des trois cuves (facteur) | 0.167 | 0.173 | 0.00646 | 3.8 % |
| 5 | Efficacité des refroidisseurs (facteur) | 0.168 | 0.174 | 0.00633 | 3.7 % |
| 6 | Rendement électrique du compresseur | 0.171 | 0.173 | 0.00182 | 1.1 % |
| 7 | Durée d'attente entre charge et décharge | 0.171 | 0.172 | 0.000791 | 0.5 % |
| 8 | Épaisseur de laine minérale | 0.173 | 0.172 | 0.000389 | 0.2 % |
| 9 | Diamètre des particules de gravier | 0.172 | 0.172 | 0.000129 | 0.1 % |
| 10 | Humidité relative ambiante | 0.172 | 0.172 | 0 | 0.0 % |

### Électricité produite (kWh)

| Rang | Paramètre | À la borne basse | À la borne haute | Balancement | Balancement relatif |
|---|---|---|---|---|---|
| 1 | Pression maximale du réservoir | 20.44 | 55.4 | 34.97 | 86.3 % |
| 2 | Température ambiante | 46.36 | 39.14 | 7.218 | 17.8 % |
| 3 | Volume des trois cuves (facteur) | 39.27 | 40.53 | 1.262 | 3.1 % |
| 4 | Durée d'attente entre charge et décharge | 41.05 | 40.24 | 0.803 | 2.0 % |
| 5 | Efficacité des refroidisseurs (facteur) | 40.01 | 40.7 | 0.693 | 1.7 % |
| 6 | Diamètre des particules de gravier | 40.53 | 40.53 | 0.000552 | 0.0 % |
| 7 | Épaisseur de laine minérale | 40.53 | 40.53 | 0 | 0.0 % |
| 8 | Humidité relative ambiante | 40.53 | 40.53 | 0 | 0.0 % |
| 9 | Rendement électrique du compresseur | 40.53 | 40.53 | 0 | 0.0 % |
| 10 | Rendement mécanique du compresseur (facteur) | 40.53 | 40.53 | 0 | 0.0 % |

### Électricité consommée (kWh)

| Rang | Paramètre | À la borne basse | À la borne haute | Balancement | Balancement relatif |
|---|---|---|---|---|---|
| 1 | Pression maximale du réservoir | 112.3 | 333.8 | 221.5 | 94.2 % |
| 2 | Rendement mécanique du compresseur (facteur) | 253 | 219.9 | 33.1 | 14.1 % |
| 3 | Température ambiante | 248.1 | 233.6 | 14.47 | 6.1 % |
| 4 | Durée d'attente entre charge et décharge | 239.7 | 234 | 5.772 | 2.5 % |
| 5 | Efficacité des refroidisseurs (facteur) | 238.6 | 233.9 | 4.694 | 2.0 % |
| 6 | Rendement électrique du compresseur | 236.5 | 234 | 2.49 | 1.1 % |
| 7 | Volume des trois cuves (facteur) | 235.6 | 234.1 | 1.508 | 0.6 % |
| 8 | Épaisseur de laine minérale | 234.9 | 235.4 | 0.531 | 0.2 % |
| 9 | Diamètre des particules de gravier | 235.3 | 235.1 | 0.173 | 0.1 % |
| 10 | Humidité relative ambiante | 235.3 | 235.3 | 0 | 0.0 % |

### Masse réservoirs + stockages (kg)

| Rang | Paramètre | À la borne basse | À la borne haute | Balancement | Balancement relatif |
|---|---|---|---|---|---|
| 1 | Volume des trois cuves (facteur) | 2 496 | 6 105 | 3 609 | 97.6 % |
| 2 | Pression maximale du réservoir | 3 220 | 4 110 | 889.4 | 24.0 % |
| 3 | Diamètre des particules de gravier | 3 699 | 3 699 | 0 | 0.0 % |
| 4 | Épaisseur de laine minérale | 3 699 | 3 699 | 0 | 0.0 % |
| 5 | Durée d'attente entre charge et décharge | 3 699 | 3 699 | 0 | 0.0 % |
| 6 | Température ambiante | 3 699 | 3 699 | 0 | 0.0 % |
| 7 | Humidité relative ambiante | 3 699 | 3 699 | 0 | 0.0 % |
| 8 | Rendement électrique du compresseur | 3 699 | 3 699 | 0 | 0.0 % |
| 9 | Rendement mécanique du compresseur (facteur) | 3 699 | 3 699 | 0 | 0.0 % |
| 10 | Efficacité des refroidisseurs (facteur) | 3 699 | 3 699 | 0 | 0.0 % |

### Pertes pendant l'attente (kWh)

| Rang | Paramètre | À la borne basse | À la borne haute | Balancement | Balancement relatif |
|---|---|---|---|---|---|
| 1 | Durée d'attente entre charge et décharge | 0.206 | 27.88 | 27.68 | 580.0 % |
| 2 | Épaisseur de laine minérale | 14.59 | 3.293 | 11.29 | 236.6 % |
| 3 | Volume des trois cuves (facteur) | 3.159 | 6.252 | 3.092 | 64.8 % |
| 4 | Pression maximale du réservoir | 3.818 | 4.999 | 1.18 | 24.7 % |
| 5 | Efficacité des refroidisseurs (facteur) | 5.164 | 4.589 | 0.575 | 12.0 % |
| 6 | Diamètre des particules de gravier | 4.801 | 4.693 | 0.108 | 2.3 % |
| 7 | Température ambiante | 4.815 | 4.764 | 0.0507 | 1.1 % |
| 8 | Humidité relative ambiante | 4.772 | 4.772 | 0 | 0.0 % |
| 9 | Rendement électrique du compresseur | 4.772 | 4.772 | 0 | 0.0 % |
| 10 | Rendement mécanique du compresseur (facteur) | 4.772 | 4.772 | 0 | 0.0 % |

### decharge.T_rejet_min_degC

| Rang | Paramètre | À la borne basse | À la borne haute | Balancement | Balancement relatif |
|---|---|---|---|---|---|
| 1 | Volume des trois cuves (facteur) | -38.53 | 14.54 | 53.07 | 364.9 % |
| 2 | Durée d'attente entre charge et décharge | 14.54 | -6.315 | 20.86 | 143.4 % |
| 3 | Pression maximale du réservoir | 14.54 | 4.327 | 10.22 | 70.2 % |
| 4 | Diamètre des particules de gravier | 14.54 | 14.54 | 0 | 0.0 % |
| 5 | Épaisseur de laine minérale | 14.54 | 14.54 | 0 | 0.0 % |
| 6 | Température ambiante | 14.54 | 14.54 | 0 | 0.0 % |
| 7 | Humidité relative ambiante | 14.54 | 14.54 | 0 | 0.0 % |
| 8 | Rendement électrique du compresseur | 14.54 | 14.54 | 0 | 0.0 % |
| 9 | Rendement mécanique du compresseur (facteur) | 14.54 | 14.54 | 0 | 0.0 % |
| 10 | Efficacité des refroidisseurs (facteur) | 14.54 | 14.54 | 0 | 0.0 % |

![tornade](tornade.png)

## 4. Sensibilité globale : indices de Sobol

Estimateur de Saltelli (`scipy.stats.sobol_indices`), n = 32 échantillons de base, 10 paramètres uniformes dans leurs plages : n·(d + 2) = 384 simulations, 1 057 s, graine 1. S_1 : part de la variance due au paramètre seul ; S_T : avec ses interactions ; intervalle de confiance à 95 % par bootstrap quand il est donné. Les indices sont bruités quand n est petit : un indice légèrement négatif vaut zéro.

### Rendement aller-retour (sans chaleur externe)

| Rang | Paramètre | S_1 | S_T | IC 95 % de S_T |
|---|---|---|---|---|
| 1 | Rendement mécanique du compresseur (facteur) | 0.32 | 0.39 | [0.22, 0.60] |
| 2 | Volume des trois cuves (facteur) | 0.05 | 0.28 | [0.13, 0.46] |
| 3 | Pression maximale du réservoir | 0.17 | 0.26 | [0.14, 0.44] |
| 4 | Température ambiante | 0.05 | 0.11 | [0.06, 0.20] |
| 5 | Épaisseur de laine minérale | 0.08 | 0.09 | [0.04, 0.19] |
| 6 | Durée d'attente entre charge et décharge | -0.08 | 0.05 | [0.02, 0.10] |
| 7 | Diamètre des particules de gravier | 0.02 | 0.01 | [0.01, 0.02] |
| 8 | Efficacité des refroidisseurs (facteur) | 0.00 | 0.01 | [0.00, 0.02] |
| 9 | Rendement électrique du compresseur | 0.03 | 0.00 | [0.00, 0.00] |
| 10 | Humidité relative ambiante | 0.00 | 0.00 | [nan, nan] |

### Électricité produite (kWh)

| Rang | Paramètre | S_1 | S_T | IC 95 % de S_T |
|---|---|---|---|---|
| 1 | Pression maximale du réservoir | 1.14 | 1.11 | [0.84, 1.29] |
| 2 | Température ambiante | 0.04 | 0.02 | [0.01, 0.03] |
| 3 | Volume des trois cuves (facteur) | 0.02 | 0.02 | [0.01, 0.03] |
| 4 | Durée d'attente entre charge et décharge | 0.01 | 0.01 | [0.00, 0.02] |
| 5 | Épaisseur de laine minérale | -0.01 | 0.01 | [0.00, 0.01] |
| 6 | Diamètre des particules de gravier | -0.01 | 0.00 | [0.00, 0.00] |
| 7 | Efficacité des refroidisseurs (facteur) | 0.00 | 0.00 | [0.00, 0.00] |
| 8 | Humidité relative ambiante | 0.00 | 0.00 | [nan, nan] |
| 9 | Rendement électrique du compresseur | 0.00 | 0.00 | [nan, nan] |
| 10 | Rendement mécanique du compresseur (facteur) | 0.00 | 0.00 | [nan, nan] |

### Électricité consommée (kWh)

| Rang | Paramètre | S_1 | S_T | IC 95 % de S_T |
|---|---|---|---|---|
| 1 | Pression maximale du réservoir | 1.16 | 1.18 | [0.84, 1.43] |
| 2 | Rendement mécanique du compresseur (facteur) | -0.09 | 0.02 | [0.01, 0.03] |
| 3 | Température ambiante | 0.01 | 0.00 | [0.00, 0.01] |
| 4 | Durée d'attente entre charge et décharge | 0.00 | 0.00 | [0.00, 0.00] |
| 5 | Volume des trois cuves (facteur) | 0.00 | 0.00 | [0.00, 0.00] |
| 6 | Efficacité des refroidisseurs (facteur) | -0.00 | 0.00 | [0.00, 0.00] |
| 7 | Rendement électrique du compresseur | 0.00 | 0.00 | [0.00, 0.00] |
| 8 | Épaisseur de laine minérale | -0.00 | 0.00 | [0.00, 0.00] |
| 9 | Diamètre des particules de gravier | -0.00 | 0.00 | [0.00, 0.00] |
| 10 | Humidité relative ambiante | 0.00 | 0.00 | [nan, nan] |

### Masse réservoirs + stockages (kg)

| Rang | Paramètre | S_1 | S_T | IC 95 % de S_T |
|---|---|---|---|---|
| 1 | Volume des trois cuves (facteur) | 0.91 | 0.92 | [0.65, 1.28] |
| 2 | Pression maximale du réservoir | 0.24 | 0.07 | [0.05, 0.09] |
| 3 | Diamètre des particules de gravier | 0.00 | 0.00 | [nan, nan] |
| 4 | Épaisseur de laine minérale | 0.00 | 0.00 | [nan, nan] |
| 5 | Durée d'attente entre charge et décharge | 0.00 | 0.00 | [nan, nan] |
| 6 | Température ambiante | 0.00 | 0.00 | [nan, nan] |
| 7 | Humidité relative ambiante | 0.00 | 0.00 | [nan, nan] |
| 8 | Rendement électrique du compresseur | 0.00 | 0.00 | [nan, nan] |
| 9 | Rendement mécanique du compresseur (facteur) | 0.00 | 0.00 | [nan, nan] |
| 10 | Efficacité des refroidisseurs (facteur) | 0.00 | 0.00 | [nan, nan] |

### Pertes pendant l'attente (kWh)

| Rang | Paramètre | S_1 | S_T | IC 95 % de S_T |
|---|---|---|---|---|
| 1 | Épaisseur de laine minérale | 0.42 | 0.29 | [0.18, 0.44] |
| 2 | Durée d'attente entre charge et décharge | 0.18 | 0.18 | [0.11, 0.33] |
| 3 | Volume des trois cuves (facteur) | 0.05 | 0.13 | [0.04, 0.28] |
| 4 | Pression maximale du réservoir | 0.06 | 0.06 | [0.03, 0.18] |
| 5 | Température ambiante | 0.01 | 0.00 | [0.00, 0.01] |
| 6 | Efficacité des refroidisseurs (facteur) | -0.01 | 0.00 | [0.00, 0.01] |
| 7 | Diamètre des particules de gravier | 0.00 | 0.00 | [0.00, 0.00] |
| 8 | Humidité relative ambiante | 0.00 | 0.00 | [nan, nan] |
| 9 | Rendement électrique du compresseur | 0.00 | 0.00 | [nan, nan] |
| 10 | Rendement mécanique du compresseur (facteur) | 0.00 | 0.00 | [nan, nan] |

### decharge.T_rejet_min_degC

| Rang | Paramètre | S_1 | S_T | IC 95 % de S_T |
|---|---|---|---|---|
| 1 | Volume des trois cuves (facteur) | 0.54 | 0.73 | [0.35, 1.31] |
| 2 | Pression maximale du réservoir | 0.14 | 0.36 | [0.16, 0.66] |
| 3 | Épaisseur de laine minérale | 0.11 | 0.11 | [0.03, 0.31] |
| 4 | Durée d'attente entre charge et décharge | -0.14 | 0.07 | [0.03, 0.13] |
| 5 | Température ambiante | 0.02 | 0.05 | [0.02, 0.11] |
| 6 | Diamètre des particules de gravier | 0.02 | 0.02 | [0.01, 0.04] |
| 7 | Efficacité des refroidisseurs (facteur) | 0.03 | 0.01 | [0.00, 0.01] |
| 8 | Humidité relative ambiante | 0.00 | 0.00 | [nan, nan] |
| 9 | Rendement électrique du compresseur | 0.00 | 0.00 | [nan, nan] |
| 10 | Rendement mécanique du compresseur (facteur) | 0.00 | 0.00 | [nan, nan] |

![sobol](sobol.png)

## 5. Propagation des incertitudes du registre

Hypercube latin de 48 tirages (graine 1) sur 4 paramètres tirés uniformément dans leur plage (151 s) : Rendement électrique du compresseur 94 à 95 % (registre (plage publiée)) ; Rendement mécanique du compresseur (facteur) × 0.93 à × 1.07 (facteur (choix de l'analyse)) ; Efficacité des refroidisseurs (facteur) × 0.9 à × 1.05 (facteur (choix de l'analyse)) ; Diamètre des particules de gravier 0.01 à 0.05 m (plage (choix de l'analyse)).

| Sortie | Nominal | Minimum | 5 % | Médiane | 95 % | Maximum | ± (90 %) | ± relatif |
|---|---|---|---|---|---|---|---|---|
| Rendement aller-retour (sans chaleur externe) | 0.172 | 0.156 | 0.159 | 0.171 | 0.18 | 0.184 | 0.0105 | 6.1 % |
| Électricité produite (kWh) | 40.53 | 40.01 | 40.01 | 40.35 | 40.7 | 40.7 | 0.346 | 0.9 % |
| Électricité consommée (kWh) | 235.3 | 220.6 | 223.4 | 236.5 | 252.6 | 255.9 | 14.62 | 6.2 % |
| Masse réservoirs + stockages (kg) | 3 699 | 3 699 | 3 699 | 3 699 | 3 699 | 3 699 | 0 | 0.0 % |
| Pertes pendant l'attente (kWh) | 4.772 | 4.555 | 4.611 | 4.858 | 5.13 | 5.177 | 0.259 | 5.4 % |
| decharge.T_rejet_min_degC | 14.54 | 14.54 | 14.54 | 14.54 | 14.54 | 14.54 | 0 | 0.0 % |

Corrélation de rang (Spearman) paramètre → sortie : +1 quand la sortie monte toujours avec le paramètre, −1 quand elle descend, ≈ 0 sans effet monotone.

| Paramètre | Rendement aller-retour (sans chaleur externe) | Électricité produite (kWh) | Électricité consommée (kWh) | Masse réservoirs + stockages (kg) | Pertes pendant l'attente (kWh) | decharge.T_rejet_min_degC |
|---|---|---|---|---|---|---|
| Rendement électrique du compresseur | -0.01 | +0.32 | +0.05 | +0.00 | -0.24 | +0.00 |
| Rendement mécanique du compresseur (facteur) | +0.96 | -0.02 | -0.99 | +0.00 | +0.01 | +0.00 |
| Efficacité des refroidisseurs (facteur) | +0.19 | +0.96 | -0.08 | +0.00 | -0.98 | +0.00 |
| Diamètre des particules de gravier | +0.27 | +0.18 | -0.26 | +0.00 | -0.26 | +0.00 |

![incertitudes](incertitudes.png)

## 6. Front de Pareto (NSGA-II)

Objectifs : **Électricité produite (kWh)** (maximiser) ; **Masse réservoirs + stockages (kg)** (minimiser). Variables : Pression maximale du réservoir 120 à 250 bar ; Volume des trois cuves (facteur) × 0.5 à × 2 ; Épaisseur de laine minérale 0.05 à 0.3 m.

| Réglage | Valeur |
|---|---|
| population | 16 |
| générations | 12 |
| croisement SBX : probabilité | 0.9 |
| croisement SBX : η | 15.0 |
| mutation polynomiale : probabilité par variable | 0.333 |
| mutation polynomiale : η | 20.0 |
| graine | 1 |
| évaluations | 208 |
| échecs (pénalisés) | 0 |
| durée (s) | 548 |

| Point | Pression maximale du réservoir | Volume des trois cuves (facteur) | Épaisseur de laine minérale | Électricité produite (kWh) | Masse réservoirs + stockages (kg) |
|---|---|---|---|---|---|
| 1 (extrémité) | 249.7 | 0.933 | 0.167 | 55.3 | 3 947 |
| 2 | 249.7 | 0.868 | 0.168 | 55.14 | 3 791 |
| 3 | 250 | 0.823 | 0.186 | 55 | 3 683 |
| 4 | 249.7 | 0.8 | 0.16 | 54.84 | 3 627 |
| 5 | 249.9 | 0.8 | 0.158 | 54.83 | 3 627 |
| 6 | 249.9 | 0.797 | 0.157 | 54.82 | 3 620 |
| 7 | 249.7 | 0.797 | 0.157 | 54.82 | 3 619 |
| 8 | 250 | 0.767 | 0.185 | 54.71 | 3 550 |
| 9 | 248.9 | 0.763 | 0.171 | 54.49 | 3 531 |
| 10 | 245.5 | 0.767 | 0.186 | 53.76 | 3 519 |
| 11 | 243.5 | 0.763 | 0.186 | 53.42 | 3 496 |
| 12 | 250 | 0.628 | 0.153 | 53.26 | 3 214 |
| 13 | 248.6 | 0.628 | 0.153 | 53.12 | 3 204 |
| 14 | 250 | 0.596 | 0.153 | 52.78 | 3 137 |
| 15 | 248 | 0.596 | 0.153 | 52.5 | 3 123 |
| 16 | 250 | 0.544 | 0.153 | 51.79 | 3 011 |
| 17 | 250 | 0.541 | 0.153 | 51.73 | 3 004 |
| 18 (coude) | 250 | 0.5 | 0.162 | 50.81 | 2 907 |
| 19 | 249.9 | 0.5 | 0.152 | 50.76 | 2 906 |
| 20 | 207.9 | 0.612 | 0.214 | 44.51 | 2 889 |
| 21 | 207.7 | 0.612 | 0.215 | 44.51 | 2 886 |
| 22 | 204.1 | 0.595 | 0.251 | 43.5 | 2 821 |
| 23 | 204.7 | 0.559 | 0.197 | 43.28 | 2 738 |
| 24 | 204 | 0.502 | 0.25 | 42.59 | 2 597 |
| 25 | 204 | 0.5 | 0.248 | 42.56 | 2 592 |
| 26 | 193.3 | 0.5 | 0.228 | 40.05 | 2 519 |
| 27 | 178.9 | 0.5 | 0.23 | 36.74 | 2 420 |
| 28 | 159.5 | 0.553 | 0.293 | 31.99 | 2 414 |
| 29 | 159.5 | 0.5 | 0.266 | 31.85 | 2 287 |
| 30 | 152.4 | 0.5 | 0.29 | 29.88 | 2 239 |
| 31 | 149.1 | 0.5 | 0.29 | 29.04 | 2 216 |
| 32 | 147.4 | 0.502 | 0.289 | 28.53 | 2 209 |
| 33 | 141.5 | 0.5 | 0.3 | 26.83 | 2 164 |
| 34 | 141.4 | 0.5 | 0.3 | 26.83 | 2 163 |
| 35 | 138.6 | 0.5 | 0.3 | 25.97 | 2 144 |
| 36 (extrémité) | 133.8 | 0.5 | 0.29 | 24.42 | 2 111 |

![pareto](pareto.png)

**Borne atteinte** : Pression maximale du réservoir est à sa borne haute (120 à 250 bar) sur 47 % du front : c'est la plage choisie qui limite le front, pas la physique ; élargir la plage (ou ajouter la contrainte qui la justifie) changerait le résultat.

**Borne atteinte** : Volume des trois cuves (facteur) est à sa borne basse (× 0.5 à × 2) sur 39 % du front : c'est la plage choisie qui limite le front, pas la physique ; élargir la plage (ou ajouter la contrainte qui la justifie) changerait le résultat.

Lecture : d'une extrémité à l'autre du front, Électricité produite (kWh) passe de 55.3 à 24.42 pendant que Masse réservoirs + stockages (kg) passe de 3 947 à 2 111. Tout point sous le front est dominé : une autre configuration fait mieux sur un objectif sans faire pire sur l'autre. Le coude est le point le plus loin de la corde entre les extrémités : au-delà, chaque gain sur un objectif coûte de plus en plus sur l'autre.

## 7. Avertissements de domaine de validité pendant les balayages

662 simulations au total. Chaque avertissement est compté une fois par simulation ; « nominal » signale qu'il apparaît déjà au point nominal. Les autres n'ont été déclenchés que par des combinaisons de paramètres : ces zones de l'espace exploré sortent du domaine d'une corrélation et leurs résultats sont à lire avec cette réserve.

| Avertissement | Simulations | Part | Nominal ? | Exemple de point (SI ou facteur) |
|---|---|---|---|---|
| [refroidisseur_3] air entrant plus froid que l'ambiant (le gravier amont a gardé du froid de la décharge) : le modèle à efficacité le réchauffe ; le modèle à pincement le laisse tel quel | 662 | 100 % | oui | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [refroidisseur_4] air humide au-delà de 10 MPa : teneur à saturation extrapolée (formulation RP-1485 valable jusqu'à 10 MPa) | 662 | 100 % | oui | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [compresseur] air humide au-delà de 10 MPa : teneur à saturation extrapolée (formulation RP-1485 valable jusqu'à 10 MPa) | 662 | 100 % | oui | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_3] en charge, condensation d'eau (air refroidi sous son point de rosée) | 661 | 100 % | oui | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_3] en charge, givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 653 | 99 % | oui | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_2] en charge, condensation d'eau (air refroidi sous son point de rosée) | 642 | 97 % | oui | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_1] en charge, condensation d'eau (air refroidi sous son point de rosée) | 561 | 85 % | oui | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_3] cuve trop froide pour atteindre la cible de 130 °C (pas d'appoint ; minimum suivi dans T_sortie_min_K) | 433 | 65 % | non | p_max = 12 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_2] cuve trop froide pour atteindre la cible de 90 °C (pas d'appoint ; minimum suivi dans T_sortie_min_K) | 371 | 56 % | non | p_max = 19 000 000, volume_cuves = 0.5, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_1] cuve trop froide pour atteindre la cible de 90 °C (pas d'appoint ; minimum suivi dans T_sortie_min_K) | 330 | 50 % | non | p_max = 25 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [refroidisseur_1] air entrant plus froid que l'ambiant (le gravier amont a gardé du froid de la décharge) : le modèle à efficacité le réchauffe ; le modèle à pincement le laisse tel quel | 300 | 45 % | non | p_max = 19 000 000, volume_cuves = 0.5, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [compresseur] refoulement au-dessus de la plage calibrée (190 bar) : lois en pression bloquées à la borne | 296 | 45 % | non | p_max = 25 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [turbine] étage 3 : air rejeté sous 0 °C : risque de givrage (humidité, phase 9) | 260 | 39 % | non | p_max = 19 000 000, volume_cuves = 0.5, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [turbine] étage 2 : air rejeté sous 0 °C : risque de givrage (humidité, phase 9) | 250 | 38 % | non | p_max = 19 000 000, volume_cuves = 0.5, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 293.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_1] en charge, givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 245 | 37 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [refroidisseur_3] givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 204 | 31 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [cuve_2] en charge, givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 186 | 28 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [refroidisseur_1] givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 170 | 26 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [refroidisseur_2] givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 151 | 23 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [turbine] étage 1 : air rejeté sous 0 °C : risque de givrage (humidité, phase 9) | 125 | 19 % | non | p_max = 19 632 857, volume_cuves = 0.554, diametre_particule = 0.0142, epaisseur_isolant = 0.153, duree_attente = 264 721, T_amb = 270.7, humidite = 0.722, rendement_electrique = 0.947, rendement_mecanique = 0.968, efficacite_refroidisseurs = 1.048 |
| [detendeur] à la sortie, givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 113 | 17 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [refroidisseur_2] air entrant plus froid que l'ambiant (le gravier amont a gardé du froid de la décharge) : le modèle à efficacité le réchauffe ; le modèle à pincement le laisse tel quel | 100 | 15 % | non | p_max = 19 632 857, volume_cuves = 0.554, diametre_particule = 0.0142, epaisseur_isolant = 0.153, duree_attente = 264 721, T_amb = 270.7, humidite = 0.722, rendement_electrique = 0.947, rendement_mecanique = 0.968, efficacite_refroidisseurs = 1.048 |
| [refroidisseur_4] givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 96 | 15 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [reservoir] condensation d'eau dans le réservoir (air plus froid que son point de rosée sous pression) | 95 | 14 % | non | p_max = 19 000 000, volume_cuves = 1, diametre_particule = 0.03, epaisseur_isolant = 0.2, duree_attente = 86 400, T_amb = 253.1, humidite = 0.5, rendement_electrique = 0.945, rendement_mecanique = 1, efficacite_refroidisseurs = 1 |
| [turbine] étage 1 : givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 22 | 3 % | non | p_max = 19 632 857, volume_cuves = 0.554, diametre_particule = 0.0142, epaisseur_isolant = 0.153, duree_attente = 264 721, T_amb = 270.7, humidite = 0.722, rendement_electrique = 0.947, rendement_mecanique = 0.968, efficacite_refroidisseurs = 1.048 |
| [turbine] étage 2 : givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 19 | 3 % | non | p_max = 19 632 857, volume_cuves = 0.554, diametre_particule = 0.0142, epaisseur_isolant = 0.153, duree_attente = 264 721, T_amb = 270.7, humidite = 0.722, rendement_electrique = 0.947, rendement_mecanique = 0.968, efficacite_refroidisseurs = 1.048 |
| [turbine] étage 3 : givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 3 | 0 % | non | p_max = 23 272 301, volume_cuves = 0.554, diametre_particule = 0.0142, epaisseur_isolant = 0.153, duree_attente = 264 721, T_amb = 270.7, humidite = 0.722, rendement_electrique = 0.947, rendement_mecanique = 0.968, efficacite_refroidisseurs = 1.048 |
| [cuve_2] en décharge, givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) | 1 | 0 % | non | p_max = 23 272 301, volume_cuves = 0.554, diametre_particule = 0.0142, epaisseur_isolant = 0.153, duree_attente = 264 721, T_amb = 270.7, humidite = 0.722, rendement_electrique = 0.947, rendement_mecanique = 0.968, efficacite_refroidisseurs = 1.048 |

*Durée totale des balayages : 1806 s.*
