# Phase 5 : banc de Dormoy + cuves de gravier, architectures A à E

*Généré par `rapports/phase5_architectures.py`. Chaque architecture enchaîne des cycles charge → attente (1 h) → décharge jusqu'au régime stable, à partir de la pression d'arrêt de sa turbine. Charge : scénario « aspiration chaude » (phase 1). Isolation des cuves parfaite (les pertes sont l'objet de la phase 6).*

## 1. Tableau comparatif (dernier cycle)

| Arch. | Cycles | Charge (kWh) | Produit (kWh) | RTE sans chaleur | Chaleur externe (kWh) | RTE avec chaleur externe | Chaleur des cuves → turbines (kWh) | T entrée turbines (°C, moy.) | Cuves : volume, pression, gravier | Chaleur restante dans les cuves (kWh) | Unités rendues sur 1000 | Fiche Dormoy (à la main) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 2 | 324.5 | 14.05 | 4.3 % | 0.0 | 4.3 % | 0.0 | -15 | – | – | **43** | 46 |
| B | 3 | 243.2 | 40.96 | 16.8 % | 51.2 | 13.9 % | 0.0 | 130 / 90 / 90 | – | – | **168** | 160 |
| C | 3 | 243.2 | 40.96 | 16.8 % | 0.0 | 16.8 % | 0.0 | 130 / 90 / 90 | – | – | **168** | ≈ 160 |
| D | 4 | 239.5 | 41.05 | 17.1 % | 0.0 | 17.1 % | 51.4 | 130 / 90 / 90 | 1.25 m³ (0.35 / 0.20 / 0.70) ; 3 / 12 / 55 bar ; 2406 kg | 48 | **171** | ≈ 150–155 |
| E | 4 | 239.4 | 41.01 | 17.1 % | 0.0 | 17.1 % | 51.2 | 130 / 90 / 89 | 1.25 m³ (0.35 / 0.20 / 0.70) ; 1 / 1 / 1 bar ; 2406 kg | 37 | **171** | ≈ 130–150 |

Les « unités rendues sur 1000 » sont l'électricité produite rapportée à l'électricité de la charge du même cycle. Pour C, la chaleur vient de la réserve d'huile idéale (étiquette `huile_ideale`) : elle n'est pas comptée comme externe.

Architecture C : réserve d'huile idéale restante après le dernier cycle : 26 kWh (la chaleur > 130 °C des refroidisseurs dépasse le besoin, comme chez Dormoy : 72 contre 46 kWh).

## 2. Tableaux « 1000 unités » par architecture

- **A : base Dormoy, 1 étage, sans réchauffage** : stocké dans l'air 329, dans les cuves 0 ; détendeur 241 ; turbines et génératrices 26 ; cuves (restitution) 0 ; **rendu 43** (résidus -0.22 % / +0.00 %). [tableau](tableau_1000_A.md), [cascade](cascade_A.png)
- **B : 3 étages, chaleur externe (Dormoy)** : stocké dans l'air 342, dans les cuves 0 ; détendeur 70 ; turbines et génératrices 111 ; cuves (restitution) 0 ; **rendu 168** (résidus -0.21 % / +0.00 %). [tableau](tableau_1000_B.md), [cascade](cascade_B.png)
- **C : 3 étages, huile idéale (chaleur > 130 °C sans perte)** : stocké dans l'air 342, dans les cuves 0 ; détendeur 70 ; turbines et génératrices 111 ; cuves (restitution) 0 ; **rendu 168** (résidus -0.21 % / +0.00 %). [tableau](tableau_1000_C.md), [cascade](cascade_C.png)
- **D : 3 étages, gravier direct (3 cuves sous pression)** : stocké dans l'air 348, dans les cuves 52 ; détendeur 71 ; turbines et génératrices 113 ; cuves (restitution) 27 ; **rendu 171** (résidus -0.22 % / +0.00 %). [tableau](tableau_1000_D.md), [cascade](cascade_D.png)
- **E : 3 étages, gravier + boucle d'air (cuves à 1 bar, 2 × 20 K)** : stocké dans l'air 348, dans les cuves 48 ; détendeur 72 ; turbines et génératrices 113 ; cuves (restitution) 23 ; **rendu 171** (résidus -0.22 % / +0.00 %). [tableau](tableau_1000_E.md), [cascade](cascade_E.png)

## 3. Dimensionnement des cuves (D et E)

Les volumes de base ([0,35 ; 0,2 ; 0,7] m³, voir `D.yaml`) sont multipliés par un facteur k. Cycles jusqu'au régime stable (au plus 4). L'objectif : la plus petite cuve qui alimente encore les turbines à leur température nominale.

| Arch. | k | Volume total | Gravier | Produit (kWh) | RTE | T min entrée turbine 1 / 2 / 3 (°C) | Chaleur restante (kWh) | Cycles |
|---|---|---|---|---|---|---|---|---|
| D | 0.25 | 0.31 m³ | 602 kg | 34.90 | 14.5 % | -4 / -46 / -65 | -8 | 4 |
| D | 0.5 | 0.62 m³ | 1203 kg | 40.32 | 16.8 % | 99 / 62 / 28 | 3 | 4 |
| D | 1 | 1.25 m³ | 2406 kg | 41.05 | 17.1 % | 130 / 90 / 90 | 48 | 4 |
| D | 2 | 2.50 m³ | 4812 kg | 41.13 | 17.2 % | 130 / 90 / 90 | 137 | 4 |
| D | 4 | 5.00 m³ | 9625 kg | 41.13 | 17.3 % | 130 / 90 / 90 | 239 | 4 |
| E | 0.25 | 0.31 m³ | 602 kg | 33.38 | 13.8 % | -5 / -49 / -75 | -5 | 4 |
| E | 0.5 | 0.62 m³ | 1203 kg | 38.87 | 16.2 % | 55 / 34 / 9 | 3 | 4 |
| E | 1 | 1.25 m³ | 2406 kg | 41.01 | 17.1 % | 130 / 90 / 74 | 36 | 4 |
| E | 2 | 2.50 m³ | 4812 kg | 41.13 | 17.2 % | 130 / 90 / 90 | 108 | 4 |
| E | 4 | 5.00 m³ | 9625 kg | 41.22 | 17.3 % | 130 / 90 / 90 | 185 | 4 |

![dimensionnement](fig_dimensionnement.png)

Lecture : au-dessous du volume de base, les turbines reçoivent de l'air trop froid (la colonne « T min » le montre) et la production baisse ; au-dessus, rien ne change (les cuves accumulent de la chaleur qu'on n'utilise pas). Le coude de la courbe est le volume à retenir.

## 4. Vérifications physiques

| Question | Réponse |
|---|---|
| Les pressions des cuves correspondent-elles à celles des turbines ? | Cuves 1 / 2 / 3 chargées à 3.3 / 12.3 / 55 bar (fin de charge) ; turbines 3 / 2 / 1 à 3 / 11 / 40 bar. Les couples s'emboîtent (cuve 3 ↔ turbine 1, etc.) ; la cuve est simplement traversée à une pression un peu différente en décharge, ce que le modèle gère (densité de l'air par CoolProp). |
| La cuve 1 suffit-elle pour la turbine 3 ? | Turbine 3 à 90 °C en moyenne (cible 90) et 90 °C au minimum ; chaleur prise 14.8 kWh. Oui au volume de base ; voir le balayage pour la marge. |
| La perte de charge dans le gravier coûte-t-elle de l'énergie ? | Δp d'Ergun en fin de charge : 29 / 13 / 1 Pa. Travail de pompage ≈ Σ Δp·V̇ ≈ 0.007 kWh sur une charge de 239 kWh : négligeable (< 0,01 %). |
| Que reste-t-il dans les cuves après la décharge ? | 48 kWh (au-dessus de 20 °C) au cycle stable : c'est le « coussin de chaleur » qui ne sert pas, à comparer aux 51 kWh prélevés par cycle. |

## 5. Comparaison avec le calcul à la main (fiche Dormoy, section 4)

| | Huile idéale (C) | Gravier direct (D) | Gravier + boucle (E) |
|---|---|---|---|
| Fiche (à la main) | 160 | 150–155 | 130–150 |
| Simulateur | 168 | 171 | 171 |

Le simulateur donne des valeurs plus proches les unes des autres que la fiche : avec des cuves correctement dimensionnées, le gravier alimente les turbines exactement à leur température nominale (bypass), donc D et E produisent autant que C et B. La différence entre les architectures n'est pas dans l'électricité produite mais dans ce qu'il faut pour y arriver : chaleur externe (B), stockage d'huile parfait (C), cuves sous pression (D) ou cuves à 1 bar avec deux échangeurs et 20 K de marge en moins (E). La pénalité de fin de décharge supposée par la fiche (−5 %) n'apparaît pas, parce que les cuves sont dimensionnées avec une marge (coude de la courbe) et qu'un bypass régule la température.

**Proposition de mise à jour des fiches Dormoy et Tola (section « cuves de gravier ») : à faire seulement avec l'accord de l'utilisateur.** Points à corriger : masse morte (18 bar, pas 50), détendeur (234 unités dans le cas de base, pas 74 ; 71 avec 3 étages), unités rendues (voir tableau 1), pas de pénalité de fin de décharge au volume de base, volumes de cuves ≈ 1,3 m³ au total au lieu de 2 m³.

## 6. Graphiques

![cascade A](cascade_A.png)

![cascade B](cascade_B.png)

![cascade C](cascade_C.png)

![cascade D](cascade_D.png)

![cascade E](cascade_E.png)
