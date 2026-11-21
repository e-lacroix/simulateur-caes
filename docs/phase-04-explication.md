# Phase 4 : le lit de gravier, ou comment garder la chaleur dans des cailloux

*Explication pour un élève de 16 ans. Phase 4 du simulateur, novembre 2026. Les formules citées (F25 à F29) sont détaillées dans `formules.md`.*

## L'idée

Les phases 1 à 3 ont montré que les refroidisseurs du compresseur de Dormoy jettent 689 unités de chaleur sur 1000 d'électricité, et que la turbine à 3 étages a besoin d'air chaud (130 °C) pour bien marcher. L'idée du projet : au lieu de jeter cette chaleur, la **mettre de côté dans des cailloux**, puis la rendre à l'air avant la turbine.

Pourquoi des cailloux ? Ils sont gratuits, ils ne brûlent pas, ils ne fuient pas, ils supportent 200 °C sans broncher, et un mètre cube de gravier stocke autant de chaleur qu'un gros chauffe-eau : 1,7 MJ par degré, soit 230 MJ (64 kWh) entre 35 et 170 °C.

## Le front thermique : la vague de chaleur

Imaginez une cuve verticale remplie de cailloux froids. On souffle de l'air chaud par le haut. Les premiers cailloux chauffent vite et refroidissent l'air, qui arrive froid sur les cailloux suivants. Résultat : une **frontière** entre une zone chaude (en haut) et une zone froide (en bas), qui descend lentement, comme une vague. Tant que la vague n'a pas atteint le fond, l'air ressort froid : rien n'est perdu. C'est le « front thermique » (ou thermocline).

À quelle vitesse descend la vague (F25) ? L'air apporte ṁ × c_f joules par seconde et par degré ; chaque mètre de cuve en absorbe (1 − ε) × ρ_s × c_s × A. Pour le banc de Dormoy (0,052 kg/s, cuve de 50 cm de diamètre) :

> v = 0,052 × 1006 / (0,7 × 2750 × 900 × 0,196) = 0,15 mm/s = **0,55 m par heure**

Une cuve de 2 m « se remplit » de chaleur en 3,6 h. Pour la grande cuve de Tola (12,3 kg/s, 5,2 m de diamètre, 10,4 m de haut), la vague met 8,5 h à descendre : avec une charge de 6 h, elle n'atteint que les deux tiers de la cuve, et l'air de sortie reste froid pendant « environ les deux tiers du temps ». C'est exactement ce que Tola observe.

Puis on inverse : en décharge, l'air froid entre par le bas, la vague remonte, et l'air ressort chaud (à la température des cailloux du haut) jusqu'à ce que la vague arrive au sommet. Ensuite, l'air sort de moins en moins chaud : c'est l'**effet de fin de décharge**, qui fait baisser la puissance de la turbine.

## Comment l'ordinateur calcule ça

On découpe la cuve en 40 à 160 tranches. À chaque pas de temps (10 à 60 secondes), on fait passer l'air de tranche en tranche (F26). Dans chaque tranche :

1. l'air se rapproche de la température des cailloux : s'il entre à 170 °C et que les cailloux sont à 20 °C, il ressort à, disons, 83 °C (il a fait 58 % du chemin : c'est l'« efficacité » de la tranche, qui dépend du coefficient d'échange h) ;
2. les cailloux reçoivent la chaleur perdue par l'air et se réchauffent un peu ;
3. l'air passe à la tranche suivante.

Le coefficient d'échange h dit à quelle vitesse la chaleur passe de l'air aux cailloux (F27). Il vient d'une formule ajustée sur des centaines d'essais (Wakao, 1979) : plus l'air va vite et plus les cailloux sont petits, mieux ça échange. Pour Dormoy, h ≈ 38 W/m²K ; pour Tola, 195 W/m²K (l'air y va plus vite).

Le modèle est **exact tranche par tranche** : on ne peut pas le faire exploser avec un pas de temps trop grand, et l'énergie est conservée au joule près (test automatique). Avec une seule tranche, on retrouve la « cuve bien mélangée » à une seule température : elle laisse sortir de l'air tiède dès le début, sans front. C'est pour ça que les cuves de stockage sont hautes et étroites.

## Les deux vérifications

**1. La solution exacte de Schumann (1929).** Pour le cas simple (cuve uniforme au départ, air chaud à température constante, pas de pertes), Schumann a résolu les équations à la main. Notre modèle est comparé à cette solution : l'erreur sur la température de sortie passe de 6 % avec 20 tranches à 0,1 % avec 160. Le code fait bien ce que les équations disent.

**2. Les cuves de Tola (2022).** Tola a simulé trois cuves de gravier de 221 m³ sur 20 cycles de charge (6 h) et de décharge (3 h). Avec les mêmes dimensions, débits et températures, et sans aucun réglage :

| Cuve | Tola : chaleur stockée | Simulateur (cycle stable) | Écart |
|---|---|---|---|
| TES-LP (3,9 bar) | 9,60 MWh | 9,61 MWh | +0,1 % |
| TES-IP (11,9 bar) | 9,54 MWh | 9,68 MWh | +1,4 % |
| TES-HP (36,8 bar) | 9,54 MWh | 9,88 MWh | +3,6 % |

Et trois comportements que Tola décrit sont retrouvés : la sortie reste constante pendant la majeure partie de chaque phase, l'air de sortie en fin de première décharge tombe exactement à 100 °C (la limite que Tola avait fixée pour dimensionner ses cuves), et le système se stabilise en quelques cycles, le premier étant le seul vraiment différent.

Attention : Tola est une simulation, pas une mesure. On a donc vérifié que notre code et le sien racontent la même histoire, ce qui est rassurant, mais ce n'est pas une validation expérimentale. Celle-ci attend l'article de Cascetta (2018), en accès libre mais que le site de l'éditeur refuse aux téléchargements automatiques : il faut le récupérer à la main.

## Ce qu'on apprend pour le banc de Dormoy

Expériences numériques sur une cuve de 0,5 m × 2 m (755 kg de gravier) :

- **Des cailloux plus petits** échangent mieux (front plus net), mais coûtent plus de perte de charge : 344 Pa avec 1 cm contre 50 Pa avec 5 cm.
- **La perte de charge** est négligeable dans tous les cas (de 5 à 90 Pa, contre des pressions de 3 à 50 bar) : traverser le gravier ne coûte rien au compresseur (F28). Question du plan réglée.
- **À 50 bar**, l'air est si dense qu'il avance à 6 mm/s : la formule de Wakao sort de sa plage de validité (Re ≈ 10) et le code le signale. Le modèle reste utilisable (il tend vers la conduction pure), mais avec une incertitude plus grande.
- **Pendant l'attente**, la chaleur s'étale par conduction à travers les cailloux : environ 1 m en deux semaines (F29). Le stock ne perd pas d'énergie par ce mécanisme, mais il devient plus tiède, donc moins utile. La phase 6 chiffrera cet effet avec les pertes par l'isolant.

## À retenir

1. Dans un lit de gravier, la chaleur avance comme une vague : tant qu'elle n'a pas atteint le fond, rien ne sort.
2. La vitesse de la vague se calcule à la main : débit d'air × c_f ÷ capacité du lit par mètre.
3. Le modèle de Schumann est vérifié contre sa solution exacte (le code est juste) et croisé avec Tola (il raconte la même chose qu'un autre modèle). La validation sur des mesures reste à faire.
4. La perte de charge dans le gravier est négligeable ; la taille des cailloux joue surtout sur la netteté du front.
