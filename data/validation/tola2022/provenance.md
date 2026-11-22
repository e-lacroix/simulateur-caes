# Jeu de validation : Tola et al. 2022 (LT-ACAES de 10 MW, lit de gravier)

**Article.** Tola V., Marcello F.C., Cocco D., Cau G. (2022), *Performance Assessment of Low-Temperature A-CAES (Adiabatic Compressed Air Energy Storage) Plants*, Journal of Thermal Science 31(5), 1279-1292, https://doi.org/10.1007/s11630-022-1632-7. PDF : `../Études/études/tola2022.pdf`. Registre : `tola2022`, paramètres `tola.*`.

**Nature.** Simulation seulement (MATLAB-Simulink), aucune mesure : **vérification croisée**, pas validation. Trois configurations (A : boucle d'air et gravier à 1 bar, pincement 20 K ; B : boucle d'huile Therminol 66, pincement 10 K ; C : gravier traversé directement par l'air comprimé).

| Donnée | Où | Ce qu'elle teste |
|---|---|---|
| Cuves de gravier du cas C (tableaux 3, 4, 8) : 3 × 220,8 m³, 12,3 / 24,5 kg/s, 170 / 35 °C, 9,60 / 9,54 / 9,54 MWh stockés, régime stable en moins de 20 cycles, sortie constante pendant ≈ 2/3 de chaque phase | `tola.tes*.*`, `materiau.gravier_tola.*` | lit de gravier (modèle de Schumann, phase 4) |
| Compresseurs (tableaux 1, 7) : rendement polytropique 0,88, 170 °C de sortie, 12,35 kg/s ; puissances 1,98 / 1,73 / 1,72 / 0,79-1,55 MW ; 39,76 MWh sur 6 h | `tola.compresseur.*` | compresseur polytropique à rendement, pincement 20 K |
| Turbines (tableaux 6, 9, 10) : rendement polytropique 0,86, 130 / 150 / 170 °C selon le cas, 24,5 kg/s ; 23,92 / 26,82 / 28,48 MWh sur 3 h ; puissance maximale 8,3 / 9,5 / 10,0 MW | `tola.turbine.*` | turbine polytropique à rendement, pression glissante à répartition égale |
| Rendement aller-retour (tableau 10) : 0,566 / 0,635 / 0,674 | `tola.rte.cas_*` | chaîne complète |
| Caverne (§ 2.2, § 3.2) : 6500 m³, 6,4 à 10 MPa, 15 à 55 °C, 470 à 735 t d'air | `tola.cave.*` | réservoir |

**Ce que Tola ne publie pas** : la corrélation d'échange air-gravier, les pertes des cuves, le modèle thermique de la caverne, la répartition des rapports entre les trois turbines (« shared out ») : autant d'hypothèses de notre côté (Wakao, isolation parfaite, caverne adiabatique, répartition égale), signalées dans le tableau de bord.

**Ambiance.** 15 °C et 0,101 MPa (tableau 1) ; humidité non donnée (hypothèse du projet).

**Incohérence relevée.** Le texte de la conclusion donne « légèrement inférieur à 0,65 » pour le cas C, le tableau 10 donne 0,674.

**Fichiers.** `references.csv` : généré par `validation/tableau_de_bord.py` à partir du registre.
