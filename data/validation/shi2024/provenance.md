# Jeu de validation : Shi et al. 2024 (A-CAES de 100 MW, prépublication)

**Article.** Shi W., Liang Y., Ding R., Su W., Lin X., Wang J. (2024), *Thermal-economic performance analysis of AA-CAES system with multi-objective optimization*, SSRN 5042640, https://ssrn.com/abstract=5042640. **Prépublication non révisée par les pairs** : à signaler à chaque usage. PDF : `../Études/études/others/aa-caes/aa-caes.pdf`. Registre : `shi2024`, paramètres `shi.*`.

**Nature.** Simulation seulement (MATLAB + REFPROP), aucune mesure. Ce jeu ne **valide** rien : c'est un **cas test** de changement d'échelle (100 MW contre 45 kW chez Dormoy) qui vérifie que les mêmes équations, avec les hypothèses de Shi (rendements constants, réservoir adiabatique, pincement 10 K, eau sous pression), redonnent ses résultats. Critère du plan : < 2 %.

| Donnée | Où | Ce qu'elle teste |
|---|---|---|
| Paramètres de conception (tableau 4) : rendements, PPTD 10 °C, pertes 0,04 et 0,2 MPa, 4 à 10 MPa, 200 °C | `shi.*` | entrées du scénario `scenarios/validation/shi_100MW.yaml` |
| États à 7 MPa (figure 7) : pressions et températures par étage, débits 198,35 / 260,15 kg/s | `shi.compresseur.p_sortie_N`, `shi.turbine.*` | répartition des étages, réchauffeurs à 180 °C |
| Puissances par étage à 7 MPa (§ 5) : 36,23 / 33,14 / 33,15 / 10,27 MW ; 20,44 / 39,80 / 39,77 MW | `shi.compresseur.puissance_N`, `shi.turbine.puissance_N` | compresseur isentropique, turbine isentropique en pression glissante |
| Bilan du cycle (tableau 5) : 887,05 MWh consommés, 600 MWh produits, RTE 67,64 %, 5712,5 t d'air, 4193,7 t d'eau, volume 1,18 × 10⁵ m³, compresseur 4 actif 7,04 h | `shi.energie_*`, `shi.rte`, `shi.masse_*`, `shi.reservoir.volume`, `shi.compresseur4.duree_fonctionnement` | cycle complet |

**Ambiance.** 25 °C et 0,1 MPa (tableau 4, figure 7) ; eau froide à 30 °C ; humidité non donnée (hypothèse du projet, 50 %).

**Lecture des figures.** Les états de la figure 7 ont été lus dans le texte extrait du PDF (valeurs imprimées sur le schéma), pas numérisés : incertitude de l'arrondi imprimé (0,01 MPa, 1 °C).

**Fichiers.** `references.csv` : généré par `validation/tableau_de_bord.py` à partir du registre.
