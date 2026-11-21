# Phase 0 : qu'est-ce qu'un registre scientifique, et pourquoi s'en donner la peine ?

*Explication pour un élève de 16 ans. Phase 0 du simulateur, 2 novembre 2026.*

## Le problème

Un simulateur, c'est un programme qui applique des lois physiques à des chiffres. Les lois (conservation de l'énergie, comportement de l'air comprimé) sont connues. Les chiffres, eux, viennent de quelque part : un article, une fiche de fabricant, une mesure, ou un calcul qu'on a fait nous-mêmes. Et c'est là que ça se complique.

Prenons un exemple vrai, tiré de l'article de Dormoy (2024) qui sert de base au projet :

- l'article dit que le compresseur a un rendement de **4,3 %** ;
- mais si on refait la division avec les chiffres de l'article (16,93 kWh produits ÷ 366,75 kWh consommés), on trouve **4,6 %** ;
- le 4,3 % vient d'une autre division : 16,93 ÷ 396 kWh, où 396 est la consommation *mesurée* sur le banc, alors que 366,75 est la consommation *simulée*.

Aucun des deux chiffres n'est faux. Mais si on les mélange sans le savoir, on fait une erreur de 7 % sans s'en rendre compte. Et au jury, quelqu'un demandera : « D'où vient ce chiffre ? »

## La solution : un registre

Le registre, c'est un tableau (un fichier CSV, qu'on ouvre dans Excel ou LibreOffice) où **chaque chiffre du simulateur a sa propre ligne** avec :

| Colonne | Exemple | À quoi ça sert |
|---|---|---|
| `id` | `essai_charge.energie_consommee` | Le nom que le code utilise pour demander la valeur |
| `valeur`, `unite` | `396`, `kWh` | La valeur, dans l'unité de la source (le code convertit en SI tout seul) |
| `source_id` | `dormoy2024` | L'article d'où ça vient |
| `localisation` | `§3.1` | Où exactement dans l'article (section, tableau, figure) |
| `conditions` | `1 → 190 bar, 5,86 m3` | Dans quelles conditions c'est vrai |
| `niveau_preuve` | `mesure` | Voir ci-dessous : c'est le plus important |
| `notes` | | Les pièges, les incohérences, les calculs |

Le code ne contient **aucun chiffre**. Quand un module a besoin du volume des réservoirs, il écrit `reg.si("reservoir.volume_total")` et reçoit la valeur avec sa source. Si quelqu'un change la valeur dans le registre, tout le simulateur suit.

## Les niveaux de preuve : pourquoi une mesure vaut plus qu'une hypothèse

Tous les chiffres ne se valent pas. Le registre en distingue six niveaux, du plus solide au plus fragile :

| Niveau | Ça veut dire | Exemple dans Dormoy |
|---|---|---|
| `mesure` | Quelqu'un l'a mesuré avec un instrument | 396 kWh consommés, 38 min de décharge |
| `fabricant` | C'est écrit sur la fiche technique | 45 kW, 1782 tr/min, rendement électrique 94–95 % |
| `calibration` | Les auteurs ont ajusté le chiffre pour que leur modèle colle aux mesures | indices polytropiques 1,35 / 1,38 / 1,44 / 1,52 ; rendement mécanique 69–74 % |
| `simulation_publiee` | Ça sort du modèle des auteurs, pas d'une mesure | 16,93 kWh produits par la turbine (il n'y a pas de turbine sur le banc !) |
| `calcul_personnel` | C'est nous qui l'avons calculé | 4,6 % ; surface totale des réservoirs 65,52 m² |
| `hypothese` | Personne ne l'a vérifié | propriétés de la fibre de carbone (estimées par Dormoy) |

Pourquoi c'est important : quand notre simulateur donnera un résultat, on pourra remonter la chaîne et dire « ce résultat repose sur 80 % de mesures et 20 % d'hypothèses, et voici lesquelles ». Si un résultat dépend d'une hypothèse fragile, on le saura avant le jury, pas pendant.

Un cas concret : la turbine. Dormoy n'en a **pas installé** sur le banc. Tout ce qui concerne la production d'électricité (16,93 kWh, 16 % avec 3 étages) est `simulation_publiee`. Notre phase 2 reproduira ces simulations, mais on ne pourra jamais dire qu'on a « validé » la turbine sur des mesures. C'est honnête, et c'est ce qu'il faudra dire.

## Ce que la phase 0 a trouvé en lisant de près

En remplissant le registre ligne par ligne, on a relevé quatre petites incohérences dans l'article (voir `JOURNAL.md`). La plus amusante : 8 réservoirs de 320 L plus 12 de 270 L font 5,80 m³, mais l'article dit 5,86 m³ partout. Les deux chiffres ne peuvent pas être vrais en même temps. Ce n'est pas grave (1 % d'écart), mais ça montre pourquoi on note tout : si notre simulation donne 1 % de moins que Dormoy, on saura peut-être déjà pourquoi.

On a aussi récupéré les **données supplémentaires** de l'article (tableaux 7 à 9), qui donnent des chiffres absents du texte principal : le rendement électrique du moteur (94–95 %), la géométrie exacte des réservoirs et les caractéristiques des trois étages de turbine. Sans elles, on aurait dû inventer des hypothèses.

## Comment lire le registre

Ouvrir `data/registre/parametres.csv` dans un tableur. Trier par `niveau_preuve` pour voir d'un coup d'œil ce qui est solide et ce qui ne l'est pas. Trier par `source_id` pour voir d'où vient chaque bloc. Chercher « Incohérence » dans la colonne `notes` pour retrouver les pièges.

En Python :

```python
from caes.registre import Registre
reg = Registre.charger()
for p in reg.par_niveau("hypothese"):
    print(p)
```

## À retenir

1. Un chiffre sans source n'est pas un résultat, c'est une opinion.
2. Une mesure, une donnée de fabricant, une calibration, une simulation, un calcul personnel et une hypothèse sont six choses différentes.
3. Le code ne contient aucun chiffre : il les demande au registre, qui répond avec la source.
4. Lire de près une source, c'est déjà faire de la science : on y trouve des incohérences que les auteurs n'ont pas vues.
