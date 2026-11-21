# Journal du simulateur

*Mis à jour à la fin de chaque session. Le plus récent en haut.*

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
