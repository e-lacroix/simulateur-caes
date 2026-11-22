# Ce que les études ne couvrent pas, et ce que le simulateur en couvre

*Mise à jour du tableau de la section 2 de `plan-v2.md` à la fin de la phase 12 (22 novembre 2026), avec la liste des erreurs trouvées dans les publications et les questions ouvertes. À relire à chaque étude ajoutée (`ajouter-une-etude.md`).*

## 1. Limites des études et réponse du simulateur

| Étude | Limite reconnue ou relevée | Réponse du simulateur | État |
|---|---|---|---|
| Dormoy 2024 | Pas de turbine sur le banc ; sécheur qui perd 19 % de l'air ; pas d'analyse d'exergie ; stockage de chaleur non simulé ; tailles non optimisées ; détendeur obligatoire | Exergie et tableau 1000 unités (phase 3) ; cuves de gravier (phases 4, 5) ; humidité, séparateur et sécheur d'appoint (phase 9 : le sécheur reste nécessaire, à 5 % de purge il rendrait 3 points) ; pression glissante et Flügel comme alternatives au détendeur (phase 7) ; sensibilité et Pareto (phase 10) | fait ; **l'écart de −15 % sur le cas de base reste non expliqué** |
| Tola 2022 | Simulation seule ; pas de perte de charge ; pas de pertes thermiques des cuves ; corrélation d'échange non publiée ; centrale non validée | Lit de gravier avec Ergun, Wakao et pertes (phase 4) ; cuves retrouvées à 0,2–1,9 %, compresseurs à −2 à −3 %, turbines expliquées (source constante contre cuves qui refroidissent) ; pertes pendant l'attente avec isolant (phases 7, 11) | fait (croisement, pas validation) ; validation expérimentale en attente des PDF de Cascetta et Barbour |
| Shi 2024 (prépublication) | Rendements constants ; machines hors point nominal ignorées ; pas de pertes de stockage ; coût du réservoir indépendant de la pression ; non validé | Formule de Flügel (phase 7) ; pertes d'isolation (phase 7) ; cas test à 100 MW : rendement 65,0 % contre 67,64 %, compresseurs à 0,1 %, durées et masse à −6 à −9 % expliqués (phase 8) ; masse du réservoir en fonction de la pression (F44, phase 10) ; scénario grande échelle (phase 11) | fait ; signalé « non révisé » à chaque usage |
| Zhang S. 2025 | Eau chaude sans lit de gravier ; décharge de 6 h ; MAPE jusqu'à 8,7 % ; article de Luo (validation à 90 L) introuvable | Pression glissante et Flügel (phase 7) ; demande variable seconde par seconde par flotte de modules (F47, phase 11) ; modèle de vanne ON/OFF et réservoir tampon non implémentés ; jeu « Luo » marqué partiel au tableau de bord | partiel |
| Baniamerian 2025 | Chaleur de réchauffage non comptée ; tunnel vidé jusqu'à 1 bar ; rendements non justifiés ; formules de coût erronées | Règle du bilan de chaleur (toute chaleur a une source, `cuve_X` ou `externe`) ; pression minimale d'arrêt ; exergie ; borne isotherme (F36) | fait |
| Bazdar 2022 (revue) | Pas de modèles dynamiques cycle après cycle ; stockage isobare non comparé ; filtres ignorés ; tableau sans sources | Cycles jusqu'au régime stable (phase 5) ; registre avec niveau de preuve ; coût des réservoirs hors sol repris avec sa source (phase 11) ; isobare et filtres non faits | partiel |
| Zhang Z. 2021 (revue) | Pas de données de validation ; matériaux à changement de phase sans nombre de cycles | Autodécharge comparée à la plage de la revue (registre) ; option MCP non faite | non fait |
| Wang 2020 | Réservoir isotherme ; indice 1,4 partout ; pas de validation ; réglages d'optimisation absents | Modèles de réservoir au choix (K global, paroi, adiabatique) ; indices calibrés ; NSGA-II avec tous ses réglages imprimés et graine fixe (phase 10) ; boucle heure par heure et scénario solaire non faits | partiel |
| Ablaoui 2023 | Propriétés de la laine minérale à 20 et 100 °C seulement | Isolant à conductivité constante, plage 0,030–0,046 propagée (phase 10) | fait |
| Herrmann 2009 (RP-1485) | Formulation valable jusqu'à 10 MPa | Extrapolation à pression partielle constante au-delà, signalée ; saturation nulle sous 130 K (phase 9) | fait, hypothèse signalée |

## 2. Erreurs et incohérences trouvées dans les publications

Relevées en remplissant le registre ou en reproduisant les résultats ; chacune est dans les `notes` du registre ou dans `JOURNAL.md`.

| Source | Incohérence | Ce que le simulateur retient |
|---|---|---|
| Dormoy 2024 | Volume total : 8 × 0,32 + 12 × 0,27 = 5,80 m³ ; l'article dit 5,86 (correspond à 275 L, valeur de la nomenclature) | 5,86 m³ (valeur utilisée par leurs simulations) |
| Dormoy 2024 | Rapport de compression de l'étage 4 : 1,52–3,5 dans le texte, 1,63–3,50 dans le tableau 7 | plage du texte, notée |
| Dormoy 2024 | Débit volumique : 1,609 × 10⁻³ m³ × 1782 tr/min = 172,0 m³/h, l'article dit 172,4 | 172,4 (valeur annoncée), écart noté |
| Dormoy 2024 | Rendement du cas de base : 4,3 % = 16,93 / 396 (mesuré) ; 16,93 / 366,75 (simulé) = 4,6 % | les deux lectures sont données |
| Dormoy 2024 | Décharge à 3 étages : 62 kW × 40 min = 41,3 kWh = 14,2 % de 290 kWh, et non 16,0 % (qui demanderait 45 min) | notre 14,1 % est entre les deux |
| Dormoy 2024 | L'optimum de pression (125–150 bar) n'existe que si la recharge est comptée depuis 1 bar ; comptée depuis la pression d'arrêt, le rendement décroît de façon monotone | artefact de convention, expliqué (phase 2) |
| Tola 2022 | Les tableaux 7 et 9 sont en grandeurs mécaniques ; le rendement 0,674 du tableau 10 applique 0,97 des deux côtés | comparaison en grandeurs mécaniques (phase 8) |
| Tola 2022 | Caverne non décrite (gaz parfait, 15 à 55 °C) ; 470 à 735 t dans 6500 m³ correspondent à ≈ 35 °C | caverne quasi isotherme, hypothèse signalée |
| Shi 2024 | Figure 7 : compresseur 4 à 7,55 MPa quand le réservoir est à 7 MPa ; le tableau 4 ne justifie que 0,24 MPa de surpression | 7,24 MPa justifiés ; −7 % sur le compresseur 4, expliqué |
| Shi 2024 | Réservoir froid supposé à 30 °C en permanence (le retour des réchauffeurs le porterait à ≈ 55 °C) | `T_froid_maintenue`, hypothèse de l'article reproduite et signalée |
| Wang 2020 | « Capacité CAES » (1 493 à 1 965 kW) non définie ; réglages de NSGA-II absents | cité comme exemple de méthode seulement |

## 3. Questions ouvertes

1. **Cas de base de Dormoy, −15 %** (16,93 kWh publiés, 14,3 simulés) : indépendant de la température initiale et du modèle thermique ; diagnostics faits (Joule-Thomson, refroidissement de la paroi, rendements) sans succès. Le seul écart non expliqué du tableau de bord. Piste : écrire aux auteurs (didier.haillot@etsmtl.ca) pour le détail du calcul du cas de base.
2. **Lois de pression non publiées** : rapport de compression de l'étage 3, rendement mécanique et efficacité du refroidisseur 4 varient avec la pression de refoulement chez Dormoy (plages publiées, loi supposée linéaire ; niveau hypothèse).
3. **Corrélation d'échange de Tola** inconnue ; Wakao utilisée (Reynolds parfois hors de 15–8500, signalé).
4. **Validation expérimentale du gravier** : PDF de Castellani 2018, Cascetta 2018 et Barbour 2015 à déposer par l'utilisateur (sites refusés aux robots) ; dossiers prêts dans `data/validation/`.
5. **Article de Luo** (validation de Zhang S. à 90 L) introuvable.
6. **Composite des bouteilles** : aucune source à DOI lue pour la résistance de la fibre (IOP et ASM refusent les robots) ; résistance spécifique calibrée sur la masse des bouteilles, coefficient de sécurité 2,25 et pression de service 300 bar en hypothèses.
7. **Sécheur** : point de rosée de −40 °C, purge de 5 % de l'appoint et séparateurs à 98 % sont des hypothèses ; fiches de fabricant à trouver.
8. **Profils** : météo (sinusoïde ± 5 K) et demande du centre d'urgence (jour / nuit) sont des hypothèses, à remplacer par des normales climatiques et un profil de bâtiment mesuré.
9. **Flotte de modules** : pas de réservoir tampon ni de régulation continue (Zhang) ; démarrage instantané.
10. **Scénario solaire** (Wang, boucle heure par heure) non fait ; stockage isobare, filtres, matériaux à changement de phase non faits.
11. **Test par un tiers** du guide de démarrage (critère de sortie de la phase 12) : à faire faire, résultat à noter dans `JOURNAL.md`.
