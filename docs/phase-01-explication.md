# Phase 1 : la charge, ou comment 396 kWh d'électricité deviennent 1200 kg d'air à 190 bar

*Explication pour un élève de 16 ans. Phase 1 du simulateur, novembre 2026. Les formules citées (F04, F05…) sont détaillées dans `formules.md`.*

## Ce que fait le module

Le module de charge imite le banc de Dormoy pendant qu'il se remplit : un compresseur à 4 pistons aspire l'air du conteneur, le comprime en quatre coups de plus en plus serrés, le refroidit entre chaque coup, le sèche, puis le pousse dans 20 bouteilles (5,86 m³ au total) jusqu'à 190 bar. Le simulateur recalcule tout ça seconde par seconde (ou toutes les 10 secondes, le résultat est le même) et compte l'électricité consommée.

Le but de la phase 1 n'est pas de découvrir quelque chose : c'est de **vérifier que notre simulateur retrouve les chiffres mesurés par Dormoy**. Si on n'y arrive pas, tout ce qu'on calculera ensuite (gravier, transport) sera douteux. Dormoy a mesuré : 396 kWh, presque 10 h, 39 kW en moyenne.

## Pourquoi l'air chauffe quand on le comprime

Prenez une pompe à vélo, bouchez la sortie avec le pouce et poussez : le corps de la pompe chauffe. Vous avez fait du travail sur l'air, et ce travail n'a nulle part où aller : il devient de l'agitation des molécules, c'est-à-dire de la chaleur.

La règle qui dit « combien ça chauffe » s'appelle la transformation polytropique (F04) :

> T_sortie = T_entrée × β^((n − 1)/n)

où β est le rapport de pression (par exemple 3,25 pour l'étage 1) et n l'**indice polytropique**. Ce n résume le comportement du compresseur :

- n = 1 : compression très lente, parfaitement refroidie, l'air ne chauffe pas du tout (isotherme) ;
- n = 1,4 : compression rapide, aucune chaleur ne s'échappe (adiabatique) ;
- un vrai compresseur : entre les deux. Dormoy a mesuré 1,35 / 1,38 / 1,44 / 1,52 pour ses quatre étages.

**Exemple sur l'étage 1.** L'air entre à 20 °C, soit 293 K (il faut toujours des kelvins dans cette formule). β = 3,25, n = 1,35, donc l'exposant vaut 0,35/1,35 = 0,259. On calcule 3,25^0,259 : avec la calculatrice, ln 3,25 = 1,179 ; 1,179 × 0,259 = 0,306 ; e^0,306 = 1,357. Donc T_sortie = 293 × 1,357 = 398 K = **125 °C**. En un seul étage, l'air est passé de 20 à 125 °C.

Et si l'air entrait à 52 °C (325 K) ? T_sortie = 325 × 1,357 = 441 K = **168 °C**. On y reviendra.

## Combien ça coûte en énergie

Le travail pour comprimer un kilogramme d'air dans un étage (F05) est, pour un gaz parfait :

> w = n/(n − 1) × R × (T_sortie − T_entrée)

avec R = 287 J/(kg·K), la constante de l'air. Pour l'étage 1 : w = (1,35/0,35) × 287 × (398 − 293) = 3,857 × 287 × 105 = **116 000 J/kg**, soit 116 kJ par kilogramme.

Remarquez que w dépend de la **différence de température**, donc de la température d'entrée. C'est pour ça qu'on refroidit l'air entre les étages : comprimer de l'air froid coûte moins cher. Sans refroidisseurs, l'étage 2 partirait de 125 °C au lieu de 40 °C et coûterait 25 % de plus.

En additionnant les 4 étages à 190 bar, on arrive à environ 520 kJ/kg. Le compresseur aspire 0,052 kg/s, donc il fournit 0,052 × 520 = 27 kW à l'air. Mais le moteur électrique n'a pas un rendement parfait (94,5 %) et il y a des frottements (rendement mécanique 69 à 74 %, mesuré par Dormoy). L'électricité consommée est donc 27 / (0,74 × 0,945) ≈ **39 kW**. C'est exactement la puissance moyenne mesurée.

## Les refroidisseurs : la méthode de l'efficacité

Entre deux étages, l'air passe dans un radiateur ventilé par l'air du dehors. On ne connaît pas la forme du radiateur, mais on n'en a pas besoin : il suffit de connaître son **efficacité** ε, c'est-à-dire la fraction du chemin qu'il fait faire à l'air vers la température extérieure (F09) :

> T_sortie = T_entrée − ε × (T_entrée − T_extérieur)

Pour l'étage 1 : T_sortie = 125 − 0,82 × (125 − 20) = 125 − 86 = **39 °C**. Le radiateur a enlevé 86 °C sur les 105 possibles, soit 82 %.

La chaleur enlevée vaut environ cp × ΔT = 1006 × 86 = 86 kJ par kilogramme d'air. Avec 0,052 kg/s, ça fait 4,5 kW qui partent dans l'air du conteneur. Sur les quatre refroidisseurs, pendant toute la charge, le simulateur trouve environ 240 kWh de chaleur rejetée : **les deux tiers de l'électricité consommée partent en chaleur par les radiateurs**. C'est cette chaleur que les phases suivantes essaieront de récupérer dans du gravier.

## Le réservoir : une tirelire à énergie

Le réservoir reçoit de l'air à environ 40 °C. Deux choses se passent (F12) :

1. **L'air qui entre pousse l'air déjà présent**, et ce travail de poussée chauffe le réservoir. Si on remplissait un réservoir vide et parfaitement isolé avec de l'air à 20 °C, l'air finirait à 137 °C (c'est le facteur γ = 1,4 : 1,4 × 293 K = 410 K). Le simulateur vérifie ce cas limite dans un test.
2. **Le réservoir perd de la chaleur** par ses parois : 8,8 W par m² et par degré, sur 65 m², soit 577 W/K. Sur 10 heures, cette perte ramène l'air presque à la température ambiante.

Le résultat : l'air stocké finit vers 28 °C dans le simulateur. Dormoy avait mesuré 55 °C au début d'un autre essai, mais on ne sait pas combien de temps après la charge. C'est un point à surveiller en phase 2.

## Ce que la validation a donné

| | Mesure de Dormoy | Simulateur (hypothèses minimales) | Simulateur (air aspiré à 52 °C) |
|---|---|---|---|
| Énergie consommée | 396 kWh | 373 kWh (−6 %) | 386 kWh (−2,5 %) |
| Durée | ≈ 10 h | 9,9 h | 9,9 h |
| Puissance moyenne | 39 kW | 37,7 kW (−3 %) | 39,1 kW (+0,3 %) |
| Chaleur récupérable > 130 °C (55 → 190 bar) | 72 kWh (simulation de Dormoy) | 48 kWh | 66 kWh |

Le simulateur retrouve les mesures à mieux que 6 % dès le départ, et à mieux que 3 % avec une seule hypothèse supplémentaire. Et Dormoy lui-même, avec son propre modèle, obtenait 367 kWh contre 396 mesurés : par rapport à **son** modèle, le nôtre est à moins de 2 %.

## La petite découverte : l'air aspiré est chaud

Un détail a attiré l'attention. Dormoy dit que son compresseur aspire 172,4 m³ d'air par heure et que ça fait 0,052 kg/s. Or, 172,4 m³/h d'air à 20 °C pèsent 0,058 kg/s, pas 0,052. Pour que le compte tombe juste, il faut que l'air pèse 1,086 kg/m³, ce qui correspond à de l'air à **52 °C** (F06).

Est-ce absurde ? Non : le compresseur est dans un conteneur fermé, avec ses radiateurs qui rejettent 25 kW de chaleur. L'air qu'il aspire est l'air du conteneur, forcément chaud.

Ce qui rend cette hypothèse convaincante, c'est qu'elle explique **trois choses à la fois** sans aucun autre réglage :

1. la puissance : 39,1 kW au lieu de 37,7 (mesure : 39) ;
2. les températures de sortie des étages 1 et 2 : 168 et 185 °C au lieu de 125 et 174 (Dormoy montre plus de 150 °C sur sa figure 18) ;
3. la chaleur récupérable à l'étage 1 : 14 kWh au lieu de 0 (Dormoy : 12,5).

Quand une seule hypothèse, déduite d'une mesure indépendante, répare trois écarts d'un coup, c'est en général qu'elle est vraie. C'est ça, le travail de validation : pas « forcer » le modèle à donner le bon chiffre, mais chercher *pourquoi* il s'en écarte.

## Ce qu'on ne sait pas encore

- La forme exacte des courbes de rapport de pression des étages 3 et 4 (figure 8 de Dormoy), qu'on a supposée droite. L'élève doit numériser cette figure pour trancher.
- La température de l'air qui ventile les refroidisseurs (20 °C supposés).
- La température de l'air dans le réservoir pendant la charge : Dormoy ne publie pas la courbe.

## À retenir

1. Comprimer de l'air le chauffe ; l'indice polytropique n dit de combien.
2. Le travail de compression dépend de la température d'entrée : refroidir entre les étages économise de l'énergie.
3. Les deux tiers de l'électricité partent en chaleur dans les refroidisseurs : c'est le trésor que les phases suivantes vont essayer de récupérer.
4. Un écart entre simulation et mesure n'est pas un échec : c'est une question. Ici, la réponse était « l'air du conteneur est chaud ».
