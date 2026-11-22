# Composants `secheur` et `perte_debit`

Deux maillons qui réduisent (ou non) le débit sans changer la pression ni la température.

## `secheur`

| `modele` | Physique | Paramètres | Source | Quand l'utiliser |
|---|---|---|---|---|
| `perte_debit` | une fraction du débit est rejetée pour régénérer l'adsorbant (F10) ; `debit_sortie_impose` force le débit sortant ; avec `point_de_rosee_sortie`, la vapeur est ramenée à ce point de rosée sous pression et l'eau liquide est drainée (F43) | `efficacite` (0,81), `debit_sortie_impose` (0,032 kg/s mesurés, ou `null`), `point_de_rosee_sortie` (−40 °C, hypothèse) | Dormoy 2024 (éq. 10, tableau 6) | Sécheur par adsorption d'un banc à haute pression (Dormoy) ; un « sécheur d'appoint » est le même modèle avec une purge réduite (`secheur.appoint.efficacite`, 5 %, hypothèse) |
| `separateur` | retient une fraction de l'eau **liquide** entraînée (gouttes après un refroidisseur), sans perte d'air (F43) | `efficacite_separation` (0,98, hypothèse) | – | Après chaque refroidisseur, pour drainer les condensats ; seul, il ne retire pas la vapeur |
| `aucun` | l'air passe tel quel | – | Tola 2022, Shi 2024 (pas de sécheur) | Grandes installations ; pour mesurer ce que coûte le sécheur |

Phase 9 : l'eau est suivie dans tout l'air (`EtatAir.w_vapeur_kg_kg`, `w_liquide_kg_kg`), à partir de l'humidité relative du bloc `ambiance` (F42). Les scénarios `scenarios/humidite/` comparent le sécheur de Dormoy, des séparateurs seuls et séparateurs plus sécheur d'appoint ; `rapports/phase9/humidite.md` donne les conditions (température, humidité) où le sécheur est évitable.

Sur Dormoy : sans sécheur, la charge 1 → 190 bar coûte 310 kWh au lieu de 386 (8,0 h au lieu de 9,9) : 19 % de l'air comprimé n'est plus jeté. Ce que ça coûte en eau (phase 9, `rapports/phase9/humidite.md`) : avec des séparateurs seuls, l'air quitte le dernier refroidisseur saturé et le réservoir, en refroidissant, condense 0,04 (−20 °C) à 1 kg (30 °C) d'eau par cycle, quelle que soit l'humidité aspirée ; la turbine non réchauffée de A givre (0,1 kg par décharge à 20 °C), le détendeur de B givre en hiver. Avec un point de rosée de −40 °C sous pression, aucune condensation ni givre en B dans les douze climats testés, 0,2 à 2 g de givre résiduel en A, que la purge soit de 19 % (Dormoy) ou de 5 % (appoint, hypothèse) : ce qui protège est le point de rosée, pas la purge.

## `perte_debit`, modèle `fraction`

Une fraction du débit est perdue, sans changement d'état (`fraction_conservee`, par exemple `compresseur.rendement_volumetrique` = 0,83).

Pourquoi un composant à part : chez Dormoy (tableau 6), le travail de compression s'applique au débit **aspiré** (0,052 kg/s) et seuls 83 % sont refoulés ; les refroidisseurs, eux, voient tout le débit. Dans les phases 1 à 5, cette convention était cachée dans le code de la charge ; depuis la phase 6 elle est visible dans la chaîne (`refoulement` après `refroidisseur_4`). Le même maillon peut représenter une fuite.

## Domaine de validité et avertissements

- Fractions dans ]0, 1] ; avertissement si le débit imposé dépasse le débit entrant.
- L'air perdu emporte son enthalpie (h − h_amb) à l'endroit où il est perdu (F13) ; dans le bilan d'exergie, l'exergie de l'air perdu est comptée à l'état de sortie de la chaîne (F21).

## Sources

Dormoy et al. 2024 (§ 2.2.4, éq. 10 ; tableau 6 ; nomenclature) ; fiches F10 et F13.
