# Figures de Dormoy (2024) à numériser

*Phase 0. Les auteurs ne partagent pas leurs données brutes : les courbes de l'article sont la seule façon de comparer notre simulateur à leurs mesures, point par point. La numérisation est faite par l'élève avec WebPlotDigitizer (voir la fin de ce fichier). Déposer chaque CSV dans `data/validation/dormoy/`.*

## Priorités

| Priorité | Figure | Ce qu'on en tire | Phase |
|---|---|---|---|
| 1 | **Fig. 10** : puissance électrique et énergie cumulée pendant la charge (mesure et simulation) | Puissance (kW) et énergie (kWh) en fonction du temps. Validation principale de la phase 1 (396 kWh, 39 kW, ≈ 10 h) | 1 |
| 1 | **Fig. 8** : rapport de compression de chaque étage en fonction de la pression du réservoir | Les 4 courbes. Entrée du modèle de compresseur (étages 3 et 4 varient avec la pression, au-dessus de 60 bar) | 1 |
| 1 | **Fig. 9** : température de sortie de l'étage 4, avant et après calibration, avec la mesure | Courbe **mesurée** en priorité ; les deux courbes simulées servent à vérifier qu'on retrouve l'effet de l'indice 1,59 → 1,52 | 1 |
| 2 | **Fig. 18** : températures d'entrée et de sortie des 4 refroidisseurs pendant la charge | 8 courbes. Validation des refroidisseurs NTU et base du calcul de chaleur récupérable (tableau 6) | 1, 5 |
| 2 | **Fig. 11** : effet de la température ambiante sur la charge (débit, durée, énergie) | Tendance −15 → 25 °C : 0,065 → 0,056 kg/s | 2 |
| 2 | **Fig. 12** : effet de la température ambiante sur la décharge, avec et sans réchauffage | Énergie produite 27 → 22 kWh, RTE 6,3 → 5,4 % | 2 |
| 2 | **Fig. 13** : effet de la pression maximale (75–300 bar) sur la décharge | Optimum à 150 bar (réchauffé) et 125 bar (non réchauffé) | 2 |
| 3 | **Fig. 14** : effet de l'indice polytropique sur la charge | Puissance et énergie quand n → 1 | 2 |
| 3 | **Fig. 15** : effet de l'indice polytropique sur la décharge | 17,9 kWh sans, 22,8 kWh avec réchauffage à n = 1 | 2 |
| 3 | **Fig. 16** : effet du nombre d'étages de détente (1 à 3) | RTE 5,5 → 16,0 % ; durées de charge et de décharge | 2 |

Il n'y a **pas** de figure de l'essai de décharge mesuré (190 → 50 bar en 38 min). Seuls les chiffres du § 3.1 et les erreurs du tableau 4 sont disponibles pour la phase 2.

## Format des fichiers CSV

Un fichier par courbe, nommé `figNN_<courbe>.csv`, par exemple `fig10_puissance_mesuree.csv`, avec une ligne d'en-tête et un commentaire de source :

```text
# Dormoy 2024, fig. 10, courbe « experimental power », numérisée le AAAA-MM-JJ par <prénom>, WebPlotDigitizer 4.x
temps_h,puissance_kW
0.00,36.1
0.25,36.4
...
```

Règles :

- unités de la figure dans l'en-tête (`temps_h`, `pression_bar`, `temperature_degC`) ; le simulateur convertit en SI ;
- au moins 30 points par courbe, davantage dans les zones courbées ;
- noter l'incertitude de lecture estimée (par exemple ± 0,5 °C, ± 1 bar) dans le commentaire ;
- le registre reçoit ensuite une ligne par fichier, niveau de preuve `mesure` (courbe mesurée) ou `simulation_publiee` (courbe simulée par Dormoy), avec la mention « numérisée ».

## Comment numériser avec WebPlotDigitizer

1. Ouvrir https://automeris.io/WebPlotDigitizer (version en ligne, gratuite) ou installer l'application.
2. Capturer la figure : ouvrir `dormoy.pdf` à la bonne page, zoomer au maximum, faire une capture d'écran nette (ou exporter la page en PNG à 300 ppp).
3. `File → Load Image`, puis choisir `2D (X-Y) Plot`.
4. **Calibrer les axes** : cliquer sur deux points connus de l'axe X (par exemple 0 h et 10 h) et deux points de l'axe Y, puis saisir leurs valeurs. Cocher « Log scale » seulement si l'axe est logarithmique (aucun chez Dormoy).
5. Choisir la couleur de la courbe à numériser (`Automatic Extraction → Color`) ou cliquer les points à la main (`Manual`). Pour des courbes qui se croisent, la méthode manuelle est plus sûre.
6. `View Data → Download CSV`. Renommer et ajouter la ligne de commentaire de source.
7. **Vérifier** : rouvrir le CSV, tracer les points avec Python ou un tableur et les comparer à l'œil avec la figure. Vérifier aussi une valeur donnée dans le texte (par exemple 396 kWh à la fin de la fig. 10).

Astuce : commencer par la fig. 10 (deux courbes simples) pour prendre la main, puis la fig. 8.
