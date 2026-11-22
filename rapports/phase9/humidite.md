# Phase 9 : humidité, sécheur et séparateur sur le banc de Dormoy

*Généré par `rapports/phase9_humidite.py`. L'eau est suivie de l'aspiration au rejet (formules F42 et F43) : condensation dans les refroidisseurs, séparateurs, sécheur, condensation dans le réservoir, givre aux sorties du détendeur et des turbines. Les hypothèses (point de rosée de −40 °C du sécheur, séparateurs à 98 %, appoint à 5 % de purge) sont au registre avec le niveau « hypothèse ».*

## 1. Trois façons de traiter l'eau, à 20 °C et 50 % d'humidité (ambiance de Dormoy, hypothèse)

| Scénario | Électricité charge (kWh) | Produit (kWh) | RTE | Eau aspirée (kg/charge) | Condensée dans les refroidisseurs | Séparée ou purgée | Vers le réservoir | Condensée dans le réservoir | T de rosée du réservoir (°C) | Givre détendeur / turbines (kg) | Air rejeté min (°C) | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `A_secheur_adsorption.yaml` | 324.5 | 14.05 | 4.3 % | 11.3 | 22.6 | 9.4 | 0.00 | 0.000 | -34 | 0.000 / 0.000 | -74 | eau maîtrisée |
| `A_separateur.yaml` | 259.8 | 13.99 | 5.4 % | 9.0 | 8.4 | 8.2 | 0.65 | 1.159 | 45 | 0.000 / 0.104 | -73 | eau non maîtrisée (condensation dans le réservoir, givre) |
| `A_separateur_appoint.yaml` | 274.3 | 14.01 | 5.1 % | 9.5 | 8.9 | 9.4 | 0.00 | 0.000 | -34 | 0.000 / 0.000 | -73 | eau maîtrisée |
| `B_secheur_adsorption.yaml` | 243.9 | 40.87 | 16.8 % | 8.3 | 17.0 | 6.9 | 0.00 | 0.000 | -35 | 0.000 / 0.000 / 0.000 / 0.000 | 15 | eau maîtrisée |
| `B_separateur.yaml` | 196.1 | 40.53 | 20.7 % | 6.6 | 6.2 | 6.1 | 0.47 | 0.872 | 43 | 0.008 / 0.000 / 0.000 / 0.000 | 15 | eau non maîtrisée (condensation dans le réservoir, givre) |
| `B_separateur_appoint.yaml` | 206.6 | 40.61 | 19.7 % | 7.0 | 6.5 | 6.9 | 0.00 | 0.000 | -35 | 0.000 / 0.000 / 0.000 / 0.000 | 15 | eau maîtrisée |

Lecture : le sécheur purge 19 % de l'air ; les séparateurs ne coûtent rien en air mais laissent l'air saturé à la température du dernier refroidisseur, sous la pression du réservoir. L'énergie et le rendement ne dépendent que de la purge (le bilan d'énergie est fait sur l'air sec ; la chaleur de condensation est donnée à part). Sans séparateur, les gouttes d'un refroidisseur repartent avec l'air et s'évaporent dans l'étage suivant : la somme de ce que condensent les refroidisseurs dépasse alors l'eau aspirée, et seul le sécheur, au bout de la chaîne, la retire. L'air déjà présent dans le réservoir au départ est supposé aussi sec que ce que la chaîne refoule (F43).

## 2. Balayage du climat : séparateurs seulement

Humidité relative 30, 60 et 90 % × température ambiante −20, 0, 20 et 30 °C (air aspiré 32 K plus chaud, comme le conteneur de Dormoy), un cycle. Chaque case : condensation dans le réservoir (kg) / givre total au détendeur et aux turbines (kg) / verdict. L'humidité aspirée ne change rien aux colonnes : quelle qu'elle soit, l'air quitte le dernier refroidisseur saturé ; seule compte la température de ce refroidisseur face aux températures les plus froides que l'air rencontre ensuite (réservoir, détendeur, turbines).

### A : 1 étage sans réchauffage

| T ambiante | φ = 30 % | φ = 60 % | φ = 90 % |
|---|---|---|---|
| -20 °C | 0.054 / 0.008 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.054 / 0.008 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.054 / 0.008 / eau non maîtrisée (condensation dans le réservoir, givre) |
| +0 °C | 0.205 / 0.034 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.205 / 0.034 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.205 / 0.034 / eau non maîtrisée (condensation dans le réservoir, givre) |
| +20 °C | 0.612 / 0.115 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.612 / 0.115 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.612 / 0.115 / eau non maîtrisée (condensation dans le réservoir, givre) |
| +30 °C | 0.992 / 0.194 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.992 / 0.194 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.992 / 0.194 / eau non maîtrisée (condensation dans le réservoir, givre) |

### B : 3 étages réchauffés à 130/90/90 °C

| T ambiante | φ = 30 % | φ = 60 % | φ = 90 % |
|---|---|---|---|
| -20 °C | 0.042 / 0.005 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.042 / 0.005 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.042 / 0.005 / eau non maîtrisée (condensation dans le réservoir, givre) |
| +0 °C | 0.162 / 0.012 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.162 / 0.012 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.162 / 0.012 / eau non maîtrisée (condensation dans le réservoir, givre) |
| +20 °C | 0.485 / 0.006 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.485 / 0.006 / eau non maîtrisée (condensation dans le réservoir, givre) | 0.485 / 0.006 / eau non maîtrisée (condensation dans le réservoir, givre) |
| +30 °C | 0.793 / 0.000 / eau non maîtrisée (condensation dans le réservoir) | 0.793 / 0.000 / eau non maîtrisée (condensation dans le réservoir) | 0.793 / 0.000 / eau non maîtrisée (condensation dans le réservoir) |

### Référence : sécheur de Dormoy et sécheur d'appoint (90 % d'humidité, un cycle)

| Architecture | Traitement | T ambiante | Eau vers le réservoir (kg) | Condensée dans le réservoir | Givre | Verdict |
|---|---|---|---|---|---|---|
| A | sécheur de Dormoy (19 %) | -20 °C | 0.002 | 0.000 | 0.002 | eau non maîtrisée (givre) |
| A | sécheur de Dormoy (19 %) | +30 °C | 0.001 | 0.000 | 0.000 | eau maîtrisée |
| A | séparateurs + appoint (5 %) | -20 °C | 0.002 | 0.000 | 0.002 | eau non maîtrisée (givre) |
| A | séparateurs + appoint (5 %) | +30 °C | 0.001 | 0.000 | 0.000 | eau maîtrisée |
| B | sécheur de Dormoy (19 %) | -20 °C | 0.001 | 0.000 | 0.000 | eau maîtrisée |
| B | sécheur de Dormoy (19 %) | +30 °C | 0.001 | 0.000 | 0.000 | eau maîtrisée |
| B | séparateurs + appoint (5 %) | -20 °C | 0.001 | 0.000 | 0.000 | eau maîtrisée |
| B | séparateurs + appoint (5 %) | +30 °C | 0.001 | 0.000 | 0.000 | eau maîtrisée |

![givre](fig_givre.png)

## 3. Verdict

**Le sécheur ne peut pas être évité, mais il peut être petit.**

- **Séparateurs seuls : jamais suffisants.** Les gouttes sont drainées, mais l'air quitte le dernier refroidisseur *saturé* à sa température de sortie (≈ 45 °C à 20 °C d'ambiance). Dès que le réservoir refroidit en dessous (attente, détente), l'eau condense au fond : 0,04 kg par cycle à −20 °C, 0,2 kg à 0 °C, 0,5 à 0,6 kg à 20 °C, 0,8 à 1,0 kg à 30 °C, pour les deux architectures et quelle que soit l'humidité aspirée. La condition pour s'en passer serait un dernier refroidisseur plus froid que tout ce que le réservoir rencontre ensuite ; avec un refroidisseur à l'air ambiant, elle n'est jamais remplie, été comme hiver.
- **L'hiver assèche le réservoir mais givre le détendeur.** À −20 °C, le refroidisseur sort l'air plus froid, donc plus sec sous pression (25 fois moins d'eau au réservoir qu'à 30 °C) ; en revanche le détendeur de B, qui sort l'air vers −5 °C à 20 °C d'ambiance, givre (5 à 12 g par décharge entre −20 et 0 °C, rien à 30 °C). En A, c'est l'inverse : l'air rejeté à −74 °C givre d'autant plus que le réservoir est humide (8 g à −20 °C, 190 g à 30 °C).
- **Sécheur à −40 °C de point de rosée sous pression** (Dormoy, 19 % d'air purgé) : aucune condensation dans le réservoir ni givre en B, dans les douze climats ; en A, où l'air sort de la turbine sous −74 °C, l'eau résiduelle du point de rosée de −40 °C laisse 0,2 g de givre par décharge à 20 °C et 2 g à −20 °C (le verdict compte tout givre au-dessus de 1 g). Le même point de rosée avec 5 % de purge (séparateurs + appoint) donne le même résultat sur l'eau et rend 19,7 % au lieu de 16,8 % en B (RTE), 5,1 % au lieu de 4,3 % en A : ce qui protège l'installation est le **point de rosée**, pas la quantité d'air purgée. La fraction de purge d'un sécheur réel dépend de sa technologie (régénération à chaud ou par détente) : les 5 % sont une hypothèse à remplacer par une fiche de fabricant.
- **Règle pour un chercheur** : le point de rosée sous pression de l'air stocké doit être inférieur à la température la plus froide que l'air atteint ensuite : le réservoir en hiver (ambiance), la sortie du détendeur (B : vers −5 °C), la sortie de la turbine sans réchauffage (A : −74 °C, hors de portée d'un sécheur ordinaire : seul le réchauffage protège A). Un sécheur frigorifique (air refroidi à +3 °C avant le réservoir) n'est pas modélisé ; il couvrirait l'été mais pas l'hiver québécois.
- Limites : bilan d'énergie sur l'air sec (l'eau est suivie en masse, sa chaleur latente est donnée à part) ; au-delà de 10 MPa la saturation est extrapolée (F42) ; équilibre instantané, la cinétique du givrage (dépôt sur les aubes) n'est pas modélisée ; séparateurs à 98 % et point de rosée de −40 °C sont des hypothèses, pas des mesures de Dormoy.


*Durée : 67 s.*
