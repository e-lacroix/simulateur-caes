# Scénario d'exemple : transport et conservation de la chaleur

*Généré par `rapports/scenarios_transport.py` à partir de `scenarios/exemples/transport/transport.yaml` (architecture D, gravier direct, 20 cm de laine minérale, un cycle : charge au départ, attente pendant le transport, décharge à l'arrivée). Chaque case est une simulation complète ; les hypothèses sont dans le fichier YAML et au registre.*

**Question.** On charge l'installation (air à 190 bar, cuves de gravier chaudes) puis on la transporte. Combien de chaleur reste-t-il à l'arrivée, et combien d'électricité ? À partir de quand le gravier ne sert plus à rien ?

## 1. Durée du transport et épaisseur d'isolant (20 °C constant)

Chaleur après la charge : ce que les cuves contiennent au-dessus de l'ambiant au départ (toutes les cases partent du même état chargé). Restante : après l'attente. Électricité : de la décharge à l'arrivée, cuves telles qu'elles sont (sans appoint). Rendement : électricité produite / consommée à la charge.

| Isolant | Durée | Chaleur après charge (kWh) | Pertes (kWh) | Restante (kWh) | Part restante | Électricité livrée (kWh) | Rendement | Air rejeté min (°C) |
|---|---|---|---|---|---|---|---|---|
| 10 cm | 7 j | 92.8 | 44.2 | 48.6 | 52 % | 36.68 | 14.9 % | -34 |
| 10 cm | 14 j | 92.8 | 66.7 | 26.1 | 28 % | 32.82 | 13.3 % | -60 |
| 10 cm | 21 j | 92.8 | 78.3 | 14.5 | 16 % | 30.87 | 12.5 % | -71 |
| 10 cm | 28 j | 92.8 | 84.4 | 8.4 | 9 % | 29.87 | 12.1 % | -77 |
| 10 cm | 42 j | 92.8 | 89.4 | 3.4 | 4 % | 29.06 | 11.8 % | -81 |
| 10 cm | 56 j | 92.8 | 90.8 | 2.0 | 2 % | 28.83 | 11.7 % | -82 |
| 20 cm | 7 j | 92.5 | 27.3 | 65.2 | 70 % | 39.05 | 15.9 % | -4 |
| 20 cm | 14 j | 92.5 | 46.4 | 46.2 | 50 % | 36.33 | 14.7 % | -37 |
| 20 cm | 21 j | 92.5 | 59.7 | 32.8 | 35 % | 34.07 | 13.8 % | -52 |
| 20 cm | 28 j | 92.5 | 69.0 | 23.5 | 25 % | 32.49 | 13.2 % | -62 |
| 20 cm | 42 j | 92.5 | 80.3 | 12.3 | 13 % | 30.62 | 12.4 % | -73 |
| 20 cm | 56 j | 92.5 | 85.9 | 6.7 | 7 % | 29.69 | 12.1 % | -78 |
| 40 cm | 7 j | 92.4 | 15.4 | 77.0 | 83 % | 39.32 | 16.0 % | 15 |
| 40 cm | 14 j | 92.4 | 28.2 | 64.2 | 69 % | 39.00 | 15.8 % | -5 |
| 40 cm | 21 j | 92.4 | 38.8 | 53.6 | 58 % | 37.59 | 15.3 % | -25 |
| 40 cm | 28 j | 92.4 | 47.6 | 44.8 | 48 % | 36.16 | 14.7 % | -38 |
| 40 cm | 42 j | 92.4 | 61.0 | 31.4 | 34 % | 33.89 | 13.8 % | -53 |
| 40 cm | 56 j | 92.4 | 70.3 | 22.1 | 24 % | 32.33 | 13.1 % | -63 |

Référence sans transport (attente d'une heure, 20 cm) : 40.61 kWh livrés, rendement 16.5 %, chaleur après charge 92.5 kWh.

## 2. Hiver québécois et été (profil météo, 20 cm)

Profil : sinusoïde journalière de ± 5 K (hypothèse) autour de −20 °C (`meteo_hiver.csv`) ou de 30 °C (`meteo_ete.csv`), appliquée à tout le cycle : l'air aspiré, les refroidisseurs, les pertes des cuves et du réservoir suivent la température extérieure (F32). L'air aspiré reste 32 K au-dessus de l'extérieur (conteneur du compresseur).

| Climat | Durée | Électricité consommée (kWh) | Chaleur après charge | Restante | Part | Électricité livrée | Rendement | Air rejeté min (°C) |
|---|---|---|---|---|---|---|---|---|
| hiver (−20 °C) | 7 j | 255.1 | 82.1 | 58.0 | 71 % | 39.65 | 15.5 % | -61 |
| hiver (−20 °C) | 14 j | 255.1 | 82.1 | 41.2 | 50 % | 36.30 | 14.2 % | -79 |
| hiver (−20 °C) | 21 j | 255.1 | 82.1 | 29.4 | 36 % | 33.97 | 13.3 % | -92 |
| hiver (−20 °C) | 28 j | 255.1 | 82.1 | 21.1 | 26 % | 32.34 | 12.7 % | -100 |
| hiver (−20 °C) | 42 j | 255.1 | 82.1 | 11.1 | 14 % | 30.37 | 11.9 % | -110 |
| hiver (−20 °C) | 56 j | 255.1 | 82.1 | 6.1 | 7 % | 29.37 | 11.5 % | -115 |
| été (30 °C) | 7 j | 246.9 | 91.1 | 64.2 | 70 % | 38.51 | 15.6 % | 9 |
| été (30 °C) | 14 j | 246.9 | 91.1 | 45.5 | 50 % | 36.52 | 14.8 % | -28 |
| été (30 °C) | 21 j | 246.9 | 91.1 | 32.4 | 36 % | 34.37 | 13.9 % | -44 |
| été (30 °C) | 28 j | 246.9 | 91.1 | 23.2 | 25 % | 32.85 | 13.3 % | -54 |
| été (30 °C) | 42 j | 246.9 | 91.1 | 12.1 | 13 % | 31.05 | 12.6 % | -65 |
| été (30 °C) | 56 j | 246.9 | 91.1 | 6.6 | 7 % | 30.15 | 12.2 % | -70 |

Avertissements propres à l'hiver (14 j) : condensation d'eau dans le réservoir (air plus froid que son point de rosée sous pression) ; en charge, condensation d'eau (air refroidi sous son point de rosée) ; en charge, givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre) ; givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de givre).

## 3. Effet d'échelle (28 jours, 20 cm)

Les trois cuves sont multipliées par 1, 4 et 16 en volume (même forme, H = 2 D) ; le réservoir d'air et le compresseur ne changent pas, donc la chaleur à stocker non plus : une cuve plus grosse a moins de surface par mètre cube et une constante de temps plus longue (τ ∝ V/A ∝ D).

| Cuves | Volume total (m³) | Chaleur après charge (kWh) | Pertes 28 j (kWh) | Part restante | Électricité livrée (kWh) | Rendement |
|---|---|---|---|---|---|---|
| × 1 | 1.25 | 92.5 | 69.0 | 25 % | 32.49 | 13.2 % |
| × 4 | 5.00 | 140.4 | 85.5 | 39 % | 33.24 | 13.9 % |
| × 16 | 20.00 | 142.5 | 64.2 | 55 % | 31.66 | 13.2 % |

## 4. Fuites d'air du réservoir (28 jours, 20 cm)

`fuite_par_jour` : fraction de la masse d'air qui s'échappe chaque jour pendant l'attente (F12 ; 0,5 %/j est l'hypothèse du registre, 2 %/j un réservoir en mauvais état).

| Fuite | Air perdu (kg) | Masse au début de la décharge (kg) | Électricité livrée (kWh) | Rendement |
|---|---|---|---|---|
| 0.0 %/j | 0 | 1185 | 32.49 | 13.2 % |
| 0.5 %/j | 155 | 1030 | 26.37 | 10.7 % |
| 2.0 %/j | 508 | 677 | 11.71 | 4.8 % |

## 5. Solution de repli : chaudière d'appoint (20 cm, 20 °C)

`transport_appoint.yaml` ajoute une source externe après chaque cuve : l'air atteint toujours 130 / 90 / 90 °C. La chaleur externe est comptée ; le rendement est donné sans elle (électricité seule) et avec elle (électricité + chaleur au dénominateur).

| Durée | Électricité livrée (kWh) | Chaleur externe (kWh) | Rendement sans chaleur | Rendement avec chaleur externe | Air rejeté min (°C) |
|---|---|---|---|---|---|
| 7 j | 39.32 | 1.6 | 16.0 % | 15.9 % | 15 |
| 14 j | 39.32 | 14.3 | 16.0 % | 15.1 % | 15 |
| 21 j | 39.32 | 24.4 | 16.0 % | 14.5 % | 15 |
| 28 j | 39.32 | 30.0 | 16.0 % | 14.2 % | 15 |
| 42 j | 39.32 | 36.8 | 16.0 % | 13.9 % | 15 |
| 56 j | 39.32 | 40.3 | 16.0 % | 13.7 % | 15 |

## 6. Vérification à la main : constante de temps

Cuve de 2 m³ de gravier (H = 2 D : D = 1.08 m, A = 9.2 m²) sous 20 cm de laine minérale (k = 0.036 W/m·K, h_ext = 2.5 W/m²K) : U = 0.168 W/m²K, capacité 3.46 MJ/K, **τ = C / (U·A) = 26 jours** (fiche Dormoy : ≈ 23 jours). Les cuves du scénario sont plus petites : τ = 14 j (cuve 1, 0.35 m³), 12 j (cuve 2, 0.2 m³), 18 j (cuve 3, 0.7 m³). Après un temps t, une cuve isolée garde e^(−t/τ) de sa chaleur au-dessus de l'ambiant : la colonne « part restante » du tableau 1 doit suivre cette loi, aux pertes par les fonds et aux gradients internes près.

![chaleur](transport_chaleur.png)

![électricité](transport_electricite.png)

*43 simulations, 154 s.*
