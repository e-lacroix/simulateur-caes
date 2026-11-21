# Phase 2 : la décharge, ou comment l'air comprimé redevient de l'électricité

*Explication pour un élève de 16 ans. Phase 2 du simulateur, novembre 2026. Les formules citées (F15 à F20) sont détaillées dans `formules.md`.*

## Ce que fait le module

Le module de décharge imite ce qui se passe quand on ouvre les réservoirs : l'air à 190 bar traverse un **détendeur** qui ramène sa pression à une valeur fixe (35 bar dans l'essai de Dormoy, 40 bar pour la turbine à 3 étages, 3 bar pour la turbine à 1 étage), puis une ou plusieurs **turbines** où il se détend jusqu'à 1 bar en faisant tourner une génératrice. Entre deux étages, on peut **réchauffer** l'air.

Le simulateur suit, seconde par seconde, la pression et la température dans les réservoirs, la température après le détendeur, la chaleur ajoutée et l'électricité produite, jusqu'à ce que le détendeur n'ait plus assez de pression pour fonctionner (il lui faut 15 bar de plus que sa consigne).

## Le détendeur : faire chuter la pression sans rien gagner

Un détendeur, c'est un robinet à moitié fermé. L'air passe de 190 bar à 35 bar, mais ce faisant **il ne pousse rien** : aucun travail n'est produit. On dit que la détente est *isenthalpique* (F15) : l'énergie que l'air transporte (son enthalpie) ne change pas.

Deux effets quand même :

1. **L'air se refroidit un peu.** Pour un gaz parfait, la température ne bougerait pas. L'air réel à haute pression, lui, perd environ 20 °C entre 190 et 35 bar : c'est l'effet Joule-Thomson, celui qui rend une bombe aérosol froide quand on appuie dessus. Dormoy a mesuré cette température de sortie et son modèle la retrouve à 0,4 % près. Le nôtre utilise le même modèle, et une deuxième formule (celle de Cheayb, F16) donne la même chose à 1 °C près.
2. **La pression perdue est perdue pour de bon.** De l'air à 190 bar peut produire beaucoup plus de travail que de l'air à 35 bar. Cette capacité, le détendeur la détruit. On la mesurera en phase 3 avec l'exergie.

Et il y a une troisième conséquence, sournoise : comme le détendeur a besoin de 15 bar d'écart, la décharge s'arrête quand le réservoir est encore à 50 bar (ou 18 bar avec la turbine à 1 étage). L'air qui reste, c'est la **masse morte** : de l'air comprimé qu'on a payé et qu'on ne peut pas utiliser. Il n'est pas perdu (il reste pour le cycle suivant), mais il occupe du volume.

## Pourquoi l'air se refroidit, et pourquoi on le réchauffe

Dans la turbine, l'air se détend en poussant les aubes : il fournit du travail, donc il perd de l'énergie, donc **il se refroidit** (F17). C'est la pompe à vélo à l'envers. Pour l'étage 3 de la turbine DEPRAG (3 bar → 1 bar), un air entré à 90 °C ressort à 16 °C. Entré à 20 °C sans réchauffage, il ressort vers **−40 °C** ; dans le cas de base du simulateur, on descend jusqu'à −63 °C. À ces températures, la moindre humidité givre et bloque la turbine. C'est pour ça que Dormoy sèche l'air et prévoit de le réchauffer.

Le réchauffage a un deuxième intérêt : **plus l'air est chaud, plus il pousse fort**. Le travail d'un étage est proportionnel à la température d'entrée (en kelvins). Réchauffer de 20 °C à 130 °C (de 293 à 403 K) fait gagner 37 % de travail.

**Exemple sur l'étage 1 (F17, F18).** Air à 130 °C = 403 K, détente de 40 à 11,5 bar, n = 1,19. Exposant (n − 1)/n = 0,16. (11,5/40)^0,16 = 0,82, donc T_sortie = 403 × 0,82 = 330 K = 57 °C (DEPRAG annonce 59 °C). Travail de détente : w = (1,19/0,19) × 287 × (403 − 330) = 131 kJ/kg. Rendement mécanique 53 % (frottements), rendement de la génératrice 90 % : 131 × 0,53 × 0,90 = 62 kJ électriques par kilogramme. Avec 0,321 kg/s, ça fait 20 kW. DEPRAG annonce 20,0 kW : le modèle reproduit la fiche technique.

## Pourquoi 3 étages valent mieux qu'un

Avec un seul étage de 3 bar à 1 bar, on laisse tomber l'air de 190 à 3 bar dans le détendeur : presque toute la pression est gaspillée. Avec trois étages (40 → 11,5 → 3,5 → 1 bar), le détendeur ne descend que de 190 à 40 bar, et les trois turbines exploitent le reste. Bonus : entre les étages, on réchauffe l'air, ce qui évite le givre et augmente le travail.

Résultats du simulateur :

| | 1 étage, sans réchauffage | 3 étages, réchauffés |
|---|---|---|
| Électricité produite | 14,3 kWh | 39,0 kWh |
| Chaleur à fournir | 0 | 44,6 kWh |
| Air qui reste (masse morte) | 138 kg (18 bar) | 407 kg (55 bar) |
| Recharge nécessaire | de 18 à 190 bar : 352 kWh | de 55 à 190 bar : 276 kWh |
| Rendement sans compter la chaleur | 4,1 % | 14,1 % |
| Rendement en comptant la chaleur | 4,1 % | 12,2 % |

Trois étages produisent presque trois fois plus d'électricité, et en plus la recharge coûte moins cher, parce que le coussin d'air à 55 bar reste dans les réservoirs d'un cycle à l'autre.

## Les deux rendements (F20)

Dormoy annonce 16 % pour les 3 étages. Mais il ne compte pas la chaleur de réchauffage (44,6 kWh, presque autant que l'électricité produite !). Si on la compte comme si c'était de l'électricité, le rendement tombe à 12 %. Qui a raison ? Ça dépend d'où vient la chaleur :

- si elle vient d'une chaudière ou d'une résistance électrique, il faut la compter : 12 % ;
- si elle vient de la chaleur de compression qu'on aurait jetée de toute façon (phase 1 : les refroidisseurs rejettent 191 kWh pendant la recharge), elle est gratuite : 14 à 16 %.

C'est pour trancher cette question que le simulateur **étiquette chaque joule de chaleur** avec sa source (F19). Pour l'instant, l'étiquette dit « externe ». Les phases 4 et 5 brancheront des cuves de gravier chauffées par le compresseur, et l'étiquette dira « cuve_3 ».

## Ce que la validation a donné

| Comparaison | Dormoy | Simulateur | Verdict |
|---|---|---|---|
| Essai mesuré : durée de 190 à 50 bar | 38 min | 37,3 min | reproduit (−2 %) |
| Turbine DEPRAG : températures et puissances par étage (tableau 9) | 59 / 21 / 16 °C ; 20,0 / 20,1 / 21,8 kW | à 2,5 °C et 3 % près | reproduit |
| Chaleur de réchauffage par étage (tableau 5) | 24,8 / 6,4 / 15,0 kWh | 24,4 / 6,0 / 14,1 kWh | reproduit (−4 %) |
| Cas de base, 1 étage | 16,93 kWh | 14,3 kWh | **écart de −15 %, non expliqué** |
| Tendances (température ambiante, pression, indice n, étages) | figures 11 à 16 | mêmes sens de variation | reproduit qualitativement |

## L'écart qu'on n'explique pas, et pourquoi on le dit

Le cas de base donne 14,3 kWh au lieu de 16,93. On a cherché : ce n'est pas la température de départ (un réservoir plus chaud donne la même énergie, parce qu'il contient moins d'air), ni le modèle de paroi. En supprimant *artificiellement* le refroidissement de l'air (dans le détendeur et dans le réservoir), on remonte à 15,8 kWh. Dormoy a pourtant ces deux effets dans son modèle. Il reste donc un détail de son calcul de turbine qu'on ne connaît pas.

On aurait pu « régler » un paramètre pour tomber sur 16,93. On ne l'a pas fait : un écart documenté vaut mieux qu'un chiffre arrangé. Et le reste du modèle est validé par des mesures indépendantes (l'essai de décharge, la fiche DEPRAG, le tableau 5), ce qui donne confiance dans sa physique.

## Une incohérence trouvée chez Dormoy

Sa turbine produit 62 kW et sa décharge dure 40 min : ça fait 41 kWh, soit 14 % de 290 kWh, pas 16 %. Pour obtenir 16 %, il faudrait 45 min de décharge. Notre 14,1 % se situe entre les deux. C'est le genre de détail qu'on ne voit qu'en refaisant les calculs, et c'est une bonne question pour le jury.

## À retenir

1. Le détendeur ne produit rien : il détruit de la pression utile, et il condamne la « masse morte » qui reste sous sa pression d'arrêt.
2. L'air qui se détend se refroidit ; sans réchauffage, il givre.
3. Trois étages réchauffés produisent trois fois plus qu'un seul, et la recharge coûte moins cher.
4. Un rendement n'a de sens que si on dit ce qu'on compte au dénominateur : avec ou sans la chaleur.
5. Un écart non expliqué se signale, il ne se cache pas.
