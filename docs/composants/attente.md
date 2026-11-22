# Composant `attente`

Le temps qui passe entre la charge et la décharge : une heure sur le banc, plusieurs semaines pendant un transport. L'air comprimé ne perd pas son énergie utile en refroidissant : seule la chaleur stockée se perd, et c'est ce que les scénarios de transport (phase 11) mesurent.

Phase 11 : pendant l'attente, le réservoir peut fuir (`fuite_par_jour`, F12) et l'ambiance peut suivre un profil météo ; les scénarios de transport (`scenarios/exemples/transport/`) balaient durée, isolant, climat et fuites.

## Les modèles disponibles

| `modele` | Physique | Paramètres | Quand l'utiliser |
|---|---|---|---|
| `pertes_statiques` | le réservoir fait des pas sans débit (F12) ; chaque stockage de chaleur perd U·A·(T − T_amb) (F29, F41) avec la température extérieure du profil météo | `duree`, `dt` (10 min par défaut) | Tout cas réel ; les pertes dépendent du `coefficient_perte` ou du bloc `isolation` de chaque stockage |
| `sans_pertes` | le temps passe, rien ne change | `duree` | Borne optimiste (isolation parfaite, hypothèse de la phase 5) ; avertissement au-delà d'un jour |

Le composant est nommé dans `simulation.attente` ; sans lui, la décharge suit immédiatement la charge.

## Sur le banc de Dormoy (architecture D, 14 jours entre charge et décharge)

| Attente | Chaleur perdue | Produit | Entrée des turbines |
|---|---|---|---|
| sans pertes | 0 | 41,2 kWh | 130 / 90 / 90 °C |
| 20 cm de laine minérale sur chaque cuve | 46,5 kWh (tout) | 37,4 kWh | 99 / 58 / 66 °C |

Les cuves de base (0,35, 0,2 et 0,7 m³) ont beaucoup de surface par litre : derrière 20 cm de laine minérale (U = 0,17 W/m²K), elles perdent l'essentiel de leur chaleur en 14 jours (constante de temps de 10 à 20 jours) et les turbines reçoivent de l'air trop froid. C'est le point de départ du scénario de transport : plus de gravier, plus d'isolant, ou des modules plus gros (le volume croît plus vite que la surface).

## Domaine de validité et avertissements

- Pas de ponts thermiques ni de fond ; conduction axiale dans les lits ; réservoirs de liquide bien mélangés.
- Pendant l'attente, une cuve de type `etage` garde la pression de sa dernière traversée (sans débit, elle n'intervient que dans l'air interstitiel, négligé).
- La plage d'autodécharge des grandes installations (0,05 à 1 % par jour, Zhang Z. 2021, tableau 11) est un repère : une petite cuve perd beaucoup plus.

## Ce qu'il déclare

Durée, chaleur perdue par les stockages, chaleur cédée par l'air du réservoir. Les cycles enregistrent `pertes_attente_kwh`.

## Sources

Fiches F12, F29, F41 ; Ablaoui 2023 ; Zhang Z. 2021 (`zhangZ.autodecharge_tes`) ; plan v2, scénario « transport et conservation de la chaleur ».
