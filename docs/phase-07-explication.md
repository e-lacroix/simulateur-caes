# Phase 7 : plusieurs modèles pour une même chose, et comment choisir

*Explication pour un élève de 16 ans. Phase 7 du simulateur, novembre 2026. Les formules citées (F34 à F41) sont détaillées dans `formules.md` ; les modèles sont comparés dans `docs/composants/` et dans `rapports/phase7/variantes.md`.*

## La question

La phase 6 a transformé le simulateur en briques qu'on assemble par fichier. Mais chaque brique n'avait qu'une seule physique : celle de Dormoy. Un chercheur qui lit Tola, Shi ou Zhang voit d'autres façons de décrire les mêmes machines : un rendement isentropique au lieu d'un exposant calibré, un pincement au lieu d'une efficacité, de l'huile ou de l'eau au lieu du gravier, pas de détendeur du tout. La question de la phase 7 : **pourquoi plusieurs modèles pour une même chose, et comment savoir lequel utiliser ?**

## Pourquoi plusieurs modèles

Un modèle n'est pas « la vérité » : c'est une description qui vaut dans un domaine. Trois raisons d'en avoir plusieurs :

1. **Ce qu'on sait de la machine.** Dormoy a mesuré son compresseur : on a calibré un exposant par étage (F04). Shi n'a pas de machine, il suppose un rendement de 86 % (F34). Tola décrit ses compresseurs par un rendement polytropique de 88 % (F35). Si on n'a que la fiche du fabricant, c'est le rendement qu'on connaît, pas l'exposant.
2. **La taille.** Les 20 bouteilles de Dormoy (5,86 m³) perdent leur chaleur par leurs parois en quelques heures : il faut le modèle « paroi » (F12). Une caverne de 118 000 m³ (Shi) n'a presque pas de paroi par mètre cube : le modèle « adiabatique » (F38) suffit. Le simulateur montre ce qui se passe quand on se trompe de modèle : le réservoir adiabatique appliqué à Dormoy finit sa charge à **167 °C au lieu de 29 °C**, avec 35 % d'air en moins. « La physique change avec la taille » n'est pas une phrase en l'air.
3. **La question qu'on pose.** La borne isotherme (F36) n'existe pas en vrai, mais elle répond à « quel est le minimum possible ? » : 304 kWh pour la charge de Dormoy, contre 386 mesurés. Les 82 kWh d'écart sont le prix de la chaleur de compression, celle que le gravier essaie de récupérer.

C'est comme les cartes d'une région : la carte routière, la carte topographique et le plan de métro décrivent le même endroit, mais on ne choisit pas la même selon qu'on conduit, qu'on marche ou qu'on prend le train.

## Le tableau des choix

| Fonction | Modèle validé sur des mesures | Autres modèles | Comment choisir |
|---|---|---|---|
| Compresseur | polytropique calibré (Dormoy, −2,5 %) | isentropique (Shi), polytropique à rendement (Tola), isotherme (borne) | Mesures disponibles → calibré ; fiche fabricant → rendement ; question « minimum » → isotherme |
| Refroidisseur | efficacité calibrée (Dormoy) | pincement (Tola 20 K, Shi 10 K) | Échangeur mesuré → efficacité ; échangeur à dimensionner → pincement |
| Sécheur | perte de débit (Dormoy) | aucun | Haute pression hors sol → sécheur ; caverne → aucun |
| Réservoir d'air | paroi (Dormoy) | K global, adiabatique (Shi) | Petit réservoir → paroi ; caverne → adiabatique |
| Détente | isenthalpique, Cheayb (Dormoy) | pression glissante (Shi, Zhang S.) | Détendeur réel → isenthalpique ; turbine conçue pour une pression variable → glissante |
| Turbine | polytropique DEPRAG (Dormoy, 3 %) | isentropique, polytropique à rendement, Flügel | Point nominal connu → DEPRAG ; pression variable → Flügel (seul modèle qui dit ce que ça coûte) |
| Stockage de chaleur | gravier (vérifié, Tola) | huile à deux réservoirs, eau sous pression, huile idéale, source externe | Ce qu'on veut comparer ; l'eau est plafonnée par son ébullition |
| Attente | pertes statiques avec isolant | sans pertes | Sans pertes = borne optimiste, jamais pour un transport |

## Trois résultats qui comptent

**Le détendeur et la pression glissante.** Chez Dormoy, le détendeur ramène l'air de 190 à 40 bar avant la turbine et détruit beaucoup d'énergie utile (phase 3). Shi et Zhang disent : enlevez-le, laissez la turbine recevoir la pression du réservoir. Avec un rendement constant (l'hypothèse de Shi), la décharge produit 39,0 kWh, comme avec le détendeur, mais demande 70 kWh de réchauffage au lieu de 45 : l'étage 1 détend de 190 à 11,5 bar et sort glacé. Avec la formule de Flügel (F39), qui dit comment une turbine réagit hors de son point nominal, la turbine DEPRAG à 190 bar avale **2,5 fois son débit nominal** : le réservoir se vide en 15 minutes au lieu de 38, la puissance quadruple, l'air sort à −78 °C, et le gain n'est que de 5 %. Conclusion honnête : la pression glissante n'est un gain que pour une turbine **conçue** pour cette plage ; la DEPRAG ne l'est pas. Le simulateur le dit avec des chiffres et des avertissements, pas avec un « ça devrait marcher ».

**L'eau bout, le gravier non.** Shi stocke la chaleur dans de l'eau à 190 °C et 18 bar. À cette pression, l'eau bout à 207 °C : le simulateur plafonne le réservoir chaud à 202 °C (F40) et signale chaque fois que le compresseur sort plus chaud. Sur le banc de Dormoy (170 à 195 °C), ça passe de justesse ; à 250 °C (le cas étudié par Shi), ça ne passe plus. Le gravier n'a pas de plafond. C'est la question originale du projet, et maintenant elle a une réponse chiffrée.

**La chaleur fond pendant le voyage.** Avec 20 cm de laine minérale (conductivité 0,036 W/m·K, Ablaoui 2023, F41) autour des trois cuves de D, et 14 jours d'attente, les cuves perdent **toute** leur chaleur utile (46,5 kWh) et les turbines reçoivent 99 / 58 / 66 °C au lieu de 130 / 90 / 90. Les petites cuves ont trop de surface par litre : constante de temps de 10 à 20 jours. Le même cas « sans pertes » (la borne optimiste) produit 41,2 kWh ; avec l'isolant, 37,4. C'est le point de départ du scénario de transport de la phase 11 : plus d'isolant, plus de gravier, ou des modules plus gros.

## Un exemple : réservoir à paroi ou adiabatique selon la taille

Le temps que met la chaleur à sortir d'un réservoir vaut à peu près (masse d'air × cv) / (K × surface) : c'est une constante de temps, comme pour une tasse de café qui refroidit. Pour Dormoy (registre : 65,5 m² de surface d'échange, K = 8,8 W/m²K, environ 1000 kg d'air en fin de charge) : 1000 × 718 / (8,8 × 65,5) ≈ 1250 s, soit 20 minutes. Pendant une charge de 10 h, la paroi a tout le temps d'agir : il faut le modèle « paroi ». Pour une caverne de 118 000 m³ (Shi), il y a 5700 tonnes d'air derrière quelques dizaines de milliers de mètres carrés de roche : **calcul personnel**, avec un coefficient de l'ordre de 1 W/m²K, la constante de temps se compte en jours, et pendant une charge de 8 h presque rien ne sort. Règle pratique : si cette constante de temps est longue devant la durée de la charge, le modèle adiabatique suffit ; sinon il faut la paroi. Le simulateur avertit quand le modèle adiabatique est appliqué sous 1000 m³.

## Ce qui garantit que tout tient ensemble

- Chaque modèle a sa fiche (F34 à F41), ses paramètres au registre avec leur source et leur DOI (Tola, Shi, Zhang S., Baniamerian, Wolf et Budt, Ablaoui, Wagner et Pruß), ses tests (bilan, cas limite, avertissement) et sa page de comparaison.
- Un test parcourt **toutes les combinaisons** du noyau sur le cas de Dormoy (48 chaînes de charge, 36 de décharge, 6 cycles) et vérifie que les bilans d'énergie ferment à 1 %. Les quelques combinaisons physiquement absurdes (détendre de 190 à 11 bar sans réchauffer : l'air se condenserait) s'arrêtent proprement avec un avertissement au lieu de planter.
- Les chiffres des phases 1 à 5 sont toujours reproduits à 0,00000 % (le modèle de Dormoy n'a pas bougé).

## À retenir

1. Un modèle vaut dans un domaine ; en avoir plusieurs permet de choisir celui qui correspond à ce qu'on sait, à la taille et à la question.
2. Le simulateur ne choisit pas à votre place : il simule le modèle demandé et **avertit** quand on le sort de son domaine (adiabatique sur un petit réservoir, Flügel loin du point nominal, eau qui bout, isolation parfaite sur deux semaines).
3. Trois réponses chiffrées sont nées de la phase 7 : la pression glissante ne vaut rien sans une turbine faite pour ; l'eau est plafonnée par son ébullition là où le gravier ne l'est pas ; les petites cuves perdent leur chaleur en deux semaines même bien isolées.
