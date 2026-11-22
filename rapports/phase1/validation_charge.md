# Validation de la charge sur Dormoy (2024)

*Généré par `validation/dormoy_charge.py`. Références : registre (`data/registre/parametres.csv`). Toute valeur « Dormoy » est une mesure du § 3.1 sauf mention « simulation ».*

## 1. Scénarios comparés

| Code | Scénario | Air aspiré | Débit aspiré | Débit vers réservoirs |
|---|---|---|---|---|
| A | `dormoy_charge_1_190` | 20 °C | 0.0520 kg/s | 0.0350 kg/s |
| B | `dormoy_charge_1_190_aspiration_chaude` | 52 °C | 0.0520 kg/s | 0.0350 kg/s |
| C | `dormoy_charge_1_190_debit_mesure` | 20 °C | 0.0520 kg/s | 0.0320 kg/s |
| D | `dormoy_charge_1_190_aspiration_chaude_debit_mesure` | 52 °C | 0.0520 kg/s | 0.0320 kg/s |

Le scénario A applique les hypothèses minimales : tout à 20 °C (l'article ne donne pas la température ambiante), débit aspiré mesuré imposé (0,052 kg/s), débit vers les réservoirs égal au produit des rendements volumétrique (83 %) et du sécheur (81 %). Le scénario B déduit la température d'aspiration du débit mesuré : 0,052 kg/s à 172,4 m³/h et 1,013 bar correspond à de l'air à 52 °C, ce qui est plausible pour un compresseur qui aspire l'air d'un conteneur qu'il réchauffe. C et D imposent le débit mesuré à la sortie du sécheur (0,032 kg/s) au lieu de 0,035 kg/s.

## 2. Essai de charge complet, 1 → 190 bar

| Grandeur | Dormoy | Scénario | Simulé | Écart | Explication |
|---|---|---|---|---|---|
| Énergie consommée | 396 kWh | A | 373.0 kWh | -5.8 % | voir § 2.1 |
| Énergie consommée | 396 kWh | B | 386.2 kWh | -2.5 % | voir § 2.1 |
| Énergie consommée | 396 kWh | C | 408.6 kWh | +3.2 % | voir § 2.1 |
| Énergie consommée | 396 kWh | D | 423.1 kWh | +6.8 % | voir § 2.1 |
| Durée | ≈ 10 h | A | 9.89 h | -1.1 % | la durée dépend seulement du débit vers les réservoirs et de la température finale |
| Durée | ≈ 10 h | B | 9.89 h | -1.1 % | la durée dépend seulement du débit vers les réservoirs et de la température finale |
| Durée | ≈ 10 h | C | 10.83 h | +8.3 % | la durée dépend seulement du débit vers les réservoirs et de la température finale |
| Durée | ≈ 10 h | D | 10.83 h | +8.3 % | la durée dépend seulement du débit vers les réservoirs et de la température finale |
| Puissance moyenne | 39 kW | A | 37.7 kW | -3.3 % | dépend du débit aspiré, des indices n et des rendements |
| Puissance moyenne | 39 kW | B | 39.1 kW | +0.2 % | dépend du débit aspiré, des indices n et des rendements |
| Puissance moyenne | 39 kW | C | 37.7 kW | -3.3 % | dépend du débit aspiré, des indices n et des rendements |
| Puissance moyenne | 39 kW | D | 39.1 kW | +0.2 % | dépend du débit aspiré, des indices n et des rendements |
| Énergie consommée (simulation de Dormoy, cas de base) | 366.75 kWh | A | 373.0 kWh | +1.7 % | notre modèle est comparé ici au modèle de Dormoy, pas à la mesure |

### 2.1 Lecture des écarts

- **Énergie et puissance.** Le scénario A (hypothèses minimales) donne 373 kWh, soit -5.8 % par rapport à la mesure, mais seulement +1.7 % par rapport à la **simulation** de Dormoy (366,75 kWh). L'écart entre notre modèle et celui de Dormoy est donc petit ; l'écart avec la mesure est en grande partie celui que Dormoy a lui-même (−7,4 %).
- **La durée** ne dépend que du débit vers les réservoirs et de la température de l'air stocké. Avec le débit calculé (0,035 kg/s) la charge dure 9.9 h ; avec le débit mesuré (0,032 kg/s) elle dure 10.8 h. Les deux encadrent les « presque 10 h » de l'article.
- **Température d'aspiration.** Le scénario B (52 °C) relève la puissance de 37.7 à 39.1 kW, ce qui tombe sur les 39 kW mesurés. Ce n'est pas un ajustement : la valeur 52 °C est imposée par le débit massique mesuré et la cylindrée du compresseur (voir § 4, chaleur, pour une seconde confirmation indépendante).
- **Température finale du réservoir.** Le modèle donne 29 °C en fin de charge. Dormoy mesure 55 °C au début de l'essai de décharge, mais rien n'indique que cet essai a suivi immédiatement la charge complète, et le réservoir de l'essai de décharge (2,56 m³) n'est pas le même. Écart à surveiller en phase 2 ; la courbe de température mesurée n'est pas publiée.

## 3. Rapports de compression et températures

| Grandeur | Dormoy | Simulé (A) | Simulé (B) | Remarque |
|---|---|---|---|---|
| Rapport étage 3, à 190 bar | 4,44 (fig. 8) | 4.44 | 4.44 | borne du registre, imposée par la loi linéaire |
| Rapport étage 4, à 190 bar | 3,5 (texte) / 3,50 (tabl. 7) | 3.47 | 3.47 | **calculé** : reste du rapport total ; concorde |
| Rapport étage 4, à basse pression | 1,52 (texte) / 1,63 (tabl. 7) | 1.51 | 1.51 | fixé par la pression de refoulement minimale (66 bar, calcul personnel) |
| Sortie compression étage 1, fin de charge | ≈ 160 (fig. 9/18) °C | 124 °C | 168 °C | B concorde, A est trop froid : l'air aspiré à 20 °C ne chauffe qu'à 124 °C |
| Sortie compression étage 2, fin de charge | 185–200 (fig. 18) °C | 174 °C | 185 °C | B plus proche |
| Sortie compression étage 3, fin de charge | 190–220, > 200 après 3 h (fig. 18) °C | 215 °C | 218 °C | concorde |
| Sortie compression étage 4, fin de charge | jusqu'à ≈ 200 en fin de charge (fig. 9) °C | 175 °C | 175 °C | A et B concordent entre eux ; l'écart avec la fig. 9 dépend de la loi n = 1,52 et de l'efficacité du refroidisseur 3 |
| Sortie refroidisseur 4, fin de charge | 45–60 (fiche) °C | 43 °C | 43 °C | un peu froid : efficacité 85 % avec source froide à 20 °C |

Les valeurs « Dormoy » de ce tableau sont lues sur les figures de l'article (approximatives). La comparaison point par point attend les courbes numérisées (§ 6).

## 4. Chaleur rejetée par les refroidisseurs, charge 55 → 190 bar

Dormoy (tableau 6, simulation) calcule la chaleur récupérable au-dessus de 130 °C pendant une recharge de 55 à 190 bar, avec un débit de 0,052 kg/s.

| Grandeur | Dormoy (simulation) | A : base | B : aspiration 52 °C |
|---|---|---|---|
| Durée | 6.8 h | 6.86 h (+0.9 %) | 6.86 h (+0.9 %) |
| Chaleur totale rejetée | 189.2 kWh | 174.2 kWh (-7.9 %) | 191.6 kWh (+1.2 %) |
| Chaleur au-dessus de 130 °C, total | 72.2 kWh | 47.5 kWh (-34.2 %) | 66.4 kWh (-8.1 %) |
| … dont refroidisseur 1 | 12.5 kWh | 0.0 kWh | 13.7 kWh |
| … dont refroidisseur 2 | 23.4 kWh | 16.0 kWh | 20.1 kWh |
| … dont refroidisseur 3 | 30.0 kWh | 25.8 kWh | 26.7 kWh |
| … dont refroidisseur 4 | 6.3 kWh | 5.7 kWh | 5.8 kWh |

Le scénario A ne récupère **rien** à l'étage 1 (l'air n'y dépasse pas 130 °C), alors que Dormoy y trouve 12,5 kWh. Le scénario B, dont la seule différence est l'air aspiré à 52 °C, retrouve l'ordre de grandeur de chaque étage et la chaleur totale à +1.2 %. C'est la confirmation indépendante annoncée au § 2.1 : dans le modèle de Dormoy, l'air entre dans le compresseur à environ 50 °C. La chaleur « au-dessus de 130 °C » reste sous-estimée de 8 %, surtout aux étages 2 et 3 : les températures de sortie de ces étages dépendent de la température de l'air de refroidissement (20 °C supposés) et de la répartition des rapports entre les étages 3 et 4, deux hypothèses à confronter aux figures 8 et 18 numérisées.

## 5. Bilan d'énergie (scénario A, 1 → 190 bar)

| Poste | kWh | % de l'électricité |
|---|---|---|
| Pertes mécaniques et électriques du compresseur | 123.9 | 33.2 % |
| Chaleur rejetée pendant la compression (n < γ) | 6.9 | 1.8 % |
| Chaleur retirée par les 4 refroidisseurs | 240.8 | 64.6 % |
| Enthalpie de l'air rejeté (volumétrique + sécheur) | 0.5 | 0.1 % |
| Chaleur perdue par les réservoirs | 40.2 | 10.8 % |
| Énergie stockée dans l'air (relative à l'air aspiré) | -39.2 | -10.5 % |
| **Total** | **373.0** | **100.0 %** (résidu 0.0000 %) |

L'énergie « stockée dans l'air » est comptée par rapport à l'enthalpie de l'air aspiré : elle est négative parce que l'air stocké finit à peu près à la température ambiante, avec une énergie interne massique plus faible que l'enthalpie de l'air entré (c'est le bilan d'énergie du premier principe ; l'énergie **utile** de l'air comprimé est une exergie, calculée en phase 3).

## 6. Courbes numérisées

| Fichier | Scénario | RMSE | MAPE |
|---|---|---|---|
| `fig10_puissance_mesuree.csv` | absent | – | – |
| `fig10_energie_mesuree.csv` | absent | – | – |
| `fig09_T_sortie_etage4_mesuree.csv` | absent | – | – |

Aucune courbe n'était numérisée à la date de ce rapport : voir `data/validation/dormoy/A_NUMERISER.md` (fig. 10, 8 et 9 en priorité).

## 7. Hypothèses propres au modèle (niveau « hypothese » ou « calcul_personnel »)

| Paramètre | Valeur | Provenance |
|---|---|---|
| `ambiance.T_amb` | 293.15 | ambiance.T_amb_essai_charge [hypothese, dormoy2024, §3.1] |
| `ambiance.T_aspiration` | 293.15 | ambiance.T_amb_essai_charge [hypothese, dormoy2024, §3.1] |
| `ambiance.p_amb` | 101325 | ambiance.p_amb_essai [hypothese, dormoy2024, §3.1] |
| `compresseur.pression_refoulement_min` | 6.6e+06 | compresseur.pression_refoulement_min [calcul_personnel, dormoy2024, §3.1 ; fig. 8] |
| `compresseur.rendement_volumetrique` | 0.83 | compresseur.rendement_volumetrique [calcul_personnel, dormoy2024, §3.1 ; tableau 7 (supp.)] |
| `reservoir.T_initiale` | 293.15 | ambiance.T_amb_essai_charge [hypothese, dormoy2024, §3.1] |
| `reservoir.capacite_thermique_paroi` | 1.767e+06 | reservoir.capacite_thermique_paroi [calcul_personnel, dormoy2024supp, tableau 8] |
| `reservoir.surface` | 65.52 | reservoir.surface_equivalente_totale [calcul_personnel, dormoy2024, éq. 12 ; tableau 8 (supp.)] |
| `simulation.dt` | 10 | scénario : 10 s (choix numérique ; l'écart avec dt = 1 s est inférieur à 0,1 % (tests)) |
| `simulation.duree_max` | 86400 | scénario : 24 h (garde-fou contre une boucle infinie) |
| `compresseur.loi_rapport_etage3` | linéaire en pression de refoulement, de 3,54 à p_refoulement_min jusqu'à 4,44 à 190 bar | hypothese, Dormoy dit « linear increase beyond the 60-bar threshold ». La pente exacte sera lue sur la fig. 8 numérisée. L'étage 4 prend le reste du rapport total. |
| `compresseur.loi_rendement_mecanique` | linéaire en pression de refoulement, de 69 % à p_refoulement_min jusqu'à 74 % à 190 bar | hypothese, Dormoy donne seulement la plage 69-74 % « depending on reservoir pressure », sans le sens de variation. Hypothèse : croissant (meilleur rendement à forte charge). À confronter à la fig. 10. |
| `refroidisseur.loi_efficacite_etage4` | linéaire en pression de refoulement, de 74 % à p_refoulement_min jusqu'à 85 % à 190 bar | hypothese, Dormoy : « efficiency scaling alongside reservoir pressure », sans la loi exacte. |

## 8. Graphiques

![fig1_puissance.png](fig1_puissance.png)

![fig2_energie.png](fig2_energie.png)

![fig3_pression.png](fig3_pression.png)

![fig4_T_reservoir.png](fig4_T_reservoir.png)

![fig5_T_etages_B.png](fig5_T_etages_B.png)

![fig6_T_etages_A.png](fig6_T_etages_A.png)

![fig7_rapports.png](fig7_rapports.png)

## 9. Conclusion

- Le critère de sortie de la phase 1 (écart < 5 % sur l'énergie et la durée) est **atteint par le scénario B** (−2,5 % et −1,1 %). Le scénario A le manque de peu sur l'énergie (−5,8 %), en grande partie à cause des 7 % d'écart que Dormoy a lui-même entre sa simulation et sa mesure ; par rapport au modèle de Dormoy, A est à +1,7 %. Les scénarios C et D (débit mesuré de 0,032 kg/s) rallongent la charge à 10,8 h : le « presque 10 h » de l'article est trop imprécis pour trancher entre 0,032 et 0,035 kg/s ; la courbe de la fig. 10, une fois numérisée, le permettra.
- L'hypothèse la plus utile dégagée par la validation : l'air aspiré par le compresseur est à ≈ 50 °C, pas à l'ambiant. Elle découle du débit mesuré et explique à la fois la puissance (39 kW) et la chaleur récupérable par étage.
- Points ouverts : la loi de variation des rapports des étages 3 et 4 (fig. 8), la température de l'air de refroidissement, et la température finale du réservoir (pas de mesure publiée).
