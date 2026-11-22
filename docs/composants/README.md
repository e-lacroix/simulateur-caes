# Bibliothèque de composants

Chaque fonction d'une installation d'air comprimé est un **composant** avec une interface commune (`caes/composants/base.py`, fiche F33). Un scénario YAML choisit le composant par `type` et sa physique par `modele` ; chaque modèle a ses paramètres, ses sources et son domaine de validité, décrits dans la page du type, qui compare aussi les modèles entre eux (quand utiliser lequel). Depuis la phase 7, chaque fonction du noyau a au moins deux modèles ; `tests/test_combinaisons.py` vérifie que toutes les combinaisons ferment leurs bilans à 1 %.

| `type` | Page | Modèles disponibles | Fiches | Encore à faire |
|---|---|---|---|---|
| `compresseur` | [compresseur.md](compresseur.md) | `polytropique_dormoy`, `isentropique` (Shi), `polytropique_rendement` (Tola), `isotherme` (borne, Baniamerian) | F04 à F08, F34 à F36 | rendement variable avec la charge, piston liquide |
| `refroidisseur` | [refroidisseur.md](refroidisseur.md) | `efficacite` (Dormoy), `pincement` (Tola, Shi) ; `perte_de_charge` (Shi) | F09, F37 | – |
| `secheur` | [secheur.md](secheur.md) | `perte_debit` (Dormoy, avec point de rosée de sortie), `separateur`, `aucun` | F10, F43 | cinétique du givrage |
| `perte_debit` | [secheur.md](secheur.md) | `fraction` | F10, F13 | – |
| `reservoir_air` | [reservoir_air.md](reservoir_air.md) | `K_global`, `paroi` (Dormoy), `adiabatique` (Shi) ; `surpression_entree` | F11, F12, F38 | caverne (Tola, Wang), fuites, isobare (Pimm) |
| `stockage_chaleur` | [stockage_chaleur.md](stockage_chaleur.md) | `gravier` (Schumann, Tola), `huile_deux_reservoirs` (Tola, Wolf et Budt), `eau_sous_pression` (Shi), `huile_ideale` (Dormoy), `source_externe` ; bloc `isolation` (Ablaoui) | F25 à F31, F40, F41 | matériau à changement de phase (Zhang Z.) |
| `detente` | [detente.md](detente.md) | `isenthalpique`, `cheayb` (Dormoy), `isotherme` (diagnostic), `pression_glissante` (Shi, Zhang S.) | F15, F16, F39 | vanne ON/OFF et tampon (Zhang S.), éjecteur, tuyères |
| `turbine` | [turbine.md](turbine.md) | `polytropique_deprag` (Dormoy), `isentropique` (Shi, Zhang S.), `polytropique_rendement` (Tola), `flugel` (Zhang S.) | F17, F18, F34, F35, F39 | données hors point nominal d'une petite turbine |
| `attente` | [attente.md](attente.md) | `pertes_statiques`, `sans_pertes` | F12, F29, F41 | ponts thermiques |

## L'interface commune

Un composant reçoit un **état de l'air** (`EtatAir` : pression absolue en Pa, température en K, débit massique en kg/s, eau en vapeur et en liquide par kg d'air, F42) et un **contexte** (`Contexte` : propriétés de l'air, ambiance, instant, pas de temps, pression de refoulement de la chaîne). Il rend le nouvel état et un **flux** (`Flux`) : travail reçu ou produit, chaleur ajoutée avec l'étiquette de sa source, chaleur retirée avec sa destination, débit perdu, perte de charge, et l'objet détaillé du modèle physique.

| Méthode | Qui | Rôle |
|---|---|---|
| `pas(etat, ctx)` | refroidisseur, sécheur, perte de débit, détente, étage de compresseur ou de turbine | transformer l'air pendant un pas |
| `charger_air(etat, ctx)` | stockage de chaleur | recevoir la chaleur de l'air chaud (charge) |
| `rechauffer(etat, ctx, T_cible)` | stockage de chaleur | réchauffer l'air avant une turbine, au plus jusqu'à la cible |
| `remplir`, `vider`, `attendre` | réservoir d'air | bilans de masse et d'énergie |
| `preparer(p_reservoir, p_amb, surpression)` | compresseur | fixer la pression de refoulement du pas |
| `debit(p_disponible)` | turbine | débit du pas (variable avec le modèle `flugel`) |
| `executer(ctx, reservoir, stockages)` | attente | faire passer le temps |
| `verifier_validite()` | tous | vérifications statiques des paramètres |
| `avertir(message)` | tous | signaler, pendant le calcul, une sortie du domaine de validité |
| `mettre_a_l_equilibre(etat, flux, composant)` | tous (fonction de `humidite.py`) | remettre l'eau à l'équilibre vapeur / liquide après une transformation ; condensation, évaporation, givre (F43) |

Règles communes : unités SI en interne ; aucun chiffre en dur (tout vient du scénario, avec sa provenance) ; la seule source de température et de pression extérieures est l'ambiance du contexte (F32) ; toute chaleur ajoutée à l'air porte une étiquette de source (nom du stockage ou `externe`) ; un avertissement n'arrête jamais la simulation mais apparaît dans `resume.md` ; une sortie du domaine où le modèle a un sens (par exemple une détente jusqu'à la condensation de l'air) lève `HorsDomaine`, que la simulation transforme en arrêt propre et signalé.

## Ajouter un modèle ou un composant

1. Écrire la fiche de la formule dans `docs/formules.md` (format en bas de ce fichier) et mettre ses paramètres au registre avec leur niveau de preuve (référence avec DOI vérifié).
2. Mettre la physique dans `caes/composants/<type>/<modele>.py` (fonctions pures, testables seules) et brancher le modèle dans la classe du type (`MODELES`, branche dans `pas` ou équivalent) ; ou créer une classe qui hérite de `Composant` et l'inscrire dans `FABRIQUES` (`caes/composants/__init__.py`).
3. Écrire les tests (`tests/test_modeles_phase7.py` comme exemple) : bilan de masse et d'énergie, cas limite (rendement 1, pression égale, réservoir vide), avertissement hors domaine ; ajouter le modèle aux combinaisons de `tests/test_combinaisons.py` ; vérifier que la non-régression passe.
4. Ajouter un bloc dans `scenarios/variantes/generer_variantes.py` (un scénario d'exemple dérivé de Dormoy) et régénérer.
5. Compléter la page `docs/composants/<type>.md` (tableau des modèles : physique, paramètres, source, quand l'utiliser) et, quand des données existent, une ligne dans le tableau de bord de validation (phase 8).
