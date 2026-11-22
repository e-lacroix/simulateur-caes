# Composant `compresseur`

Une machine à plusieurs étages. Dans une chaîne de charge, chaque étage est un maillon (`compresseur.1`, `compresseur.2`, …) entre lesquels on place les stockages de chaleur et les refroidisseurs. La machine est préparée une fois par pas de temps à partir de la pression du réservoir : pression de refoulement p_ref = max(p_réservoir + surpression, p_min), puis chaque étage calcule son rapport.

## Les modèles disponibles

| `modele` | Physique | Paramètres propres | Source | Quand l'utiliser |
|---|---|---|---|---|
| `polytropique_dormoy` | p·vⁿ = cte par étage, n calibré ; rapports fixes puis linéaires en pression ; rendement mécanique calibré linéaire en pression (F04 à F08) | `etages[].indice_polytropique`, `rapport_pression`, `rapport_pression_min/max`, `rendement_mecanique_min/max`, `pression_refoulement_min/max` | Dormoy 2024 (tableau 2, tableau 7) | Le banc de Dormoy et tout compresseur à pistons dont on a calibré les indices ; **seul modèle validé sur des mesures** (phase 1, −2,5 %) |
| `isentropique` | compression adiabatique, h_out = h_in + Δh_s/η_s (F34) | `rendement_isentropique` (machine ou par étage), `rendement_mecanique`, `etages[].rapport_pression` ou `T_sortie` ou rien | Shi 2024 (0,86), Zhang S. 2025 | Grandes turbomachines, cas test de Shi (phase 8), changement d'échelle |
| `polytropique_rendement` | compression adiabatique, (n−1)/n = (γ−1)/(γ·η_p) (F35) | `rendement_polytropique` (0,88) | Tola 2022 (tableau 1) | Compresseurs à plusieurs étages décrits par leur rendement polytropique (Tola) |
| `isotherme` | T constante, w = p·v·ln β (F36) | aucun rendement thermodynamique | Baniamerian 2025, éq. 8 | **Borne** : le travail minimal possible ; mesure ce que coûte la chaleur de compression |

Paramètres communs : `debit_volumique_aspire` (cylindrée × vitesse, F06) ou `debit_massique_aspire` (imposé), `rendement_electrique`, `pression_refoulement_min` (soupape, 0 par défaut pour les modèles génériques).

### Répartition des rapports (modèles génériques)

Chaque étage déclare au choix `rapport_pression` (fixe), `T_sortie` (le rapport est résolu pour atteindre cette température de sortie, règle de Tola et de Shi : 170 °C, 200 °C) ou rien ; les étages sans consigne se partagent à parts égales le rapport restant jusqu'à p_ref (F33). Si la pression est déjà atteinte en amont, l'étage est inactif (rapport 1, avertissement) : c'est le compresseur 4 de Shi qui ne tourne que 7 h sur 8. Les pertes de charge des maillons placés après le dernier étage (refroidisseur à `perte_de_charge`) sont compensées par ce dernier étage.

## Sur le banc de Dormoy (`rapports/phase7/variantes.md`)

| Modèle | Électricité 1 → 190 bar | Chaleur rejetée | T sortie étage 3 |
|---|---|---|---|
| Dormoy calibré | 386 kWh | 266 kWh | 197 °C |
| isentropique 0,86 (rendements mécanique et électrique de Dormoy) | 445 kWh | 310 kWh | 180 °C |
| polytropique 0,88 | 465 kWh | 321 kWh | 186 °C |
| isotherme (borne) | 304 kWh | 17 kWh | 21 °C |

Les rendements de Shi et de Tola, pris pour de grosses turbomachines, ne décrivent pas le compresseur à pistons de 45 kW de Dormoy ; ils sont là pour le changement d'échelle, pas pour la validation. La borne isotherme dit qu'aucun compresseur ne peut descendre sous 304 kWh ; l'écart avec Dormoy (82 kWh) est le prix de la chaleur de compression, que le gravier récupère en partie.

## Domaine de validité et avertissements

- Dormoy : lois en pression calibrées entre `pression_refoulement_min` et `pression_refoulement_max` ; au-delà, bloquées à la borne (avertissement). Indices vérifiés dans [1 ; 1,6].
- Génériques : rendements dans ]0, 1] ; étage inactif signalé ; température visée inatteignable signalée.
- Isotherme : avertissement statique « borne, pas une machine réelle ».
- Tous : l'air aspiré vient de l'ambiance (`T_aspiration`, F32).
- Pas encore : rendement variable avec la charge, machine hors point nominal, piston liquide (n ≈ 1,06).

## Ce qu'il déclare

Par étage : `ResultatEtage` (p, T, ρ en entrée et sortie, β, n équivalent, travail, Δh, chaleur échangée pendant la compression). Le travail électrique est calculé au niveau de la machine (F08). Les séries gardent les colonnes des phases 1 à 5 (`beta_i`, `T_out_comp_i_K`, `w_pol_i_j_kg`, …).

## Sources

Dormoy 2024 ; Shi 2024 (tableau 4, `shi.compresseur.rendement_isentropique`) ; Tola 2022 (tableau 1, `tola.compresseur.rendement_polytropique`) ; Baniamerian 2025 (éq. 8) ; fiches F04 à F08, F34 à F36 ; `rapports/phase1/validation_charge.md`, `rapports/phase7/variantes.md`.
