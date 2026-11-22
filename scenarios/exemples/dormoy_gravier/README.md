# Scénario 1 : le banc de Dormoy avec cuves de gravier (cas de référence)

**La question.** Dormoy et al. (2024) mesurent 4,3 % de rendement aller-retour sur leur banc (compresseur 45 kW, 20 bouteilles composites, 190 bar, turbine DEPRAG, un étage sans réchauffage) et simulent 16,8 % avec trois étages réchauffés à 130 / 90 / 90 °C, sans dire d'où vient la chaleur. Si cette chaleur est celle de la compression, récupérée dans des cuves de gravier comme chez Tola (2022), que reste-t-il du 16,8 % ? Et que devient le résultat par −20 °C ?

**Les fichiers.** Les cinq architectures de la phase 5, dans le format « composants » de la phase 6 :

| Fichier | Architecture |
|---|---|
| `scenarios/A.yaml` | 1 étage, sans réchauffage : le cas de base mesuré |
| `scenarios/B.yaml` | 3 étages réchauffés par une source externe (chaudière) **comptée** |
| `scenarios/C.yaml` | 3 étages, réserve d'huile idéale (hypothèse comptable de Dormoy) |
| `scenarios/D.yaml` | 3 étages, cuves de gravier traversées par l'air comprimé (cas C de Tola) |
| `scenarios/E.yaml` | 3 étages, cuves de gravier et boucle d'air à pression atmosphérique |
| `scenarios/D_hiver.yaml` | D par −20 °C, air aspiré à la température extérieure |

Tout vient du registre (`registre:<id>`) ou porte sa source ; les volumes des cuves (0,35 / 0,2 / 0,7 m³) sont un calcul personnel décrit dans `D.yaml`. L'ambiance (20 °C, 50 %, air aspiré à 52 °C dans le conteneur) est l'hypothèse de la phase 1 ; `D_hiver` ne change que la température.

**Régénérer.**

```
python rapports/scenarios_dormoy_gravier.py        # → rapports/scenarios/dormoy_gravier.md (≈ 3 min)
python -m caes simuler scenarios/D.yaml            # un cas, en détail (resume.md, séries, 1000 unités)
```

**Comment lire la réponse.** Deux rendements sont toujours donnés : sans chaleur externe (électricité seule) et avec (la chaleur achetée au dénominateur). Les cas avec gravier (D, E) se stabilisent après quelques cycles parce que les cuves gardent de la chaleur d'un cycle à l'autre ; le rapport donne le dernier cycle. Les avertissements (cuve trop froide pour la cible, givre, Reynolds hors de Wakao) font partie de la réponse. La validation de ces modèles est dans `rapports/validation/tableau_de_bord.md` (phase 8) : la charge et la décharge mesurées de Dormoy sont reproduites à 2,5 % ; le gravier est vérifié contre Schumann et croisé avec Tola, pas encore validé sur une mesure.
