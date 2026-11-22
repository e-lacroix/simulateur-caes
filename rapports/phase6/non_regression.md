# Phase 6 : non-régression de l'architecture « composants »

*Généré par `validation/non_regression_phase6.py`. Chaque ligne compare la nouvelle architecture (scénarios `scenarios/*.yaml`, assemblés par `caes.assembleur`) aux chiffres calculés par les modules des phases 1 à 5 (`caes.systeme`, `caes.integre`, scénarios `scenarios/v1/`), enregistrés dans `tests/reference/phases_1_5.yaml`. Critère du plan : 0,1 %.*

## 1. Scénarios de validation de Dormoy (phases 1 et 2)

| Scénario | Grandeur | Phase 6 | Référence | Écart |
|---|---|---|---|---|
| dormoy_charge_1_190 | energie_electrique_kwh | 372.984 | 372.984 | +0.0000 % |
| dormoy_charge_1_190 | duree_h | 9.88611 | 9.88611 | +0.0000 % |
| dormoy_charge_1_190 | puissance_moyenne_kw | 37.7281 | 37.7281 | +0.0000 % |
| dormoy_charge_1_190 | chaleur_refroidisseurs_kwh | 240.798 | 240.798 | +0.0000 % |
| dormoy_charge_1_190 | chaleur_sup_seuil_kwh | 63.6067 | 63.6067 | +0.0000 % |
| dormoy_charge_1_190 | chaleur_paroi_reservoir_kwh | 40.1561 | 40.1561 | -0.0000 % |
| dormoy_charge_1_190 | T_finale_degC | 28.5556 | 28.5556 | +0.0000 % |
| dormoy_charge_1_190 | masse_stockee_kg | 1244.21 | 1244.21 | +0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | energie_electrique_kwh | 386.202 | 386.202 | -0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | duree_h | 9.88611 | 9.88611 | +0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | puissance_moyenne_kw | 39.0651 | 39.0651 | -0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | chaleur_refroidisseurs_kwh | 265.811 | 265.811 | +0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | chaleur_sup_seuil_kwh | 90.7436 | 90.7436 | -0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | chaleur_paroi_reservoir_kwh | 40.1842 | 40.1842 | +0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | T_finale_degC | 28.5599 | 28.5599 | +0.0000 % |
| dormoy_charge_1_190_aspiration_chaude | masse_stockee_kg | 1244.1 | 1244.1 | +0.0000 % |
| dormoy_charge_55_190 | energie_electrique_kwh | 267.216 | 267.216 | -0.0000 % |
| dormoy_charge_55_190 | duree_h | 6.85833 | 6.85833 | +0.0000 % |
| dormoy_charge_55_190 | puissance_moyenne_kw | 38.9623 | 38.9623 | -0.0000 % |
| dormoy_charge_55_190 | chaleur_refroidisseurs_kwh | 174.189 | 174.189 | -0.0000 % |
| dormoy_charge_55_190 | chaleur_sup_seuil_kwh | 47.49 | 47.49 | -0.0000 % |
| dormoy_charge_55_190 | chaleur_paroi_reservoir_kwh | 29.6851 | 29.6851 | -0.0000 % |
| dormoy_charge_55_190 | T_finale_degC | 28.5554 | 28.5554 | +0.0000 % |
| dormoy_charge_55_190 | masse_stockee_kg | 863.153 | 863.153 | +0.0000 % |
| dormoy_decharge_essai | energie_electrique_kwh | 0 | 0 | 0 / 0 |
| dormoy_decharge_essai | duree_min | 37.2667 | 37.2667 | +0.0000 % |
| dormoy_decharge_essai | chaleur_rechauffage_kwh | 0 | 0 | 0 / 0 |
| dormoy_decharge_essai | p_finale_bar | 49.9608 | 49.9608 | +0.0000 % |
| dormoy_decharge_essai | T_finale_degC | 5.89395 | 5.89395 | +0.0000 % |
| dormoy_decharge_essai | T_rejet_min_degC | 2.47947 | 2.47947 | +0.0000 % |
| dormoy_decharge_essai | masse_soutiree_kg | 330.928 | 330.928 | +0.0000 % |
| dormoy_decharge_base | energie_electrique_kwh | 14.3454 | 14.3454 | -0.0000 % |
| dormoy_decharge_base | duree_min | 51.5333 | 51.5333 | +0.0000 % |
| dormoy_decharge_base | chaleur_rechauffage_kwh | 0 | 0 | 0 / 0 |
| dormoy_decharge_base | p_finale_bar | 17.9924 | 17.9924 | +0.0000 % |
| dormoy_decharge_base | T_finale_degC | -3.28397 | -3.28397 | -0.0000 % |
| dormoy_decharge_base | T_rejet_min_degC | -62.7723 | -62.7723 | -0.0000 % |
| dormoy_decharge_base | masse_soutiree_kg | 992.532 | 992.532 | +0.0000 % |
| dormoy_decharge_base | chaleur_rechauffage_1_kwh | 0 | 0 | 0 / 0 |
| dormoy_decharge_3etages | energie_electrique_kwh | 39.0385 | 39.0385 | +0.0000 % |
| dormoy_decharge_3etages | duree_min | 37.5667 | 37.5667 | +0.0000 % |
| dormoy_decharge_3etages | chaleur_rechauffage_kwh | 44.5716 | 44.5716 | -0.0000 % |
| dormoy_decharge_3etages | p_finale_bar | 54.9714 | 54.9714 | +0.0000 % |
| dormoy_decharge_3etages | T_finale_degC | 8.16584 | 8.16584 | +0.0000 % |
| dormoy_decharge_3etages | T_rejet_min_degC | 14.5428 | 14.5428 | +0.0000 % |
| dormoy_decharge_3etages | masse_soutiree_kg | 723.534 | 723.534 | +0.0000 % |
| dormoy_decharge_3etages | chaleur_rechauffage_1_kwh | 24.4159 | 24.4159 | +0.0000 % |
| dormoy_decharge_3etages | chaleur_rechauffage_2_kwh | 6.04685 | 6.04685 | -0.0000 % |
| dormoy_decharge_3etages | chaleur_rechauffage_3_kwh | 14.1088 | 14.1088 | -0.0000 % |
| dormoy_decharge_3etages | chaleur externe | 44.5716 | 44.5716 | +0.0000 % |

## 2. Architectures A à E, réglages de la phase 5

| Arch. | Cycles | Charge (kWh) | Produit (kWh) | Réf. produit | Écart | Chaleur par source (kWh) | Réf. | Cuves fin (kWh) | Réf. | Unités rendues | Réf. | Résidus exergie | Durée |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 2 | 324.49 | 14.0457 | 14.0457 | -0.0000 % | – | – | 0.00 | 0.00 | 43.3 | 43.3 | -0.22 % / +0.00 % | 3 s |
| B | 3 | 243.24 | 40.9610 | 40.9610 | -0.0000 % | externe 51.20 | externe 51.20 | 0.00 | 0.00 | 168.4 | 168.4 | -0.21 % / +0.00 % | 4 s |
| C | 3 | 243.24 | 40.9610 | 40.9610 | -0.0000 % | huile 51.20 | huile 51.20 | 0.00 | 0.00 | 168.4 | 168.4 | -0.21 % / +0.00 % | 3 s |
| D | 4 | 239.46 | 41.0476 | 41.0476 | -0.0000 % | cuve_3 30.23, cuve_2 6.36, cuve_1 14.83 | cuve_3 30.23, cuve_2 6.36, cuve_1 14.83 | 48.10 | 48.10 | 171.4 | 171.4 | -0.22 % / +0.00 % | 42 s |
| E | 4 | 239.43 | 41.0137 | 41.0137 | -0.0000 % | cuve_3 30.23, cuve_2 6.36, cuve_1 14.65 | cuve_3 30.23, cuve_2 6.36, cuve_1 14.65 | 36.60 | 36.60 | 171.3 | 171.3 | -0.22 % / +0.00 % | 41 s |

**Pire écart relatif sur l'ensemble : 0.00000 %** (critère : 0,1 %). Les écarts nuls à la précision affichée sont attendus : la nouvelle architecture appelle les mêmes fonctions physiques dans le même ordre ; seule la façon de les assembler a changé.

## 3. Ce que la phase 6 ajoute sans changer les chiffres

- Bloc `ambiance` unique (F32) : source froide, pertes, air aspiré et état mort viennent du même endroit ; profil météo optionnel.
- Chaînes de composants (F33) : la chaîne de Dormoy et les architectures A à E sont décrites par des fichiers YAML sans code spécifique ; `python -m caes simuler` écrit les résultats.
- Avertissements de domaine de validité (Wakao, Cheayb, givrage, cuve trop froide, lois en pression extrapolées).
- Étiquettes de chaleur : le nom du composant (`cuve_3`, `huile`) ou `externe` ; `huile_ideale` de la phase 5 est devenu `huile` (le nom du composant dans `C.yaml`).
