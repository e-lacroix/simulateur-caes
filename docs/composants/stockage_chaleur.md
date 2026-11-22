# Composant `stockage_chaleur`

Ce qui réchauffe l'air avant un étage de turbine, et d'où vient cette chaleur. En charge, un stockage placé après un étage de compression prend la chaleur de l'air chaud avant le refroidisseur ; en décharge, placé avant un étage de turbine, il réchauffe l'air au plus jusqu'à la température nominale de cet étage (sa **cible**). Toute chaleur ajoutée porte l'étiquette de sa source : le nom du composant, ou `externe`.

## Les modèles disponibles

| `modele` | Physique | Paramètres propres | Source | Quand l'utiliser |
|---|---|---|---|---|
| `gravier` | cuve cylindrique de gravier, Schumann 1D, Wakao, Ergun, bypass et pincement (F25 à F31) | `materiau`, `diametre_particule` (facultatif : granulométrie propre à la cuve, sinon celle du matériau), `volume`, `rapport_hauteur_diametre`, `n_cellules`, `pression` (`etage` ou `atmospherique`), `pincement`, `bypass`, `coefficient_perte` ou `isolation` | Tola 2022 (cas A et C), Schumann, Wakao, Ergun | Lit de roches traversé par l'air ; **vérifié contre la solution exacte et croisé avec Tola** (phase 4) ; validation expérimentale en attente (Cascetta, Barbour) |
| `huile_deux_reservoirs` | réservoirs chaud et froid d'huile, échangeurs à pincement (F40) | `masse`, `cp` (1494 J/kg·K), `pincement` (10 K), `T_max` optionnel, `coefficient_perte` + `surface` ou `isolation` | Tola 2022 (cas B, Therminol 66), Wolf et Budt 2014 (LTA-CAES, via Bazdar) | L'« huile de Dormoy » rendue physique ; référence contre laquelle comparer le gravier |
| `eau_sous_pression` | même modèle avec de l'eau liquide à `pression_cuve`, plafonnée par l'ébullition (F40) | `masse`, `pression_cuve` (18 bar), `pincement`, `marge_ebullition` | Shi 2024 (figure 7, tableau 5) ; IAPWS-95 via CoolProp | La question originale : l'eau est plafonnée (202 °C à 18 bar), le gravier non |
| `huile_ideale` | réserve parfaite (hypothèse comptable de Dormoy, § 3.3.5) alimentée par `recuperation_vers` des refroidisseurs ; appoint externe si elle manque | `appoint_externe`, `T_seuil` | Dormoy 2024 | Reproduire l'architecture C de la phase 5 ; signalé comme hypothèse |
| `source_externe` | l'air atteint toujours la cible ; chaleur étiquetée `externe` (F20) | – | Dormoy 2024 (130 / 90 / 90 °C) | Chaudière ou réseau non modélisé ; rendement « avec chaleur externe » |

### Isolation (F41)

Au lieu de `coefficient_perte`, un bloc `isolation: {materiau: laine_minerale, epaisseur: 0.2 m}` calcule U = 1/(e/k + 1/h_ext) avec la conductivité de l'isolant lue au registre (`materiau.laine_minerale.conductivite`, 0,036 W/m·K à 20 °C, Ablaoui 2023) et `isolation.h_ext` (2,5 W/m²K, la valeur de Dormoy pour l'extérieur de ses réservoirs). Avec 20 cm : U = 0,168 W/m²K.

## Sur le banc de Dormoy (architecture D, 3 turbines réchauffées à 130 / 90 / 90 °C)

| Stockage | Produit | Chaleur rendue | Restante après décharge | Remarque |
|---|---|---|---|---|
| gravier direct (3 cuves, 1,25 m³) | 41,05 kWh | 51,4 kWh | 48 kWh | cibles atteintes (bypass) |
| huile, 1500 kg, deux réservoirs | 41,05 | 51,4 | 29 kWh | cibles atteintes ; réservoir froid vide pendant la charge (stockage saturé : les refroidisseurs prennent le reste) |
| eau sous pression, 600 kg, 18 bar | 41,05 | 51,4 | 40 kWh | cibles atteintes ; plafonnée à 202 °C quand l'étage 3 sort plus chaud |
| gravier + 20 cm de laine minérale, 14 j d'attente | 37,4 | 46,2 | 0 (46,5 kWh perdus) | turbines à 99 / 58 / 66 °C en moyenne |

Les trois stockages alimentent les turbines à leur température nominale quand ils sont assez grands ; ils diffèrent par ce qu'ils exigent (cuves sous pression, huile inflammable, cuve d'eau à 18 bar) et par leur plafond : l'eau à 18 bar ne peut pas dépasser 202 °C, les compresseurs de Dormoy sortent à 170 à 195 °C ; à 200 °C et plus (Shi), elle bout.

## Domaine de validité et avertissements

- Gravier : Wakao Re de 15 à 8500 (hors plage : extrapolation signalée) ; cuve trop froide pour la cible ; `n_cellules` ≥ 5 (20 recommandées).
- Deux réservoirs : cp constant (huile : valeur à l'ambiant de Tola ; eau : cp à mi-chemin entre l'ambiant et le plafond) ; réservoirs bien mélangés ; échangeur équilibré. Avertissements : liquide plafonné, réservoir froid vide (saturé), réservoir chaud vide (pas d'appoint), huile sans `T_max`.
- Tous les stockages physiques : « isolation parfaite » signalée quand `coefficient_perte` = 0.
- Après une décharge, le bas d'une cuve de gravier peut être sous l'ambiant (froid de l'air détendu) : à la charge suivante, l'air qui en sort est sous l'ambiant (avertissement du refroidisseur aval).
- Pas encore : stratification dans les réservoirs de liquide, pertes de charge des échangeurs, matériau à changement de phase.

## Ce qu'il déclare

Charge : chaleur retirée à l'air (destination = nom du composant), perte de charge d'Ergun (gravier). Décharge : chaleur ajoutée (source = nom du composant ou `externe`), fraction de bypass. Cycles : énergie stockée au-dessus de l'ambiant, exergie (F31, F40), profil de température (gravier) ou températures des deux réservoirs.

## Sources

Schumann 1929, Wakao 1979, Jeffreson 1972, Ergun 1949 ; Tola 2022 (tableaux 2, 3, 8) ; Wolf et Budt 2014 (`wolfbudt.rte`) ; Shi 2024 (figure 7, `shi.eau.*`) ; Wagner et Pruß 2002 (IAPWS-95, `eau.cp_source`) ; Ablaoui 2023 (`materiau.laine_minerale.*`) ; Dormoy 2024 (§ 3.3.5) ; fiches F25 à F31, F40, F41 ; `rapports/phase4/`, `rapports/phase5/`, `rapports/phase7/variantes.md`.
