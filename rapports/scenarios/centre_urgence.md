# Scénario d'exemple : centre d'urgence à demande variable

*Généré par `rapports/scenarios_centre_urgence.py` à partir de `scenarios/exemples/centre_urgence/module.yaml` (un module = architecture D isolée, chargée la veille) et de `demande_72h.csv` (profil jour / nuit, hypothèse). Les comparaisons viennent du registre (fiches Tesla 2020 et Caterpillar 2020, rapport NREL 2023, Bazdar via Dormoy).*

**Question.** Tenir 7.2 MWh sur 72 h (100 kW en moyenne, 120 kW le jour, 60 kW la nuit) avec des modules d'air comprimé chargés d'avance. Combien en faut-il, que pèsent-ils, et est-ce raisonnable face aux solutions existantes ?

## 1. Un module

| Module | Électricité pour le charger (kWh) | Électricité livrée (kWh) | Durée de décharge (min) | Puissance nominale (kW) | Rendement | Air rejeté min (°C) | Masse réservoirs + gravier (t) |
|---|---|---|---|---|---|---|---|
| base | 246.3 | 39.32 | 37.8 | 62.4 | 16.0 % | 15 | 3.70 |
| 250 bar | 352.2 | 54.37 | 52.3 | 62.4 | 15.4 % | 8 | 4.11 |
| hiver | 252.6 | 43.77 | 43.8 | 62.4 | 17.3 % | -28 | 3.70 |

La puissance d'un module n'est pas constante : elle suit la pression du réservoir et la température des cuves (figure). La masse compte les 20 bouteilles (F44, à la pression de conception) et le gravier ; compresseur, turbine et échangeurs ne sont pas comptés (non publiés).

## 2. Répartition de la flotte sur la demande (F47)

Règle : à chaque seconde, on démarre un module de plus si la puissance en marche ne couvre pas la demande ; on met le dernier en pause (vanne fermée, air conservé) si l'excédent dépasse la puissance d'un module ; entre les deux, l'excédent est écrêté. Nombre de modules : le plus petit qui fournit au moins 99,9 % de l'énergie demandée.

| Module | Demande | Modules nécessaires | Énergie demandée (MWh) | Fournie | Non servie | Écrêtée | Démarrages | Masse de la flotte (t) | Volume des bouteilles (m³) | Électricité pour charger la flotte (MWh) |
|---|---|---|---|---|---|---|---|---|---|---|
| base | jour / nuit | **192** | 7.20 | 100.0 % | 0.0 kWh | 331.8 kWh | 192 | 710 | 1125 | 47.3 |
| base | constante 100 kW | **229** | 7.20 | 99.9 % | 4.4 kWh | 1775.6 kWh | 229 | 847 | 1342 | 56.4 |
| 250 bar | jour / nuit | **139** | 7.20 | 100.0 % | 0.0 kWh | 339.4 kWh | 139 | 571 | 815 | 49.0 |
| hiver | jour / nuit | **229** | 7.20 | 100.0 % | 0.0 kWh | 2805.8 kWh | 229 | 847 | 1342 | 57.9 |

Borne énergétique : 7200 kWh / 39.3 kWh par module = 183.1 modules ; la répartition en demande 192 parce que la puissance d'un module tombe en fin de décharge et que l'écrêtage en perd un peu.

## 3. Comparaison avec les solutions existantes

| Solution | Unités | Énergie disponible (MWh) | Masse (t) | Volume ou emprise (m³) | Consommable | Coût d'après les sources (M$ US) | Source |
|---|---|---|---|---|---|---|---|
| Modules d'air comprimé (D isolée, 190 bar) | 192 modules | 7.5 | 710 | 1125 (bouteilles seules) | 47 MWh d'électricité pour charger | 1.4 à 1.8 (réservoirs seuls, 200–250 $/kWh) | Dormoy tableau 1 (Bazdar 2022) |
| Batteries lithium-ion en conteneur (Megapack 4 h, 2020) | 3 | 9.2 | 76 | 90 | 8.0 MWh d'électricité pour charger | 1.8 à 2.9 (projection 2030, 245–403 $/kWh) | Tesla 2020, NREL 2023 |
| Génératrices diesel Cat D100 GC (100 kW) + carburant | 2 + 2.23 t de diesel | illimitée tant qu'il y a du carburant | 4.2 | 2.6 m³ de carburant | 2627 L de diesel sur 72 h | non chiffré | Caterpillar 2020 |

Une génératrice fait 100 kW : la pointe de 120 kW en demande 2, qui se partagent la charge ; sous 50 % de charge la consommation est prise à sa valeur de 50 % (prudent). Carburant : 2627 L en 72 h, soit 0.36 L/kWh.

## 4. Qu'est-ce qu'il faudrait pour être viable ?

| Indicateur | Module D isolée | Megapack | Rapport |
|---|---|---|---|
| Électricité livrée par tonne (kWh/t) | 10.6 | 121 | × 11 |
| Électricité livrée par m³ (kWh/m³) | 6.7 | 103 | × 15 |
| Rendement aller-retour | 16.0 % | 90 % | × 5.6 |

Pour qu'une flotte d'air comprimé pèse autant que les batteries qui font le même travail, il faudrait multiplier l'électricité livrée par tonne par 11. Les leviers connus du simulateur (phases 3, 5, 7 et 10) : supprimer le détendeur (pression glissante), monter la pression, réduire les cuves, améliorer le compresseur ; leur somme ne dépasse pas un facteur 2 à 3 sur le rendement. L'air comprimé hors sol n'est pas une solution de secours transportable pour 72 h à cette échelle ; son intérêt est ailleurs : stockage fixe de longue durée, caverne, cogénération de chaleur (phases 4, 8 et scénario 4).

![flotte](centre_urgence_flotte.png)

![module](centre_urgence_module.png)

*3 simulations de module, répartition au pas de 1 s sur 72 h, 68 s.*
