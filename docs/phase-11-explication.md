# Phase 11 : transformer une question en configuration, et lire la réponse sans se tromper

*Explication pour un élève de 16 ans. Phase 11 du simulateur, novembre 2026. Les quatre scénarios sont dans `scenarios/exemples/` ; leurs pages de résultats dans `rapports/scenarios/` se régénèrent chacune par une commande.*

## La question

Depuis la phase 6, le simulateur sait assembler n'importe quelle installation à partir d'un fichier. Mais savoir assembler ne dit pas **quoi** assembler. Un chercheur qui arrive avec une question (« combien de temps la chaleur tient-elle pendant un transport ? », « combien de modules pour un centre d'urgence ? ») doit la traduire en fichiers, en balayages et en chiffres sourcés, puis lire la réponse sans se faire piéger par une unité, une hypothèse ou un résultat trop beau. La phase 11 montre cette démarche sur quatre questions.

## La démarche en quatre étapes

1. **Écrire la question avec ses nombres**, et dire d'où vient chaque nombre. « 100 kW pendant 72 h » est un choix du projet : il est au registre au niveau « hypothèse », pas caché dans le code. « 3 080 kWh par Megapack » vient d'une fiche de fabricant lue et déposée dans `data/sources/`.
2. **Partir du scénario le plus proche et ne changer que ce que la question change.** Le transport, c'est l'architecture D avec un isolant et une attente plus longue ; le centre d'urgence, c'est le même module avec un jour d'attente. Les fichiers dérivés sont générés par un script, jamais recopiés à la main : si D change, tout suit.
3. **Balayer plutôt que multiplier les fichiers.** Six durées × trois isolants, c'est dix-huit simulations lancées par `--modifier`, en parallèle, pas dix-huit fichiers.
4. **Lire la réponse avec ses réserves** : les avertissements font partie du résultat, les hypothèses sont listées, et un résultat négatif est écrit comme tel.

## Scénario 1 : le banc de Dormoy avec gravier (le cas de référence)

La question : que reste-t-il des 16,8 % de Dormoy quand la chaleur des réchauffeurs vient vraiment de la compression ? Réponse (régime stable) : A 4,3 % (mesuré), B 16,8 % mais 13,9 % si on compte la chaleur achetée, D (gravier direct) 17,1 % sans rien acheter, et **19,5 % par −20 °C** parce que l'air froid est plus dense et se comprime pour moins cher. Le piège : la cellule « D hiver » affiche aussi un air rejeté à −38 °C, parce que les cuves n'atteignent plus leurs cibles ; le rendement monte, mais la turbine givre. Un chiffre seul ne suffit jamais.

## Scénario 2 : le transport

La question : charger l'installation, la transporter de 7 à 56 jours, la décharger à l'arrivée. Ce que dit le rapport :

| Transport | Chaleur restante (20 cm) | Électricité livrée | Au lieu de |
|---|---|---|---|
| 7 jours | 70 % | 39,0 kWh | 40,6 kWh sans transport |
| 14 jours | 50 % | 36,3 kWh | |
| 28 jours | 25 % | 32,5 kWh | |
| 56 jours | 7 % | 29,7 kWh | |

Trois choses à comprendre. **La chaleur part comme une exponentielle** : une cuve isolée garde e^(−t/τ) de sa chaleur, et le rapport calcule τ à la main (26 jours pour 2 m³ sous 20 cm de laine ; 18 jours pour la cuve 3 du banc, plus petite). Les courbes simulées suivent cette loi : c'est la vérification que le modèle fait ce qu'on croit. **L'électricité tient mieux que la chaleur** : à 56 jours il reste 7 % de la chaleur mais 73 % de l'électricité, parce que l'air comprimé, lui, ne perd rien en refroidissant ; ce qu'on perd, c'est le réchauffage des turbines. Mais l'air sort alors à −78 °C : sans chaleur, la turbine givre (phase 9). **L'hiver n'aide pas et ne nuit pas beaucoup** au transport lui-même (l'isolant fait son travail), mais il fait givrer les refroidisseurs du compresseur à −20 °C et ramène l'air rejeté à −100 °C après 28 jours. Les fuites d'air, elles, sont redoutables : 0,5 % par jour pendant 28 jours coûtent 155 kg d'air et 6 kWh ; 2 % par jour divisent l'électricité par trois. Enfin, une chaudière d'appoint rend les 39 kWh quel que soit le délai, au prix de 1,6 kWh de chaleur à 7 jours et 40 kWh à 56 jours : le rapport donne le rendement avec et sans cette chaleur.

## Scénario 3 : le centre d'urgence (un résultat négatif)

La question : tenir 7,2 MWh sur 72 h, 120 kW le jour et 60 kW la nuit, avec des modules chargés d'avance. Un module livre 39 kWh à 62 kW pendant 38 minutes. Piloter une flotte seconde par seconde (un module de plus quand il en manque, un de moins quand il y en a trop, comme la vanne de Zhang) donne **192 modules**, 710 tonnes de bouteilles et de gravier, 1 125 m³ de bouteilles, et 47 MWh d'électricité pour les charger. Trois Megapack font le même travail avec 76 tonnes ; deux génératrices diesel avec 2,6 m³ de carburant. Le rapport chiffre ce qu'il faudrait pour être viable : multiplier l'électricité livrée par tonne par 11 et par mètre cube par 15. Les leviers connus (pression glissante, pression plus haute, cuves plus petites, meilleur compresseur) ne donnent pas ça. Conclusion écrite telle quelle : l'air comprimé hors sol n'est pas une solution de secours transportable à cette échelle ; son intérêt est le stockage fixe de longue durée, la caverne et la cogénération.

Ce que ce scénario montre aussi : une comparaison honnête demande des sources de même niveau. Les trois solutions sont comparées avec des fiches de fabricant lues et un rapport de coût avec DOI, et les coûts sont donnés en fourchettes avec leur année.

## Scénario 4 : la grande échelle

La même bibliothèque décrit la centrale de 100 MW de Shi (2024) : 118 000 m³ au lieu de 5,86, 65 % de rendement au lieu de 17. Ce n'est pas que « le gros est meilleur » : le fichier YAML rend visibles les quatre choix qui font la différence (réservoir adiabatique au lieu d'une paroi qui refroidit, pression glissante au lieu d'un détendeur, eau sous pression au lieu de gravier, 10 MPa au lieu de 19). Et il rappelle que ce cas vient d'une prépublication sans mesure : c'est un cas test, pas une validation.

## Lire un résultat sans se tromper

- **Les unités.** Tout est en SI à l'intérieur (Pa, K, J) ; les tableaux convertissent à la sortie. Un « 190 » est en bar, un « 0,172 » est un rendement, un « 15 » en bas d'une colonne « air rejeté » est en °C. Quand on doute, le fichier YAML donne l'unité de chaque entrée.
- **Les hypothèses.** Le registre dit pour chaque nombre s'il est mesuré, pris chez un fabricant, calibré, publié par une simulation, calculé par nous ou supposé. Les profils météo et le profil de demande de cette phase sont des hypothèses : le rapport le dit, et un chercheur les remplacera par des données.
- **Les avertissements.** Un résultat qui s'accompagne de « cuve trop froide pour la cible » ou « givre » n'est pas faux, mais il décrit une installation qui a un problème. Les ignorer, c'est le piège le plus courant.
- **L'intervalle.** La phase 10 donne ± 1 point sur le rendement de D avec les fourchettes du registre. Deux scénarios dont les résultats diffèrent de moins que ça ne se départagent pas.
- **Le résultat négatif.** Le centre d'urgence ne marche pas avec cette technologie. L'écrire est la seule façon de rendre le simulateur crédible quand il dit qu'autre chose marche.

## À retenir

1. Une question devient une configuration en trois gestes : des nombres sourcés, le scénario le plus proche modifié au minimum, des balayages par `--modifier`.
2. Pendant un transport, la chaleur part en exponentielle (τ ≈ 3 semaines sous 20 cm de laine) mais l'air comprimé reste ; ce qu'on perd, c'est le réchauffage, et avec lui l'air rejeté passe sous le point de givre.
3. Pour un centre d'urgence de 72 h, l'air comprimé hors sol demande dix fois plus de masse que des batteries : résultat négatif, présenté comme tel, avec ce qu'il faudrait changer.
