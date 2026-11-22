# Tableau de bord de validation

*Généré par `validation/tableau_de_bord.py` en 89 s. Chaque ligne compare une grandeur simulée par le simulateur à un chiffre publié, avec son niveau de preuve. Verdict : « reproduit » si l'écart est sous 5 %, sinon « écart expliqué » (paragraphe en section 4) ou **non expliqué**. Une validation faite dans les conditions ambiantes d'un article ne vaut que pour ces conditions.*

**Bilan** : 5 jeux disponibles (2 mesurés, les deux essais de Dormoy ; 3 simulations publiées), 5 en attente ; 51 grandeurs comparées : 30 reproduites, 20 écarts expliqués, 1 non expliqué(s).

## 1. Jeux de données

| Jeu | Nature | Ambiance | État | Provenance |
|---|---|---|---|---|
| Dormoy 2024, essai de charge mesuré (§ 3.1, 20 réservoirs, 5,86 m³) | mesure | 20 °C, 1,013 bar, 50 % (hypothèses), air aspiré à 52 °C (déduit du débit mesuré) | disponible | `data/validation/dormoy/provenance.md` |
| Dormoy 2024, essai de décharge mesuré (§ 3.1, 8 réservoirs, 2,56 m³) | mesure | 20 °C, 1,013 bar, 50 % (hypothèses), air aspiré à 52 °C (déduit du débit mesuré) | disponible | `data/validation/dormoy/provenance.md` |
| Dormoy 2024, simulations publiées et données fabricant (tableaux 5, 6, 9 ; § 3.3) | simulation publiée | mêmes hypothèses | disponible | `data/validation/dormoy/provenance.md` |
| Tola 2022, LT-ACAES de 10 MW (tableaux 1, 6 à 10) | simulation publiée | 15 °C, 1,01 bar (tableau 1) ; humidité : hypothèse | disponible | `data/validation/tola2022/provenance.md` |
| Shi 2024, A-CAES de 100 MW (prépublication non révisée ; tableau 4, figure 7, tableau 5) | simulation publiée | 25 °C, 0,1 MPa (tableau 4) ; eau froide 30 °C ; humidité : hypothèse | disponible | `data/validation/shi2024/provenance.md` |
| Castellani 2018, micro-CAES de 2,2 kW (Energies 11:1921, accès libre) | mesure | à renseigner | en attente du PDF (MDPI refuse les robots) : à déposer dans `data/sources/castellani2018/` | `data/validation/castellani2018/provenance.md` |
| Luo et al. (via Zhang S. 2025, § 3.3) : 3 × 90 L, tampon 50 L | mesure | non donnée | partiel : article de Luo introuvable, courbes de Zhang non numérisées, modèle de vanne non implémenté | `data/validation/luo_zhangS2025/provenance.md` |
| Cascetta 2018, lit de roches mesuré (Energy Procedia, accès libre) | mesure | à renseigner | en attente du PDF (ScienceDirect refuse les robots) | `data/validation/cascetta2018/provenance.md` |
| Barbour 2015, A-CAES avec lit compact (Applied Energy, accès libre) | mesure et modèle | à renseigner | en attente du PDF | `data/validation/barbour2015/provenance.md` |
| Venkataramani 2018, petit CAES expérimental | mesure | non disponible | non accessible légalement pour l'instant | `data/validation/venkataramani2018/provenance.md` |

Courbes numérisées de Dormoy déposées dans `data/validation/dormoy/` : aucune (voir `A_NUMERISER.md`).

## 2. Tableau de bord

| Jeu | Nature | Composant ou chaîne | Grandeur | Référence | Simulé | Unité | Écart | Verdict | Scénario | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| Dormoy 2024 | mesure | chaîne de charge (compresseur, refroidisseurs, sécheur, réservoir) | énergie électrique 1 → 190 bar | 396 | 386.2 | kWh | -2.5 % | reproduit | `dormoy_charge_1_190_aspiration_chaude.yaml` |  |
| Dormoy 2024 | mesure | chaîne de charge | durée 1 → 190 bar | 10 | 9.886 | h | -1.1 % | reproduit | `dormoy_charge_1_190_aspiration_chaude.yaml` | « almost 10 h » |
| Dormoy 2024 | mesure | chaîne de charge | puissance moyenne | 39 | 39.07 | kW | +0.2 % | reproduit | `dormoy_charge_1_190_aspiration_chaude.yaml` |  |
| Dormoy 2024 | mesure | réservoir (paroi) + détendeur isenthalpique | durée 190 → 50 bar (2,56 m³, 0,148 kg/s) | 38 | 37.27 | min | -1.9 % | reproduit | `dormoy_decharge_essai.yaml` |  |
| Dormoy 2024 | mesure | réservoir (paroi) + détendeur de Cheayb | durée 190 → 50 bar | 38 | 37.27 | min | -1.9 % | reproduit | `dormoy_decharge_essai.yaml (--modifier composants.detendeur.modele=cheayb)` |  |
| Dormoy 2024 | simulation publiée | chaîne de charge | durée 55 → 190 bar | 6.8 | 6.858 | h | +0.9 % | reproduit | `dormoy_charge_55_190.yaml (--modifier ambiance.T_aspiration=52degC)` |  |
| Dormoy 2024 | simulation publiée | refroidisseurs (efficacité) | chaleur rejetée 55 → 190 bar | 189.2 | 191.6 | kWh | +1.3 % | reproduit | `dormoy_charge_55_190.yaml (--modifier ambiance.T_aspiration=52degC)` |  |
| Dormoy 2024 | simulation publiée | refroidisseurs (efficacité) | chaleur rejetée au-dessus de 130 °C | 72.2 | 66.36 | kWh | -8.1 % | écart expliqué ([chaleur_sup130](#chaleur_sup130)) | `dormoy_charge_55_190.yaml (--modifier ambiance.T_aspiration=52degC)` |  |
| Dormoy 2024 | fabricant | turbine DEPRAG, étage 1 | température de sortie | 59.2 | 60.59 | °C | +1.4 °C | reproduit | `dormoy_decharge_3etages.yaml (point nominal)` | tolérance : RMSE du modèle de Dormoy (2,83 °C) |
| Dormoy 2024 | fabricant | turbine DEPRAG, étage 1 | puissance électrique | 20 | 20.22 | kW | +1.1 % | reproduit | `dormoy_decharge_3etages.yaml (point nominal)` |  |
| Dormoy 2024 | fabricant | turbine DEPRAG, étage 2 | température de sortie | 20.7 | 20.64 | °C | -0.1 °C | reproduit | `dormoy_decharge_3etages.yaml (point nominal)` | tolérance : RMSE du modèle de Dormoy (2,83 °C) |
| Dormoy 2024 | fabricant | turbine DEPRAG, étage 2 | puissance électrique | 20.1 | 20.11 | kW | +0.0 % | reproduit | `dormoy_decharge_3etages.yaml (point nominal)` |  |
| Dormoy 2024 | fabricant | turbine DEPRAG, étage 3 | température de sortie | 16 | 14.54 | °C | -1.5 °C | reproduit | `dormoy_decharge_3etages.yaml (point nominal)` | tolérance : RMSE du modèle de Dormoy (2,83 °C) |
| Dormoy 2024 | fabricant | turbine DEPRAG, étage 3 | puissance électrique | 21.8 | 22.02 | kW | +1.0 % | reproduit | `dormoy_decharge_3etages.yaml (point nominal)` |  |
| Dormoy 2024 | simulation publiée | réchauffage à 3 étages | chaleur de réchauffage (tableau 5 : 46,2 kWh) | 46.2 | 44.57 | kWh | -3.5 % | reproduit | `dormoy_decharge_3etages.yaml` | puissances du tableau 5 × 40 min = 45.2 kWh |
| Dormoy 2024 | simulation publiée | décharge à 3 étages | durée 190 → 55 bar | 40 | 37.57 | min | -6.1 % | écart expliqué ([trois_etages](#trois_etages)) | `dormoy_decharge_3etages.yaml` |  |
| Dormoy 2024 | simulation publiée | décharge à 3 étages | énergie produite (16 % de 290 kWh) | 46.4 | 39.04 | kWh | -15.9 % | écart expliqué ([trois_etages](#trois_etages)) | `dormoy_decharge_3etages.yaml` |  |
| Dormoy 2024 | simulation publiée | cycle à 3 étages | rendement aller-retour sans compter la chaleur | 16 | 14.13 | % | -11.7 % | écart expliqué ([trois_etages](#trois_etages)) | `dormoy_decharge_3etages.yaml / dormoy_charge_55_190.yaml` |  |
| Dormoy 2024 | simulation publiée | décharge à 1 étage sans réchauffage | énergie produite (cas de base) | 16.93 | 14.35 | kWh | -15.3 % | **non expliqué** ([cas_base](#cas_base)) | `dormoy_decharge_base.yaml` |  |
| Dormoy 2024 | simulation publiée | cycle à 1 étage réchauffé à 90 °C | rendement aller-retour (fig. 16) | 5.5 | 5.376 | % | -2.2 % | reproduit | `dormoy_decharge_base.yaml (chaudière à 90 °C) / charge 18 → 190` |  |
| Tola 2022 | simulation publiée | lit de gravier (Schumann), cuve TES-LP | chaleur rendue par cycle stable (tableau 8) | 9.6 | 9.45 | MWh | -1.6 % | reproduit | `validation/lit_gravier.py (ici 30 cellules, 12 cycles)` |  |
| Tola 2022 | simulation publiée | lit de gravier (Schumann), cuve TES-IP | chaleur rendue par cycle stable (tableau 8) | 9.54 | 9.516 | MWh | -0.2 % | reproduit | `validation/lit_gravier.py (ici 30 cellules, 12 cycles)` |  |
| Tola 2022 | simulation publiée | lit de gravier (Schumann), cuve TES-HP | chaleur rendue par cycle stable (tableau 8) | 9.54 | 9.719 | MWh | +1.9 % | reproduit | `validation/lit_gravier.py (ici 30 cellules, 12 cycles)` |  |
| Tola 2022 | simulation publiée | compresseur polytropique (0,88) + pincement 20 K, étage CLP | puissance mécanique moyenne (tableau 7) | 1980 | 1933 | kW | -2.4 % | reproduit | `validation/tola_charge.yaml` | tableaux 7 et 9 : grandeurs mécaniques (le tableau 10 applique 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / 0,97) = 0,674) |
| Tola 2022 | simulation publiée | compresseur polytropique (0,88) + pincement 20 K, étage CIP | puissance mécanique moyenne (tableau 7) | 1730 | 1684 | kW | -2.6 % | reproduit | `validation/tola_charge.yaml` | tableaux 7 et 9 : grandeurs mécaniques (le tableau 10 applique 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / 0,97) = 0,674) |
| Tola 2022 | simulation publiée | compresseur polytropique (0,88) + pincement 20 K, étage CHP | puissance mécanique moyenne (tableau 7) | 1720 | 1683 | kW | -2.1 % | reproduit | `validation/tola_charge.yaml` | tableaux 7 et 9 : grandeurs mécaniques (le tableau 10 applique 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / 0,97) = 0,674) |
| Tola 2022 | simulation publiée | compresseur CVHP (6,4 → 10 MPa) et caverne | énergie mécanique sur la charge (tableau 7) | 7.16 | 8.328 | MWh | +16.3 % | écart expliqué ([tola_cave](#tola_cave)) | `validation/tola_charge.yaml` |  |
| Tola 2022 | simulation publiée | chaîne de compression | énergie mécanique totale (tableau 7) | 39.76 | 40.13 | MWh | +0.9 % | reproduit | `validation/tola_charge.yaml` |  |
| Tola 2022 | simulation publiée | caverne (quasi isotherme) | pression en fin de charge de 6 h | 100 | 97.82 | bar | -2.2 % | reproduit | `validation/tola_charge.yaml` |  |
| Tola 2022 | simulation publiée | turbines polytropiques (0,86) en pression glissante, cas A | énergie mécanique produite sur 3 h (tableau 9) | 23.92 | 27.71 | MWh | +15.8 % | écart expliqué ([tola_turbines](#tola_turbines)) | `validation/tola_decharge_A.yaml` | tableaux 7 et 9 : grandeurs mécaniques (le tableau 10 applique 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / 0,97) = 0,674) |
| Tola 2022 | simulation publiée | turbines, cas A | puissance mécanique maximale (début de décharge, tableau 9) | 8300 | 9616 | kW | +15.9 % | écart expliqué ([tola_turbines](#tola_turbines)) | `validation/tola_decharge_A.yaml` |  |
| Tola 2022 | simulation publiée | turbines polytropiques (0,86) en pression glissante, cas B | énergie mécanique produite sur 3 h (tableau 9) | 26.82 | 29.01 | MWh | +8.2 % | écart expliqué ([tola_turbines](#tola_turbines)) | `validation/tola_decharge_B.yaml` | tableaux 7 et 9 : grandeurs mécaniques (le tableau 10 applique 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / 0,97) = 0,674) |
| Tola 2022 | simulation publiée | turbines, cas B | puissance mécanique maximale (début de décharge, tableau 9) | 9500 | 1.007e+04 | kW | +6.0 % | écart expliqué ([tola_turbines](#tola_turbines)) | `validation/tola_decharge_B.yaml` |  |
| Tola 2022 | simulation publiée | turbines polytropiques (0,86) en pression glissante, cas C | énergie mécanique produite sur 3 h (tableau 9) | 28.48 | 30.32 | MWh | +6.5 % | écart expliqué ([tola_turbines](#tola_turbines)) | `validation/tola_decharge_C.yaml` | tableaux 7 et 9 : grandeurs mécaniques (le tableau 10 applique 0,97 des deux côtés : 28,48 × 0,97 / (39,76 / 0,97) = 0,674) |
| Tola 2022 | simulation publiée | turbines, cas C | puissance mécanique maximale (début de décharge, tableau 9) | 1e+04 | 1.052e+04 | kW | +5.2 % | écart expliqué ([tola_turbines](#tola_turbines)) | `validation/tola_decharge_C.yaml` |  |
| Tola 2022 | simulation publiée | cycle complet, cas C | rendement aller-retour (tableau 10, 0,97 des deux côtés) | 67.4 | 71.08 | % | +5.5 % | écart expliqué ([tola_turbines](#tola_turbines)) | `validation/tola_charge.yaml / tola_decharge_C.yaml` |  |
| Shi 2024 | simulation publiée | cycle complet | rendement aller-retour | 67.64 | 65 | % | -3.9 % | reproduit | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | chaîne de charge (isentropique 0,86, eau sous pression, réservoir adiabatique) | énergie consommée par cycle | 887 | 838.9 | MWh | -5.4 % | écart expliqué ([shi_cycle](#shi_cycle)) | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | chaîne de charge | durée de charge 4 → 10 MPa | 8 | 7.467 | h | -6.7 % | écart expliqué ([shi_cycle](#shi_cycle)) | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | chaîne de décharge (pression glissante, isentropique 0,90) | énergie produite par cycle | 600 | 545.3 | MWh | -9.1 % | écart expliqué ([shi_cycle](#shi_cycle)) | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | chaîne de décharge | durée de décharge 10 → 4 MPa | 6 | 5.633 | h | -6.1 % | écart expliqué ([shi_cycle](#shi_cycle)) | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | réservoir adiabatique de 1,18 × 10⁵ m³ | masse d'air stockée par cycle | 5712 | 5332 | t | -6.7 % | écart expliqué ([shi_cycle](#shi_cycle)) | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | compresseur 1 (isentropique 0,86) | puissance électrique à 7 MPa | 3.623e+04 | 3.622e+04 | kW | -0.0 % | reproduit | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | compresseur 2 (isentropique 0,86) | puissance électrique à 7 MPa | 3.314e+04 | 3.315e+04 | kW | +0.0 % | reproduit | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | compresseur 3 (isentropique 0,86) | puissance électrique à 7 MPa | 3.315e+04 | 3.315e+04 | kW | -0.0 % | reproduit | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | compresseur 4 (isentropique 0,86) | puissance électrique à 7 MPa | 1.027e+04 | 9522 | kW | -7.3 % | écart expliqué ([shi_comp4](#shi_comp4)) | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | turbine 1 (isentropique 0,90) | puissance électrique à 7 MPa | 2.044e+04 | 2.043e+04 | kW | -0.0 % | reproduit | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | turbine 2 (isentropique 0,90) | puissance électrique à 7 MPa | 3.98e+04 | 3.958e+04 | kW | -0.6 % | reproduit | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | turbine 3 (isentropique 0,90) | puissance électrique à 7 MPa | 3.977e+04 | 3.853e+04 | kW | -3.1 % | reproduit | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | simulation publiée | compresseur 4 (étage libre) | durée de fonctionnement par charge | 7.04 | 7.467 | h | +6.1 % | écart expliqué ([shi_cycle](#shi_cycle)) | `validation/shi_100MW.yaml (dernier cycle)` |  |
| Shi 2024 | calcul personnel | stockage d'eau sous pression | chaleur stockée par charge (4193,7 t de 30 à 190 °C) | 781 | 725.5 | MWh | -7.1 % | écart expliqué ([shi_eau](#shi_eau)) | `validation/shi_100MW.yaml (dernier cycle)` | référence recalculée, cp ≈ 4,19 kJ/kg·K |

![écarts](ecarts.png)

## 3. Ce que chaque jeu valide, et ce qu'il ne valide pas

- **Dormoy, mesures** : la seule source mesurée. Valide la chaîne de charge (énergie, durée, puissance) et le réservoir en décharge avec le détendeur. Ne valide pas la turbine (Dormoy ne l'a pas installée), ni le gravier, ni l'hiver (20 °C supposés).
- **Dormoy, simulations** : vérification croisée avec un modèle calibré sur les mêmes mesures ; la turbine DEPRAG est une donnée fabricant au point nominal.
- **Tola** : vérification croisée d'un modèle à 10 MW ; le lit de gravier est en plus vérifié contre la solution exacte de Schumann (phase 4). Hypothèses de notre côté : Wakao, caverne quasi isotherme, répartition égale des turbines, isolation parfaite.
- **Shi** : cas test de changement d'échelle (100 MW) avec les hypothèses de Shi (rendements constants, réservoir adiabatique) ; prépublication non révisée.
- Trois mots différents : **vérifier** (solution exacte), **croiser** (autre simulation), **valider** (mesure) ; voir `docs/phase-08-explication.md`.

## 4. Explications des écarts

<a id="cas_base"></a>
**Cas de base de Dormoy (1 étage, 3 → 1 bar, sans réchauffage) : −15 %, non expliqué depuis la phase 2.** Indépendant de la température initiale et du modèle thermique du réservoir. Diagnostics faits : le refroidissement Joule-Thomson du détendeur (190 → 3 bar) et le refroidissement de l'air dans le réservoir coûtent ≈ 1,4 kWh chacun ; sans les deux, 15,8 kWh. Dormoy modélise pourtant ces effets. Hypothèse restante : un détail du calcul de turbine non publié (travail calculé aux conditions nominales du tableau 9 ?). C'est une question ouverte du projet ; l'écart est montré, pas calibré.

<a id="trois_etages"></a>
**Décharge à 3 étages : durée −6 %, énergie −16 % par rapport à « 16 % de 290 kWh ».** Dormoy donne 62 kW pendant 40 min, soit 41,3 kWh et 14,2 % de 290 kWh, et non 16 % (qui demanderait 45 min) : son texte est incohérent. Notre 39,0 kWh en 37,6 min (14,1 % de notre charge 55 → 190 bar) est entre les deux lectures. La durée plus courte vient de l'arrêt à 55 bar (consigne 40 + écart 15) et du modèle de réservoir à paroi, validé sur l'essai de décharge.

<a id="chaleur_sup130"></a>
**Chaleur des refroidisseurs au-dessus de 130 °C : −8 %.** Elle dépend de la répartition des rapports entre les étages 3 et 4 (lois linéaires en pression, hypothèse F07) et de la température de l'air de refroidissement (20 °C supposés). Les étages 2 et 3 portent l'écart ; la chaleur totale (191,6 contre 189,2 kWh) est reproduite.

<a id="tola_cave"></a>
**Chaîne de compression de Tola : énergie du compresseur CVHP et durée.** Tola ne décrit pas le modèle thermique de sa caverne (gaz parfait entre 15 et 55 °C) ; nous la prenons quasi isotherme à l'ambiant (15 °C), ce qui y met 7 % d'air de plus qu'à 35 °C : la charge de 6 h n'atteint pas tout à fait 10 MPa et le CVHP travaille à des rapports un peu plus bas. Les compresseurs CLP, CIP et CHP, à rapport fixe, ne dépendent pas de la caverne.

<a id="tola_turbines"></a>
**Turbines de Tola : énergie plus haute que le tableau 9, rendement aller-retour du cas C +5 %.** Nos scénarios réchauffent l'air à une température constante (130, 150 ou 170 °C) par une source externe ; chez Tola, les cuves de gravier rendent cette température pendant environ deux tiers de la décharge, puis de l'air de plus en plus froid (jusqu'à ≈ 80 °C dans le cas A). L'écart mesure cette fin de décharge, que le lit de gravier de la phase 4 reproduit à part (ligne « cuves TES »). La répartition des rapports entre les trois turbines (« shared out ») est aussi une hypothèse (parts égales). Précision sur le tableau 10 de Tola : les tableaux 7 et 9 sont mécaniques et le rendement 0,674 applique 0,97 des deux côtés (28,48 × 0,97 / (39,76 / 0,97)) ; nous faisons de même.

<a id="shi_cycle"></a>
**Cas de Shi : bilan du cycle.** Shi impose 8 h de charge et 6 h de décharge et calcule le volume (1,18 × 10⁵ m³) qui les permet ; nous imposons le volume et laissons les durées sortir. Les écarts restants viennent du réservoir adiabatique, dont la température en fin de charge dépend de l'historique des cycles (Shi donne 2,78 → 70 °C sans dire comment il obtient 2,78 °C), et du refroidisseur du compresseur 4, qui rejette ici à l'ambiant plutôt que dans l'eau (à 80 °C, cette eau diluerait le réservoir chaud). Le réservoir froid est maintenu à 30 °C comme chez Shi (refroidissement du retour non modélisé). Prépublication non révisée : ses propres chiffres ne sont pas tous cohérents (fiche `maths-vulgarisees-secondaire5.md`).

<a id="shi_comp4"></a>
**Cas de Shi : compresseur 4 à 7 MPa, −7 %.** La figure 7 de Shi fait sortir le compresseur 4 à 7,55 MPa quand le réservoir est à 7 MPa, soit 0,55 MPa de surpression, alors que le tableau 4 n'en justifie que 0,24 (0,2 MPa à l'entrée du réservoir et 0,04 dans le dernier échangeur). Avec 0,24 MPa, le rapport de l'étage 4 vaut 1,50 au lieu de 1,57 et sa puissance est plus basse de 7 %. Les trois premiers compresseurs sont reproduits à 0,1 % près.

<a id="shi_eau"></a>
**Cas de Shi : chaleur stockée dans l'eau.** Référence recalculée (calcul personnel) à partir de 4193,7 t d'eau chauffée de 30 à 190 °C ; notre stockage à deux réservoirs bien mélangés plafonne l'eau à 207 °C et prend l'air du compresseur 4 à part (refroidisseur ambiant), d'où une quantité stockée différente.

<a id="tes_tola"></a>
**Cuves de gravier de Tola : +0,1 à +4 %.** Tola ne publie ni sa corrélation d'échange ni ses pertes ; Wakao et isolation parfaite ici. Avec 30 cellules et 12 cycles (phase 4 : 52 cellules, 20 cycles), l'accord est en partie une coïncidence de modèles proches ; la validation expérimentale (Cascetta, Barbour) attend les PDF.

## 5. Régénérer

```text
.venv\Scripts\python validation/tableau_de_bord.py
```

Les scripts détaillés des phases 1 à 5 restent disponibles (`validation/dormoy_charge.py`, `validation/dormoy_decharge.py`, `validation/lit_gravier.py`) avec leurs graphiques ; ce tableau en reprend les chiffres de synthèse avec les scénarios du format « composants ».
