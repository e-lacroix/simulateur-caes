# Phase 3 : l'exergie, ou pourquoi « la chaleur à 20 °C ne fait rien tourner »

*Explication pour un élève de 16 ans. Phase 3 du simulateur, novembre 2026. Les formules citées (F21 à F24) sont détaillées dans `formules.md`.*

## Le problème avec l'énergie

En phase 1, on a vérifié que l'énergie se conserve : les 352 kWh d'électricité de la charge se retrouvent intégralement en chaleur dans les radiateurs, en chaleur dans les parois, dans l'air rejeté et dans l'air stocké. Le bilan ferme à 0,001 %. Et pourtant, on n'a récupéré que 14 kWh à la fin. Où sont passés les 338 autres ?

Ils sont encore là : dans l'air du conteneur, qui est un peu plus chaud. Le problème, c'est que de l'air à 25 °C dans un conteneur à 20 °C ne peut **plus rien faire**. L'énergie n'a pas disparu, elle s'est **dégradée**. Le premier principe (l'énergie se conserve) ne voit pas cette dégradation. Il faut le deuxième principe.

## L'exergie : la partie utile de l'énergie

L'**exergie** d'une chose, c'est le travail maximal qu'on pourrait en tirer en la ramenant à l'état de l'air ambiant (20 °C, 1 bar), qu'on appelle l'état mort (F21). Quelques exemples, par kilogramme d'air :

| État de l'air | Énergie (enthalpie, par rapport à l'ambiant) | Exergie |
|---|---|---|
| 190 bar, 20 °C | 0 | 440 kJ/kg |
| 1 bar, 130 °C | 111 kJ/kg | 17 kJ/kg |
| 1 bar, 45 °C | 25 kJ/kg | 1 kJ/kg |
| 1 bar, −60 °C | −80 kJ/kg | 12 kJ/kg (du froid, ça vaut quelque chose aussi) |

Deux leçons :

1. **L'air comprimé à température ambiante n'a aucune énergie en plus, mais énormément d'exergie.** C'est bien de la pression qu'on stocke, pas de la chaleur.
2. **La chaleur vaut d'autant moins qu'elle est tiède.** Le facteur de Carnot (F23) dit qu'une chaleur à la température T ne vaut que (1 − T₀/T) de sa valeur en travail : 27 % à 130 °C, 8 % à 45 °C, 0 % à 20 °C. « La chaleur à 20 °C ne fait rien tourner. »

Et surtout, contrairement à l'énergie, **l'exergie se détruit**. Chaque frottement, chaque robinet, chaque radiateur qui jette de la chaleur dehors en détruit une partie, définitivement. La formule est simple (F24) : exergie détruite = T₀ × entropie créée. Le simulateur calcule l'entropie qui entre et qui sort de chaque composant ; la différence, multipliée par 293 K, c'est la casse.

## Le tableau « 1000 unités »

On prend l'électricité consommée pendant la charge, on l'appelle 1000 unités, et on suit l'exergie, étape par étape, jusqu'à l'électricité rendue. Pour le cas de base de Dormoy (un seul étage de turbine, sans réchauffage), voici ce que le simulateur trouve :

| Étape | Exergie perdue | Il reste |
|---|---|---|
| Électricité du réseau | | 1000 |
| Moteur, frottements et air non refoulé par les pistons | 418 | 582 |
| Chaleur rejetée par les 4 refroidisseurs (689 unités de **chaleur**, mais tiède) | 156 | 426 |
| Air rejeté par le sécheur | 81 | 345 |
| Entrée dans les réservoirs (laminage, mélange, parois) | 14 | 331 |
| **Stocké dans les réservoirs** | | **329** (+ 16 de coussin déjà là) |
| Détendeur : 190 bar → 3 bar sans rien produire | **234** | 105 |
| Turbine et génératrice | 25 | 80 |
| Air rejeté à −60 °C (du froid perdu) | 19 | 62 |
| Coussin qui reste à 18 bar (pas une perte : il sert au cycle suivant) | 22 | 40 |
| **Électricité rendue** | | **40** |

Rendement : 4,0 %. Le graphique `rapports/phase3/cascade_base.png` montre la même chose en cascade.

## Ce que le tableau nous apprend

**1. La recharge coûte 670 unités avant même de stocker.** Le moteur et la mécanique en prennent 418 (avec le rendement mécanique de 69 à 74 % mesuré par Dormoy). Les refroidisseurs jettent 689 unités de chaleur, mais cette chaleur ne vaut que 156 unités d'exergie, parce qu'une bonne partie est tiède. C'est important pour la suite : une cuve de gravier ne pourra jamais récupérer « 689 », au mieux « 156 », et surtout la part au-dessus de 130 °C.

**2. Le détendeur est le vrai coupable de la décharge.** Dans le cas de base, il fait chuter la pression de 190 à 3 bar sans rien produire et détruit 234 unités, soit 68 % de tout ce qui était stocké. Le calcul à la main de la fiche Dormoy disait 74 : il supposait un détendeur réglé à 35 bar. En relisant l'article (phase 2), on a compris que le cas de base utilise le dernier étage de la turbine, à 3 bar. Ça change toute l'histoire : la turbine à 3 étages (détendeur à 40 bar) n'est pas d'abord un moyen de produire plus, c'est un moyen de **moins détruire**.

**3. La masse morte n'est pas une perte.** L'air qui reste à 18 bar (22 unités) sera encore là au cycle suivant. C'est de l'exergie immobilisée, pas détruite. La fiche comptait 65 unités perdues avec un arrêt à 50 bar.

**4. Le froid est une perte aussi.** L'air sort de la turbine à −60 °C. Ce froid a une exergie (il a fallu de l'énergie pour le produire) et on le jette : 19 unités. Réchauffer l'air avant la turbine évite ce gaspillage, en plus du givre.

## Le cas à 3 étages : la chaleur compte pour beaucoup… et pour peu

Avec la turbine à 3 étages et l'air réchauffé à 130, 90 et 90 °C, on produit 155 unités au lieu de 40. Mais il a fallu fournir 204 unités de **chaleur** externe. Combien d'exergie cette chaleur apporte-t-elle vraiment ? Seulement **21 unités**, à cause du facteur de Carnot. C'est le paradoxe de l'A-CAES : la chaleur de réchauffage est indispensable (sans elle, le détendeur et le froid détruisent tout), mais elle vaut peu en exergie. Elle est donc « presque gratuite » **si** elle vient d'une chaleur qu'on aurait jetée de toute façon : celle des refroidisseurs. C'est exactement ce que les phases 4 et 5 vont essayer de faire avec du gravier.

## Comparaison avec le calcul à la main

Le simulateur donne 329 unités stockées (la fiche disait 360) et 40 rendues (la fiche disait 46, Dormoy 43 à 46). Les grandes lignes concordent : deux tiers perdus à la recharge, le reste détruit surtout en décharge. Les différences viennent de trois choses : l'air réel au lieu du gaz parfait, le rendement électrique du moteur (94,5 %) que la fiche ignorait, et surtout le détendeur à 3 bar au lieu de 35 bar. Le détail est dans `rapports/phase3/exergie.md`.

## À retenir

1. L'énergie se conserve ; l'exergie, la partie utile, se détruit. Le bilan d'énergie dit **combien** sort, le bilan d'exergie dit **ce que ça vaut**.
2. L'air comprimé stocke de la pression, pas de la chaleur : à 20 °C et 190 bar, 440 kJ/kg d'exergie et zéro énergie en plus.
3. La chaleur vaut (1 − T₀/T) de sa valeur : 27 % à 130 °C, presque rien à 45 °C.
4. Dans le cas de base, le détendeur détruit 68 % de ce qui est stocké. Les étages de turbine servent d'abord à le contourner.
5. La masse morte est immobilisée, pas perdue ; le froid rejeté, lui, est perdu.
