# Validation du lit de gravier (phase 4)

*Généré par `validation/lit_gravier.py`. Modèle : Schumann 1D à deux équations, corrélation de Wakao, correction de Jeffreson, perte de charge d'Ergun (`caes/lit_gravier.py`).*

## 1. Vérification contre la solution analytique de Schumann

Cas test : cuve de 0,5 m × 2 m, gravier de Tola, h imposé à 50 W/m²K, gaz parfait, isolation parfaite, pas de conduction. La solution exacte (fonction J de Goldstein, intégrale de Bessel) donne la température de sortie de l'air en fonction du temps.

| Cellules | Erreur max sur θ de sortie | Énergie stockée |
|---|---|---|
| 10 | 0.1387 | 25.55 kWh |
| 40 | 0.0182 | 26.80 kWh |
| 160 | 0.0009 | 26.94 kWh |

L'erreur décroît comme 1/n : le schéma converge vers la solution exacte. Le bilan d'énergie ferme exactement (chaleur cédée par l'air = chaleur stockée).

## 2. Vérification croisée avec les cuves de Tola (cas C)

Trois cuves de 5.2 m de diamètre et 10.4 m de haut (221 m³), charge de 6 h à 12.3 kg/s et 170 °C, décharge de 3 h à 24.5 kg/s et 35 °C, 20 cycles. Tola : énergie stockée 9,60 / 9,54 / 9,54 MWh, sortie constante pendant environ les deux tiers de chaque phase, régime stable en moins de 20 cycles. Tola ne publie ni sa corrélation d'échange ni ses pertes : isolation parfaite ici.

| Cuve | Pression | Cycle | Chaleur stockée en charge | Chaleur rendue en décharge | Sortie constante (charge) | Sortie constante (décharge) | T sortie fin de décharge | Re | Bi | Δp |
|---|---|---|---|---|---|---|---|---|---|---|
| TES-LP | 3.9 bar | 1 | 10.10 MWh | 9.02 MWh | 99 % | 50 % | 100 °C | 1584 | 0.53 | 5.1 kPa |
| TES-LP | 3.9 bar | 2 | 9.96 MWh | 9.33 MWh | 74 % | 54 % | 117 °C | 1531 | 0.53 | 5.2 kPa |
| TES-LP | 3.9 bar | 5 | 9.67 MWh | 9.57 MWh | 58 % | 58 % | 132 °C | 1489 | 0.54 | 5.3 kPa |
| TES-LP | 3.9 bar | 10 | 9.61 MWh | 9.61 MWh | 57 % | 58 % | 134 °C | 1482 | 0.54 | 5.3 kPa |
| TES-LP | 3.9 bar | 20 | 9.61 MWh | 9.61 MWh | 57 % | 58 % | 134 °C | 1482 | 0.54 | 5.3 kPa |
| TES-IP | 11.9 bar | 1 | 10.18 MWh | 9.10 MWh | 98 % | 50 % | 100 °C | 1576 | 0.53 | 1.7 kPa |
| TES-IP | 11.9 bar | 2 | 10.03 MWh | 9.41 MWh | 73 % | 54 % | 117 °C | 1524 | 0.54 | 1.7 kPa |
| TES-IP | 11.9 bar | 5 | 9.73 MWh | 9.64 MWh | 58 % | 58 % | 132 °C | 1484 | 0.54 | 1.7 kPa |
| TES-IP | 11.9 bar | 10 | 9.68 MWh | 9.67 MWh | 57 % | 58 % | 134 °C | 1478 | 0.55 | 1.7 kPa |
| TES-IP | 11.9 bar | 20 | 9.68 MWh | 9.68 MWh | 57 % | 58 % | 134 °C | 1478 | 0.55 | 1.7 kPa |
| TES-HP | 36.8 bar | 1 | 10.40 MWh | 9.33 MWh | 95 % | 51 % | 100 °C | 1551 | 0.54 | 0.5 kPa |
| TES-HP | 36.8 bar | 2 | 10.22 MWh | 9.64 MWh | 71 % | 54 % | 117 °C | 1502 | 0.55 | 0.5 kPa |
| TES-HP | 36.8 bar | 5 | 9.93 MWh | 9.85 MWh | 58 % | 58 % | 130 °C | 1467 | 0.55 | 0.6 kPa |
| TES-HP | 36.8 bar | 10 | 9.89 MWh | 9.88 MWh | 57 % | 58 % | 132 °C | 1462 | 0.55 | 0.6 kPa |
| TES-HP | 36.8 bar | 20 | 9.88 MWh | 9.88 MWh | 57 % | 58 % | 132 °C | 1462 | 0.55 | 0.6 kPa |

| Cuve | Tola : énergie stockée | Simulé (cycle stable, chaleur rendue) | Écart |
|---|---|---|---|
| TES-LP | 9.60 MWh | 9.61 MWh | +0.1 % |
| TES-IP | 9.54 MWh | 9.68 MWh | +1.4 % |
| TES-HP | 9.54 MWh | 9.88 MWh | +3.6 % |

Cycles avant stabilisation (variation < 1 % d'un cycle au suivant) : TES-LP : 4, TES-IP : 4, TES-HP : 4 (Tola : moins de 20, « only the first charging cycle shows a remarkable difference »). Fraction de la phase à sortie constante attendue : 67 %.

## 3. Expériences numériques à l'échelle du banc de Dormoy

Cuve de 0,5 m × 2 m (0,39 m³, 755 kg de gravier), air à 0,052 kg/s entrant à 170 °C pendant 2 h, lit initialement à 20 °C, isolation parfaite.

| Cailloux | Porosité | Pression | Re | Bi | h | Chaleur stockée en 2 h | Sortie constante | Δp |
|---|---|---|---|---|---|---|---|---|
| 3 cm | 0.3 | 3 bar | 431 | 0.21 | 33 W/m²K | 15.8 kWh | 92 % | 89 Pa |
| 1 cm | 0.3 | 3 bar | 145 | 0.11 | 54 W/m²K | 15.8 kWh | 100 % | 344 Pa |
| 5 cm | 0.3 | 3 bar | 703 | 0.28 | 26 W/m²K | 15.5 kWh | 63 % | 50 Pa |
| 3 cm | 0.4 | 3 bar | 422 | 0.21 | 33 W/m²K | 15.6 kWh | 74 % | 33 Pa |
| 3 cm | 0.3 | 12 bar | 428 | 0.21 | 33 W/m²K | 15.9 kWh | 90 % | 22 Pa |
| 3 cm | 0.3 | 50 bar | 410 | 0.22 | 35 W/m²K | 16.5 kWh | 85 % | 5 Pa |

Lecture : des cailloux plus petits échangent mieux (front plus net, plus de chaleur stockée) mais coûtent plus de perte de charge ; à haute pression l'air est plus dense, la vitesse baisse et la perte de charge devient négligeable (quelques pascals pour 2 m de lit). La perte de charge d'Ergun ne coûte donc rien de mesurable au compresseur de Dormoy.

## 4. Validation expérimentale (Cascetta 2018)

**Non faite.** L'article de Cascetta et al. (2018, Energy Procedia 148:234-241, DOI 10.1016/j.egypro.2018.08.073) est en accès libre (CC BY-NC-ND) mais le site de l'éditeur refuse les téléchargements automatiques. Même chose pour Barbour et al. (2015, CC BY). À télécharger à la main et à déposer dans `data/sources/cascetta2018/` ; le script comparera alors les profils de température mesurés. En attendant, le modèle est vérifié contre la solution exacte de Schumann (§ 1) et confronté aux résultats publiés de Tola (§ 2).

## 5. Graphiques

![fig1_schumann.png](fig1_schumann.png)

![fig2_tola_profils.png](fig2_tola_profils.png)

![fig3_tola_sorties.png](fig3_tola_sorties.png)

![fig4_tola_cycles.png](fig4_tola_cycles.png)

## 6. Conclusion

- Le modèle converge vers la solution analytique de Schumann et conserve l'énergie exactement.
- Sur les cuves de Tola, la chaleur rendue au cycle stable vaut 9.61 MWh pour TES-LP (Tola : 9,60), avec une sortie constante pendant la majeure partie de chaque phase et une stabilisation en quelques cycles, comme chez Tola. Les écarts viennent de ce que Tola ne publie ni sa corrélation d'échange, ni ses pertes, ni son critère exact de « constance ».
- La validation sur des mesures (Cascetta 2018) attend le PDF.
- À l'échelle de Dormoy, la perte de charge dans le gravier est négligeable (< 100 Pa) ; l'échange est bon (Bi ≈ 0,2, front net).
