# Phase 10 : quels réglages comptent, avec quelle marge d'erreur, et quels compromis

*Explication pour un élève de 16 ans. Phase 10 du simulateur, novembre 2026. Les méthodes sont les fiches F44 à F46 de `formules.md` ; les chiffres viennent de `rapports/phase10/analyse.md`, régénéré par `python -m caes analyser scenarios/analyse/D.yaml --sortie rapports/phase10` (environ 50 minutes sur dix processus).*

## La question

Le simulateur a des dizaines de réglages : pression maximale, taille des cuves, grosseur du gravier, épaisseur d'isolant, rendements des machines, température dehors… Un chercheur qui veut améliorer l'installation ne peut pas tout essayer. Il a besoin de trois réponses :

1. **Quels réglages comptent vraiment ?** (sensibilité)
2. **Quelle est la marge d'erreur du résultat ?** Un rendement de 17,2 % calculé avec des données qui ont chacune une fourchette n'est pas « 17,2 % », c'est « entre tant et tant ». (incertitudes)
3. **Quand deux objectifs se contredisent, quels sont les bons compromis ?** (front de Pareto)

La phase 10 répond aux trois avec une seule commande et un fichier d'analyse qui dit ce qu'on fait varier. La configuration étudiée est l'architecture D (trois étages, cuves de gravier traversées par l'air comprimé, 20 cm de laine minérale, un jour d'attente).

## Chercher les réglages qui comptent : deux méthodes

**Un paramètre à la fois.** On prend chaque réglage, on le met tout en bas de sa plage puis tout en haut, les autres restant à leur valeur normale, et on note de combien le résultat bouge. Classés du plus grand au plus petit, ces « balancements » dessinent un graphique en forme de tornade. Pour le rendement aller-retour de D :

| Rang | Réglage | Plage | Rendement, borne basse → haute | Balancement |
|---|---|---|---|---|
| 1 | Rendement mécanique du compresseur | × 0,93 à × 1,07 | 16,0 % → 18,4 % | 14 % du nominal |
| 2 | Température ambiante | −20 à 30 °C | 18,7 % → 16,8 % | 11 % |
| 3 | Pression maximale | 120 à 250 bar | 18,2 % → 16,6 % | 9 % |
| 4 | Volume des cuves | × 0,5 à × 2 | 16,7 % → 17,3 % | 4 % |
| 5 | Efficacité des refroidisseurs | × 0,9 à × 1,05 | 16,8 % → 17,4 % | 4 % |
| 6 à 10 | rendement électrique, durée d'attente, isolant, gravier, humidité | | | ≤ 1 % |

Trois choses à voir : le compresseur domine (chaque point de rendement mécanique perdu se paie à la charge, qui est cinq fois plus grosse que la décharge) ; l'hiver *améliore* le rendement (air plus dense, compression moins chère) ; et monter la pression *baisse* le rendement (le détendeur jette plus d'exergie, phase 3) tout en multipliant l'électricité livrée par 2,7 (20 → 55 kWh). Le rendement et l'énergie livrée ne racontent pas la même histoire.

**Tous ensemble : les indices de Sobol.** La tornade a un défaut : elle bouge un réglage pendant que les autres dorment. Or certains réglages ne comptent qu'*en combinaison*. Les indices de Sobol tirent tous les réglages en même temps au hasard, 384 fois, et découpent la variation totale du résultat en parts : la part due à chaque réglage seul (S_1) et la part qu'il prend avec ses interactions (S_T). Pour le rendement de D :

| Réglage | S_1 (seul) | S_T (avec interactions) | Intervalle de confiance de S_T |
|---|---|---|---|
| Rendement mécanique du compresseur | 0,32 | 0,39 | 0,22 à 0,60 |
| Volume des cuves | 0,05 | 0,28 | 0,13 à 0,46 |
| Pression maximale | 0,17 | 0,26 | 0,14 à 0,44 |
| Température ambiante | 0,05 | 0,11 | 0,06 à 0,20 |
| Épaisseur d'isolant | 0,08 | 0,09 | 0,04 à 0,19 |

Le volume des cuves remonte du 4e au 2e rang : seul, il ne fait presque rien (S_1 = 0,05), mais avec la pression et la durée d'attente il compte beaucoup (S_T = 0,28). C'est logique : des cuves plus grosses ne servent que si la pression leur donne plus de chaleur à stocker et si l'attente ne la laisse pas fuir. **Les trois réglages dominants de D sont donc le rendement mécanique du compresseur, le volume des cuves et la pression maximale**, avec les intervalles ci-dessus. L'humidité ambiante a un indice nul : ce n'est pas une découverte, c'est une limite du simulateur, dont le bilan d'énergie est fait sur l'air sec (phase 9) ; l'humidité agit sur l'eau et le givre, qui ne sont pas dans les sorties de cette analyse.

Avec 32 échantillons de base, les indices sont bruités : un S_1 légèrement négatif vaut zéro, et l'indice de la pression sur l'électricité livrée ressort à 1,1 alors qu'il ne peut pas dépasser 1. L'intervalle de confiance est là pour le rappeler.

## Un résultat sans fourchette ne vaut pas grand-chose

Le registre donne, pour certaines données, une fourchette plutôt qu'un chiffre : le rendement électrique du compresseur est « 94 à 95 % », son rendement mécanique « 69 à 74 % » selon la pression, l'efficacité du refroidisseur 4 « 74 à 85 % ». Si on ne garde que la valeur du milieu, on oublie que le résultat hérite de ces fourchettes. La propagation tire 48 fois chaque donnée au hasard dans sa plage (plus la granulométrie du gravier) et regarde ce que devient le résultat :

| Résultat | Nominal | 5 % des tirages en dessous de | 95 % en dessous de | ± |
|---|---|---|---|---|
| Rendement aller-retour | 17,2 % | 15,9 % | 18,0 % | ± 1,05 point (6 %) |
| Électricité consommée | 235 kWh | 223 | 253 | ± 15 kWh (6 %) |
| Électricité produite | 40,5 kWh | 40,0 | 40,7 | ± 0,3 kWh (1 %) |

Autrement dit : **le rendement de D est 17,2 % ± 1 point**, et cette marge vient presque entièrement du rendement mécanique du compresseur (corrélation de rang +0,96 avec le rendement, −0,99 avec l'électricité consommée). C'est le chiffre à mesurer en priorité si on construisait la machine. L'électricité produite, elle, ne dépend pas de ces données-là.

## Les compromis : le front de Pareto

Deux objectifs contradictoires : livrer le plus d'électricité possible et peser le moins possible (réservoirs d'air à paroi mince, F44, plus gravier des cuves). Trois variables : pression maximale (120 à 250 bar), volume des cuves (× 0,5 à × 2), épaisseur d'isolant (5 à 30 cm). Aucune configuration ne gagne sur les deux tableaux ; celles que personne ne bat « des deux côtés » forment le **front de Pareto**. L'algorithme NSGA-II (16 configurations par génération, 12 générations, 208 simulations, graine fixée) le trouve en croisant et en mutant les meilleures, comme une sélection naturelle accélérée.

| Point du front | Pression | Cuves | Isolant | Électricité livrée | Masse |
|---|---|---|---|---|---|
| le plus léger | 134 bar | × 0,5 | 29 cm | 24,4 kWh | 2 111 kg |
| coude | 250 bar | × 0,5 | 16 cm | 50,8 kWh | 2 907 kg |
| le plus productif | 250 bar | × 0,93 | 17 cm | 55,3 kWh | 3 947 kg |
| configuration de départ (D) | 190 bar | × 1 | 20 cm | 40,5 kWh | 3 699 kg |

Trois leçons :

- **La configuration de départ est dominée.** Avec les mêmes 40 kWh, le front propose 2 520 kg au lieu de 3 699 (193 bar, cuves × 0,5) : les cuves de D, dimensionnées en phase 5 pour que les turbines atteignent leurs cibles de température, sont deux fois trop grosses pour l'objectif « électricité par kilogramme ».
- **Le coude** (point le plus loin de la corde qui joint les extrémités) est à 250 bar et cuves × 0,5 : jusque-là, chaque kilogramme ajouté rapporte beaucoup ; au-delà, livrer 4,5 kWh de plus coûte 1 000 kg de gravier.
- **Deux bornes sont actives.** Près de la moitié du front (47 %) est à 250 bar et 39 % à cuves × 0,5, les limites qu'on a données à l'analyse : c'est la plage qui arrête le front, pas la physique. Le rapport le signale automatiquement. Dormoy simule jusqu'à 300 bar ; le compresseur est conçu pour 350.

Mais attention à ce qu'un front à deux objectifs ne voit pas. Avec les cuves à × 0,5, l'air sort de la dernière turbine à **−38 °C** au lieu de +15 °C : les cuves ne tiennent plus leurs cibles, et la phase 9 a montré ce que l'air froid fait à une turbine (givre). Un chercheur ajouterait une contrainte (« air rejeté au-dessus de 0 °C ») ou un troisième objectif. Le simulateur donne les outils ; choisir les objectifs reste une décision humaine.

## Ce que ça change dans la façon de lire un chiffre

Avant la phase 10 : « D rend 17,2 % ». Après : « D rend 17,2 % ± 1 point, surtout à cause du rendement mécanique du compresseur ; les trois réglages qui comptent sont ce rendement, le volume des cuves et la pression ; et pour livrer plus d'électricité par kilogramme, il faut monter en pression et réduire les cuves, jusqu'à ce que l'air rejeté devienne trop froid. » La seconde phrase est plus longue, mais c'est elle qui permet de décider.

## Ce que le simulateur ne sait pas encore

- Les plages « choix de l'analyse » (pression, cuves, isolant, climat) sont des choix, affichés comme tels ; seules les plages marquées « registre » viennent d'une publication. Les hypothèses sans fourchette reçoivent ± 20 % par défaut.
- Les paramètres sont tirés indépendamment et uniformément : le registre ne donne pas de loi de probabilité, ni de corrélation entre données.
- 32 échantillons de base pour Sobol, c'est peu (les intervalles de confiance sont larges) ; la version de référence a coûté 50 minutes sur dix processus. Doubler n double le temps.
- La masse ne compte que les réservoirs (paroi mince calibrée sur les bouteilles de Dormoy, 107 kg retrouvés à 3 % près) et le gravier : pas le compresseur, les turbines, les échangeurs ni la structure.
- Le front est une approximation qui dépend de la population, des générations et de la graine : tout est imprimé dans le rapport, pour qu'un autre puisse le refaire à l'identique.

## À retenir

1. Trois réglages dominent le rendement de D : le rendement mécanique du compresseur, le volume des cuves (surtout en interaction) et la pression maximale. L'humidité n'y fait rien par construction, l'isolant et la granulométrie presque rien.
2. Le rendement de D vaut 17,2 % ± 1 point avec les fourchettes du registre ; la marge vient du compresseur.
3. Pour livrer plus d'électricité par kilogramme : plus de pression, moins de gravier, jusqu'au point où l'air rejeté gèle. Un front de Pareto montre les compromis, il ne choisit pas à notre place.
