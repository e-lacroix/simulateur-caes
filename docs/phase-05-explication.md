# Phase 5 : brancher les cuves de gravier sur le banc de Dormoy

*Explication pour un élève de 16 ans. Phase 5 du simulateur, novembre 2026. Les formules citées (F30, F31) sont détaillées dans `formules.md`.*

## La question

Jusqu'ici, la turbine à 3 étages de Dormoy obtenait sa chaleur d'une source « externe » dont on ne savait rien. Les phases 1 et 3 ont montré que les refroidisseurs du compresseur jettent bien plus de chaleur qu'il n'en faut (191 kWh rejetés, 51 nécessaires). La question de la phase 5 : **si on met cette chaleur dans des cuves de gravier pendant la charge, les turbines reçoivent-elles vraiment l'air à 130 °C pendant la décharge, et combien de gravier faut-il ?**

## Les cinq architectures comparées

On a simulé cinq versions du même banc, dans les mêmes conditions, chacune pendant plusieurs cycles (charge de 6 h, attente de 1 h, décharge de 40 min) jusqu'à ce qu'elle se répète à l'identique :

| | Ce qui réchauffe l'air avant les turbines |
|---|---|
| A | Rien : un seul étage, l'air sort à −60 °C (le cas de base de Dormoy) |
| B | Une source externe qui fournit toujours 130/90/90 °C (l'hypothèse de Dormoy) |
| C | De l'huile « idéale » : toute la chaleur des refroidisseurs au-dessus de 130 °C est gardée sans aucune perte |
| D | Trois cuves de gravier sous pression, traversées directement par l'air comprimé (comme le cas C de Tola) |
| E | Trois cuves de gravier à pression atmosphérique, reliées par une boucle d'air et deux échangeurs qui perdent 20 °C chacun (comme le cas A de Tola) |

Dans D, chaque cuve est placée après un étage de compression : la cuve 1 voit de l'air à 3 bar et 168 °C, la cuve 2 à 12 bar et 178 °C, la cuve 3 à 55 bar et 188 °C. Pendant la décharge, l'air qui sort du détendeur à 40 bar et −10 °C traverse la cuve 3 (la plus chaude) avant la turbine 1, puis la cuve 2 avant la turbine 2, puis la cuve 1 avant la turbine 3. Les pressions s'emboîtent : c'est ce que la fiche Dormoy avait deviné, et le simulateur le confirme.

## Le résultat qui compte

| | Électricité produite par cycle | Rendement | Ce qu'il a fallu |
|---|---|---|---|
| A | 14,1 kWh | 4,3 % | rien |
| B | 41,0 kWh | 16,8 % (13,9 % si on compte la chaleur) | 51 kWh de chaleur externe |
| C | 41,0 kWh | 16,8 % | un stockage d'huile parfait |
| D | 41,1 kWh | 17,1 % | 1,25 m³ de gravier (2,4 t) dans trois cuves sous pression |
| E | 41,0 kWh | 17,1 % | 1,25 m³ de gravier dans trois cuves à 1 bar, plus deux échangeurs |

Le gravier fait exactement le travail de la source externe de Dormoy : **les turbines reçoivent l'air à 130, 90 et 90 °C**, et la chaleur vient entièrement des cuves (étiquettes `cuve_3`, `cuve_2`, `cuve_1` dans le simulateur, aucune chaleur « externe »). Le rendement de 16 % de Dormoy devient honnête : 17 % avec la chaleur comptée, parce qu'elle ne coûte rien.

Un détail amusant : D et E consomment un peu moins d'électricité que B à la charge (239 kWh au lieu de 243). Pourquoi ? Quand une cuve absorbe la chaleur de l'air avant le refroidisseur, celui-ci reçoit de l'air moins chaud et le rend un peu plus froid, donc l'étage suivant comprime de l'air plus froid, ce qui coûte moins.

## Pourquoi E vaut D malgré ses échangeurs

La fiche prévoyait une pénalité pour E (130 à 150 unités contre 150 à 155 pour D), à cause des 40 °C perdus dans les deux échangeurs. Le simulateur ne la trouve pas. La raison : l'air sort des compresseurs à 168–188 °C, mais la turbine n'a besoin que de 130 °C. Même après deux fois 20 °C de perte, il reste 128 à 148 °C disponibles. La marge de température de Dormoy absorbe la pénalité. Seule la cuve 1 d'E (chargée à 148 °C) est juste pour alimenter la turbine 3 à 90 °C : au volume de base, elle descend à 74 °C en fin de décharge (contre 90 pour D). Avec un peu plus de gravier, l'écart disparaît.

Chez Tola, la pénalité existe (56,6 % contre 67,4 %) parce que son compresseur ne sort qu'à 170 °C pour des turbines qui en voudraient 170 : il n'a aucune marge.

## Combien de gravier ?

On a fait varier le volume des cuves (F30 explique comment la cuve est branchée) :

| Volume total de gravier | Électricité par cycle (D) | Température minimale à l'entrée des turbines |
|---|---|---|
| 0,31 m³ | 34,9 kWh | −4 / −46 / −65 °C : les cuves sont vides avant la fin |
| 0,62 m³ | 40,3 kWh | 99 / 62 / 28 °C : la fin de décharge souffre |
| 1,25 m³ | 41,1 kWh | 130 / 90 / 90 °C : les cuves suffisent |
| 2,5 m³ | 41,1 kWh | 130 / 90 / 90 °C : rien de plus |
| 5 m³ | 41,1 kWh | 130 / 90 / 90 °C : rien de plus |

C'est le genre de courbe qu'on cherche en ingénierie : elle monte, puis elle s'aplatit. Le « coude », vers 1,25 m³, est le volume à retenir. En dessous, l'effet de fin de décharge décrit par Tola apparaît (l'air sort de moins en moins chaud des cuves et la turbine produit moins). Au-dessus, le gravier supplémentaire ne fait qu'accumuler une chaleur qu'on n'utilise jamais (137 kWh « restants » avec 2,5 m³).

Le calcul du volume de base se fait à la main (F25) : chaleur nécessaire par turbine (24,8 / 6,4 / 15,0 kWh), divisée par la capacité du gravier (0,48 kWh par m³ et par degré), par l'écart de température disponible (environ 150 K) et par un taux d'utilisation de 60 % (le front thermique n'exploite pas toute la cuve) : 0,7 / 0,2 / 0,35 m³. Le simulateur confirme que ça suffit.

## Les trois vérifications demandées par le plan

1. **Les pressions des cuves correspondent-elles à celles des turbines ?** Oui : cuves à 3,3 / 12,3 / 55 bar en charge, turbines à 3 / 11 / 40 bar. Chaque cuve est traversée à une pression un peu différente en décharge, ce qui ne change que la densité de l'air.
2. **La cuve 1 suffit-elle pour la turbine 3 ?** Oui au volume de base pour D (90 °C garantis) ; presque pour E (74 °C au minimum en fin de décharge).
3. **La perte de charge dans le gravier coûte-t-elle de l'énergie au compresseur ?** Non : 29 / 13 / 1 Pa, soit 0,007 kWh de pompage sur une charge de 239 kWh.

## Ce qui reste dans les cuves

Au cycle stable, la cuve de D contient encore 48 kWh de chaleur après la décharge, presque autant que les 51 kWh prélevés. Cette chaleur n'est pas perdue : elle sera là au cycle suivant. Mais elle montre que la cuve « travaille » avec une réserve permanente. C'est cette réserve que la phase 6 verra fondre pendant un transport de plusieurs semaines.

## Dans le tableau « 1000 unités »

Sur 1000 unités d'électricité, D en rend 171. Le gravier stocke 58 unités d'exergie en charge et en restitue 52 en décharge ; l'échange air-gravier en détruit 3 en charge et 27 en décharge (la chaleur passe d'un gravier à 180 °C à de l'air qui n'a besoin que de 130 °C). Le gros des pertes n'a pas bougé : moteur et mécanique (326), air non refoulé et sécheur (171), détendeur (71 avec 3 étages, contre 234 avec un seul).

## À retenir

1. Des cuves de gravier de 1,25 m³ au total suffisent pour que la turbine à 3 étages de Dormoy reçoive l'air à sa température nominale : le 16 % devient un vrai 17 %, sans chaleur extérieure.
2. Sous le volume du coude, la fin de décharge souffre ; au-dessus, le gravier ne sert à rien.
3. La boucle d'air (E) ne coûte presque rien ici, parce que le compresseur de Dormoy sort 40 à 60 °C plus chaud que ce dont la turbine a besoin.
4. Les grosses pertes restent celles de la compression : le gravier règle le problème de la chaleur, pas celui du moteur, du sécheur ni du détendeur.
