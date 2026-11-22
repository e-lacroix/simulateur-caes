# Journal du simulateur

*Mis à jour à la fin de chaque session. Le plus récent en haut.*

## 2026-11-22 : phase 12 terminée (documentation pour chercheurs et reproductibilité)

### Fait

- **Guides** : `docs/demarrage.md` (installation, première simulation, lecture des sorties, scénarios d'exemple, moins d'une heure), `docs/ajouter-un-composant.md` (interface F33, liste de contrôle en neuf points, exemple réel du séparateur, pièges), `docs/ajouter-une-etude.md` (fiche, registre, trois issues : composant, jeu de validation, paramètre ; exemples Shi et Ablaoui), `docs/limites-couvertes.md` (tableau « limites des études → réponse du simulateur » mis à jour pour dix études, onze incohérences trouvées dans les publications, onze questions ouvertes).
- **Référence de l'API** `docs/api.md` générée par `docs/generer_api.py` depuis les docstrings (50 modules, classes, méthodes, fonctions, signatures), sans dépendance.
- **`generer_tout.py`** : quatorze étapes (registre, scénarios dérivés, validation, non-régression, tableau de bord, 1000 unités, phases 5, 7, 9, 10, exemples, API, vérification, tests) avec durées, `--etapes`, `--sauf`, `--sans-longs`, `--continuer`, `--liste`, journal `rapports/generer_tout.log`, tableau des durées.
- **Vérification des chiffres cités** : `docs/chiffres_cles.yaml` (dix chiffres des pages des phases 9, 10 et 11, lus dans les rapports par expression régulière, mis en forme, cherchés dans la page) ; `generer_tout.py --etapes verifier`. Le premier passage a attrapé un arrondi (39,0 et non 39,1 kWh) et un motif lu dans le mauvais tableau.
- **Intégration continue** `.github/workflows/tests.yml` (Ubuntu, Python 3.11 et 3.12, registre + `verifier` + pytest) ; `CITATION.cff` ; `pyproject.toml` en version 0.12.0, licence GPL-3.0-or-later inchangée (`LICENSE`).
- Bootstrap de Sobol rendu reproductible (graine du générateur global) : les intervalles de confiance de `rapports/phase10/analyse.md` sont désormais fixes.
- Tests `tests/test_phase12.py` (4) ; 298 au total. `docs/phase-12-explication.md`.

### Résultats

- `generer_tout.py --sauf tests,verifier` de bout en bout : voir le tableau des durées dans `rapports/generer_tout.log` (≈ 3 h : validation détaillée 55 min, analyse de sensibilité 50 min) ; `verifier` : 10/10 chiffres retrouvés ; tests : 298 verts.

### Choix et limites

- Pas d'outil de documentation externe (Sphinx, pdoc) : un script de 100 lignes suffit et n'ajoute pas de dépendance ; la sortie est sèche mais complète.
- L'intégration continue ne lance que les tests (≈ 6 à 10 min) ; les rapports longs restent locaux.
- **Critère de sortie non atteint par nous-mêmes** : le test du guide de démarrage par une personne extérieure (moins d'une heure pour reproduire un scénario) reste à faire faire ; noter ici le résultat.
- Archivage Zenodo : préparé (`CITATION.cff`), décision et dépôt public laissés à l'utilisateur.
- Le tableau des limites dans `plan-v2.md` (section 2) n'a pas été modifié (fiches d'études : accord de l'utilisateur requis) ; `docs/limites-couvertes.md` en est la version à jour.

### Prochaine étape

Phase 13 : rapport et jury (chaque chiffre régénérable ; `generer_tout.py` et `chiffres_cles.yaml` sont les outils).

## 2026-11-22 : phase 11 terminée (scénarios d'exemple)

### Fait

- **Quatre scénarios d'exemple** dans `scenarios/exemples/` (README par dossier : question, fichiers, hypothèses, commande, lecture) et quatre rapports régénérables dans `rapports/scenarios/` : `dormoy_gravier` (A à E et D_hiver, format phase 6), `transport` (`transport.yaml`, `transport_appoint.yaml`, profils `meteo_hiver.csv` / `meteo_ete.csv`), `centre_urgence` (`module.yaml`, `demande_72h.csv`), `grande_echelle` (cas de Shi mis en regard de D). Fichiers dérivés et profils générés par `scenarios/exemples/generer_exemples.py`. Le scénario 5 (solaire, Wang) n'est pas fait.
- **Fuite d'air du réservoir** pendant l'attente : `fuite_par_jour` (F12, 0 par défaut ; `reservoir.fuite_par_jour` 0,5 %/j au registre, hypothèse) ; `masse_fuite_kg` suivi.
- **Flotte de modules** `caes/flotte.py` (F47) : répartition seconde par seconde d'une demande sur N modules identiques (démarrage, pause avec reprise, écrêtage, énergie non servie ; plus petit N qui couvre 99,9 %), profil jour / nuit.
- **Lots de simulations** `caes/analyse/lot.py` : `simuler_lot` (variantes d'un scénario) et `simuler_scenarios` (scénarios différents) en parallèle, résumés transportables (totaux, cycles, avertissements, séries de décharge à la demande), erreurs rendues et non levées.
- **Registre** : références `tesla2020` (fiche Megapack rev. 2.1, PDF déposé), `caterpillar2020` (fiche D100 GC, PDF déposé), `nrel2023` (DOI vérifié par OSTI) ; paramètres `megapack.*`, `groupe_diesel.*` (dont PCI et masse volumique calculés de la fiche), `batterie.cout_2030_*`, `caes.cout_reservoir_hors_sol` (200–250 $/kWh, Dormoy d'après Bazdar), `centre_urgence.*` et `meteo.amplitude_journaliere` (hypothèses) ; unités `L/h`, `$/kWh`, `MJ/kg`. 26 références, 377 paramètres.
- Fiche F47 ; F12 complétée (fuite) ; pages `reservoir_air.md`, `attente.md` ; `docs/phase-11-explication.md`. Tests `tests/test_phase11.py` (6) ; 294 au total.

### Résultats (`rapports/scenarios/`)

- **Dormoy avec gravier** (régime stable) : A 4,3 % ; B 16,8 % (13,9 % avec la chaleur achetée) ; C 16,8 % ; D 17,1 % et E 17,1 % sans chaleur externe ; D par −20 °C : 19,5 % mais air rejeté à −38 °C (cuves sous la cible). Givre à la turbine de A.
- **Transport** (D isolée, 20 cm) : chaleur restante 70 % à 7 j, 50 % à 14 j, 25 % à 28 j, 7 % à 56 j (exponentielle, τ calculé à la main : 26 j pour 2 m³, 18 j pour la cuve 3) ; électricité 39,0 → 29,7 kWh (40,6 sans transport) ; 10 cm : 9 % de chaleur à 28 j ; 40 cm : 48 %. Hiver (profil −20 °C) : mêmes parts, 32,3 kWh à 28 j, air rejeté −100 °C, givre dans les refroidisseurs ; été : 32,9 kWh. Échelle × 4 : 39 % de chaleur restante à 28 j, × 16 : 55 % mais électricité moindre (lit plus froid). Fuites : 0,5 %/j → 26,4 kWh à 28 j (−19 %), 2 %/j → 11,7 kWh. Chaudière d'appoint : 39,3 kWh à toute durée pour 1,6 (7 j) à 40 kWh (56 j) de chaleur externe.
- **Centre d'urgence** (7,2 MWh en 72 h, 120 / 60 kW) : un module livre 39,3 kWh à 62 kW en 38 min ; **192 modules** (139 à 250 bar, 229 en hiver), 710 t de bouteilles et gravier, 1 125 m³, 47 MWh pour charger ; contre 3 Megapack (76 t, 90 m³) ou 2 génératrices et 2 627 L de diesel (0,36 L/kWh). Viabilité : × 11 sur l'électricité par tonne, × 15 par m³ : résultat négatif, écrit comme tel.
- **Grande échelle** : Shi 65,0 % contre D 17,1 % ; 4,6 kWh/m³ de réservoir contre 7,0 ; 102 kWh/t d'air contre 54 ; quatre choix de modèle expliqués (paroi / adiabatique, détendeur / pression glissante, gravier / eau, 19 / 10 MPa).

### Choix et limites

- Profils météo (sinusoïde ± 5 K) et de demande (jour / nuit 1,2 / 0,6) sont des hypothèses au registre, à remplacer par des normales climatiques et un profil de bâtiment mesuré (données ouvertes : NREL End-Use Load Profiles, non intégrées).
- Flotte : modules identiques, courbe figée, démarrage instantané, pas de réservoir tampon ni de régulation continue (Zhang) ; la masse d'un module ne compte que bouteilles (F44) et gravier.
- Comparaisons : fiche Megapack de 2020 (les fiches 2025 sont chiffrées, non lues) ; coûts NREL en dollars de 2022, projection 2030 ; coût CAES = réservoirs seuls. Ordres de grandeur, pas un devis.
- « Chaleur après charge » du transport = chaleur initiale + chaleur reçue pendant la charge (les pertes pendant la charge elle-même ne sont pas retranchées).
- Fuite : taux constant, air perdu à l'état du réservoir ; aucune mesure d'étanchéité disponible.

### Prochaine étape

Phase 12 : documentation pour chercheurs et reproductibilité (`generer_tout.py`, guides d'installation et d'ajout, API, intégration continue, archivage).

## 2026-11-21 : phase 10 terminée (sensibilité, incertitudes, Pareto)

### Fait

- **Paquet `caes/analyse/`** : `parametres.py` (fichier d'analyse YAML : scénario de base, `modifications_de_base`, paramètres avec plage `registre` / `hypothese` ± 20 % / `{min, max}` / `facteur` sur plusieurs feuilles, sorties, réglages), `evaluation.py` (point → scénario modifié → simulation → sorties ; cache ; bassin de processus), `sensibilite.py` (un paramètre à la fois ; indices de Sobol par `scipy.stats.sobol_indices`, bootstrap), `incertitudes.py` (hypercube latin, intervalles 5–95 %, Spearman), `pareto.py` (NSGA-II en numpy : tri non dominé, encombrement, tournoi, SBX, mutation polynomiale, élitisme, pénalité des échecs, front sans doublons), `masse.py` (F44, masse des réservoirs à paroi mince et des stockages), `rapport.py` (exécution, Markdown, CSV, quatre figures, `resultats.pkl`, section « avertissements de domaine » ; `--rendu` réécrit sans resimuler). Commande `python -m caes analyser <analyse.yaml> [--sortie] [--procs] [--etapes] [--rapide] [--rendu]`.
- **Fichiers d'analyse** `scenarios/analyse/` : `D.yaml` (référence : D isolée, un jour d'attente, deux cycles, pas doublés ; dix paramètres ; Sobol n = 32 ; incertitudes n = 48 sur les plages du registre ; Pareto électricité livrée contre masse sur pression, cuves, isolant), `B_rapide.yaml` (démonstration, tests), `README.md` (format, sorties, méthodes).
- **Registre** : référence `asm1990` (ASM Handbook vol. 2, DOI vérifié) ; `reservoir.alu.limite_elastique` (276 MPa), `reservoir.pression_service` (300 bar, hypothèse d'après le cas à 300 bar de Dormoy), `reservoir.coefficient_securite` (2,25, hypothèse), `reservoir.resistance_specifique_equivalente` (385 kJ/kg, calibration sur les masses du tableau 8 : bouteilles de 320 et 270 L retrouvées à 3 %) ; unité `MPa`. 23 références, 352 paramètres.
- **Stockage de gravier** : paramètre facultatif `diametre_particule` (granulométrie propre à la cuve) ; les scénarios C, D, D_hiver, E le déclarent explicitement depuis le registre. **Sécheur** : `point_de_rosee_sortie` ajouté au sécheur de Dormoy dans les scénarios de base A à E et `dormoy_charge_*` (reste de la phase 9 : sans lui, le réservoir affichait une condensation que le sécheur réel empêche) ; variantes régénérées.
- Fiches F44 (masse d'un réservoir à paroi mince), F45 (sensibilité et incertitudes), F46 (dominance de Pareto et NSGA-II). Tests `tests/test_analyse.py` (10 : F44 contre Dormoy, dominance, ZDT1 à 3 % du front exact et reproductible, échecs pénalisés, Sobol sur une fonction additive, fichier d'analyse, tornade et intervalles sur B, point échoué → nan) ; 288 au total. `docs/phase-10-explication.md`.

### Résultats (`rapports/phase10/analyse.md`, D isolée, 662 simulations, 50 à 70 min sur dix processus selon la charge de la machine)

- **Trois paramètres dominants du rendement** (Sobol, indice total et intervalle à 95 %) : rendement mécanique du compresseur 0,39 [0,22 ; 0,60] ; volume des cuves 0,28 [0,13 ; 0,46] (seul : 0,05 ; il n'agit qu'avec la pression et l'attente) ; pression maximale 0,26 [0,14 ; 0,44]. Puis température ambiante 0,11, isolant 0,09. Tornade : rendement mécanique ± 1,2 point, hiver +1,5 point, pression 120 → 250 bar −1,6 point mais électricité livrée 20 → 55 kWh. Humidité : indice nul par construction (bilan sur l'air sec).
- **Incertitudes du registre** (rendements du compresseur, efficacités des refroidisseurs, granulométrie) : rendement 17,2 % ± 1,05 point (5–95 %), électricité consommée 235 ± 15 kWh, électricité produite ± 0,3 kWh ; la marge vient du rendement mécanique (Spearman +0,96).
- **Front de Pareto** (NSGA-II, 16 × 12, 208 simulations, graine 1) : du plus léger (134 bar, cuves × 0,5, 24,4 kWh, 2 111 kg) au plus productif (250 bar, cuves × 0,93, 55,3 kWh, 3 947 kg) ; coude à 250 bar et cuves × 0,5 (50,8 kWh, 2 907 kg). La configuration de départ (40,5 kWh, 3 699 kg) est dominée : 40 kWh pour 2 520 kg avec cuves × 0,5. La pression est à sa borne haute sur 47 % du front et les cuves à leur borne basse sur 39 % (signalé par le rapport : la plage limite le front). Revers : à cuves × 0,5, l'air rejeté descend à −38 °C (cibles non tenues, givre) : il faudrait une contrainte ou un troisième objectif.
- **Domaine de validité pendant les balayages** : au nominal déjà, l'air qui quitte la cuve 3 en charge est sous 0 °C (gravier refroidi par la décharge précédente) : condensation et givre dans le lit de gravier signalés par le module de la phase 9 (99 % des simulations) ; cuves « trop froides pour la cible » dans 56 à 65 % des points (petites cuves, basse pression, longue attente) ; extrapolation de l'air humide au-delà de 10 MPa partout.
- Pas doublés (charge 60 s, décharge 10 s) : rendement 17,23 % contre 17,19 % avec les pas d'origine (+0,2 %), 9,7 s par simulation au lieu de 19,6.

### Choix et limites

- Pas de `SALib` ni de `pymoo` : `scipy.stats.sobol_indices` (scipy ≥ 1.12) et NSGA-II maison, vérifié sur ZDT1 ; aucune dépendance ajoutée.
- Paramètres indépendants et uniformes dans leur plage ; plages « choix de l'analyse » affichées comme telles ; `± 20 %` pour une hypothèse sans plage.
- n = 32 pour Sobol est petit (indices bruités, un indice > 1 sur l'électricité livrée) ; doubler n double la durée. Débit réel ≈ 3 s par simulation sur dix processus (contention), pas 1 s.
- Masse : réservoirs (F44) et gravier seulement ; coefficient de sécurité 2,25 et pression de service 300 bar sont des hypothèses, la résistance spécifique équivalente est calibrée (pas de source à DOI lue pour le composite ; IOP et ASM refusent les robots).
- La ligne de commande `analyser` est traitée avant `argparse` (sous-commande à options propres).

### Prochaine étape

Phase 11 (scénarios d'exemple : transport, centre d'urgence, grande échelle, solaire) ; y ajouter une contrainte « air rejeté > 0 °C » ou un objectif de givre aux analyses Pareto.

## 2026-11-21 : phase 9 terminée (humidité, sécheur et séparateur)

### Fait

- **Air humide** `caes/composants/humidite.py` (F42, F43) : teneur en eau à saturation et point de rosée sous pression par CoolProp `HAPropsSI` (ASHRAE RP-1485, facteur d'augmentation inclus), sur la glace sous 0 °C ; saturation infinie quand p_ws(T) approche p (air chaud à basse pression) ; extrapolation à pression partielle constante au-delà de 10 MPa, signalée ; saturation nulle sous 130 K (toute l'eau gelée, signalé) ; mise en cache. `EtatAir` porte `w_vapeur_kg_kg` et `w_liquide_kg_kg` ; `Flux` porte `eau_condensee_kg_s`, `eau_separee_kg_s`, `Q_latente_w`, `givre`, `T_rosee_K`. Chaque composant appelle `mettre_a_l_equilibre` après sa transformation (compresseur : évaporation ; refroidisseur, cuve, détente, turbine : condensation ou givre, avec avertissement). L'eau entre par `ambiance.humidite_relative` (`Ambiance.w_kg_kg`).
- **Sécheur** : `perte_debit` avec `point_de_rosee_sortie` (vapeur ramenée à la saturation à ce point de rosée sous pression, liquide drainé), nouveau modèle `separateur` (`efficacite_separation`, retient les gouttes sans perte d'air). **Réservoir** : vapeur bornée par la saturation à (T, p), excès condensé au fond (`eau_liquide_kg`, `eau_condensee_cumul_kg`, avertissement), réévaporation au réchauffement, l'air sortant emporte la vapeur ; l'air initial porte au plus ce que la chaîne de charge refoule (`plafonner_eau`, non compté comme condensation).
- **Assembleur et sorties** : bilans d'eau par charge (`eau_entree_kg`, `eau_condensee_kg`, `eau_separee_kg`, `eau_reservoir_kg`, `eau_condensee_reservoir_kg`, `chaleur_condensation_kwh`, `T_rosee_reservoir_degC`) et par décharge (`givre_detendeur_kg`, `givre_i_kg`, `givre_total_kg`, points de rosée à chaque sortie, `T_rosee_rejet_K`) ; lignes « eau » dans `resume.md`.
- **Registre** : références `herrmann2009` (ASHRAE RP-1485) et `feistel2006` (IAPWS, glace) ; `humidite.formulation`, `humidite.pression_max_validite` (100 bar), `eau.enthalpie_fusion` (333,4 kJ/kg), `secheur.point_de_rosee_sortie` (−40 °C, hypothèse), `separateur.efficacite` (0,98, hypothèse), `secheur.appoint.efficacite` (0,95, hypothèse). 22 références, 348 paramètres.
- **Scénarios** `scenarios/humidite/` (générés par `generer_humidite.py`) : A et B × {sécheur par adsorption de Dormoy, séparateurs seuls, séparateurs + sécheur d'appoint à 5 %}. **Rapport** `rapports/phase9_humidite.py` → `rapports/phase9/humidite.md`, `fig_givre.png` (≈ 90 s) : six scénarios à 20 °C / 50 %, balayage 30/60/90 % × −20/0/20/30 °C avec séparateurs seuls, référence des deux sécheurs à −20 et 30 °C.
- Tests : `tests/test_humidite.py` (10) ; 278 au total, tous verts (non-régression des phases 1 à 5 toujours à 0,00000 %). Fiches F42, F43 ; `docs/composants/secheur.md`, `reservoir_air.md`, `README.md` ; `docs/phase-09-explication.md`.

### Résultats (`rapports/phase9/humidite.md`, 20 °C et 50 % sauf mention)

| Traitement | Purge | RTE B | RTE A | Eau au fond du réservoir (kg/cycle) | Givre |
|---|---|---|---|---|---|
| Sécheur de Dormoy, point de rosée −40 °C | 19 % | 16,8 % | 4,3 % | 0 | B : 0 ; A : 0,2 g (2 g à −20 °C) |
| Séparateurs seuls | 0 % | 20,7 % | 5,4 % | 0,87 (B), 1,16 (A) | B : 8 g au détendeur ; A : 0,10 kg aux turbines |
| Séparateurs + appoint, point de rosée −40 °C | 5 % | 19,7 % | 5,1 % | 0 | comme le sécheur de Dormoy |

Balayage avec séparateurs seuls : condensation au fond du réservoir de 0,04 kg (−20 °C) à 1,0 kg (30 °C) par cycle, **identique à 30, 60 et 90 % d'humidité** (l'air quitte toujours le dernier refroidisseur saturé ; seule compte sa température face aux points froids suivants). Givre : A de 8 g (−20 °C) à 194 g (30 °C) aux turbines ; B de 12 g (0 °C) à 0 (30 °C) au détendeur.

### Verdict et choix

- **Le sécheur ne peut pas être évité, mais il peut être petit.** Séparateurs seuls : jamais suffisants (douze climats, deux architectures) ; la condition pour s'en passer (dernier refroidisseur plus froid que tout ce que le réservoir rencontre ensuite) n'est jamais remplie avec un refroidisseur à l'air ambiant. Ce qui protège est le **point de rosée sous pression** (doit être sous la température la plus froide rencontrée : ambiance hivernale pour le réservoir, ≈ −5 °C au détendeur de B, −74 °C à la turbine de A, hors de portée : seul le réchauffage protège A), pas la purge. À −40 °C et 5 % de purge, B rend 19,7 % au lieu de 16,8 %. La purge de 5 % est une hypothèse à remplacer par une fiche de fabricant ; un sécheur frigorifique n'est pas modélisé.
- Bilan d'énergie sur l'air sec ; l'eau est suivie en masse, sa chaleur latente est donnée à part (≈ 4 kWh pour les 6 kg condensés d'une charge de B). Équilibre instantané (pas de cinétique de givrage ni de surfusion). Au-delà de 10 MPa, saturation extrapolée.
- Deux pièges corrigés en chemin : (1) l'air initial du réservoir à l'humidité ambiante condensait 3 à 9 kg « fictifs » dès le premier pas (d'où `plafonner_eau`) ; (2) des détentes très froides (115 K dans `tests/test_combinaisons.py`) sortaient du domaine de RP-1485 : la saturation y est prise nulle, avec avertissement, au lieu d'arrêter la simulation.
- Le tableau 1000 unités (phase 3) n'est pas modifié : l'eau n'y entre pas (bilan sur l'air sec) ; la chaleur latente apparaît dans les totaux de charge seulement.

### Prochaine étape

Phase 10 (sensibilité, Pareto, incertitudes) ou phase 11 (scénarios d'exemple) selon le chemin minimal du plan.

## 2026-11-21 : phase 8 terminée (tableau de bord de validation multi-sources)

### Fait

- **Harnais** `validation/tableau_de_bord.py` → `rapports/validation/tableau_de_bord.md`, `tableau_de_bord.csv`, `ecarts.png` : 51 grandeurs comparées à un chiffre publié (référence, simulé, écart, verdict « reproduit » sous 5 % / « écart expliqué » avec paragraphe / **non expliqué**), nature de chaque jeu (mesure, simulation publiée, fabricant), ambiance de chaque article, jeux en attente. Régénéré en ≈ 3 min. Températures comparées avec la tolérance absolue du RMSE de Dormoy (2,83 °C).
- **Jeux de données** `data/validation/<source>/` : `provenance.md` pour huit sources (Dormoy, Shi, Tola disponibles ; Castellani, Luo via Zhang S., Cascetta, Barbour, Venkataramani en attente ou partiels) et `references.csv` généré du registre pour les trois disponibles ; `A_NUMERISER.md` déplacé dans `dormoy/`.
- **Scénarios de validation** `scenarios/validation/` : `shi_100MW.yaml` (cas test de changement d'échelle : compresseurs isentropiques à T_sortie 200 °C, eau sous pression à 18 bar avec réservoir froid maintenu à 30 °C, réservoir adiabatique de 118 000 m³, turbine 1 en pression glissante), `tola_charge.yaml` (polytropique 0,88 à 170 °C, pincement 20 K, caverne quasi isotherme), `tola_decharge_A/B/C.yaml` (turbines polytropiques 0,86 à répartition égale glissante, 130 / 150 / 170 °C).
- Modèles : turbine à **répartition égale glissante** (`pression_sortie_finale`, étages sans `p_sortie`), `perte_de_charge` et `T_initiale` sur les stockages de liquide, `T_froid_maintenue` (hypothèse de Shi) sur les deux réservoirs, `Turbine.preparer` appelé à chaque pas. Registre : 342 paramètres (Tola tableaux 1, 7, 9, 10 et caverne ; Shi figure 7, tableau 5, § 5), unités `t` et `MW`.
- Tests : `tests/test_tableau_de_bord.py` (4) ; 268 au total, tous verts. `docs/phase-08-explication.md`.

### Résultats (`rapports/validation/tableau_de_bord.md`)

| Jeu | Nature | Lignes | Reproduites | Expliquées | Non expliquées |
|---|---|---|---|---|---|
| Dormoy, essais mesurés | mesure | 5 | 5 | 0 | 0 |
| Dormoy, simulations et DEPRAG | simulation publiée, fabricant | 15 | 10 | 4 | 1 (cas de base, −15 %) |
| Tola 2022 | simulation publiée | 16 | 9 (cuves +0,2 à +1,9 %, compresseurs −2 à −3 %, énergie totale +0,9 %) | 7 (turbines +6 à +16 % : source externe constante contre cuves qui refroidissent ; CVHP +16 % : caverne) | 0 |
| Shi 2024 | simulation publiée (prépublication) | 15 | 7 (compresseurs 1 à 3 à 0,1 %, turbines à 3 %, RTE 65,0 contre 67,64 %) | 8 (durées et masse −6 à −9 % : réservoir adiabatique et refroidisseur 4 ; compresseur 4 −7 % : surpression de 0,55 MPa non justifiée par le tableau 4 de Shi) | 0 |

### Découvertes et choix

- **Tola, tableaux 7 et 9 : grandeurs mécaniques**, et le rendement 0,674 du tableau 10 applique 0,97 des deux côtés (28,48 × 0,97 / (39,76 / 0,97)). Le harnais compare les grandeurs mécaniques.
- **Caverne de Tola** : non décrite (gaz parfait, 15 à 55 °C ; 470 à 735 t dans 6500 m³ correspondent à ≈ 35 °C). Adiabatique, elle chaufferait trop (charge en 3,9 h) ; modélisée quasi isotherme à l'ambiant (K_global = 1000 W/m²K, hypothèse signalée), ce qui y met 7 % d'air de plus.
- **Shi** : les refroidisseurs sont les échangeurs du stockage d'eau (air refroidi à T_eau_froide + 10 K) ; le refroidisseur du compresseur 4 (90 → 40 °C) rejette à l'ambiant (à 80 °C son eau diluerait le réservoir chaud) ; réservoir froid maintenu à 30 °C comme dans l'article (sinon le retour des réchauffeurs le porte à ≈ 55 °C et les étages 2 et 3 perdent 23 % de puissance). Sortie du compresseur 4 à 7,55 MPa dans la figure 7 contre 7,24 justifiés : incohérence relevée. La turbine 1 reçoit 10 → 4 MPa, les turbines 2 et 3 restent à pressions fixes (3,22 et 0,55 MPa d'entrée), comme sur la figure 7.
- Le critère « quatre jeux dont deux mesurés » est atteint en comptant les deux essais de Dormoy (charge et décharge, deux installations différentes) comme deux jeux mesurés : il n'existe pas d'autre mesure accessible aujourd'hui. **À faire par l'utilisateur** : déposer les PDF en accès libre de Castellani 2018 (`data/sources/castellani2018/`), Cascetta 2018 et Barbour 2015 ; le harnais a leur dossier et les signale « en attente ».
- Luo (via Zhang S.) : article introuvable, courbes non numérisées, modèle de vanne non implémenté : « partiel ».
- Les scripts des phases 1 à 5 restent fonctionnels (`scenarios/v1/`) ; le tableau de bord travaille avec les scénarios du format « composants ».

### Prochaine étape

Phase 9 (prompt 10) : humidité et sécheur (air humide, point de rosée sous pression, condensation dans les réservoirs, givrage dans les turbines, sécheur contre séparateur), ou phase 11 (scénarios d'exemple) selon le chemin minimal du plan.

## 2026-11-21 : phase 7 terminée (bibliothèque des composants et alternatives)

### Fait

- **Noyau : au moins deux modèles sélectionnables par YAML pour chaque fonction.** Compresseur : `polytropique_dormoy`, `isentropique` (Shi, F34), `polytropique_rendement` (Tola, F35), `isotherme` (borne, Baniamerian éq. 8, F36) ; étages à rapport fixe, à `T_sortie` visée (règle de Tola et Shi, résolue par bissection) ou libres (partage du rapport restant), étage inactif si la pression est déjà atteinte. Refroidisseur : `efficacite`, `pincement` (F37), `perte_de_charge` (Shi) compensée par le dernier étage. Sécheur : `perte_debit`, `aucun`. Réservoir : `K_global`, `paroi`, `adiabatique` (F38) + `surpression_entree`. Détente : `isenthalpique`, `cheayb`, `isotherme`, `pression_glissante` (`p_min`). Turbine : `polytropique_deprag`, `isentropique`, `polytropique_rendement` (pression d'entrée variable), `flugel` (F39 : loi de l'ellipse de Stodola pour le débit, correction de rendement de Zhang S. éq. 2 et 3, pressions inter-étages résolues par bissection). Stockage : `gravier`, `huile_deux_reservoirs` (Tola cas B, Wolf et Budt ; F40), `eau_sous_pression` (Shi ; plafond d'ébullition par CoolProp / IAPWS-95), `huile_ideale`, `source_externe` ; bloc `isolation: {materiau, epaisseur}` → U = 1/(e/k + 1/h_ext) (F41, laine minérale d'Ablaoui 2023). Attente : `pertes_statiques`, `sans_pertes`.
- Code : `caes/composants/<fonction>/` (paquets, physique des modèles dans `<fonction>/<modele>.py`), `caes/composants/isolation.py`, `T_de_p_s` et `gamma` dans `caes/proprietes.py`, `HorsDomaine` (arrêt propre et signalé quand une détente mène sous 100 K), débit variable par pas dans la décharge (`Turbine.debit`), surpression d'entrée du réservoir et pertes de charge aval dans la charge, avis d'assemblage conservés.
- Registre : 20 références (ajout de `wolfbudt2014`, `ablaoui2023`, `wagner2002`, DOI vérifiés via Crossref), 274 paramètres (Tola tableaux 1, 2, 6, 10 ; Shi tableau 4, figure 7, tableau 5 ; Zhang S. éq. 3 et § 4.1.1 ; laine minérale ; `isolation.h_ext` ; `zhangZ.autodecharge_tes`). Unité `j` (jour).
- Scénarios : `scenarios/variantes/` (15 fichiers, un par modèle nouveau, dérivés de Dormoy, générés par `generer_variantes.py` dont les blocs servent aussi aux tests). Rapport `rapports/phase7_variantes.py` → `rapports/phase7/variantes.md`.
- Tests : `tests/test_modeles_phase7.py` (13 : bilans, cas limites, avertissements) et `tests/test_combinaisons.py` (90 : 48 chaînes de charge, 36 de décharge, 6 cycles ; bilans fermés à 1 %) ; 264 tests au total, tous verts. Non-régression des phases 1 à 5 inchangée (0,00000 %).
- Documentation : fiches F34 à F41 ; `docs/composants/*.md` réécrites avec un tableau comparatif des modèles (physique, paramètres, source, quand l'utiliser) et les résultats sur Dormoy ; `docs/phase-07-explication.md` ; `scenarios/README.md` ; `CLAUDE.md`, `README.md`.

### Résultats sur le banc de Dormoy (`rapports/phase7/variantes.md`)

| Changement | Résultat | Lecture |
|---|---|---|
| Compresseur isentropique 0,86 / polytropique 0,88 (rendements méc. et él. de Dormoy) | 445 / 465 kWh au lieu de 386 | rendements de grosses turbomachines, pas un compresseur à pistons : pour le changement d'échelle, pas la validation |
| Borne isotherme | 304 kWh, 17 kWh de chaleur rejetée | l'écart avec Dormoy (82 kWh) est le prix de la chaleur de compression |
| Refroidisseurs à pincement 20 K | 382 kWh | presque Dormoy (ε calibrées 0,85-0,96) |
| Sans sécheur | 310 kWh en 8,0 h | 19 % de l'air comprimé n'est plus jeté |
| Réservoir adiabatique + 0,2 MPa | 252 kWh en 6,4 h, **167 °C** en fin de charge | « la physique change avec la taille » : avertissement sous 1000 m³ |
| Turbine isentropique 0,90 / polytropique 0,86 (rendements DEPRAG) | 33,1 / 32,8 kWh au lieu de 39,0 | même remarque |
| Pression glissante, η constant (Shi) | 38,96 kWh, 70 kWh de réchauffage (45 avec détendeur) | borne optimiste ; l'étage 1 détend de 190 à 11,5 bar |
| Pression glissante + Flügel | 41,05 kWh en **14,9 min**, débit moyen 0,80 kg/s (2,5 × nominal), air rejeté à −78 °C | la DEPRAG n'est pas faite pour 190 bar ; gain de 5 % seulement |
| Huile à deux réservoirs (1500 kg) / eau sous pression (600 kg, 18 bar) | 41,05 kWh, comme le gravier | cibles atteintes ; eau plafonnée à 202 °C (ébullition) ; réservoir froid vide pendant la charge (stockage saturé, les refroidisseurs prennent le reste) |
| Gravier + 20 cm de laine minérale, 14 j d'attente | 37,4 kWh (41,2 sans pertes), 46,5 kWh perdus, turbines à 99 / 58 / 66 °C | les petites cuves perdent tout en deux semaines : point de départ du scénario transport |

### Choix et limites

- Les modèles à rendement constant reçoivent les rendements mécanique et électrique de Dormoy (compresseur) ou de la DEPRAG (turbine) pour isoler l'effet du modèle thermodynamique ; les combinaisons avec les rendements de Shi (0,99 / 0,98) sont à un bloc près dans `generer_variantes.py`.
- Flügel : coefficient t4 = 0,3 de grosses turbines ; le débit du pas utilise les températures d'entrée du pas précédent ; aux grands rapports de pression la correction de rendement reste proche de 1 (débit réduit ≈ constant), le modèle dit surtout que le débit croît comme la pression.
- Deux réservoirs : cp constant (huile : valeur de Tola à l'ambiant, sous-estimée à 160 °C ; eau : cp à mi-chemin ambiant-plafond), réservoirs bien mélangés, échangeur équilibré ; Wolf et Budt 2014 n'a pas été lu (DOI vérifié ; valeurs via Bazdar tableau 3 et Tola cas B).
- Isolant : paroi plane (épaisseur petite devant le diamètre : 25 % d'erreur sur U pour 20 cm sur 0,6 m, dans le sens prudent), k à 20 °C (0,047 à 100 °C : pertes sous-estimées d'au plus 30 %), pas de fond ni de ponts thermiques.
- `HorsDomaine` : une détente sans réchauffage de 190 à 11,5 bar mène sous 100 K (condensation de l'air) ; la simulation s'arrête au premier pas avec un avertissement au lieu de planter dans CoolProp (1 combinaison sur 36).
- Non faits (variantes souhaitables / optionnelles du prompt) : vanne ON/OFF et réservoir tampon (Zhang S. ; l'essai de Luo n'est pas accessible), perte de charge des filtres et tuyauterie (Darcy-Weisbach, Colebrook), fuites du réservoir, matériau à changement de phase, stockage isobare (Pimm 2014, DOI vérifié : 10.1016/j.energy.2013.12.010, non inscrit), éjecteur, piston liquide. La perte de charge des échangeurs (Shi) est faite.
- Sources bloquées aux robots : E3S (conductivité de la laine de basalte) et MDPI (conductivité 223-573 K) ; Ablaoui 2023 lu sur PMC.

### Prochaine étape

Phase 8 (prompt 09) : tableau de bord de validation multi-sources ; le cas test de Shi (100 MW, 4 compresseurs à T_sortie 200 °C, 3 turbines, réservoir adiabatique 4-10 MPa, eau à 18 bar, pression glissante) est maintenant assemblable avec les modèles de cette phase.

## 2026-11-21 : phase 6 terminée (architecture « composants », configurations YAML libres)

### Fait

- **Interface commune des composants** (`caes/composants/base.py`) : `EtatAir` (p_abs_pa, T_K, m_dot_kg_s), `Flux` (travail, chaleur ajoutée avec sa source, chaleur retirée avec sa destination, débit perdu, résultat détaillé), `Contexte` (air, ambiance, instant, pas, pression de refoulement), `Composant` (nom, modèle, paramètres avec provenance, `verifier_validite()`, `avertir()` dédoublonné). Neuf types dans `FABRIQUES` : `compresseur` (polytropique_dormoy, étages comme maillons), `refroidisseur` (efficacite, source froide = ambiance, `recuperation_vers` pour l'huile idéale), `secheur` (perte_debit), `perte_debit` (fraction : rendement volumétrique de Dormoy rendu explicite), `reservoir_air` (K_global, paroi), `stockage_chaleur` (gravier, huile_ideale, source_externe), `detente` (isenthalpique, cheayb, isotherme), `turbine` (polytropique_deprag, laminage inter-étages à la sortie de l'étage amont), `attente` (pertes_statiques).
- **Bloc `ambiance` obligatoire** (`caes/ambiance.py`, F32) : T_amb, p_amb, humidité relative, T_aspiration (défaut T_amb), profil météo CSV optionnel (interpolation ; l'écart air aspiré − ambiant est conservé). Registre : `ambiance.humidite_relative_essai` (hypothèse 50 %), `compresseur.pression_refoulement_max` (190 bar, borne des lois en pression) ; 226 paramètres.
- **Assembleur** (`caes/assembleur.py`, F33) : lit le YAML (section `composants`, chaînes `charge.chaine` et `decharge.chaine`, `simulation.mode` charge | decharge | cycles), vérifie les liaisons (ordre des étages, un seul réservoir partagé, consigne du détendeur = entrée de l'étage 1, pressions décroissantes entre étages, cuves chargées avant d'être déchargées, clés inconnues refusées), construit `Installation` avec `simuler_charge`, `simuler_decharge`, `attendre`, `simuler_cycles`. Séries et totaux gardent les noms des phases 1 à 5 ; `exergie.py` lit désormais ses références (état mort, volume, état initial) dans `ResultatCharge.parametres` au lieu du scénario.
- **Point d'entrée** `python -m caes simuler scenario.yaml [--sortie] [--modifier chemin=valeur[unite]] [--sans-graphiques]` et `python -m caes verifier` ; `caes/sortie.py` écrit `resume.md`, CSV, `tableau_1000.md` + `cascade.png` (ou `exergie.md`), graphiques, `cycles.csv`, `provenance.md` (chaque feuille, sa valeur SI, sa source, et les références du registre citées avec DOI). `caes/tableau_1000.py` et `caes/graphiques.py` sortis de `rapports/` et `validation/` (anciens scripts inchangés via des enveloppes).
- **Scénarios réécrits** : `scenarios/dormoy_*.yaml`, `A.yaml` à `E.yaml`, `D_hiver.yaml` ; anciens fichiers dans `scenarios/v1/` (tests et scripts de validation des phases 1 à 5 redirigés). `scenarios/README.md` décrit le format.
- **Non-régression** : `tests/reference/phases_1_5.yaml` (chiffres calculés par `caes.systeme` et `caes.integre`, générateur conservé), `tests/test_non_regression.py` (16 tests, 0,1 %) ; `validation/non_regression_phase6.py` → `rapports/phase6/non_regression.md` aux réglages de la phase 5 : **pire écart 0,00000 %** sur les 6 scénarios de Dormoy et les architectures A à E (charge, durée, électricité produite, chaleur par source, chaleur restante dans les cuves, tableau 1000 unités).
- 40 tests nouveaux (161 au total, tous verts en 2 min 24 s). Fiches F32, F33 ; F13 généralisée (profil météo). `docs/composants/` (README + une page par type) ; `docs/phase-06-explication.md` ; `README.md` et `CLAUDE.md` à jour.

### Résultat nouveau : D en hiver (`D_hiver.yaml`, −20 °C, air aspiré à l'extérieur)

| | D à 20 °C | D à −20 °C |
|---|---|---|
| Charge 55 → 190 bar | 239,5 kWh, 6,05 h | 231,9 kWh, 5,50 h (air plus dense : 0,067 kg/s) |
| Sorties des étages de compression | 168 / 173 / 194 / 119 °C | 70 / 106 / 128 / 57 °C |
| Entrée des turbines (moy., cible 130 / 90 / 90) | 130 / 90 / 90 °C | 120 / 79 / 52 °C |
| Produit | 41,05 kWh, 39,5 min | 45,32 kWh, 46,2 min |
| RTE | 17,1 % | 19,5 % |
| Air rejeté (min) | 15 °C | −38 °C |

L'hiver rend plus (air plus dense, compression moins chère, réservoir plus lourd à 190 bar) mais les cuves n'atteignent plus leurs cibles et l'air rejeté descend à −38 °C : résultat à relire avec le module humidité (phase 9).

### Choix et limites

- Les modules des phases 1 à 5 (`systeme.py`, `integre.py`) sont conservés comme implémentation physique et pour les scripts de validation (1800 lignes), qui lisent `scenarios/v1/`. Leur portage vers l'assembleur est une dette à traiter en phase 8 (tableau de bord) ; les tests de non-régression protègent les deux chemins.
- `huile_ideale` reste l'hypothèse comptable de Dormoy (la chaleur au-dessus du seuil est déposée par les refroidisseurs sans changer l'air) pour reproduire C exactement ; étiquette `huile` (nom du composant) au lieu de `huile_ideale`. L'huile à deux réservoirs avec échangeurs réels est pour la phase 7.
- Le rendement volumétrique est un maillon `perte_debit` placé après le dernier refroidisseur (convention de Dormoy, tableau 6) ; sans lui, les chaleurs des refroidisseurs changeraient.
- Une seule machine par chaîne (un compresseur, une turbine) ; pas de branches parallèles.
- Découverte rendue visible par les avertissements : dans D, le bas de la cuve 3 est refroidi sous l'ambiant par l'air du détendeur (−5 °C) pendant la décharge ; à la charge suivante, le refroidisseur 3 reçoit de l'air plus froid que l'ambiant et le **réchauffe** (modèle à efficacité symétrique, identique à la phase 5). Une vanne de contournement est une variante pour la phase 7.
- Avertissements : texte fixe (sans nombre variable) pour qu'ils se dédoublonnent ; les extrêmes sont suivis dans des attributs (`T_sortie_min_K`, `T_entree_min_K`, `T_sortie_min_observee_K`).
- Les modèles de turbine et de compresseur sont à point fixe : un air reçu hors de la pression nominale est signalé, pas modélisé (Flügel en phase 7).

### Prochaine étape

Phase 7 (prompt 08) : bibliothèque des composants, au moins deux modèles sélectionnables par YAML pour chaque fonction du noyau (compression isentropique à rendement, échangeur à pincement, réservoir adiabatique, pression glissante avec Flügel, rendement polytropique constant, huile à deux réservoirs), chacun avec fiche, registre, tests et page.

## 2026-11-21 : phase 5 terminée (système intégré Dormoy + gravier)

### Fait

- `caes/systeme.py` et `caes/turbine.py` rendus « branchables » : crochets `CouplageCharge` (cuve entre un étage et son refroidisseur) et `RechauffeurDecharge` (source de chaleur par étage de turbine), reprise d'un réservoir existant pour les cycles, colonnes de séries supplémentaires (`T_in_ref_i`, `Q_cuve_i`).
- `caes/integre.py` : architectures A à E, `ConfigCuves`, `CouplageCuvesCharge`, `CouplageHuileIdeale`, `RechauffeurCuves` (bypass pour viser la cible, pincement de 20 K pour la boucle d'air, pas d'appoint), `RechauffeurHuileIdeale`, `simuler_cycles` (charge → attente → décharge jusqu'au régime stable, critère sur l'électricité et sur la chaleur des cuves), `exergie_cuve`.
- `caes/exergie.py` : bilans étendus aux cuves (exergie stockée, destruction dans l'échange, exergie puisée en décharge) ; l'état initial réel du réservoir est pris dans les totaux quand la simulation reprend un réservoir (cycles).
- Scénarios `A.yaml` à `E.yaml` ; `rapports/phase5_architectures.py` → `rapports/phase5/architectures.md`, tableaux « 1000 unités » et cascades par architecture, balayage de volume `dimensionnement.csv` et figure.
- 8 tests nouveaux (121 au total, tous verts). Fiches F30 et F31, `docs/phase-05-explication.md`.

### Résultats (cycle stable, charge « aspiration chaude »)

| Arch. | Charge | Produit | RTE | Chaleur | Unités sur 1000 | Fiche (à la main) |
|---|---|---|---|---|---|---|
| A | 324,5 kWh | 14,05 kWh | 4,3 % | – | 43 | 46 |
| B | 243,2 | 40,96 | 16,8 % (13,9 % en comptant 51,2 kWh externes) | externe | 168 | 160 |
| C | 243,2 | 40,96 | 16,8 % | huile idéale (réserve excédentaire de 26 kWh) | 168 | ≈ 160 |
| D | 239,5 | 41,05 | 17,1 % | cuves 30,2 / 6,4 / 14,8 kWh | 171 | ≈ 150–155 |
| E | 239,4 | 41,01 | 17,1 % | cuves 30,2 / 6,4 / 14,7 kWh | 171 | ≈ 130–150 |

Dimensionnement : volumes de base [0,35 ; 0,2 ; 0,7] m³ (2,4 t de gravier) = coude de la courbe ; à la moitié, la fin de décharge souffre (T min 99 / 62 / 28 °C, 40,3 kWh) ; au double, rien de plus (41,1 kWh, 137 kWh de chaleur inutilisée). Pressions des cuves 3,3 / 12,3 / 55 bar contre turbines 3 / 11 / 40 bar. Perte de charge 29 / 13 / 1 Pa (0,007 kWh par charge). Chaleur restante dans les cuves de D au cycle stable : 48 kWh.

### Ce que ça change par rapport à la fiche

- D et E produisent autant que B et C : le gravier alimente les turbines exactement à leur température nominale grâce au bypass, et la marge de 40 à 60 K entre la sortie des compresseurs (168–188 °C) et le besoin (130 °C) absorbe les deux pincements de la boucle d'air. La pénalité de fin de décharge de la fiche (−5 %) n'apparaît qu'avec des cuves trop petites.
- Les cuves consomment même un peu moins à la charge (239 contre 243 kWh) : les refroidisseurs reçoivent de l'air moins chaud et le rendent plus froid.
- Volume total ≈ 1,25 m³ au lieu des 2 m³ estimés dans la fiche.
- **Mise à jour des fiches Dormoy et Tola (sections « cuves de gravier » et « 1000 unités ») proposée dans le rapport, à faire seulement avec l'accord de l'utilisateur.**

### Choix et limites

- Réservoir en modèle « paroi » pour toutes les phases du cycle (en phase 1, la charge avait été validée avec le modèle « K global ») ; charge à dt = 30 s, décharge à dt = 5 s, cuves à 30 cellules (20 pour le balayage).
- Attente de 1 h entre charge et décharge, isolation des cuves parfaite : les pertes sont l'objet de la phase 6.
- Le bypass suppose que la sortie de la cuve ne change pas quand le débit baisse ; la température visée est atteinte à 0,5 K près.
- Dans E, la boucle d'air transporte le même débit massique que l'air comprimé (échangeur équilibré) ; pas de perte de charge ni de puissance de ventilateur pour la boucle (à ajouter si la phase 9 le demande).
- Le critère de stabilisation sur la chaleur des cuves (1 %) n'est pas atteint en 4 à 6 cycles pour les cuves surdimensionnées (k ≥ 2) : l'électricité est stable, la chaleur continue de s'accumuler lentement.

### Prochaine étape

Phase 6 (prompt 07) : module `isolation`, attente de 7 à 56 jours avec température extérieure, courbes « chaleur restante » et « électricité livrée », effet d'échelle, fuites d'air.

## 2026-11-19 : phase 4 terminée (lit de gravier)

### Fait

- `caes/materiaux.py` (matériau depuis le registre) et `caes/lit_gravier.py` : modèle de Schumann 1D à deux équations, schéma cellule par cellule exact (NTU + relaxation exponentielle, stable à tout pas de temps, énergie conservée par construction), corrélation de Wakao avec correction de Jeffreson, perte de charge d'Ergun, conduction axiale sous-cyclée, pertes latérales par un coefficient global (interface du module `isolation`, phase 6), solution analytique de Schumann (fonction J de Goldstein) pour la vérification. `n_cellules = 1` donne la cuve bien mélangée.
- Propriétés de transport de l'air ajoutées (`mu`, `k`, `prandtl`) : CoolProp pour l'air réel, Sutherland et Pr constant pour le gaz parfait.
- Registre : 17 références (ajout de Schumann 1929, Wakao 1979, Ergun 1949, Jeffreson 1972, Sutherland 1893, Robertson 1988, Cascetta 2018, Barbour 2015, tous avec DOI) et 224 paramètres (gravier de Tola, corrélations, cuves du cas C de Tola). Unités `Pa.s` et `MWh` ajoutées.
- `validation/lit_gravier.py` → `rapports/phase4/validation_lit_gravier.md` (4 graphiques, `experiences.csv`). 12 tests nouveaux (113 au total, tous verts).
- Fiches F25 à F29, `docs/phase-04-explication.md`, `data/materiaux/README.md`.

### Résultats

| Vérification | Résultat |
|---|---|
| Solution exacte de Schumann | erreur sur la sortie 6 % (20 cellules) → 0,1 % (160) ; bilan d'énergie exact |
| Tola, cas C, cycle stable : TES-LP / IP / HP | 9,61 / 9,68 / 9,88 MWh contre 9,60 / 9,54 / 9,54 (+0,1 / +1,4 / +3,6 %) |
| Tola : sortie en fin de première décharge | 100 °C, exactement la limite de dimensionnement de Tola |
| Tola : stabilisation | 4 cycles (Tola : « moins de 20 », premier cycle seul très différent) |
| Tola : fraction à sortie constante | 57–58 % avec un critère de ± 2 °C (Tola : « environ deux tiers ») |
| Dormoy, cuve 0,5 × 2 m, 0,052 kg/s | Re 145–700, Bi 0,1–0,3, h 26–54 W/m²K, Δp 5–344 Pa selon cailloux et pression |

### Sources expérimentales : non récupérées

Cascetta 2018 (CC BY-NC-ND) et Barbour 2015 (CC BY) sont en accès libre, mais ScienceDirect refuse les accès automatisés (HTTP 403) et le téléchargement direct a été refusé par les garde-fous de la session. Guo 2020 n'a pas été localisé (DOI introuvable via Crossref). **À faire par l'utilisateur :** télécharger les deux PDF à la main et les déposer dans `data/sources/cascetta2018/` et `data/sources/barbour2015/` ; le script de validation détecte le dossier et la comparaison aux profils mesurés sera alors écrite. En attendant, le modèle est vérifié (solution exacte) et croisé (Tola), pas validé expérimentalement.

### Choix et limites

- Correction de lecture du tableau 8 de Tola : diamètre 5,2 m et rapport hauteur/diamètre 2 (texte : « an aspect ratio of 2 was set »), et non 2 m / 5,2 ; vérifié par π/4 × 5,2² × 10,4 = 220,8 m³.
- Conductivité du gravier (2,5 W/m·K) : hypothèse d'après l'USGS (Tola ne la donne pas) ; k_eff = (1 − ε) k_s pour la conduction axiale (borne basse).
- Tola ne publie ni sa corrélation d'échange ni ses pertes : isolation parfaite et Wakao chez nous ; l'accord à 0,1–3,6 % est donc en partie une coïncidence de modèles proches.
- À 50 bar, Re ≈ 10 : hors de la plage de Wakao (signalé par le code).
- Temps de calcul : 3 minutes pour les 60 cycles de Tola (boucle Python par cellule) ; acceptable, optimisable si la phase 5 en a besoin.

### Prochaine étape

Phase 5 (prompt 06) : brancher les cuves sur le banc de Dormoy, architectures A à E, dimensionnement des cuves, plusieurs cycles, tableau « 1000 unités » par architecture.

## 2026-11-19 : phase 3 terminée (bilan d'exergie, tableau « 1000 unités »)

### Fait

- `caes/exergie.py` : classe `Exergie` (exergie de flux, de masse enfermée, de chaleur, éq. 22 de Baniamerian), `exergie_etage_compression`, `bilan_exergie_charge` et `bilan_exergie_decharge`. Chaque destruction est calculée par un bilan d'entropie (D = T₀ · S_gen) à partir des séries temporelles ; la fermeture du bilan global (résidu −0,2 % en charge, 0,00 % en décharge) est donc une vraie vérification.
- Séries des simulations enrichies (pressions, travaux et chaleurs par étage, états avant réchauffage, puissance mécanique par étage).
- `rapports/tableau_1000_unites.py` : enchaîne charge et décharge (la décharge part de l'état final de la charge), écrit `rapports/phase3/tableau_1000_<cas>.md`, `cascade_<cas>.png` et la synthèse `exergie.md` avec la comparaison au calcul à la main de la fiche Dormoy. Trois cas : base (charge B), 3 étages, base avec la charge A.
- 13 tests nouveaux (101 au total, tous verts) : état mort, éq. 22 = exergie fermée du gaz parfait, compresseur isotherme réversible → 0 destruction, bilans fermés à 1 %, destructions ≥ 0, cohérence stock charge / décharge, règle du bilan de chaleur.
- Fiches F21 à F24 dans `docs/formules.md`, `docs/phase-03-explication.md`.

### Résultats (cas de base, 1000 unités = 352 kWh)

| Étape | Fiche (à la main) | Simulateur |
|---|---|---|
| Moteur et mécanique (+ air non refoulé) | 285 | 331 (+ 87) |
| Compression chaude / refroidisseurs | 271 | 5 + 156 (689 unités de chaleur rejetée) |
| Sécheur | 84 | 81 |
| Stocké | 360 | 329 |
| Masse morte (coussin) | 65 (50 bar) | 22 (18 bar), pas une perte |
| Détendeur | 74 (190 → 35 bar) | **234** (190 → 3 bar) |
| Turbine et génératrice | 175 | 25 |
| Air rejeté froid | 0 | 19 |
| Électricité rendue | 46 | 40 |

Cas à 3 étages : 341 stockées, réchauffage externe de 204 unités de chaleur mais seulement 21 d'exergie, 155 rendues (15,5 %).

### Ce que ça change

- **Le détendeur est la perte dominante du cas de base** (68 % de l'exergie disponible), parce que Dormoy détend de 190 à 3 bar. La fiche Dormoy (section 2, tableau 1000 unités) devra être corrigée : masse morte 22 et non 65, détendeur 234 et non 74, turbine 25 et non 175. **Ne pas modifier la fiche sans l'accord de l'utilisateur** (consigne des prompts).
- La chaleur des refroidisseurs vaut 156 unités d'exergie pour 689 d'énergie : c'est la borne haute de ce qu'une cuve de gravier peut apporter.
- La chaleur de réchauffage apporte peu d'exergie (21 pour 204 de chaleur) : elle est « presque gratuite » si elle vient des refroidisseurs (phases 4-5).

### Choix et limites

- Le modèle polytropique de Dormoy est intérieurement réversible : la destruction dans les étages de compression est ≈ 0 ; l'irréversibilité réelle est portée par le rendement mécanique calibré. Pour les étages où n > γ (3 et 4), le modèle « absorbe » un peu de chaleur (−1 unité) : artefact signalé dans le tableau.
- L'exergie de flux de l'air rejeté par la turbine DEPRAG (1,0 bar, sous les 1,013 bar ambiants) est légèrement négative dans le cas à 3 étages : artefact des données fabricant.
- Les cas sont enchaînés (la décharge part de la fin de la charge, 29 °C), pas de 55 °C comme en phase 2 : le tableau est cohérent mais la chaleur de réchauffage à 3 étages (204 unités = 56 kWh) est plus élevée que le tableau 5 de Dormoy. La phase 6 ajoutera l'attente entre les deux.
- L'exergie apportée par le réchauffage est comptée comme le gain d'exergie de l'air (minimum qu'une source doit fournir) ; la destruction dans l'échangeur dépendra de la température de la cuve (phase 5).

### Prochaine étape

Phase 4 (prompt 05) : modèle 1D du lit de gravier (Schumann, Ergun), validation sur des essais publiés (Cascetta 2018, Barbour 2015), vérification croisée avec Tola 2022.

## 2026-11-12 : phase 2 terminée (modèle de décharge, validation sur Dormoy)

### Fait

- Modules : `caes/detendeur.py` (isenthalpique, Cheayb éq. 15, diagnostic « isotherme », arrêt à 15 bar d'écart), `caes/turbine.py` (étages polytropiques éq. 16–17, réchauffage suivi par source), `simuler_decharge` et `rendements_aller_retour` dans `caes/systeme.py` (modes « ventilation » et « turbine », bilan du réservoir et de la chaîne). Cas limite isotherme (n = 1) ajouté au compresseur pour l'analyse paramétrique.
- Scénarios : `dormoy_decharge_essai.yaml` (essai mesuré), `dormoy_decharge_base.yaml` (1 étage), `dormoy_decharge_3etages.yaml`.
- Validation : `validation/dormoy_decharge.py` → `rapports/phase2/validation_decharge.md`, 8 graphiques, 4 tableaux de tendances en CSV. Style de graphiques partagé dans `validation/style_graphiques.py`.
- 88 tests verts (24 nouveaux : détendeur, turbine, décharge).
- Documentation : fiches F15 à F20 dans `docs/formules.md`, `docs/phase-02-explication.md`.
- Registre : 189 paramètres (coefficients de Cheayb lus sur l'image de la page 8, surface et capacité des 8 réservoirs de l'essai, pression d'arrêt du cas de base, hypothèses d'état initial).

### Résultats de validation

| Comparaison | Dormoy | Simulé | Écart |
|---|---|---|---|
| Essai mesuré : durée 190 → 50 bar (2,56 m³, 0,148 kg/s) | 38 min | 37,3 min | −2 % |
| Turbine DEPRAG, tableau 9 (T de sortie, puissances) | 59,2 / 20,7 / 16,0 °C ; 61,9 kW | ≤ 2,5 K ; ≤ 3 % | reproduit |
| 3 étages : chaleur de réchauffage (tableau 5) | 46,2 kWh (24,8 / 6,4 / 15,0) | 44,6 (24,4 / 6,0 / 14,1) | −3,5 % |
| 3 étages : durée | 40 min | 37,6 min | −6 % |
| 3 étages : RTE sans chaleur (charge B, 276 kWh) | 16,0 % | 14,1 % | voir incohérence |
| 3 étages : RTE avec chaleur externe | non calculé | 12,2 % | – |
| Cas de base, 1 étage (3 → 1 bar) | 16,93 kWh | 14,3 kWh | **−15 %, non expliqué** |
| 1 étage réchauffé à 90 °C : RTE | 5,5 % | 5,6 % | ✓ |
| Optimum de pression (charge comptée depuis 1 bar) | 125 bar (sans) / 150 bar (avec) | 125 / 150 bar | ✓ |
| Tendances T ambiante, n, nombre d'étages | fig. 11–16 | mêmes sens | ✓ |

### Découvertes et choix

- **Le cas de base de Dormoy est l'étage 3 seul** (3 → 1 bar) : le détendeur est à 3 bar et la décharge s'arrête à 18 bar, pas à 50 bar. La masse morte vaut 1,6 kWh, non 65 unités sur 1000 : le tableau de la fiche Dormoy (section 4) est à refaire en phase 3.
- **État initial des décharges simulées : 55 °C** (air et paroi), la valeur mesurée au début de l'essai. C'est la seule hypothèse qui reproduit le tableau 5 étage par étage et les températures d'entrée de turbine qu'il implique (13–27 °C). À 20 °C, la chaleur de l'étage 1 est surestimée de 50 %.
- **Incohérence chez Dormoy** : 62 kW × 40 min = 41,3 kWh = 14,2 % de 290 kWh, et non 16,0 % (qui demanderait 45 min). Notre 14,1 % est entre les deux lectures.
- **L'optimum de pression de Dormoy est un artefact de convention** : il n'apparaît que si la recharge est comptée depuis 1 bar (dépense fixe de 1 à 18 bar). Comptée depuis la pression d'arrêt (cycle réel), le rendement décroît de façon monotone avec la pression.
- Le modèle de Cheayb et l'isenthalpique concordent à 1 K près ; sans courbe mesurée publiée, on ne peut pas les départager.
- Le modèle thermique « paroi » (h_int, h_ext, capacité 1,77 MJ/K) est nécessaire en décharge : sans lui (K global), la durée de l'essai tombe à 36 min.

### Écarts connus et questions ouvertes

1. **Cas de base −15 %.** Indépendant de T₀ et du modèle thermique. Diagnostics : le refroidissement Joule-Thomson (190 → 3 bar) et le refroidissement de l'air dans le réservoir coûtent ≈ 1,4 kWh chacun ; sans les deux, 15,8 kWh. Dormoy modélise pourtant ces effets. Hypothèse restante : un détail du calcul de turbine non publié (travail calculé aux conditions nominales ?). Hors du critère de sortie (17 ± 1 kWh) : signalé, pas masqué.
2. Énergie produite avec n = 1 : Dormoy 17,9 kWh (+6 % par rapport à son cas de base) ; chez nous l'énergie produite ne dépend pas de n (les refroidisseurs fixent la température de stockage). Tendance du RTE retrouvée quand même.
3. Température de l'air en fin d'essai de décharge : 6 °C simulés, aucune mesure publiée (MAPE 1,1 % annoncé par Dormoy).

### Prochaine étape

Phase 3 (prompt 04) : bilan d'exergie et tableau « 1000 unités » généré automatiquement, avec la masse morte corrigée (18 bar) et les deux colonnes énergie utile / chaleur.

## 2026-11-09 : phase 1 terminée (modèle de charge, validation sur Dormoy)

### Fait

- Modules : `caes/proprietes.py` (air réel CoolProp + gaz parfait de comparaison), `caes/compresseur.py` (étages polytropiques, éq. 1–5), `caes/refroidisseur.py` (NTU, éq. 6–9), `caes/secheur.py` (éq. 10), `caes/reservoir.py` (éq. 11–14 et 21, modèles « K global » et « paroi »), `caes/scenario.py` (YAML avec références `registre:<id>` et provenance), `caes/systeme.py` (`simuler_charge`, bilan complet), `caes/metriques.py` (RMSE, MAPE).
- Scénarios : `dormoy_charge_1_190.yaml`, `dormoy_charge_1_190_aspiration_chaude.yaml`, `dormoy_charge_55_190.yaml`.
- Validation : `validation/dormoy_charge.py` → `rapports/phase1/validation_charge.md` + 7 graphiques + `totaux.csv` + séries.
- 64 tests pytest verts (registre 12, propriétés 9, compresseur 13, refroidisseur et sécheur 8, réservoir 7, scénario 4, système 11). Bilan d'énergie fermé à moins de 0,001 % ; convergence dt = 10 s contre 2 s à moins de 0,2 %.
- Documentation : `docs/formules.md` (fiches F02 à F14), `docs/phase-01-explication.md`.
- Registre : 9 références (ajout de Lemmon 2000), 173 paramètres (ajout des hypothèses de phase 1 : T ambiante 20 °C, p atmosphérique, pression de refoulement minimale 66 bar, lois linéaires, capacité thermique des parois, R et cp de l'air). Unité `J/K` ajoutée.

### Résultats de validation (1 → 190 bar ; mesure Dormoy : 396 kWh, ≈ 10 h, 39 kW)

| Scénario | Énergie | Durée | Puissance |
|---|---|---|---|
| A : hypothèses minimales (tout à 20 °C, 0,052 kg/s aspirés) | 373 kWh (−5,8 %) | 9,9 h | 37,7 kW (−3,3 %) |
| B : air aspiré à 52 °C (déduit du débit mesuré) | 386 kWh (−2,5 %) | 9,9 h | 39,1 kW (+0,2 %) |
| C : A + débit réservoir mesuré 0,032 kg/s | 409 kWh (+3,2 %) | 10,8 h | 37,7 kW |
| D : B + débit réservoir mesuré | 423 kWh (+6,8 %) | 10,8 h | 39,1 kW |

Par rapport à la **simulation** de Dormoy (366,75 kWh), le scénario A est à +1,7 %. Charge 55 → 190 bar : 6,86 h (Dormoy 6,8 h) ; chaleur rejetée 191,6 kWh avec B (Dormoy 189,2) ; chaleur > 130 °C 66,4 kWh (Dormoy 72,2, −8 %). **Critère de sortie atteint par le scénario B.**

### Découverte : l'air aspiré est à ≈ 50 °C

0,052 kg/s mesurés avec 172,4 m³/h à 1,013 bar impliquent ρ = 1,086 kg/m³, soit 52 °C. Cette seule hypothèse, déduite d'une mesure et non ajustée, corrige en même temps la puissance (39,1 kW), les températures de sortie des étages 1 et 2 (168 et 185 °C, cohérentes avec la fig. 18) et la chaleur récupérable de l'étage 1 (13,7 kWh contre 12,5 chez Dormoy, 0 dans le scénario A). Le compresseur aspire l'air du conteneur, réchauffé par ses propres refroidisseurs.

### Choix de modélisation à retenir

- Le travail de compression s'applique au débit **aspiré** (0,052 kg/s), comme dans le tableau 6 de Dormoy ; le rendement mécanique calibré (69–74 %) absorbe sans doute une partie des pertes volumétriques. Le débit vers les réservoirs est 0,052 × 0,83 × 0,81 = 0,035 kg/s, ou 0,032 mesurés (option du scénario).
- Soupape de pression minimale : refoulement à 66 bar minimum, laminage isenthalpique vers le réservoir en dessous. Déduit des rapports minimaux des étages 3 et 4 (calcul personnel) ; Dormoy parle de 60 bar.
- Lois linéaires en pression pour β₃ (3,54 → 4,44), η_méc (69 → 74 %) et ε₄ (74 → 85 %) : hypothèses, à confronter aux fig. 8 et 10 numérisées.
- Rendement électrique 94,5 % (milieu de la plage fabricant).
- Pertes du réservoir intégrées exactement sur le pas (stable même quand la masse d'air est minuscule).
- Le cache de la chaîne de compression (au 0,1 bar près) rend la simulation rapide : 0,5 s pour une charge complète à dt = 10 s.

### Écarts connus et questions ouvertes

1. Température finale du réservoir : 29 °C simulés ; Dormoy mesure 55 °C au début de l'essai de décharge (contexte différent, réservoir de 2,56 m³). Pas de courbe publiée. À surveiller en phase 2.
2. Sortie du refroidisseur 4 : 43 °C (fiche : 45–60 °C). Température de l'air de refroidissement supposée 20 °C.
3. Chaleur > 130 °C sous-estimée de 8 % (étages 2 et 3) : dépend de la répartition β₃/β₄ et de la température de l'air de refroidissement.
4. 0,032 contre 0,035 kg/s vers le réservoir : indécidable sans la fig. 10 numérisée (durée précise).
5. Aucune courbe numérisée encore (`data/validation/A_NUMERISER.md`) ; le script de validation les intégrera automatiquement (noms de fichiers attendus : `fig10_puissance_mesuree.csv`, `fig10_energie_mesuree.csv`, `fig09_T_sortie_etage4_mesuree.csv`).

### Prochaine étape

Phase 2 (prompt 03) : décharge, détendeur (isenthalpique et Cheayb), turbine DEPRAG à 1 à 3 étages avec les vraies caractéristiques du tableau 9, validation sur l'essai de décharge (190 → 50 bar, 38 min, 0,148 kg/s) et sur les cas simulés (16,93 kWh ; 16 %).

### Note technique

Sur ce poste, un script Bash de plus d'environ 8 Ko est tronqué : écrire les gros fichiers avec l'outil d'écriture, pas avec un heredoc. La console Windows est en cp1252 : les scripts qui impriment des caractères spéciaux forcent `sys.stdout.reconfigure(encoding="utf-8")`.

## 2026-11-02 : phase 0 terminée (projet et registre scientifique)

### Fait

- Projet créé : `pyproject.toml` (Python ≥ 3.11, CoolProp, numpy, scipy, pandas, matplotlib, pyyaml, pytest), `.venv`, dépôt git initialisé (aucun commit).
- **Données supplémentaires de Dormoy récupérées** (tableaux 7, 8, 9) : `data/sources/dormoy-supplementaire/dormoy2024-supplementaire-mmc1.pdf`, téléchargé depuis le CDN d'Elsevier (annexe A de l'article, CC BY-NC). Le PDF est en images : transcription manuelle dans `tableaux-7-8-9.md`, à vérifier sur l'image avant toute conclusion.
- Registre : `data/registre/references.csv` (8 sources, toutes avec DOI ou URL vérifiés) et `parametres.csv` (164 paramètres de Dormoy, dont les 33 du tableau 9 de la turbine DEPRAG). Généré par `generer_registre_phase0.py`.
- `caes/registre.py` : chargeur avec `Parametre` (valeur, plage, unité source, conversion SI, source, niveau de preuve) et `Registre` (vérifications). 12 tests pytest, tous verts.
- `data/validation/A_NUMERISER.md` : liste des 10 figures de Dormoy à numériser, par priorité, avec le mode d'emploi de WebPlotDigitizer pour l'élève.
- `docs/phase-00-explication.md` et squelette de `docs/formules.md`.

### Découvertes utiles

- **Rendement électrique du moteur : 94–95 %** (tableau 7). Il est donc séparé du rendement mécanique calibré (69–74 %). L'hypothèse prévue pour la phase 1 n'est plus nécessaire.
- **Turbine DEPRAG (tableau 9)** : pressions 40 / 11 / 3 bar en entrée, 11,5 / 3,5 / 1,0 bar en sortie ; rendements mécaniques 53 / 64 / 73 % ; électriques 90 / 91 / 92 % ; 0,321 kg/s ; 20,0 + 20,1 + 21,8 = 61,9 kW. Les rapports de pression ne sont pas égaux : l'hypothèse « étages égaux » de la fiche Dormoy (section 4) sera à corriger en phase 2.
- **Réservoirs (tableau 8)** : diamètre intérieur 0,372 m ; paroi aluminium 5 mm (167 W/m·K, 869 J/kg·K, 2700 kg/m³) et fibre de carbone 11 mm (0,60 W/m·K, 900 J/kg·K, 1400 kg/m³) ; masses 107 et 95 kg. Les propriétés de la fibre sont des estimations de Dormoy (niveau `hypothese`).

### Incohérences relevées dans la source (à mentionner dans le rapport, phase 11)

1. Volume total : 8 × 0,32 + 12 × 0,27 = 5,80 m³, mais l'article dit 5,86 m³ (ce qui correspond à 275 L, la valeur de la nomenclature). On garde 5,86.
2. Rapport de compression de l'étage 4 : 1,52–3,5 dans le texte, 1,63–3,50 dans le tableau 7.
3. Débit volumique : 1,609 × 10⁻³ m³ × 1782 tr/min = 172,0 m³/h, l'article dit 172,4.
4. Rendement du cas de base : 4,3 % annoncé = 16,93 / 396 (mesuré) ; 16,93 / 366,75 (simulé) = 4,6 %.

### Questions ouvertes

- Faut-il écrire aux auteurs (didier.haillot@etsmtl.ca) pour demander les courbes brutes ? L'article dit qu'ils n'ont pas la permission de les partager ; les données supplémentaires suffisent pour commencer. Décision reportée après la phase 1.
- `pymupdf` a été installé dans `.venv` uniquement pour lire le PDF supplémentaire en images ; il n'est pas une dépendance du projet.

### Décisions (prises par l'utilisateur le 2 nov. 2026)

Emplacement `Expo-sciences-2026-2027\simulateur\` ; Python ≥ 3.11 (3.11.9 installé) ; Claude écrit le code et l'élève lit les explications ; modules en français, variables physiques usuelles acceptées ; date limite janvier 2027 ; git sans push ni commit sans demande.
