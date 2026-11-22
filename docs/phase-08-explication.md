# Phase 8 : vérifier, croiser, valider

*Explication pour un élève de 16 ans. Phase 8 du simulateur, novembre 2026. Le tableau complet est dans `rapports/validation/tableau_de_bord.md` ; il se régénère avec `python validation/tableau_de_bord.py`.*

## La question

Depuis la phase 1, on dit que le simulateur est « validé sur Dormoy ». C'est vrai, mais c'est un seul banc, dans un seul climat, sans turbine installée et sans gravier. Un chercheur demandera : et sur autre chose ? La phase 8 répond par un **tableau de bord** : une ligne par grandeur comparée à un chiffre publié, avec sa source, son niveau de preuve, l'écart et un verdict. Cinquante et une lignes, trois sources, régénérées en trois minutes par une commande.

## Trois mots pour trois choses différentes

On confond souvent « valider » avec « ça donne le bon chiffre ». En réalité, il y a trois niveaux, du plus faible au plus fort :

| Mot | Contre quoi on compare | Ce que ça prouve | Exemple ici |
|---|---|---|---|
| **Vérifier** | une solution exacte (mathématique) | que le code résout bien ses propres équations, sans bug | lit de gravier contre la solution de Schumann (phase 4) : 0,1 % d'erreur avec 160 cellules |
| **Croiser** | une autre simulation, publiée par d'autres | que nos équations et nos hypothèses donnent la même chose que celles d'une autre équipe ; si les deux se trompent de la même façon, on ne le voit pas | Tola (10 MW), Shi (100 MW), les simulations de Dormoy |
| **Valider** | une mesure sur une vraie machine | que le modèle décrit la réalité, dans les conditions de la mesure | les deux essais de Dormoy : charge 1 → 190 bar, décharge 190 → 50 bar |

Le tableau de bord note chaque ligne avec son mot. Aujourd'hui, **seules cinq lignes sont des validations** (Dormoy) ; les quarante-six autres sont des croisements ou des données de fabricant (la turbine DEPRAG). Ce n'est pas une faiblesse cachée : c'est écrit en haut du tableau. Les mesures de Castellani (micro-CAES de 2,2 kW), de Cascetta et de Barbour (lits de roches) attendent que leurs PDF soient déposés à la main, parce que les sites des éditeurs refusent les robots.

## Ce que dit le tableau

| Source | Nature | Lignes | Reproduites (< 5 %) | Écarts expliqués | Non expliqués |
|---|---|---|---|---|---|
| Dormoy, essais mesurés | mesure | 5 | 5 | 0 | 0 |
| Dormoy, simulations et fabricant | croisement | 15 | 10 | 4 | **1** |
| Tola 2022 | croisement | 16 | 9 | 7 | 0 |
| Shi 2024 (prépublication) | croisement | 15 | 7 | 8 | 0 |

Les cinq mesures sont reproduites à 2,5 % près. Les écarts expliqués ont chacun leur paragraphe : par exemple, les turbines de Tola produisent 6 à 16 % de plus chez nous parce que nous les alimentons à température constante alors que ses cuves de gravier se refroidissent en fin de décharge ; ou la chaleur stockée dans l'eau de Shi, parce que le quatrième refroidisseur rejette chez nous à l'air ambiant. Le **seul écart non expliqué** est celui qu'on connaît depuis la phase 2 : le cas de base de Dormoy, −15 % sur 16,93 kWh. Il reste dans le tableau tel quel, avec la liste des hypothèses déjà testées. On ne le fera pas disparaître en tournant un bouton.

## Deux pièges trouvés en chemin

**Les chiffres mécaniques et électriques.** Les tableaux 7 et 9 de Tola donnent des puissances mécaniques, et son rendement de 0,674 applique le rendement moteur-génératrice de 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / 0,97). Si on compare nos puissances électriques à ses puissances mécaniques, on se trompe de 3 % dans un sens, puis de 3 % dans l'autre. Le tableau de bord compare maintenant les bonnes grandeurs.

**Une surpression que le texte ne justifie pas.** La figure 7 de Shi fait sortir son compresseur 4 à 7,55 MPa quand le réservoir est à 7 MPa, mais son tableau 4 n'explique que 0,24 MPa de surpression. Avec les chiffres du tableau, notre compresseur 4 fait 7 % de moins que le sien ; les trois premiers sont reproduits à 0,1 % près. C'est une prépublication non révisée : le tableau de bord le rappelle à chaque ligne.

## Les conditions ambiantes font partie du verdict

Chaque jeu a sa colonne « ambiance » : 20 °C et 50 % d'humidité supposés pour Dormoy (l'article ne les donne pas), 15 °C pour Tola, 25 °C pour Shi. Une ligne « reproduit » vaut pour ces conditions. Le simulateur sait tourner à −20 °C (phase 6), mais **aucune ligne du tableau ne valide l'hiver**, parce qu'aucune source n'a mesuré en hiver. Dire les deux choses dans la même phrase, c'est ça, l'honnêteté scientifique.

## Pourquoi un tableau plutôt qu'un chiffre

Un rendement de 16,8 % peut sortir d'un modèle juste ou d'un modèle qui se trompe deux fois en sens inverse. Un tableau de cinquante lignes, composant par composant, rend ça très improbable : si la chaleur des refroidisseurs, la durée de la décharge, les températures de la turbine et l'énergie des cuves sont toutes dans la bonne fourchette, le rendement final a de bonnes raisons de l'être aussi. Et quand une ligne sort de la fourchette, on sait où regarder.

## À retenir

1. Vérifier (solution exacte), croiser (autre simulation), valider (mesure) sont trois niveaux de confiance ; le tableau note chaque ligne avec le sien.
2. Les cinq mesures disponibles sont reproduites à 2,5 % près ; un écart de −15 % reste non expliqué et est affiché comme tel.
3. Le tableau se régénère en une commande ; les prochaines mesures (Castellani, Cascetta, Barbour) ont déjà leur dossier et attendent leurs PDF.
