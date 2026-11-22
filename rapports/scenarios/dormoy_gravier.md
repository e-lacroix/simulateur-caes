# Scénario d'exemple : le banc de Dormoy avec cuves de gravier

*Généré par `rapports/scenarios_dormoy_gravier.py` à partir de `scenarios/A.yaml` à `E.yaml` et `D_hiver.yaml` (format « composants », phase 6). Chaque ligne est le dernier cycle d'une simulation « charge → attente d'une heure → décharge » répétée jusqu'au régime stable (1 % sur l'électricité livrée et la chaleur des cuves).*

**Question.** Dormoy mesure 4,3 % de rendement sans réchauffage et simule 16,8 % en supposant 130 / 90 / 90 °C à l'entrée des turbines sans dire d'où vient la chaleur. Si cette chaleur vient de la compression, stockée dans du gravier (Tola), que reste-t-il du 16,8 % ? Et par −20 °C ?

## Résultats

| Cas | Architecture | Cycles | Électricité consommée (kWh) | Électricité livrée (kWh) | Chaleur rendue à l'air par les cuves (kWh) | Chaleur externe (kWh) | Rendement sans chaleur externe | Rendement avec chaleur externe | Chaleur restante dans les cuves (kWh) | Air rejeté min (°C) | Givre total (kg) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A** | 1 étage, sans réchauffage (cas de base de Dormoy) | 2 | 324.5 | 14.05 | 0.0 | 0.0 | 4.3 % | 4.3 % | 0.0 | -74 | 0.000 |
| **B** | 3 étages réchauffés par une source externe comptée | 3 | 243.2 | 40.96 | 0.0 | 51.2 | 16.8 % | 13.9 % | 0.0 | 15 | 0.000 |
| **C** | 3 étages, réserve d'huile idéale (hypothèse comptable de Dormoy) | 3 | 243.2 | 40.96 | 51.2 | 0.0 | 16.8 % | 16.8 % | 0.0 | 15 | 0.000 |
| **D** | 3 étages, cuves de gravier traversées par l'air comprimé (cas C de Tola) | 4 | 239.5 | 41.05 | 51.4 | 0.0 | 17.1 % | 17.1 % | 48.1 | 15 | 0.000 |
| **E** | 3 étages, cuves de gravier et boucle d'air à pression atmosphérique | 4 | 239.4 | 41.01 | 51.2 | 0.0 | 17.1 % | 17.1 % | 36.6 | 2 | 0.000 |
| **D hiver** | D par −20 °C, air aspiré à la température extérieure | 4 | 231.9 | 45.32 | 61.3 | 0.0 | 19.5 % | 19.5 % | 16.6 | -38 | 0.000 |

Lecture : le rendement « sans chaleur externe » ne compte que l'électricité ; le rendement « avec chaleur externe » met au dénominateur l'électricité de la charge plus la chaleur achetée (B). Pour A, C, D et E les deux sont égaux (aucune chaleur achetée) ; pour C, la chaleur vient d'une réserve parfaite jamais vide, ce qui est une hypothèse comptable, pas une installation. Le détail de chaque cas (bilans, tableau 1000 unités, séries) s'obtient avec `python -m caes simuler scenarios/D.yaml`.

Avertissements à retenir : **A** : 1 (par exemple « [turbine] étage 1 : givre : de l'eau se dépose en glace (air sous 0 °C et sous son point d ») ; **D** : 4 (par exemple « [cuve_1] en charge, condensation d'eau (air refroidi sous son point de rosée) ») ; **E** : 4 (par exemple « [cuve_1] cuve trop froide pour atteindre la cible de 90 °C (pas d'appoint ; minimum suivi  ») ; **D hiver** : 13 (par exemple « [refroidisseur_1] givre : de l'eau se dépose en glace (air sous 0 °C et sous son point de  »).

![rendements](dormoy_gravier_rendements.png)

*6 simulations, 83 s.*
