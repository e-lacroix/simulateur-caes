# Phase 6 : des briques interchangeables assemblées par un fichier

*Explication pour un élève de 16 ans. Phase 6 du simulateur, novembre 2026. Les formules citées (F32, F33) sont détaillées dans `formules.md` ; le format des fichiers est décrit dans `scenarios/README.md`.*

## La question

Jusqu'à la phase 5, le simulateur savait faire tourner **une** installation : le banc de Dormoy, avec ou sans cuves de gravier. La chaîne (compresseur à 4 étages, 4 refroidisseurs, sécheur, réservoirs, détendeur, turbine DEPRAG) était écrite dans le code. Pour simuler autre chose, il fallait programmer. Le plan v2 demande autre chose : qu'un chercheur qui ne nous connaît pas décrive **sa** propre installation dans un fichier texte, et obtienne les mêmes sorties que nous (séries temporelles, bilans, tableau « 1000 unités », rendements). La question de la phase 6 : **comment découper le simulateur en briques qu'on assemble sans toucher au code, et prouver que le résultat n'a pas changé ?**

## L'idée : une prise normalisée

Chez toi, un grille-pain, une lampe et un ordinateur se branchent sur la même prise. Le grille-pain n'a pas besoin de savoir comment la centrale produit l'électricité, et la centrale n'a pas besoin de savoir ce que tu branches. Ce qui rend ça possible, c'est une **interface** : une forme de prise, une tension, une fréquence, décidées une fois pour toutes.

En informatique, c'est pareil. On a décidé que chaque brique du simulateur (un étage de compresseur, un refroidisseur, une cuve de gravier, un réservoir, un détendeur, un étage de turbine) reçoit l'air dans le **même format** et le rend dans le **même format** : une pression, une température, un débit. En plus, chaque brique déclare ce qu'elle a fait pendant le pas de temps : le travail qu'elle a reçu ou produit, la chaleur qu'elle a ajoutée à l'air (et d'où elle vient), la chaleur qu'elle a retirée (et où elle va), l'air qu'elle a perdu.

Une fois cette « prise » définie, on peut :

- **enchaîner** les briques dans l'ordre qu'on veut : l'air sort d'une brique et entre dans la suivante ;
- **remplacer** une brique par une autre qui a la même prise : un refroidisseur à efficacité par un échangeur à pincement, une cuve de gravier par une cuve d'huile (phase 7) ;
- **vérifier** que le circuit est branchable avant de le lancer : les pressions se suivent, chaque étage est là une fois, le réservoir est au bout.

## Comment on lit un fichier de configuration

Un scénario est un fichier YAML (du texte indenté, lisible sans formation). Il a quatre parties :

```yaml
ambiance:          # les conditions extérieures, une seule fois pour tout le monde
  T_amb: ...
composants:        # chaque brique : sa fonction (type), sa physique (modele), ses paramètres
  compresseur: {type: compresseur, modele: polytropique_dormoy, ...}
  cuve_3: {type: stockage_chaleur, modele: gravier, volume: ...}
charge:            # l'ordre dans lequel l'air traverse les briques
  chaine: [compresseur.1, cuve_1, refroidisseur_1, compresseur.2, ..., reservoir]
decharge:
  chaine: [reservoir, detendeur, cuve_3, turbine.1, cuve_2, turbine.2, cuve_1, turbine.3]
```

La chaîne de décharge de l'architecture D se lit comme une phrase : « l'air sort du réservoir, passe par le détendeur, traverse la cuve 3 qui le réchauffe, entre dans le premier étage de la turbine, traverse la cuve 2, entre dans le deuxième étage, traverse la cuve 1, entre dans le troisième étage ». C'est exactement le schéma de la phase 5, mais écrit par l'utilisateur plutôt que par le programmeur.

Chaque nombre du fichier vient soit du registre scientifique (`registre:turbine.etage1.pression_entree` : la valeur, sa source, sa page, son niveau de preuve), soit d'une valeur du scénario avec sa justification écrite. Le dossier de résultats contient un fichier `provenance.md` qui liste tout, avec les DOI des articles cités. Un chercheur peut vérifier chaque chiffre.

## Les huit fonctions

| Brique (`type`) | Ce qu'elle fait | Modèles disponibles |
|---|---|---|
| compresseur | comprime l'air, étage par étage | polytropique calibré sur Dormoy |
| refroidisseur | refroidit l'air avec l'air extérieur | efficacité (NTU) |
| sécheur, perte de débit | enlève une partie de l'air (régénération, rendement volumétrique) | fraction |
| réservoir d'air | stocke l'air comprimé | pertes globales, ou paroi avec capacité |
| stockage de chaleur | prend la chaleur de l'air chaud, la rend à l'air froid | gravier (Schumann), huile idéale, source externe |
| détente | ramène la pression à la consigne de la turbine | isenthalpique, Cheayb |
| turbine | détend l'air et produit l'électricité, étage par étage | polytropique DEPRAG |
| attente | fait passer le temps entre charge et décharge | pertes statiques |

Un détail nouveau : la chaleur de réchauffage n'est plus « magique ». Dans l'architecture B de Dormoy, les 130 / 90 / 90 °C venaient d'une « source externe » invisible dans le code. Maintenant, c'est une brique comme les autres (`chaudiere`, modèle `source_externe`) placée avant chaque étage de turbine dans la chaîne ; sa chaleur est étiquetée `externe` et comptée dans le rendement. Si on enlève la brique, la turbine reçoit l'air froid, point. Toute chaleur a un composant qui la fournit.

## Un seul réglage pour l'extérieur

Avant, la température ambiante apparaissait à plusieurs endroits du fichier (pour les refroidisseurs, pour le réservoir, pour l'air aspiré). Maintenant, il y a un seul bloc `ambiance`, et **toutes** les briques y puisent : les refroidisseurs y prennent leur air froid, le réservoir et les cuves y perdent leur chaleur, le compresseur y aspire son air, et le bilan d'exergie s'en sert comme zéro. On peut même donner un profil météo (un fichier CSV avec la température heure par heure) pour un transport de plusieurs semaines (F32).

C'est le critère de sortie de la phase : changer `T_amb` de 20 °C à −20 °C dans un fichier doit suffire à simuler l'hiver québécois. On l'a fait avec l'architecture D (`D_hiver.yaml`) :

| | D, été (20 °C) | D, hiver (−20 °C) |
|---|---|---|
| Air aspiré par le compresseur | 52 °C (air du conteneur), 0,052 kg/s | −20 °C, 0,067 kg/s (air plus dense) |
| Électricité pour recharger de 55 à 190 bar | 239,5 kWh en 6,05 h | 231,9 kWh en 5,50 h |
| Sortie des étages de compression (moyenne) | 168 / 173 / 194 / 119 °C | 70 / 106 / 128 / 57 °C |
| Chaleur stockée dans les cuves par charge | 57 kWh | 61 kWh |
| Entrée des turbines (moyenne ; cible 130 / 90 / 90 °C) | 130 / 90 / 90 °C | 120 / 79 / 52 °C |
| Électricité produite | 41,05 kWh en 39,5 min | 45,32 kWh en 46,2 min |
| Rendement aller-retour | 17,1 % | 19,5 % |
| Air rejeté par la dernière turbine (minimum) | 15 °C | −38 °C |

Le résultat surprend : **l'hiver rend plus**. Deux raisons. L'air froid est plus dense : le compresseur aspire 28 % de masse en plus par tour, et le réservoir contient plus de kilos d'air à 190 bar (il finit la charge à 0 °C au lieu de 40 °C), donc la décharge dure plus longtemps. Et comprimer de l'air froid coûte moins de travail par kilo. Mais le simulateur signale aussi ce qui cloche : les étages de compression sortent 60 à 100 °C plus froids, les cuves n'atteignent plus leurs cibles (la cuve 3 donne 120 °C en moyenne au lieu de 130, la cuve 1 seulement 52 °C au lieu de 90), et la dernière turbine rejette de l'air à −38 °C : avec de l'humidité, ça givre. Ces avertissements sont écrits dans `resume.md` ; le module humidité de la phase 9 dira si le givrage bloque la turbine. Le chiffre de 19,5 % est donc à lire avec ses réserves, comme tous les chiffres du simulateur.

## Rien n'a changé dans les résultats

Réécrire un programme est l'occasion idéale d'y introduire des erreurs. Pour s'en protéger, on a d'abord **enregistré** les chiffres des phases 1 à 5 (calculés par l'ancien code, qui existe toujours), puis on a fait tourner les nouveaux fichiers et comparé. Le plan demandait 0,1 % d'écart au plus ; on obtient 0,00000 % sur tout : énergie de charge, durée, électricité produite, chaleur par source, chaleur restante dans les cuves, tableau « 1000 unités ». C'est normal : les nouvelles briques appellent les mêmes fonctions physiques, dans le même ordre ; seule la façon de les assembler a changé. Un test automatique (`tests/test_non_regression.py`) refera cette vérification à chaque changement futur ; le rapport complet est `rapports/phase6/non_regression.md`.

Au passage, le nouveau code a rendu visible une chose que l'ancien faisait sans le dire : dans l'architecture D, le bas de la cuve 3 est refroidi par l'air à −5 °C qui sort du détendeur pendant la décharge. À la charge suivante, l'air chaud qui traverse la cuve en ressort par ce bas froid, parfois sous 20 °C, et le refroidisseur 3 le **réchauffe** au lieu de le refroidir. Le modèle à efficacité est symétrique, donc le calcul est le même qu'en phase 5 (c'est pour ça que les chiffres ne bougent pas), mais maintenant un avertissement le signale. Une vraie installation aurait une vanne de contournement ; c'est une variante pour la phase 7.

## Comment lancer une simulation

```text
.venv\Scripts\python -m caes simuler scenarios/D.yaml --sortie resultats/D
.venv\Scripts\python -m caes simuler scenarios/D.yaml --modifier ambiance.T_amb=-20degC
.venv\Scripts\python -m caes verifier scenarios/mon_installation.yaml
```

La deuxième ligne fait la même chose que `D_hiver.yaml` sans créer de fichier : `--modifier` remplace une valeur à la volée (pratique pour les balayages de la phase 10). La troisième vérifie un fichier sans le simuler : elle dit ce qui manque ou ce qui ne se branche pas (« la consigne du détendeur doit égaler la pression d'entrée du premier étage de turbine », « l'étage 2 sort à 3,5 bar mais l'étage 1 demande 40 bar »).

## À retenir

1. Une **interface** est un contrat : chaque brique reçoit et rend l'air dans le même format, et déclare ses flux d'énergie avec leur source. C'est ce qui permet d'assembler, de remplacer et de vérifier.
2. Une installation se décrit dans un fichier : des composants (type, modèle, paramètres sourcés) et deux chaînes (l'ordre de passage de l'air). Pas une ligne de code.
3. L'extérieur est réglé à un seul endroit ; changer un nombre suffit à passer de l'été à l'hiver, et le simulateur dit où les composants sortent de leur domaine.
4. La preuve qu'on n'a rien cassé est un test, pas une promesse : les chiffres des phases 1 à 5 sont reproduits exactement.
