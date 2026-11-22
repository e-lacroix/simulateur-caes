# Phase 9 : l'eau dans l'air, le givre dans la turbine

*Explication pour un élève de 16 ans. Phase 9 du simulateur, novembre 2026. Les formules citées (F42, F43) sont détaillées dans `formules.md` ; les chiffres viennent de `rapports/phase9/humidite.md`, régénéré par `python rapports/phase9_humidite.py`.*

## La question

Le banc de Dormoy jette 19 % de l'air qu'il a comprimé pour faire tourner son sécheur. C'est le poste le plus cher de toute la charge après les compresseurs eux-mêmes : sans sécheur, la charge coûterait 310 kWh au lieu de 386. Alors pourquoi le garder ? Parce que l'air contient de l'eau, et que l'eau, dans une installation d'air comprimé, fait deux choses désagréables : elle s'accumule au fond des réservoirs (rouille, bouchons) et elle gèle dans les turbines. La phase 9 suit chaque gramme d'eau de l'aspiration au rejet pour répondre à une question simple : **peut-on se passer du sécheur, et à quelles conditions ?**

## L'air est une éponge qui rétrécit quand on la presse

L'air de ta chambre, à 20 °C et 50 % d'humidité, porte environ 7 g d'eau par kilo d'air, sous forme de vapeur invisible. Il pourrait en porter le double (15 g) : à ce moment-là il est « saturé », l'humidité est à 100 %, et la moindre goutte en plus se dépose en buée. Cette capacité maximale a deux propriétés qui font toute la phase :

1. **Elle monte très vite avec la température.** À 45 °C, un kilo d'air à 1 bar porte jusqu'à 65 g d'eau ; à −20 °C, moins de 1 g.
2. **Elle baisse quand on comprime.** À 190 bar et 45 °C, le même kilo d'air ne garde que 0,4 g. Comprimer, c'est essorer l'éponge.

C'est pour ça que les refroidisseurs des compresseurs coulent : l'air qui sort du dernier étage à 190 bar et 45 °C a dû abandonner presque toute son eau en route. Mais « presque » n'est pas « tout ». Il en reste 0,4 g par kilo, et cet air est **saturé** : il est à 100 % d'humidité, à sa température et sa pression. La température où un air devient saturé s'appelle son **point de rosée** ; pour l'air qui entre dans le réservoir de Dormoy, c'est 45 °C **sous 190 bar**. Le simulateur calcule tout ça avec les tables de l'air humide réel (CoolProp, formulation ASHRAE RP-1485), parce qu'à haute pression l'air dissout un peu plus d'eau que ne le dit la loi des gaz parfaits (facteur d'augmentation, 1,5 à 100 bar).

## Deux endroits où ça fait mal

**Le réservoir qui refroidit.** L'air entre saturé à 45 °C. La nuit, ou pendant l'attente, le réservoir redescend à la température extérieure. Comme l'éponge rétrécit avec le froid, l'eau en trop se dépose au fond : environ 0,6 kg par cycle à 20 °C d'ambiance, 1 kg à 30 °C, 0,2 kg à 0 °C, 0,04 kg à −20 °C. Ce n'est pas énorme, mais c'est à chaque cycle, dans des bouteilles en aluminium et en carbone.

**La turbine qui gèle.** À la décharge, l'air se détend et se refroidit. Dans l'architecture A (sans réchauffage), il sort de la turbine à −74 °C. Même l'air « sec » du réservoir (0,4 g/kg) ne peut pas porter cette eau à −74 °C : elle se dépose en **givre** sur les aubes, 0,1 kg par décharge à 20 °C, 0,19 kg à 30 °C. Du givre sur les aubes d'une turbine qui tourne très vite, c'est un déséquilibre, puis une casse. Dans l'architecture B (réchauffée à 130/90/90 °C), les turbines sortent à 15 °C et plus : aucun givre. Mais le détendeur, lui, n'est pas réchauffé : il sort l'air vers −5 °C et givre un peu en hiver (5 à 12 g par décharge entre −20 et 0 °C).

## Trois façons de traiter l'eau

| Traitement | Air purgé | Ce qu'il enlève | RTE de B | RTE de A | Eau au fond du réservoir | Givre |
|---|---|---|---|---|---|---|
| Sécheur par adsorption de Dormoy (point de rosée −40 °C) | 19 % | la vapeur et les gouttes | 16,8 % | 4,3 % | 0 | 0 (A : 0,2 g à 20 °C, 2 g à −20 °C) |
| Séparateurs après chaque refroidisseur | 0 % | les gouttes seulement | 20,7 % | 5,4 % | 0,6 à 0,9 kg par cycle | B : 8 g au détendeur ; A : 0,1 kg aux turbines |
| Séparateurs + petit sécheur d'appoint (point de rosée −40 °C) | 5 % | les gouttes puis la vapeur | 19,7 % | 5,1 % | 0 | 0 |

Le séparateur, c'est un piège à gouttes : il retire ce qui est déjà liquide. Il ne touche pas à la vapeur, et c'est la vapeur qui condense plus tard dans le réservoir froid. Le sécheur par adsorption, lui, retire la vapeur jusqu'à un point de rosée de −40 °C sous pression : l'air stocké ne peut plus condenser nulle part, sauf à −74 °C dans la turbine de A, où il reste 0,2 g de givre par décharge (2 g à −20 °C d'ambiance). Ce qui protège l'installation, ce n'est pas la quantité d'air qu'on jette, c'est le **point de rosée** qu'on atteint. Un sécheur qui atteint −40 °C en jetant 5 % d'air au lieu de 19 % ferait exactement le même travail sur l'eau et ferait passer le rendement de B de 16,8 à 19,7 %. Ces 5 % sont une hypothèse : la purge réelle dépend de la technologie du sécheur (régénération à chaud ou par détente), et il faudra une fiche de fabricant pour la remplacer.

## Pourquoi l'humidité dehors ne change rien, et pourquoi l'hiver change tout

On a fait tourner les séparateurs seuls à 30, 60 et 90 % d'humidité, à −20, 0, 20 et 30 °C. Surprise : **les trois colonnes d'humidité sont identiques**. Quelle que soit l'humidité aspirée, l'air sort saturé du dernier refroidisseur ; ce qui arrive ensuite ne dépend que de la température de ce refroidisseur. Le surplus d'eau d'une journée humide est simplement condensé plus tôt, dans les premiers refroidisseurs.

L'hiver, par contre, change tout, dans deux sens opposés. Le refroidisseur sort l'air plus froid, donc beaucoup plus sec sous pression : à −20 °C, le réservoir reçoit 25 fois moins d'eau qu'à 30 °C. Mais le détendeur, qui sortait l'air à −5 °C l'été, descend plus bas et givre. En A, c'est le contraire : plus il fait chaud dehors, plus le réservoir contient d'eau, plus la turbine givre.

## Le verdict

Le sécheur **ne peut pas être évité** avec des séparateurs seuls, dans aucun des douze climats testés, pour aucune des deux architectures : l'air quitte toujours le dernier refroidisseur saturé, et le réservoir finit toujours plus froid que ce refroidisseur. Mais il **peut être petit** : la condition précise est que le point de rosée sous pression de l'air stocké soit plus bas que la température la plus froide rencontrée ensuite, c'est-à-dire l'ambiance en hiver pour le réservoir, −5 °C environ pour le détendeur de B, et −74 °C pour la turbine de A, où aucun sécheur ordinaire ne descend : là, seul le réchauffage protège.

## Ce que le simulateur ne sait pas encore

- Le bilan d'énergie est fait sur l'air sec ; l'eau est suivie en masse et sa chaleur de condensation est donnée à part (elle vaut 2,4 MJ par kilo, soit 4 kWh pour les 6 kg condensés d'une charge : une partie de la chaleur des refroidisseurs vient de là).
- L'équilibre est supposé instantané. Dans une vraie turbine, le givre met du temps à se déposer, et l'eau peut rester liquide sous 0 °C (surfusion) ; le simulateur donne la quantité d'eau qui *doit* finir en glace, pas la vitesse à laquelle elle bouche la machine.
- Au-delà de 100 bar, les tables de l'air humide sont extrapolées (à pression partielle de vapeur constante) ; c'est signalé dans chaque résumé.
- Les séparateurs à 98 %, le point de rosée de −40 °C et la purge de 5 % sont des hypothèses, pas des mesures de Dormoy.

## À retenir

1. Comprimer l'air l'essore, mais l'air qui entre dans le réservoir est saturé à la température du dernier refroidisseur : tout refroidissement ultérieur fait de l'eau liquide, tout passage sous 0 °C fait du givre.
2. Le séparateur enlève les gouttes, pas la vapeur ; seul un sécheur abaisse le point de rosée. L'humidité dehors ne change pas le résultat ; la température dehors, oui.
3. Le sécheur est nécessaire partout, mais ce qui compte est son point de rosée, pas l'air qu'il jette : à point de rosée égal, un sécheur à 5 % de purge ferait gagner 3 points de rendement à B.
