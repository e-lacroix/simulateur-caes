# Phase 12 : pourquoi « refaire » fait partie de la science

*Explication pour un élève de 16 ans. Phase 12 du simulateur, novembre 2026. Les guides sont `docs/demarrage.md`, `docs/ajouter-un-composant.md`, `docs/ajouter-une-etude.md`, `docs/limites-couvertes.md` et `docs/api.md` ; la commande qui régénère tout est `python generer_tout.py`.*

## La question

Depuis la phase 0, le projet promet qu'un chercheur pourra se servir du simulateur **sans nous**. Jusqu'ici, tout ce qu'on savait faire tenait dans la tête de ceux qui l'avaient construit : quelle commande lancer, dans quel ordre, quel fichier modifier, à quoi ressemble un résultat normal. La phase 12 sort ces connaissances de nos têtes pour les mettre dans des fichiers, et ajoute une chose que peu de projets scolaires font : **une commande qui refait tout, puis vérifie que le texte dit encore la vérité.**

## Reproduire, ce n'est pas seulement « ça marche chez moi »

Un résultat scientifique n'est pas une phrase, c'est une phrase **plus** le moyen de la vérifier. « D rend 17,1 % » n'a de valeur que si quelqu'un d'autre, avec le même fichier et la même commande, retrouve 17,1 %. Ça paraît évident, et pourtant c'est ce qui manque à plusieurs des études qu'on a lues : Wang ne donne pas les réglages de son optimisation, Shi est une prépublication sans mesure, Tola ne publie pas sa corrélation d'échange. Chaque fois, on a dû deviner, et l'écrire au niveau « hypothèse ».

Trois choses rendent un résultat reproductible ici :

1. **Les entrées sont tracées.** Chaque nombre du simulateur vient du registre (avec sa source, son unité, son niveau de preuve) ou d'un fichier de scénario qui porte sa source. Il n'y a pas de chiffre caché dans le code : un test le vérifie.
2. **Les calculs sont déterministes.** Deux lancements du même scénario donnent le même résultat au dernier chiffre. Même le hasard de la phase 10 (indices de Sobol, front de Pareto, intervalle bootstrap) a une graine fixe, imprimée dans le rapport.
3. **Les sorties se régénèrent.** Aucune page de résultats n'est écrite à la main : `rapports/scenarios/transport.md`, `rapports/phase10/analyse.md`, le tableau de bord de validation, le registre lui-même sortent de scripts.

## Le piège des chiffres recopiés

Il reste un maillon faible : les pages d'explication, comme celle-ci, sont écrites par une personne qui recopie des chiffres des rapports. Un jour, un modèle change, un rapport est régénéré, et la page dit encore l'ancien chiffre. Personne ne le voit : c'est de la science périmée qui a l'air à jour.

La phase 12 y répond avec `docs/chiffres_cles.yaml` : une liste de chiffres cités (le rendement de D, le nombre de modules du centre d'urgence, la part de chaleur restante après 14 jours…), chacun avec le rapport où le lire et la façon de l'écrire. `python generer_tout.py --etapes verifier` relit chaque rapport, met le chiffre en forme et vérifie qu'il figure dans la page. Le premier essai a attrapé deux erreurs : un « 39,1 kWh » qui devait s'écrire « 39,0 » (arrondi) et un indice de Sobol lu dans le mauvais tableau. C'est exactement à ça que sert l'outil.

## Ce qu'un chercheur attend d'un outil

Pas de la magie : de la confiance, qui se gagne point par point.

| Il demande | Ce que le dépôt répond |
|---|---|
| « Comment je l'installe ? » | `docs/demarrage.md` : cinq commandes, un scénario reproduit en moins d'une heure (à faire tester par un tiers ; le résultat ira dans le journal) |
| « D'où vient ce chiffre ? » | le registre, `provenance.md` dans chaque dossier de résultats, les fiches `formules.md` |
| « Est-ce validé ? » | le tableau de bord : cinq mesures reproduites à 2,5 %, un écart non expliqué affiché tel quel |
| « Et si j'ajoute mon composant ? » | `ajouter-un-composant.md` : l'interface, la liste de contrôle, un exemple réel |
| « Et si j'ajoute mon étude ? » | `ajouter-une-etude.md` : fiche, registre, validation, tableau des limites |
| « Qu'est-ce que ça ne sait pas faire ? » | `limites-couvertes.md` : ce que chaque étude ne couvre pas, ce qu'on en a fait, les erreurs trouvées dans les publications, onze questions ouvertes |
| « Comment je cite ça ? » | `CITATION.cff`, licence GPL-3.0 dans `LICENSE` et `pyproject.toml` |
| « Ça casse quand on y touche ? » | 298 tests, lancés à chaque modification par l'intégration continue |

## Ce que la phase 12 ne règle pas

- Le **test par un tiers** du guide de démarrage n'est pas fait : c'est le critère de sortie, et seule une personne extérieure peut le passer.
- `generer_tout.py` prend environ trois heures (la validation détaillée de Dormoy 55 minutes, l'analyse de sensibilité 50 minutes sur dix processus) ; l'intégration continue ne lance que les tests.
- La référence de l'API est générée depuis les docstrings : elle est complète mais sèche ; les guides sont là pour le reste.
- L'archivage avec identifiant pérenne (Zenodo) demande une décision de l'utilisateur et un dépôt public : préparé (`CITATION.cff`), pas fait.

## À retenir

1. Un résultat reproductible, c'est des entrées tracées, un calcul déterministe et des sorties régénérées par une commande.
2. Le maillon faible est le texte qui recopie des chiffres : `chiffres_cles.yaml` le vérifie à chaque régénération.
3. Un chercheur ne demande pas un outil parfait, il demande un outil qui dit ce qu'il sait, ce qu'il suppose et ce qu'il ne sait pas : c'est ce que `limites-couvertes.md` écrit noir sur blanc.
