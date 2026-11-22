# Ajouter une étude ou un jeu de données

*Procédure des consignes communes du projet, à suivre à chaque nouvel article ou nouvelle fiche de fabricant. Deux exemples du dépôt : Shi 2024 (jeu de validation complet, phase 8) et Ablaoui 2023 (un paramètre, la laine minérale, phase 7).*

## 1. Lire et résumer : la fiche d'étude (`../Études/études/others/<etude>/`)

Trois fichiers, pour l'élève et pour le chercheur : `resume-*.md` (ce que dit l'étude, en langage simple), `maths-*.md` (les équations, avec les symboles), `pistes-simulation.md` (ce que l'étude apporte, ses limites, ses données réutilisables, ce qu'on peut confirmer, explorer, informer, améliorer). Les calculs faits par nous sont marqués « calcul personnel ». Ces fiches ne se modifient pas sans l'accord de l'utilisateur.

Règle absolue : **aucune source sans DOI vérifié ou PDF lu**. Si l'article est payant, le noter dans `JOURNAL.md` et proposer BAnQ ou un courriel aux auteurs ; un PDF en accès libre que le site refuse aux robots est déposé à la main dans `data/sources/<source>/` ; jamais de téléchargement illégal. Une prépublication non révisée se signale à chaque usage (Shi).

## 2. Mettre au registre (`data/registre/generer_registre_phase0.py`)

- **Référence** : une ligne dans la liste `references` (identifiant court `auteur+année`, auteurs, année, titre, revue, DOI ou URL, type, accès, fichier local, notes). Le DOI est vérifié (il résout vers le bon titre) et la date de vérification est notée.
- **Paramètres** : un appel `p(...)` par nombre réutilisé, avec l'unité de la source (le code convertit en SI), la localisation exacte (tableau, figure, section), les conditions et le **niveau de preuve** : `mesure`, `fabricant`, `calibration`, `simulation_publiee`, `calcul_personnel`, `hypothese`. Une plage (`vmin`, `vmax`) quand l'article en donne une ; elle sert à la propagation des incertitudes (phase 10).
- Régénérer : `python -I data/registre/generer_registre_phase0.py` (affiche le nombre de références et de paramètres, refuse les doublons).

Exemple (Ablaoui 2023, laine minérale, phase 7) :

```python
p("materiau.laine_minerale.conductivite",
  "Conductivité thermique de la laine minérale à 20 °C (densité > 26 kg/m3)",
  0.036, "W/mK", "ablaoui2023", "tableau 1 (projet d'Eurocode, réf. [19])",
  "fabricant", "20 °C", vmin=0.03, vmax=0.046)
```

## 3. Trois issues possibles

**a) Un composant ou une variante** (l'étude apporte un modèle) : suivre `ajouter-un-composant.md`. Exemples : pression glissante et Flügel (Zhang S.), eau sous pression (Shi), isolant (Ablaoui).

**b) Un jeu de validation** (l'étude apporte des chiffres à reproduire) : un dossier `data/validation/<source>/` avec `provenance.md` (nature des données : mesure, simulation publiée, fabricant ; conditions ambiantes de l'article ; ce qui a été numérisé ou transcrit et comment ; ce qui manque) et `references.csv` généré depuis le registre ; un scénario dans `scenarios/validation/<source>.yaml` qui reproduit l'installation de l'article avec les composants de la bibliothèque (chaque valeur vient du registre) ; une fonction `cas_<source>()` dans `validation/tableau_de_bord.py` qui ajoute les lignes (grandeur, valeur publiée, valeur simulée, écart, verdict). Un écart > 5 % reçoit un paragraphe dans `EXPLICATIONS` ou la mention « non expliqué » ; **on ne calibre jamais pour faire disparaître un écart**. Les courbes à numériser sont listées dans `A_NUMERISER.md` du dossier.

Exemple (Shi 2024, phase 8) : `scenarios/validation/shi_100MW.yaml` (compresseurs isentropiques, eau sous pression, réservoir adiabatique, pression glissante), `cas_shi()` avec quinze lignes (compresseurs, turbines, durées, masse, rendement) ; sept reproduites, huit expliquées (réservoir adiabatique, quatrième refroidisseur, surpression non justifiée par le tableau 4 de l'article) ; signalée « prépublication non révisée ».

**c) Un paramètre seulement** (l'étude donne une propriété, un coût, une fiche technique) : registre, puis usage dans un scénario ou un rapport avec `registre:<id>`. Exemples : fiche Megapack et fiche D100 GC (phase 11), rapport NREL (coûts).

## 4. Dire ce que l'étude ne couvre pas

Ajouter une ligne dans le tableau « limites des études → réponse du simulateur » (`docs/limites-couvertes.md`, et section 2 de `plan-v2.md` avec l'accord de l'utilisateur) : la limite reconnue ou relevée, ce que le simulateur en fait, la phase. Les erreurs ou incohérences trouvées dans la publication vont dans la liste de la même page et dans les `notes` du registre : les lire de près fait partie du travail.

## 5. Fermer

- `python -m pytest -q` : tout vert (le tableau de bord a ses tests ; une ligne de validation nouvelle est couverte par `tests/test_tableau_de_bord.py`).
- `python validation/tableau_de_bord.py` : le tableau se régénère avec la nouvelle ligne.
- Entrée dans `JOURNAL.md` : ce qui est fait, les écarts, les questions ouvertes (PDF manquant, courbe non numérisée, courriel à envoyer).
