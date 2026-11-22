# Composant `detente`

Ce qui se passe entre le réservoir (jusqu'à 190 bar) et la turbine. Dans la chaîne de décharge, il vient juste après le réservoir.

## Les modèles disponibles

| `modele` | Physique | Paramètres propres | Source | Quand l'utiliser |
|---|---|---|---|---|
| `isenthalpique` | laminage, h_out = h_in ; l'air réel se refroidit (Joule-Thomson) (F15) | `p_consigne`, `ecart_min` (15 bar) | Dormoy 2024 | Détendeur à consigne fixe ; **validé sur l'essai de décharge** (37,3 min contre 38) |
| `cheayb` | relation semi-empirique T(P) = a·P² + b·P + c (F16) | `cheayb.a1 … b4`, `p_min_validite`, `p_max_validite` | Cheayb et al. via Dormoy | Même usage ; valide de 25 à 150 bar (avertissement au-delà) ; concorde avec l'isenthalpique à 1 K près |
| `isotherme` | T_out = T_in : **diagnostic seulement** | – | – | Mesurer l'effet du refroidissement Joule-Thomson |
| `pression_glissante` | pas de détendeur : la turbine reçoit l'air à la pression du réservoir (F39) | `p_min` (arrêt de la décharge) | Shi 2024, Zhang S. 2025 | Supprimer la perte du détendeur ; exige une turbine à pression d'entrée variable (`isentropique`, `polytropique_rendement`, `flugel`) |

Pour les trois premiers modèles, la décharge s'arrête quand la pression du réservoir passe sous `p_consigne + ecart_min` ; l'assembleur vérifie que la consigne égale la pression d'entrée du premier étage de turbine. Avec `pression_glissante` et une turbine à point fixe (`polytropique_deprag`), l'air serait laminé à l'entrée nominale : l'assembleur le signale.

## Sur le banc de Dormoy

Le détendeur est la perte dominante du cas de base (234 unités sur 1000, phase 3 ; 71 avec 3 étages). En pression glissante avec un rendement constant (hypothèse de Shi), la décharge produit 38,96 kWh contre 39,04 avec le détendeur, mais demande 70 kWh de réchauffage au lieu de 45 : l'étage 1 détend de 190 à 11,5 bar et sort très froid. Le gain apparaît seulement si la turbine est conçue pour cette plage (voir `turbine.md`, modèle `flugel`).

## Domaine de validité et avertissements

- `cheayb` hors de 25 à 150 bar : avertissement (le cas de Dormoy commence à 190 bar).
- `isotherme` : avertissement statique.
- `pression_glissante` : `p_min > 0` ; le choix de `p_min` (55 bar comme Dormoy, 40 bar comme Shi) fixe la masse morte.
- Pas encore : vanne ON/OFF et réservoir tampon (Zhang S.), éjecteur, tuyères.

## Ce qu'il déclare

`ResultatDetente` : p et T en entrée et sortie, h_in, h_out, modèle, drapeau hors validité (Δh nul pour l'isenthalpique et la pression glissante).

## Sources

Dormoy et al. 2024 (§ 2.2.5, éq. 15) ; Shi 2024 (§ 1.3, § 3) ; Zhang S. 2025 ; fiches F15, F16, F39 ; `rapports/phase2/validation_decharge.md`, `rapports/phase7/variantes.md`.
