# Jeu de validation : Dormoy et al. 2024 (banc ÉTS / Hydro-Québec, 190 bar)

**Article.** Dormoy E., Le Lostec B., Haillot D. (2024), *Aboveground compressed air energy storage systems: Experimental and numerical approach*, Energy Conversion and Management 321, 119073, https://doi.org/10.1016/j.enconman.2024.119073 (CC BY-NC). Données supplémentaires (tableaux 7, 8, 9) : `data/sources/dormoy-supplementaire/`. Registre : `dormoy2024`, `dormoy2024supp`.

**Nature.** Le seul jeu **mesuré** disponible aujourd'hui, plus des simulations publiées par les auteurs (leur modèle est calibré sur leurs mesures, MAPE < 3,6 % sur la charge, < 1,1 % sur le réservoir en décharge).

| Donnée | Nature | Où | Ce qu'elle valide |
|---|---|---|---|
| Essai de charge 1 → 190 bar : 396 kWh, ≈ 10 h, 39 kW | mesure (§ 3.1) | `essai_charge.*` | compresseur, refroidisseurs, sécheur, réservoir (chaîne de charge) |
| Essai de décharge 190 → 50 bar, 2,56 m³, 38 min, 0,148 kg/s | mesure (§ 3.1) | `essai_decharge.*` | réservoir en décharge (modèle à paroi), détendeur |
| Turbine DEPRAG, tableau 9 : températures de sortie et puissances par étage | fabricant (données supplémentaires) | `turbine.etageN.*` | turbine à point nominal |
| Charge 55 → 190 bar : 6,8 h, 189,2 kWh rejetés dont 72,2 au-dessus de 130 °C | simulation publiée (tableau 6, § 3.3.5) | `charge_55_190.*`, `refroidisseur.*` | chaleur des refroidisseurs |
| Chaleur de réchauffage à 3 étages : 46,2 kWh (24,8 / 6,4 / 15,0) sur 40 min | simulation publiée (tableau 5) | `turbine.etageN.puissance_chaleur_requise` | réchauffage, décharge à 3 étages |
| Cas de base : 16,93 kWh, 4,3 % ; 3 étages : 16 % | simulation publiée (§ 3.3, § 3.3.4) | `cas_base.*`, `cas_etages.*` | décharge complète |

**Ambiance.** L'article ne donne ni la température ambiante ni l'humidité : 20 °C, 1,013 bar et 50 % sont des hypothèses du projet (`ambiance.*`, niveau `hypothese`). L'air aspiré par le compresseur est déduit du débit mesuré (52 °C, phase 1). Toute validation faite ici vaut pour ces conditions, pas pour l'hiver.

**Courbes numérisées.** Aucune encore : `A_NUMERISER.md` liste les figures à numériser (fig. 8, 9, 10, 18 en priorité) et le format attendu. Le harnais `validation/tableau_de_bord.py` et `validation/dormoy_charge.py` intègrent automatiquement les CSV déposés ici (`fig10_puissance_mesuree.csv`, `fig10_energie_mesuree.csv`, `fig09_T_sortie_etage4_mesuree.csv`).

**Incertitudes.** Valeurs du texte arrondies (« almost 10 h », 396 kWh, 38 min) ; incohérences internes listées dans `JOURNAL.md` (phase 0 et phase 2 : volume 5,80 contre 5,86 m³, 62 kW × 40 min ≠ 16 % de 290 kWh, 4,3 % contre 4,6 %).

**Fichiers.** `references.csv` : généré par `validation/tableau_de_bord.py` à partir du registre (grandeur, valeur, unité, localisation, niveau de preuve).
