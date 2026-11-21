# Validation de la décharge sur Dormoy (2024)

*Généré par `validation/dormoy_decharge.py`. Références : registre (`data/registre/parametres.csv`).*

## 1. Essai de décharge mesuré (§ 3.1)

2,56 m³ (8 réservoirs de 320 L) à 190 bar et 55 °C, détendeur à 35 bar, débit mesuré de 0,148 kg/s imposé, arrêt à 50 bar. Modèle thermique « paroi » (h_int = 25,42 et h_ext = 2,47 W/m²K calibrés par Dormoy sur cet essai), paroi initialement à 55 °C (hypothèse).

| Grandeur | Dormoy | Simulé | Écart | Remarque |
|---|---|---|---|---|
| Durée jusqu'à 50 bar | 38 min | 37.3 min | -1.9 % | la durée ne dépend que de la masse soutirée, donc de la température de l'air |
| Durée, paroi initiale à 20 °C | 38 min | 35.9 min | -5.7 % | la chaleur stockée dans la structure compte (remarque de Dormoy, § 3.2) |
| Durée, modèle « K global » (charge) | 38 min | 34.7 min | -8.7 % | sans la capacité thermique de la paroi, l'air se refroidit plus |
| Masse soutirée | – | 331 kg | – | 0,148 kg/s × durée |
| Température de l'air en fin d'essai | non publiée | 5.9 °C | – | MAPE de Dormoy sur la température du réservoir : 1,10 % |
| Sortie du détendeur, modèle isenthalpique | MAPE 0,39 % | 12.8 °C en moyenne | – | refroidissement Joule-Thomson : 12.9 K sous la température du réservoir |
| Sortie du détendeur, modèle de Cheayb | MAPE 0,21 % | 12.9 °C en moyenne | – | hors de sa plage de validité (25–150 bar) au-dessus de 150 bar ; écart avec l'isenthalpique 0.0 K |

La durée mesurée est retrouvée à 2 % près avec les coefficients calibrés de Dormoy, sans aucun réglage. Les deux modèles de détendeur donnent la même température à 1 K près ; comme Dormoy ne publie pas la courbe mesurée, on ne peut pas les départager.

## 2. Cas de base simulé (1 étage, sans réchauffage, § 3.3)

Dormoy : « a single-stage expansion device represented by the last stage of the selected turbine » → étage 3 de la DEPRAG (3 → 1 bar, n = 1,27, η_méc 73 %, η_él 92 %, 0,321 kg/s). Le détendeur est donc réglé à 3 bar et la décharge s'arrête à 18 bar (3 + 15). Référence : 16.93 kWh produits pour 366.75 kWh consommés.

| Variante | Énergie produite | Écart | Durée | T moyenne à l'entrée de la turbine | T finale du réservoir |
|---|---|---|---|---|---|
| T₀ = 55 °C (défaut, état mesuré avant décharge) | 14.35 kWh | -15.3 % | 52 min | 3 °C | -3 °C |
| T₀ = 20 °C (air à l'ambiant) | 14.33 kWh | -15.4 % | 59 min | -33 °C | -31 °C |
| Diagnostic : détendeur sans refroidissement JT | 15.27 kWh | -9.8 % | 52 min | 20 °C | -3 °C |
| Diagnostic : réservoir isotherme (h_int → ∞) | 14.93 kWh | -11.8 % | 52 min | 13 °C | 6 °C |
| Diagnostic : les deux | 15.83 kWh | -6.5 % | 52 min | 29 °C | 6 °C |
| Arrêt à 3 bar au lieu de 18 bar | 15.94 kWh | -5.9 % | 57 min | 2 °C | -8 °C |

### 2.1 Lecture

- Le modèle donne **14.3 kWh**, soit -15.3 % par rapport aux 16,93 kWh de Dormoy. **Cet écart n'est pas expliqué.** Il ne dépend pas de la température initiale (une décharge plus chaude soutire moins de masse, ce qui compense), ni du modèle thermique.
- Les diagnostics montrent d'où vient l'énergie manquante : le refroidissement Joule-Thomson dans le détendeur (190 → 3 bar) et le refroidissement de l'air qui se détend dans le réservoir coûtent chacun environ 1,4 kWh. En supprimant artificiellement les deux, on obtient 15.8 kWh, proche de la valeur de Dormoy. Son modèle contient pourtant ces deux effets (détendeur isenthalpique validé, bilan du réservoir validé en décharge). Hypothèses restantes : état initial différent, ou détail du modèle de turbine non publié (par exemple le travail calculé avec les températures nominales du tableau 9 plutôt qu'avec la température réelle d'entrée).
- Sans la marge de 15 bar du détendeur (arrêt à 3 bar), on gagnerait 1.6 kWh : c'est la « masse morte » du cas de base, bien plus petite que celle supposée dans la fiche Dormoy (section 4), qui prenait un arrêt à 50 bar. À corriger dans le tableau « 1000 unités » (phase 3).
- L'air sort de la turbine à -63 °C au plus froid : sans réchauffage, le givrage est certain (Dormoy l'évoque pour justifier le sécheur).
- Rendement aller-retour : 4.2 % avec la charge A (340 kWh de 18 à 190 bar) et 4.1 % avec la charge B (352 kWh). Dormoy : 4,3 % (16,93 / 396) ou 4,6 % (16,93 / 366,75). Avec réchauffage à 90 °C (fig. 16, 1 étage) : 18.9 kWh, soit 5.6 % (Dormoy : 5,5 %).

## 3. Turbine à 3 étages avec réchauffage (§ 3.3.4 et 3.3.5)

Décharge de 190 à 55 bar, turbine DEPRAG complète, air réchauffé à 130 / 90 / 90 °C par une source **externe** (comme Dormoy, qui ne la compte pas dans le rendement). État initial : 55 °C (air et paroi).

| Grandeur | Dormoy (simulation) | Simulé, T₀ = 55 °C | Simulé, T₀ = 20 °C | Écart (55 °C) |
|---|---|---|---|---|
| Durée de la décharge | 40 min | 37.6 min | 43.2 min | -6.1 % |
| Chaleur de réchauffage, total | 46.2 kWh | 44.6 kWh | 60.2 kWh | -3.5 % |
| … avant l'étage 1 | 24.8 kWh | 24.4 kWh | 37.0 kWh | -1.5 % |
| … avant l'étage 2 | 6.4 kWh | 6.0 kWh | 7.0 kWh | -5.5 % |
| … avant l'étage 3 | 15.0 kWh | 14.1 kWh | 16.2 kWh | -5.9 % |
| Température avant le réchauffage 1 (implicite dans le tableau 5 : 13 à 27 °C) | 13–27 °C | 5 à 36 °C | -25 à -4 °C | concorde à 55 °C |
| Puissance électrique | 62.0 kW (tableau 9) | 62.4 kW | 62.4 kW | +0.6 % |
| Énergie produite | 16 % × 290 = 46.4 kWh ; ou 62.0 kW × 40 min = 41.3 kWh | 39.0 kWh | 44.9 kWh | -5.6 % (contre 62 kW × 40 min) |
| Énergie consommée, recharge 55 → 190 bar | 290 kWh | A : 267 kWh ; B : 276 kWh | idem | -4.7 % (B) |
| RTE sans compter la chaleur (définition de Dormoy) | 16.0 % | A : 14.6 % ; B : 14.1 % | A : 16.8 % | – |
| RTE en comptant la chaleur externe | non calculé par Dormoy | A : 12.5 % ; B : 12.2 % | – | – |

### 3.1 Lecture

- **La chaleur de réchauffage du tableau 5 est reproduite étage par étage** (écarts de quelques pour cent) quand l'air part de 55 °C, l'état mesuré au début de l'essai de décharge. Avec un départ à 20 °C, l'air arrive trop froid au premier réchauffeur et la chaleur de l'étage 1 est surestimée de 50 %. C'est ce qui a fixé l'hypothèse « 55 °C » du registre (`cas_base.temperature_initiale_decharge`).
- **Incohérence relevée chez Dormoy.** Avec la turbine à sa puissance nominale (62.0 kW) pendant les 40 min du tableau 5, l'énergie produite vaut 41.3 kWh, soit 14.3 % de 290 kWh, et non 16,0 %. Le 16 % suppose 45 min de décharge, ou une consommation de 258 kWh. Notre résultat (14.1 % avec la charge B) se situe entre les deux lectures.
- **La chaleur externe compte.** Si on l'ajoute au dénominateur, le rendement tombe à 12.2 %. Cette chaleur ne devient « gratuite » que si elle vient des refroidisseurs du compresseur (phases 4 et 5), qui en rejettent 191 kWh pendant la recharge, dont 66 kWh au-dessus de 130 °C (phase 1).

## 4. Tendances de l'analyse paramétrique (fig. 11 à 16)

Chaque point enchaîne une charge (modèle de la phase 1) et une décharge qui part de l'état final de la charge (pression, température de l'air et de la paroi). Les courbes « avec réchauffage » chauffent l'air à 90 °C avant l'étage unique. La charge part de la pression d'arrêt de la décharge (18 bar pour un étage).

### 4.1 Température ambiante (fig. 11 et 12)

| T ambiante | Débit aspiré | Énergie de charge | Durée de charge | Produit sans réchauffage | Produit avec | RTE sans | RTE avec |
|---|---|---|---|---|---|---|---|
| -15 °C | 0.066 kg/s | 348 kWh | 8.3 h | 13.6 kWh | 24.4 kWh | 3.9 % | 7.0 % |
| -5 °C | 0.063 kg/s | 345 kWh | 8.2 h | 13.8 kWh | 23.3 kWh | 4.0 % | 6.7 % |
| 5 °C | 0.061 kg/s | 342 kWh | 8.1 h | 13.9 kWh | 22.2 kWh | 4.1 % | 6.5 % |
| 15 °C | 0.059 kg/s | 340 kWh | 8.1 h | 14.0 kWh | 21.3 kWh | 4.1 % | 6.3 % |
| 25 °C | 0.057 kg/s | 338 kWh | 8.0 h | 14.1 kWh | 20.5 kWh | 4.2 % | 6.1 % |

Dormoy : débit 0,065 → 0,056 kg/s, énergie produite avec réchauffage 27 → 22 kWh, RTE avec réchauffage 6,3 → 5,4 %, durée de charge 595 min à 25 °C, RTE sans réchauffage à peu près constant. Les tendances sont retrouvées ; les niveaux dépendent de l'écart du cas de base (§ 2).

### 4.2 Pression maximale de stockage (fig. 13)

Deux conventions pour l'énergie consommée : la recharge depuis la pression d'arrêt (18 bar, cycle réel) ou depuis 1 bar (« full capacity », convention du cas de base de Dormoy, dont les 366,75 kWh partent de la pression atmosphérique).

| p max | Charge depuis 18 bar | Charge depuis 1 bar | Puissance en fin de charge | Produit sans | Produit avec | RTE sans (18 bar) | RTE avec (18 bar) | RTE sans (1 bar) | RTE avec (1 bar) |
|---|---|---|---|---|---|---|---|---|---|
| 75 bar | 112 kWh | 147 kWh | 35.5 kW | 5.2 kWh | 7.2 kWh | 4.67 % | 6.39 % | 3.58 % | 4.90 % |
| 100 bar | 163 kWh | 197 kWh | 37.7 kW | 7.4 kWh | 10.3 kWh | 4.55 % | 6.35 % | 3.75 % | 5.25 % |
| 125 bar | 215 kWh | 249 kWh | 39.6 kW | 9.4 kWh | 13.4 kWh | 4.39 % | 6.25 % | 3.78 % | 5.39 % |
| 150 bar | 268 kWh | 302 kWh | 41.3 kW | 11.3 kWh | 16.4 kWh | 4.23 % | 6.13 % | 3.75 % | 5.44 % |
| 190 bar | 352 kWh | 386 kWh | 43.7 kW | 14.0 kWh | 20.9 kWh | 3.99 % | 5.95 % | 3.64 % | 5.42 % |
| 250 bar | 473 kWh | 508 kWh | 46.6 kW | 17.5 kWh | 27.1 kWh | 3.70 % | 5.72 % | 3.45 % | 5.33 % |
| 300 bar | 567 kWh | 602 kWh | 48.8 kW | 19.9 kWh | 31.6 kWh | 3.50 % | 5.56 % | 3.30 % | 5.24 % |

Dormoy : optimum à 125 bar sans réchauffage (4,2 → 3,8 %) et 150 bar avec (5,3 → 5,1 %) ; puissance du compresseur 39 → 48 kW à 300 bar. Simulé avec la convention « depuis 1 bar » : maximum à 125 bar sans et 150 bar avec réchauffage ; puissance 49 kW à 300 bar. L'optimum n'existe que parce que la charge de 1 à 18 bar est une dépense fixe qui pèse plus quand p max est faible ; avec la convention « cycle » (depuis 18 bar), le rendement baisse de façon monotone avec la pression, parce que le travail par kilogramme augmente. Au-delà de 190 bar, les rapports de pression des étages 3 et 4 sont extrapolés (loi linéaire bornée) : tendance indicative seulement.

### 4.3 Indice polytropique du compresseur (fig. 14 et 15)

Les quatre étages reçoivent le même indice n.

| n | Énergie de charge | Puissance moyenne | Durée | Produit sans | Produit avec | RTE sans | RTE avec |
|---|---|---|---|---|---|---|---|
| 1.0 | 280 kWh | 31.1 kW | 9.0 h | 14.1 kWh | 21.1 kWh | 5.0 % | 7.5 % |
| 1.1 | 300 kWh | 33.4 kW | 9.0 h | 14.1 kWh | 21.1 kWh | 4.7 % | 7.0 % |
| 1.2 | 319 kWh | 35.5 kW | 9.0 h | 14.1 kWh | 21.0 kWh | 4.4 % | 6.6 % |
| 1.3 | 337 kWh | 37.5 kW | 9.0 h | 14.1 kWh | 21.0 kWh | 4.2 % | 6.2 % |
| 1.4 | 353 kWh | 39.4 kW | 9.0 h | 14.0 kWh | 21.0 kWh | 4.0 % | 5.9 % |

Dormoy à n = 1 : puissance < 36 kW, 17,9 kWh sans réchauffage, 22,8 kWh avec, RTE 7,5 % avec réchauffage. Tendances retrouvées : le compresseur isotherme consomme moins et stocke plus de masse (air plus froid). Le niveau de l'énergie produite porte l'écart du cas de base.

### 4.4 Nombre d'étages de détente, avec réchauffage (fig. 16)

| Étages | Arrêt | Énergie de charge | Durée de charge | Produit | Chaleur externe | Durée de décharge | RTE sans chaleur | RTE avec chaleur |
|---|---|---|---|---|---|---|---|---|
| 1 | 18 bar | 352 kWh | 8.9 h | 20.9 kWh | 36.6 kWh | 57 min | 6.0 % | 5.4 % |
| 2 | 26 bar | 336 kWh | 8.5 h | 37.6 kWh | 54.1 kWh | 54 min | 11.2 % | 9.7 % |
| 3 | 55 bar | 276 kWh | 6.9 h | 42.8 kWh | 56.3 kWh | 41 min | 15.5 % | 12.9 % |

Dormoy : consommation « nearly 380 » → 290 kWh et RTE 5,5 → 16,0 % de 1 à 3 étages (chaleur non comptée). Le gain vient à la fois d'une détente mieux étagée (plus de travail par kilogramme) et d'une recharge plus courte (le coussin d'air de 55 bar n'est pas perdu : il reste dans les réservoirs d'un cycle à l'autre).

## 5. Bilan d'énergie de la décharge à 3 étages

| Poste | kWh |
|---|---|
| Enthalpie sortie des réservoirs | 81.4 |
| Chaleur cédée par l'air à la paroi (négative : la paroi chauffe l'air) | -13.6 |
| Variation d'énergie interne du réservoir | -67.8 |
| Chaleur de réchauffage (externe) | 44.6 |
| Écart d'enthalpie dans le détendeur | -0.0 |
| Travail à l'arbre des turbines | 42.9 |
| Pertes des génératrices | 3.9 |
| Électricité produite | 39.0 |
| Chaleur implicite des turbines (chute d'enthalpie − travail) | -0.1 |
| Enthalpie de l'air rejeté à 1 bar | 83.2 |
| Résidu du bilan de la chaîne | 0.0000 % |
| Résidu du bilan du réservoir | 0.0000 kWh |

## 6. Hypothèses propres à la phase 2

| Paramètre | Valeur | Provenance |
|---|---|---|
| `cas_base.temperature_initiale_decharge` | 55.0 degC | hypothese ; Valeur mesurée au début de l'essai de décharge (§3.1). Retenue parce qu'elle reproduit le tableau 5 (chaleur de réchauffage 24,8 / 6,4 / 15,0 kWh) et les températures d'entrée de turbine qu'il implique (13-27 °C). Variantes testées : 20 °C (air revenu à l'ambiant) et 29 °C (fin de la charge simulée en phase 1). Voir rapports/phase2/validation_decharge.md. |
| `essai_decharge.temperature_paroi_initiale` | 55.0 degC | hypothese ; Non mesurée. Dormoy note que la chaleur accumulée dans la structure pendant la charge influence la température de l'air en décharge. |
| `cas_base.turbine` | étage 3 de la turbine DEPRAG (3 → 1 bar, n = 1,27, 0,321 kg/s) | simulation_publiee ; « a single-stage expansion device represented by the last stage of the selected turbine (Table 9) ». Le détendeur est donc réglé à 3 bar et la décharge s'arrête à 18 bar, pas à 50 bar comme dans l'essai mesuré. |
| `cas_base.pression_arret` | 18.0 bar | calcul_personnel ; Pression d'entrée de l'étage 3 (3 bar) + écart minimal du détendeur (15 bar). |
| `cas_2etages.pression_arret` | 26.0 bar | calcul_personnel ; 11 bar + 15 bar. Hypothèse : les 2 étages sont les étages 2 et 3 de la turbine DEPRAG. |
| `turbine.rechauffage.source` | externe, non comptée dans le rendement | simulation_publiee ; Dormoy impose 130/90/90 °C sans modéliser la source. Le simulateur marque cette chaleur « externe » et calcule aussi le rendement qui la compte. |

## 7. Graphiques

![fig1_essai_pression.png](fig1_essai_pression.png)

![fig2_essai_temperatures.png](fig2_essai_temperatures.png)

![fig3_3etages_chaleur.png](fig3_3etages_chaleur.png)

![fig4_3etages_temperatures.png](fig4_3etages_temperatures.png)

![fig5_tendance_Tamb.png](fig5_tendance_Tamb.png)

![fig6_tendance_pmax.png](fig6_tendance_pmax.png)

![fig7_tendance_n.png](fig7_tendance_n.png)

![fig8_tendance_etages.png](fig8_tendance_etages.png)

## 8. Conclusion

- **Essai mesuré reproduit** : durée à -1.9 % avec les coefficients calibrés de Dormoy. Les deux modèles de détendeur concordent.
- **Cas à 3 étages** : chaleur de réchauffage du tableau 5 reproduite étage par étage (à condition de partir de 55 °C), énergie produite cohérente avec 62 kW × durée, rendement 14.1 % sans compter la chaleur et 12.2 % en la comptant. Le « 16 % » de Dormoy est incohérent avec ses propres 40 min de décharge (14,2 %).
- **Cas de base** : 14.3 kWh contre 16,93 : écart de −15 % **non expliqué**, hors du critère de sortie (17 ± 1 kWh). Les diagnostics localisent l'énergie manquante dans le refroidissement de l'air (détendeur et réservoir), que Dormoy modélise pourtant aussi. Point ouvert signalé dans le journal.
- **Tendances** des figures 11 à 16 retrouvées qualitativement (sens de variation, optimum de pression, gain des étages).
- **Masse morte** : avec l'étage 3 seul, l'arrêt est à 18 bar et non à 50 bar : le tableau « 1000 unités » de la fiche Dormoy devra être refait en phase 3.
