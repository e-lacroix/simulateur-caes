# Composant `reservoir_air`

Le réservoir équivalent (volume et surface sommés, F11) : bilans de masse et d'énergie à chaque pas (F12), air réel (CoolProp, F02). Dernier maillon de la chaîne de charge, premier de la chaîne de décharge ; dans les cycles, le même objet sert aux deux. L'air qui arrive à une pression supérieure est laminé à enthalpie constante.

## Les modèles disponibles

| `modele` | Pertes thermiques | Paramètres propres | Source | Quand l'utiliser |
|---|---|---|---|---|
| `K_global` | K·A·(T − T_amb) vers l'ambiant (éq. 14) | `K_global` (8,8 W/m²K) | Dormoy 2024 (calibration) | Charge d'un réservoir hors sol (phase 1) |
| `paroi` | la paroi a une capacité ; h_int·A·(T − T_paroi) et h_ext·A·(T_paroi − T_amb) (éq. 21) | `h_int`, `h_ext`, `capacite_thermique_paroi` | Dormoy 2024 (calibration) | Décharge et cycles d'un réservoir hors sol : nécessaire (phase 2 : 37,3 min contre 38 mesurées ; 36 min avec K global) |
| `adiabatique` | aucune (F38) | – | Shi 2024 (tableau 4) | Caverne ou très gros réservoir, où la paroi ne compte pas pendant une charge |

Paramètres communs : `volume`, `surface`, `p_max` (avertissement si dépassée), `surpression_entree` (Shi : 0,2 MPa que la chaîne de compression doit fournir au-dessus de la pression du réservoir).

## Sur le banc de Dormoy : « la physique change avec la taille »

| Modèle | Charge 1 → 190 bar | Durée | T finale de l'air |
|---|---|---|---|
| paroi / K global (Dormoy) | 386 kWh | 9,9 h | 29 °C |
| adiabatique (+ 0,2 MPa) | 252 kWh | 6,4 h | **167 °C** |

Sans paroi, le travail de refoulement reste dans l'air : il chauffe, la pression cible est atteinte avec 35 % de masse en moins, et cette masse « manquante » coûterait la différence à la décharge. Pour 5,86 m³ en bouteilles d'aluminium et de carbone, la paroi évacue cette chaleur en quelques heures (Dormoy le mesure) ; pour une caverne de 118 000 m³ (Shi), elle n'a pas le temps. `verifier_validite` avertit quand le modèle adiabatique est appliqué sous 1000 m³.

## Domaine de validité et avertissements

- Température uniforme, volume constant, pas de rayonnement (hypothèses de Dormoy).
- Avertissements : air entrant à une pression inférieure à celle du réservoir ; pression au-dessus de `p_max` ; température de l'air hors de −73 à 177 °C ; adiabatique sous 1000 m³.
- La perte thermique est intégrée exactement sur le pas (stable quand la masse d'air est petite).
- Eau (phase 9, F43) : la vapeur de l'air stocké ne dépasse pas la saturation à (T, p) du réservoir ; l'excès se condense au fond (`eau_liquide_kg`, `eau_condensee_cumul_kg`, avertissement « condensation d'eau dans le réservoir ») et s'y réévapore si l'air se réchauffe ; l'air qui sort emporte la vapeur, pas l'eau du fond. L'air présent au départ porte au plus la saturation à son (T, p) et au plus ce que la chaîne de charge refoule (`plafonner_eau`) : cette eau initiale n'est pas comptée comme condensation.
- Fuite lente (phase 11, F12) : `fuite_par_jour` (fraction de la masse par jour, 0 par défaut) s'applique pendant l'attente ; l'air perdu est compté dans `masse_fuite_kg`. Avertissement si hors de [0, 1[.
- Pas encore : caverne avec échange rocheux (Tola, Wang), stockage isobare.

## Sources

Dormoy et al. 2024 (§ 2.2.5, éq. 11 à 14 et 21 ; tableau 8 des données supplémentaires) ; Shi 2024 (tableau 4, `shi.reservoir.*`, `shi.perte_charge_entree_reservoir`) ; fiches F11, F12, F38.
