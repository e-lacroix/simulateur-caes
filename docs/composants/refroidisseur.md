# Composant `refroidisseur`

Un échangeur qui refroidit l'air comprimé avec l'air ambiant, après un étage de compression (ou après un stockage de chaleur qui a pris sa part). Sa source froide est **toujours** la température ambiante du bloc `ambiance` (F32).

## Les modèles disponibles

| `modele` | Physique | Paramètres propres | Source | Quand l'utiliser |
|---|---|---|---|---|
| `efficacite` | T_out = T_in − ε·(T_in − T_amb), ε fixe ou linéaire en pression de refoulement (F09, F07) | `efficacite`, ou `efficacite_min`, `efficacite_max`, `p_min`, `p_max` | Dormoy 2024 (tableau 2, calibration) | Un échangeur dont on a mesuré l'efficacité ; **validé sur Dormoy** (191,6 kWh rejetés contre 189,2) |
| `pincement` | T_out = T_amb + δ (écart minimal), sauf si l'air est déjà plus froid (F37) | `pincement` (20 K air/air chez Tola, 10 K chez Shi) | Tola 2022 (tableau 2), Shi 2024 (tableau 4) | Un échangeur dimensionné, pas mesuré : études de conception, boucle d'air de l'architecture E |

Paramètres communs : `T_seuil_chaleur_utile` (chaleur comptée « récupérable » au-dessus de ce seuil, tableau 6 de Dormoy), `perte_de_charge` (Shi : 0,04 MPa par échangeur ; chute isenthalpique après le refroidissement), `recuperation_vers` (nom d'un stockage `huile_ideale` qui reçoit la chaleur au-dessus du seuil sans changer l'état de l'air : hypothèse comptable de Dormoy, § 3.3.5).

## Sur le banc de Dormoy

Le pincement de 20 K donne presque le même résultat que les efficacités calibrées (382 contre 386 kWh ; air à 40 °C au lieu de 43 à 46 °C en sortie), parce que les refroidisseurs de Dormoy sont bons (ε = 0,85 à 0,96). Avec 10 K et 0,04 MPa de perte par échangeur (Shi) et un compresseur isentropique, la charge coûte 448 kWh : les pertes de charge sont compensées par le dernier étage.

## Domaine de validité et avertissements

- ε dans [0, 1] ; `p_min < p_max` ; δ ≥ 0 ; perte de charge ≥ 0.
- Si l'air entre plus froid que l'ambiant (cuve de gravier amont qui a gardé le froid de la décharge), le modèle à efficacité le **réchauffe** symétriquement (comportement des phases 1 à 5, conservé pour la non-régression) ; le modèle à pincement le laisse tel quel. Un avertissement le signale dans les deux cas.
- Avec le compresseur de Dormoy (rapports fixes), une perte de charge n'est pas compensée : l'assembleur le signale.
- La géométrie des échangeurs de Dormoy est inconnue : l'efficacité calibrée tient lieu de modèle ; Shi : chaque °C de pincement en plus coûte 0,35 point de rendement.

## Ce qu'il déclare

`ResultatRefroidisseur` : T_in, T_out, ε (ou efficacité équivalente), q, q au-dessus du seuil. Dans le flux : chaleur retirée (destination `ambiant`, et le stockage de récupération s'il y en a un), perte de charge.

## Sources

Dormoy 2024 (§ 2.2.4, éq. 6 à 9) ; Tola 2022 (tableau 2, `tola.pincement_air`, `tola.pincement_huile`) ; Shi 2024 (tableau 4, `shi.pincement`, `shi.perte_charge_echangeur`) ; fiches F09, F37.
