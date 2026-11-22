# Phase 7 : les modèles de la bibliothèque comparés sur le banc de Dormoy

*Généré par `rapports/phase7_variantes.py`. Chaque ligne est un scénario de `scenarios/` ou `scenarios/variantes/` ; seul le composant nommé change par rapport à la référence. Les avertissements sont ceux du simulateur (domaine de validité).*

## 1. Charge 1 → 190 bar (référence : aspiration chaude, 386 kWh)

| Scénario | Modèle changé | Électricité (kWh) | Durée (h) | Chaleur des refroidisseurs (kWh) | dont > 130 °C | T sortie étage 3 (°C, moy.) | T finale réservoir (°C) | Avertissements |
|---|---|---|---|---|---|---|---|---|
| `dormoy_charge_1_190_aspiration_chaude.yaml` | référence (Dormoy) | 386.2 | 9.89 | 265.8 | 90.7 | 197 | 29 | air humide au-delà de 10 MPa ; air humide au-delà de 10 MPa |
| `charge_compresseur_isentropique.yaml` | compresseur isentropique η_s = 0,86 (Shi) | 445.3 | 9.86 | 309.6 | 134.8 | 180 | 29 | air humide au-delà de 10 MPa ; air humide au-delà de 10 MPa |
| `charge_compresseur_polytropique_rendement.yaml` | compresseur polytropique η_p = 0,88 (Tola) | 465.0 | 9.85 | 321.1 | 149.3 | 186 | 29 | air humide au-delà de 10 MPa ; air humide au-delà de 10 MPa |
| `charge_compresseur_isotherme.yaml` | compresseur isotherme (borne, Baniamerian) | 303.5 | 9.96 | 16.8 | 0.0 | 21 | 27 | modèle « isotherme » ; étage 2 ; étage 3 ; (+3) |
| `charge_refroidisseur_pincement.yaml` | refroidisseurs à pincement 20 K (Tola) | 382.1 | 9.90 | 263.5 | 81.2 | 190 | 28 | air humide au-delà de 10 MPa ; air humide au-delà de 10 MPa |
| `charge_refroidisseur_perte_de_charge.yaml` | isentropique + pincement 10 K + Δp 0,04 MPa (Shi) | 448.3 | 9.93 | 324.6 | 108.2 | 163 | 28 | air humide au-delà de 10 MPa ; air humide au-delà de 10 MPa |
| `charge_secheur_aucun.yaml` | sans sécheur | 310.4 | 7.95 | 213.7 | 72.9 | 197 | 30 | air humide au-delà de 10 MPa ; air humide au-delà de 10 MPa ; condensation d'eau dans le réservoir (air plus froid que son point de  |
| `charge_reservoir_adiabatique.yaml` | réservoir adiabatique + 0,2 MPa (Shi) | 251.6 | 6.44 | 173.2 | 59.2 | 197 | 167 | modèle « adiabatique » sur un petit réservoir ; air humide au-delà de 10 MPa ; refoulement au-dessus de la plage calibrée (190 bar) ; (+1) |

## 2. Décharge 190 → 55 bar, 3 étages (référence : DEPRAG, réchauffage externe)

| Scénario | Modèle changé | Électricité (kWh) | Durée (min) | Débit moyen (kg/s) | Chaleur externe (kWh) | T rejet min (°C) | p entrée étage 1 (bar, début → fin) | Avertissements |
|---|---|---|---|---|---|---|---|---|
| `dormoy_decharge_3etages.yaml` | référence (DEPRAG, détendeur) | 39.04 | 37.6 | 0.321 | 44.6 | 15 | 40 → 40 | condensation d'eau dans le réservoir (air plus froid que son point de  |
| `decharge_turbine_isentropique.yaml` | turbine isentropique η_s = 0,90 (Shi) | 33.12 | 37.6 | 0.321 | 57.4 | 2 | 40 → 40 | condensation d'eau dans le réservoir (air plus froid que son point de  ; étage 2 |
| `decharge_turbine_polytropique_rendement.yaml` | turbine polytropique η_p = 0,86 (Tola) | 32.79 | 37.6 | 0.321 | 57.3 | 4 | 40 → 40 | condensation d'eau dans le réservoir (air plus froid que son point de  ; étage 2 |
| `decharge_pression_glissante.yaml` | pression glissante, η_s constant (Shi) | 38.96 | 37.6 | 0.321 | 69.6 | 2 | 190 → 55 | condensation d'eau dans le réservoir (air plus froid que son point de  ; air humide au-delà de 10 MPa ; étage 1 ; (+2) |
| `decharge_flugel.yaml` | pression glissante + Flügel (Zhang S.) | 41.05 | 14.9 | 0.802 | 60.8 | -78 | 190 → 55 | modèle « flugel » ; condensation d'eau dans le réservoir (air plus froid que son point de  ; air humide au-delà de 10 MPa ; (+5) |

## 3. Cycles avec stockage de chaleur (référence : D, gravier direct, attente 1 h)

| Scénario | Stockage / attente | Cycles | Charge (kWh) | Produit (kWh) | RTE | Chaleur rendue (kWh) | Chaleur restante (kWh) | Pertes pendant l'attente (kWh) | T entrée turbines (°C, moy.) | Avertissements |
|---|---|---|---|---|---|---|---|---|---|---|
| `D.yaml` | gravier direct, attente 1 h sans pertes (phase 5) | 4 | 239.5 | 41.05 | 17.1 % | 51.4 | 48.1 | 0.0 | 130 / 90 / 90 | isolation parfaite (aucune perte pendant l'attente) ; isolation parfaite (aucune perte pendant l'attente) ; isolation parfaite (aucune perte pendant l'attente) ; (+7) |
| `cycles_huile_deux_reservoirs.yaml` | huile à deux réservoirs (Tola, Wolf et Budt) | 3 | 238.7 | 41.05 | 17.2 % | 51.4 | 29.1 | 0.0 | 130 / 90 / 90 | huile sans T_max ; cp de l'huile pris constant (valeur de Tola à l'ambiant) ; concept LTA ; isolation parfaite (aucune perte pendant l'attente) ; (+4) |
| `cycles_eau_sous_pression.yaml` | eau sous pression 18 bar (Shi) | 3 | 238.7 | 41.05 | 17.2 % | 51.4 | 39.7 | 0.0 | 130 / 90 / 90 | eau sous pression ; isolation parfaite (aucune perte pendant l'attente) ; air humide au-delà de 10 MPa ; (+4) |
| `cycles_attente_sans_pertes_14j.yaml` | gravier, 14 j sans pertes (borne) | 2 (non stab.) | 240.7 | 41.22 | 17.1 % | 50.7 | 47.2 | 0.0 | 130 / 90 / 90 | modèle « sans_pertes » sur plus d'un jour ; air humide au-delà de 10 MPa ; air entrant plus froid que l'ambiant (le gravier amont a gardé du froi ; (+5) |
| `cycles_gravier_isolant_14j.yaml` | gravier, 14 j, 20 cm de laine minérale | 2 (non stab.) | 232.6 | 37.37 | 16.1 % | 46.2 | -0.6 | 46.5 | 99 / 58 / 66 | air humide au-delà de 10 MPa ; air entrant plus froid que l'ambiant (le gravier amont a gardé du froi ; air entrant plus froid que l'ambiant (le gravier amont a gardé du froi ; (+11) |

## 4. Lecture

- Les modèles génériques (isentropique, polytropique à rendement) avec les rendements de Tola et de Shi ne reproduisent pas le banc de Dormoy : ce sont des rendements de grosses turbomachines appliqués à un compresseur à pistons de 45 kW. Ils servent au changement d'échelle (phase 8, cas de Shi), pas à la validation.
- La borne isotherme dit ce qu'aucun compresseur ne peut battre ; l'écart avec Dormoy mesure la chaleur de compression.
- La pression glissante supprime la perte du détendeur ; avec la formule de Flügel, le débit suit la pression et la turbine DEPRAG se retrouve très loin de son point nominal : le gain n'est réel qu'avec une turbine conçue pour cette plage.
- Les deux réservoirs d'huile ou d'eau alimentent les turbines comme le gravier au volume de base ; l'eau est plafonnée par son ébullition (18 bar : 202 °C) alors que les compresseurs de Dormoy sortent jusqu'à 195 °C en moyenne.
- Après 14 jours derrière 20 cm de laine minérale, les cuves de base perdent une part de leur chaleur et les turbines reçoivent de l'air plus froid ; c'est le point de départ du scénario de transport (phase 11).
