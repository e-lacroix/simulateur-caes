# Composant `turbine`

Une machine à plusieurs étages de détente. Dans la chaîne de décharge, chaque étage est un maillon (`turbine.1`, `turbine.2`, …) précédé des stockages de chaleur qui le réchauffent. La température nominale d'entrée `T_entree_cible` d'un étage est la **cible** de ces réchauffeurs ; sans réchauffeur, l'étage reçoit l'air tel quel (pas d'appoint implicite).

## Les modèles disponibles

| `modele` | Physique | Paramètres propres | Source | Quand l'utiliser |
|---|---|---|---|---|
| `polytropique_deprag` | détente polytropique entre les pressions nominales, rendements mécanique et électrique par étage (F17, F18) ; point fixe | `etages[].p_entree`, `p_sortie`, `indice_polytropique`, `rendement_mecanique`, `rendement_electrique` | Dormoy 2024 (tableau 9, DEPRAG) | Le banc de Dormoy : **reproduit le tableau 9 à 3 % près** (phase 2) |
| `isentropique` | détente adiabatique à η_s constant (F34) ; accepte une pression d'entrée variable | `rendement_isentropique` (0,90 Shi, 0,88 Zhang), `rendement_mecanique`, `rendement_electrique` (machine ou par étage) ; `etages[].p_entree` optionnel | Shi 2024, Zhang S. 2025 | Grandes turbines, cas test de Shi, pression glissante en borne optimiste |
| `polytropique_rendement` | détente adiabatique à η_p constant (F35) | `rendement_polytropique` (0,86) | Tola 2022 (tableau 6) | Turbines décrites par Tola |
| `flugel` | η_s nominal corrigé hors du point nominal, débit imposé par la loi de l'ellipse de Stodola (F39) | `rendement_isentropique`, `t4` (0,3), `etages[].p_entree`, `p_sortie`, `T_entree_nominale` (point nominal) | Zhang S. 2025 (éq. 1 à 7) | Pression glissante réelle : le débit suit la pression du réservoir |

La petite chute de pression entre la sortie d'un étage et l'entrée du suivant (11,5 → 11 bar chez DEPRAG) est un laminage isenthalpique appliqué à la sortie de l'étage amont (F33) ; avec `flugel`, les pressions entre étages sont résolues pour que tous passent le même débit. Pour n'utiliser qu'un étage (cas de base : étage 3 seul), on ne déclare que celui-là.

## Sur le banc de Dormoy (190 → 55 bar, réchauffage externe à 130 / 90 / 90 °C)

| Modèle | Électricité | Durée | Débit | Chaleur externe | Air rejeté (min) |
|---|---|---|---|---|---|
| DEPRAG + détendeur | 39,0 kWh | 37,6 min | 0,321 kg/s | 44,6 kWh | 15 °C |
| isentropique 0,90 (rendements DEPRAG) | 33,1 | 37,6 | 0,321 | 57,4 | 2 °C |
| polytropique 0,86 | 32,8 | 37,6 | 0,321 | 57,3 | 4 °C |
| pression glissante, η_s constant | 39,0 | 37,6 | 0,321 | 69,6 | 2 °C |
| pression glissante + Flügel | 41,1 | **14,9** | **0,802** | 60,8 | **−78 °C** |

Avec Flügel, la DEPRAG à 190 bar laisse passer 2,5 fois son débit nominal (4,7 fois au début) : le réservoir se vide en 15 min, la puissance quadruple, et l'air sort à −78 °C. Le gain de 5 % par rapport au détendeur n'est réel que pour une turbine conçue pour cette plage de pression ; les coefficients de Flügel viennent de grosses turbines (avertissement statique). C'est la question de recherche ouverte par Shi et Zhang, posée ici en chiffres.

## Domaine de validité et avertissements

- `polytropique_deprag` : point fixe ; air reçu hors de la pression nominale → laminé (au-dessus) ou calcul à la nominale (au-dessous), avec avertissement.
- Modèles à rendement : η dans ]0, 1] ; étage inactif si la pression d'entrée est au niveau de la sortie.
- `flugel` : coefficients à vérifier pour une petite turbine (avertissement) ; rendement relatif plancher à 0,05 ; avertissement sous 0,5 ; le débit du pas est calculé avec les températures d'entrée du pas précédent.
- Tous : air rejeté sous 0 °C → « risque de givrage » (phase 9) ; une détente qui mènerait sous 100 K (zone de condensation de l'air) arrête proprement la simulation avec un avertissement (`HorsDomaine`).
- Pression de sortie du dernier étage DEPRAG (1,0 bar) sous l'atmosphère : artefact des données fabricant signalé en phase 3.

## Ce qu'il déclare

Par étage : `ResultatDetenteEtage` (p, T en entrée et sortie, travail, mécanique, électrique, Δh, chaleur résiduelle, rendement relatif). Le réchauffage amont et sa source sont déclarés par les stockages ; la simulation les rattache à l'étage (`Q_rech_i_w`, `chaleur_par_source`). Avec `flugel`, `debit_kg_s` des totaux est la moyenne sur la décharge.

## Sources

Dormoy et al. 2024 (§ 2.2.6, éq. 16 et 17 ; tableau 9 des données supplémentaires) ; Shi 2024 (tableau 4) ; Tola 2022 (tableau 6) ; Zhang S. 2025 (§ 3.1.1, `zhangS.flugel.t4`, `zhangS.turbine.rendement_isentropique`) ; fiches F17 à F19, F34, F35, F39 ; `rapports/phase2/validation_decharge.md`, `rapports/phase7/variantes.md`.
