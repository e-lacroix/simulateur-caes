# Référence de l'API du paquet `caes`

*Générée par `python docs/generer_api.py` depuis les docstrings (premier paragraphe de chaque objet). Les modules des phases 1 à 5 (`systeme`, `integre`, `compresseur`, `turbine`, `reservoir`, `lit_gravier`, `exergie`) restent l'implémentation physique ; les composants de la phase 6 les enveloppent. Le point d'entrée est `python -m caes` (`caes/__main__.py`). Les équations sont dans `formules.md` (le code y renvoie par `#Fnn`).*

## Modules

- `caes`
- `caes.__main__`
- `caes.ambiance`
- `caes.analyse`
- `caes.analyse.evaluation`
- `caes.analyse.incertitudes`
- `caes.analyse.lot`
- `caes.analyse.masse`
- `caes.analyse.parametres`
- `caes.analyse.pareto`
- `caes.analyse.rapport`
- `caes.analyse.sensibilite`
- `caes.assembleur`
- `caes.composants`
- `caes.composants.attente`
- `caes.composants.base`
- `caes.composants.compresseur`
- `caes.composants.compresseur.isotherme`
- `caes.composants.compresseur.rendement`
- `caes.composants.detente`
- `caes.composants.humidite`
- `caes.composants.isolation`
- `caes.composants.refroidisseur`
- `caes.composants.refroidisseur.pincement`
- `caes.composants.reservoir_air`
- `caes.composants.secheur`
- `caes.composants.stockage_chaleur`
- `caes.composants.stockage_chaleur.deux_reservoirs`
- `caes.composants.turbine`
- `caes.composants.turbine.flugel`
- `caes.composants.turbine.rendement`
- `caes.compresseur`
- `caes.detendeur`
- `caes.exergie`
- `caes.flotte`
- `caes.graphiques`
- `caes.integre`
- `caes.lit_gravier`
- `caes.materiaux`
- `caes.metriques`
- `caes.proprietes`
- `caes.refroidisseur`
- `caes.registre`
- `caes.reservoir`
- `caes.scenario`
- `caes.secheur`
- `caes.sortie`
- `caes.systeme`
- `caes.tableau_1000`
- `caes.turbine`

## `caes`

## `caes.__main__`

Point d'entrée unique du simulateur (phase 6).

### `main(argv: 'list[str] | None' = None) -> 'int'`

## `caes.ambiance`

Conditions de l'air ambiant d'une installation (bloc ``ambiance``).

### classe `Ambiance`

Conditions ambiantes, constantes ou suivant un profil dans le temps.

- propriété `a_un_profil` : 
- propriété `w_kg_kg` : Teneur en eau de l'air extérieur [kg/kg] à (T_amb, p_amb, φ) (F42) ; constante même avec un profil (l'humidité absolue de l'air aspiré est prise au point de référence du bloc).
- propriété `ecart_aspiration_K` : Écart déclaré entre l'air aspiré et l'ambiant [K].
- `T_amb_a(self, t_s: 'float') -> 'float'` : Température extérieure [K] à l'instant ``t_s`` (#F32).
- `T_aspiration_a(self, t_s: 'float') -> 'float'` : Température de l'air aspiré [K] à l'instant ``t_s``.
- `verifier_validite(self) -> 'list[str]'` : Avertissements sur des conditions inhabituelles.
- `description(self) -> 'str'` : 

### classe `ErreurAmbiance`

Le bloc ``ambiance`` est absent ou incomplet.

### `ambiance_depuis_valeurs(bloc: 'dict[str, Any] | None', provenance: 'dict[str, str]', dossier: 'Path | None' = None) -> 'Ambiance'`

Construit l'ambiance à partir du bloc résolu (valeurs SI).

### `charger_profil(chemin: 'Path') -> 'tuple[np.ndarray, np.ndarray]'`

Lit un CSV de profil météo : une colonne de temps (``t_s``, ``t_h`` ou ``t_j``) et une de température (``T_amb_K`` ou ``T_amb_degC``). Retourne (t en s, T en K), temps croissants.

## `caes.analyse`

Analyse d'une configuration (phase 10) : sensibilité, incertitudes, front de Pareto, masse des réservoirs, surveillance des domaines de validité.

## `caes.analyse.evaluation`

Évaluer un point de l'espace des paramètres : scénario modifié → simulation → sorties, en série ou dans un bassin de processus.

### classe `Evaluateur`

Simule le scénario de l'analyse en un point donné.

- `scenario_modifie(self, point: 'dict[str, float]') -> 'Scenario'` : 
- `evaluer(self, point: 'dict[str, float]') -> 'ResultatPoint'` : 
- `ouvrir(self, procs: 'int | None') -> 'Evaluateur'` : Ouvre un bassin de processus (``procs`` ≤ 1 : en série).
- `fermer(self) -> 'None'` : 
- `evaluer_points(self, points: 'list[dict[str, float]]', rappel: 'Callable[[int, int, ResultatPoint], None] | None' = None) -> 'list[ResultatPoint]'` : Évalue une liste de points (cache, puis bassin ou série).
- `point_nominal(self, parametres: 'Iterable[ParametreAnalyse]') -> 'dict[str, float]'` : 

### classe `ResultatPoint`

Sorties d'une simulation en un point.

- propriété `valide` : 

### `extraire_sorties(res: 'ResultatSimulation', inst: 'Installation', noms: 'Iterable[str]', pm: 'ParametresMasse | None', p_conception_pa: 'float | None') -> 'dict[str, float]'`

Les sorties demandées, lues dans le résultat de simulation.

## `caes.analyse.incertitudes`

Propagation des incertitudes du registre vers les résultats (formules.md#F45).

### classe `IntervalleSortie`

IntervalleSortie(sortie: 'str', nominal: 'float', minimum: 'float', p05: 'float', mediane: 'float', p95: 'float', maximum: 'float', ecart_type: 'float', n_valides: 'int')

- propriété `demi_largeur_90` : 

### classe `ResultatIncertitudes`

ResultatIncertitudes(parametres: 'list[ParametreAnalyse]', sorties: 'list[str]', n: 'int', graine: 'int', echantillons: 'np.ndarray', valeurs: 'np.ndarray', intervalles: 'list[IntervalleSortie]', spearman: 'np.ndarray', resultats: 'list[ResultatPoint]' = <factory>)

- propriété `echecs` : 
- `intervalle(self, sortie: 'str') -> 'IntervalleSortie'` : 

### `propager(ev: 'Evaluateur', parametres: 'list[ParametreAnalyse]', sorties: 'list[str]', n: 'int' = 64, graine: 'int' = 1, rappel=None) -> 'ResultatIncertitudes'`

Hypercube latin de ``n`` points dans les plages, simulations, intervalles et corrélations de rang.

## `caes.analyse.lot`

Simuler un lot de variantes d'un scénario, en parallèle, et n'en garder qu'un résumé transportable (totaux, cycles, avertissements).

### classe `ResumeSimulation`

ResumeSimulation(modifications: 'list[str]', rendements: 'dict[str, float]', charge: 'dict[str, float]', decharge: 'dict[str, float]', attente_h: 'float' = 0.0, chaleur_cuves_debut_kwh: 'float' = 0.0, chaleur_cuves_fin_kwh: 'float' = 0.0, pertes_attente_kwh: 'float' = 0.0, nombre_cycles: 'int' = 0, converge: 'bool | None' = None, avertissements: 'list[str]' = <factory>, erreur: 'str' = '', series_decharge: 'pd.DataFrame | None' = None, masse_fuite_kg: 'float' = 0.0)

- propriété `valide` : 

### `resumer(res: 'ResultatSimulation', modifs: 'list[str]', series: 'bool' = False) -> 'ResumeSimulation'`

### `simuler_lot(chemin: 'Path | str', lot: 'list[list[str]]', procs: 'int | None' = None, series: 'bool' = False, rappel: 'Callable[[int, int, ResumeSimulation], None] | None' = None) -> 'list[ResumeSimulation]'`

Toutes les variantes du lot (bassin de processus si ``procs`` > 1), dans l'ordre du lot.

### `simuler_scenarios(taches: 'list[tuple[Path | str, list[str]]]', procs: 'int | None' = None, series: 'bool' = False, rappel: 'Callable[[int, int, ResumeSimulation], None] | None' = None) -> 'list[ResumeSimulation]'`

Comme :func:`simuler_lot`, mais chaque tâche porte son propre scénario : ``[(chemin, modifications), ...]``.

### `simuler_un(chemin: 'Path | str', modifs: 'list[str]', registre: 'Registre | None' = None, series: 'bool' = False) -> 'ResumeSimulation'`

Une variante, en série, résumée ; une erreur d'assemblage ou de simulation est rendue dans ``erreur`` plutôt que levée.

## `caes.analyse.masse`

Masse des réservoirs d'air à paroi mince (formules.md#F44) et masse des stockages de chaleur.

### classe `MasseReservoir`

MasseReservoir(masse_kg: 'float', volume_cylindre_m3: 'float', volume_fonds_m3: 'float', epaisseur_equivalente_m: 'float')

### classe `ParametresMasse`

Bloc ``masse`` du fichier d'analyse, résolu.

### `masse_reservoir_paroi_mince(p_conception_pa: 'float', volume_m3: 'float', diametre_m: 'float', resistance_specifique_j_kg: 'float', coefficient_securite: 'float', masse_volumique_kg_m3: 'float | None' = None) -> 'MasseReservoir'`

Masse d'une enveloppe cylindrique à fonds hémisphériques (#F44).

### `masses_installation(inst: 'Installation', p_conception_abs_pa: 'float', pm: 'ParametresMasse') -> 'dict[str, float]'`

Masses des réservoirs d'air (F44) et des stockages de chaleur (gravier : volume × (1 − ε) × ρ ; liquides : masse déclarée).

## `caes.analyse.parametres`

Fichier d'analyse (YAML) : scénario de base, paramètres et plages.

### classe `Analyse`

Contenu résolu d'un fichier d'analyse.

- `parametre(self, nom: 'str') -> 'ParametreAnalyse'` : 
- `selection(self, noms: 'list[str] | None') -> 'list[ParametreAnalyse]'` : 

### classe `ErreurAnalyse`

Fichier d'analyse incohérent.

### classe `ParametreAnalyse`

Un paramètre que l'analyse fait varier.

- propriété `nominal` : 
- `modifications(self, x: 'float') -> 'dict[str, float]'` : Les feuilles du scénario à remplacer pour la valeur ``x``.
- `affichage(self, x: 'float') -> 'float'` : ``x`` dans l'unité d'affichage (facteur : tel quel).
- `depuis_normalise(self, u: 'float') -> 'float'` : u ∈ [0, 1] → valeur dans la plage.
- `texte_plage(self) -> 'str'` : 

### `charger_analyse(chemin: 'Path | str', registre: 'Registre | None' = None) -> 'Analyse'`

Lit un fichier d'analyse et résout ses paramètres.

### `depuis_si(valeur: 'float', unite: 'str') -> 'float'`

### `vers_si(valeur: 'float', unite: 'str') -> 'float'`

## `caes.analyse.pareto`

Front de Pareto à deux objectifs par NSGA-II (formules.md#F46).

### classe `ReglagesNSGA2`

ReglagesNSGA2(population: 'int' = 24, generations: 'int' = 15, p_croisement: 'float' = 0.9, eta_croisement: 'float' = 15.0, p_mutation: 'float | None' = None, eta_mutation: 'float' = 20.0, graine: 'int' = 1)

### classe `ResultatPareto`

ResultatPareto(reglages: 'ReglagesNSGA2', X: 'np.ndarray', F: 'np.ndarray', front: 'np.ndarray', generations: 'list[np.ndarray]' = <factory>)

- propriété `evaluations` : 
- propriété `echecs` : 

### `distance_encombrement(F: 'np.ndarray', front: 'list[int]') -> 'np.ndarray'`

Distance d'encombrement de chaque point du front (∞ aux bouts).

### `nsga2(evaluer: 'Callable[[np.ndarray], np.ndarray]', d: 'int', reglages: 'ReglagesNSGA2' = ReglagesNSGA2(population=24, generations=15, p_croisement=0.9, eta_croisement=15.0, p_mutation=None, eta_mutation=20.0, graine=1), rappel: 'Callable[[int, np.ndarray, np.ndarray], None] | None' = None) -> 'ResultatPareto'`

``evaluer(U)`` reçoit une matrice (k, d) de variables dans [0, 1] et rend (k, m) objectifs à minimiser (nan si échec).

### `tri_non_domine(F: 'np.ndarray') -> 'list[list[int]]'`

Rangs de non-dominance (minimisation) : liste de fronts, chacun une liste d'indices. Front 0 = points non dominés.

## `caes.analyse.rapport`

Exécution complète d'une analyse et écriture du rapport (Markdown, CSV, figures) dans un dossier.

### classe `ResultatsAnalyse`

ResultatsAnalyse(nominal: 'ResultatPoint', tornade: 'ResultatTornade | None' = None, sobol: 'ResultatSobol | None' = None, incertitudes: 'ResultatIncertitudes | None' = None, pareto: 'ResultatPareto | None' = None, pareto_variables: 'list[ParametreAnalyse]' = <factory>, pareto_objectifs: 'list[dict]' = <factory>, pareto_points: 'list[ResultatPoint]' = <factory>, durees_s: 'dict[str, float]' = <factory>, procs: 'int' = 1)

- `tous_les_points(self) -> 'list[ResultatPoint]'` : 

### `ecrire_rapport(an: 'Analyse', res: 'ResultatsAnalyse', dossier: 'Path', commande: 'str' = '') -> 'Path'`

### `executer(an: 'Analyse', procs: 'int | None' = None, etapes: 'tuple[str, ...]' = ('tornade', 'sobol', 'incertitudes', 'pareto'), rapide: 'bool' = False) -> 'ResultatsAnalyse'`

Lance les étapes demandées ; ``rapide`` réduit les tailles d'échantillon (essai de format, pas un résultat).

### `main(argv: 'list[str] | None' = None) -> 'int'`

Ligne de commande (appelée par ``python -m caes analyser``).

### `relire_resultats(dossier: 'Path') -> 'ResultatsAnalyse'`

Résultats d'une exécution précédente (``resultats.pkl``), pour réécrire le rapport sans resimuler (``--rendu``).

## `caes.analyse.sensibilite`

Sensibilité d'une configuration (formules.md#F45).

### classe `LigneTornade`

LigneTornade(parametre: 'ParametreAnalyse', sortie: 'str', nominal: 'float', bas: 'float', haut: 'float')

- propriété `balancement` : 

### classe `ResultatSobol`

ResultatSobol(parametres: 'list[ParametreAnalyse]', sorties: 'list[str]', n: 'int', graine: 'int', premier_ordre: 'np.ndarray', total: 'np.ndarray', premier_ordre_ic: 'np.ndarray | None' = None, total_ic: 'np.ndarray | None' = None, resultats: 'list[ResultatPoint]' = <factory>, echecs: 'int' = 0)

- `classement(self, sortie: 'str') -> 'list[tuple[ParametreAnalyse, float, float]]'` : 

### classe `ResultatTornade`

ResultatTornade(lignes: 'list[LigneTornade]', nominal: 'ResultatPoint', resultats: 'list[ResultatPoint]')

- `classement(self, sortie: 'str') -> 'list[LigneTornade]'` : Lignes de la sortie, du plus grand balancement au plus petit (les écarts non calculables, nan, à la fin).
- propriété `echecs` : 

### `indices_de_sobol(ev: 'Evaluateur', parametres: 'list[ParametreAnalyse]', sorties: 'list[str]', n: 'int' = 64, graine: 'int' = 1, bootstrap: 'bool' = True, rappel=None) -> 'ResultatSobol'`

Indices de Sobol de premier ordre et totaux par l'estimateur de Saltelli (``scipy.stats.sobol_indices``), paramètres uniformes dans leurs plages. ``n`` doit être une puissance de 2.

### `un_parametre_a_la_fois(ev: 'Evaluateur', parametres: 'list[ParametreAnalyse]', sorties: 'list[str]', rappel=None) -> 'ResultatTornade'`

Nominal, puis chaque paramètre à ses deux bornes (2d + 1 runs).

## `caes.assembleur`

Assembleur : du fichier YAML à la simulation (phase 6).

### classe `ChaineCharge`

ChaineCharge(elements: 'list[ElementChaine]', compresseur: 'Compresseur', reservoir: 'ReservoirAir', segments: 'list[Segment]', stockage_par_etage: 'dict[int, StockageChaleur]', p_cible_pa: 'float', dt_s: 'float', duree_max_s: 'float', etat_initial: 'dict[str, float] | None', surpression_aval_pa: 'float' = 0.0)

### classe `ChaineDecharge`

ChaineDecharge(elements: 'list[ElementChaine]', reservoir: 'ReservoirAir', detente: 'Detente | None', turbine: 'Turbine | None', segments: 'list[Segment]', cibles: 'dict[int, float | None]', debit_impose_kg_s: 'float | None', dt_s: 'float', duree_max_s: 'float', etat_initial: 'dict[str, float] | None')

### classe `Cycle`

Cycle(numero: 'int', charge: 'ResultatCharge', decharge: 'ResultatDecharge', attente_h: 'float', chaleur_cuves_debut_kwh: 'float', chaleur_cuves_fin_kwh: 'float', pertes_attente_kwh: 'float')

### classe `ErreurAssemblage`

Le scénario ne décrit pas une installation cohérente.

### classe `Installation`

Installation(nom: 'str', description: 'str', scenario: 'Scenario', ambiance: 'Ambiance', air: 'Air', registre: 'Registre', composants: 'dict[str, Composant]', mode: 'str', charge: 'ChaineCharge | None', decharge: 'ChaineDecharge | None', attente: 'Attente | None', options: 'dict[str, Any]', avis_statiques: 'list[Avertissement]' = <factory>, avis_assemblage: 'list[Avertissement]' = <factory>)

- propriété `stockages` : 
- propriété `reservoir` : 
- `avertissements(self) -> 'list[Avertissement]'` : Avis statiques (vérification) puis dynamiques (simulation).
- `verifier(self) -> 'list[Avertissement]'` : Vérifications statiques de l'ambiance et des composants.
- `description_composants(self) -> 'list[str]'` : 
- `simuler(self) -> 'ResultatSimulation'` : Lance la simulation selon ``simulation.mode``.
- `simuler_charge(self, reprise: 'bool' = False, t0_s: 'float' = 0.0) -> 'ResultatCharge'` : Charge jusqu'à la pression cible (formules.md#F13).
- `simuler_decharge(self, reprise: 'bool' = False, t0_s: 'float' = 0.0) -> 'ResultatDecharge'` : Décharge jusqu'à l'arrêt du détendeur (formules.md#F17 à #F20).
- `attendre(self, t0_s: 'float') -> 'tuple[dict[str, float], float]'` : Attente entre charge et décharge ; retourne (pertes, t final).
- `simuler_cycles(self) -> 'ResultatSimulation'` : Charge → attente → décharge jusqu'au régime stable.

### classe `ResultatSimulation`

Ce que rend :meth:`Installation.simuler`, selon le mode.

- propriété `dernier_cycle` : 
- propriété `charge_finale` : 
- propriété `decharge_finale` : 
- `rendements(self) -> 'dict[str, float] | None'` : 
- propriété `avertissements` : 
- `resume(self) -> 'str'` : 

### `appliquer_modifications(sc: 'Scenario', modifications: 'list[str]') -> 'Scenario'`

Applique des remplacements « chemin=valeur[unite] » (ligne de commande), par exemple ``ambiance.T_amb=-20degC``.

### `charger_installation(chemin: 'Path | str | Scenario', registre: 'Registre | None' = None, air: 'Air | None' = None, modifications: 'list[str] | None' = None) -> 'Installation'`

Lit un scénario YAML (format phase 6) et assemble l'installation.

### `construire_installation(sc: 'Scenario', registre: 'Registre | None' = None, air: 'Air | None' = None) -> 'Installation'`

Construit l'installation décrite par un scénario résolu (SI).

### `simuler(chemin: 'Path | str | Scenario', registre: 'Registre | None' = None, modifications: 'list[str] | None' = None) -> 'ResultatSimulation'`

Raccourci : charge le scénario, vérifie et simule.

## `caes.composants`

Bibliothèque de composants interchangeables (phase 6).

## `caes.composants.attente`

Composant « attente » : le temps qui passe entre charge et décharge.

### classe `Attente`

Classe de base : nom, modèle, paramètres, provenance, avis.

- `pas_de_temps(self) -> 'float'` : 
- `executer(self, ctx: 'Contexte', reservoir: 'ReservoirAir | None', stockages: 'list[StockageChaleur]') -> 'dict[str, float]'` : Fait passer le temps ; retourne les pertes [J] et la durée.
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).

## `caes.composants.base`

Interface commune de tous les composants (phase 6).

### classe `Avertissement`

Avertissement(composant: 'str', message: 'str', occurrences: 'int' = 1)

### classe `Composant`

Classe de base : nom, modèle, paramètres, provenance, avis.

- `param(self, cle: 'str', defaut: 'Any' = <object object at 0x000002123F497640>) -> 'Any'` : Valeur SI d'un paramètre ; erreur claire s'il manque.
- `nombre(self, cle: 'str', defaut: 'Any' = <object object at 0x000002123F497640>) -> 'float'` : 
- `avertir(self, message: 'str') -> 'None'` : Enregistre un avertissement (dédoublonné, compté).
- propriété `avertissements` : 
- `effacer_avertissements(self) -> 'None'` : 
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).
- `reinitialiser(self) -> 'None'` : Remet l'état interne à zéro (composants avec mémoire).
- `description(self) -> 'str'` : 
- `parametres_affiches(self) -> 'dict[str, Any]'` : Paramètres à montrer dans les rapports (SI).

### classe `Contexte`

Ce que chaque composant reçoit à chaque pas, en plus de l'air.

- propriété `T_amb_K` : 
- propriété `p_amb_pa` : 
- propriété `T_aspiration_K` : 

### classe `ElementChaine`

Un maillon d'une chaîne : un composant, ou un étage d'une machine.

- propriété `nom` : 
- propriété `type_` : 

### classe `ErreurComposant`

Paramètre manquant, modèle inconnu ou valeur hors limites.

### classe `EtatAir`

État d'un écoulement d'air à un point de la chaîne.

- propriété `w_total_kg_kg` : 
- `remplacer(self, **changements: 'float') -> 'EtatAir'` : 

### classe `Flux`

Flux d'énergie d'un composant pendant un pas, en puissances [W].

### classe `HorsDomaine`

L'état de l'air sort du domaine où le modèle a un sens (par exemple une détente jusqu'à la liquéfaction) : la simulation s'arrête proprement et le signale.

### classe `Segment`

Dans une chaîne, ce qui suit un étage de machine jusqu'au suivant.

## `caes.composants.compresseur`

Composant « compresseur » : une machine à plusieurs étages.

### classe `Compresseur`

Classe de base : nom, modèle, paramètres, provenance, avis.

- propriété `nb_etages` : 
- `etage(self, numero: 'int') -> 'EtageCompresseur'` : 
- `rendement_etage(self, numero: 'int') -> 'float'` : 
- `nb_etages_libres_depuis(self, numero: 'int') -> 'int'` : Étages sans consigne (ni rapport ni T_sortie) de ``numero`` à la fin, l'étage ``numero`` compris.
- `preparer(self, p_reservoir_pa: 'float', p_aspiration_pa: 'float', surpression_pa: 'float' = 0.0) -> 'None'` : Fixe la pression de refoulement du pas (et les rapports pour le modèle de Dormoy).
- propriété `cle_cache` : 
- `debit_aspire(self, ctx: 'Contexte') -> 'float'` : Débit massique aspiré [kg/s] (formules.md#F06).
- `rendement_mecanique(self) -> 'float'` : 
- `puissance_electrique_depuis_travail(self, W_pol_w: 'float') -> 'float'` : Puissance électrique [W] pour un travail polytropique total [W] fourni à l'air par tous les étages (formules.md#F08).
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).

### classe `EtageCompresseur`

Vue « maillon » de l'étage ``numero`` d'une machine.

- propriété `nom` : 
- `rapport(self, ctx: 'Contexte', p_in: 'float', T_in: 'float') -> 'float'` : Rapport de pression de l'étage pour ce pas (formules.md#F33).
- `pas(self, etat: 'EtatAir', ctx: 'Contexte') -> 'tuple[EtatAir, Flux]'` : Compression d'un étage selon le modèle de la machine.

## `caes.composants.compresseur.isotherme`

Compression isotherme : la borne inférieure du travail (formules.md#F36).

### `comprimer_isotherme(air: 'Air', p_in_pa: 'float', T_in_K: 'float', beta: 'float') -> 'ResultatEtage'`

Compression isotherme réversible : T_out = T_in, w = p·v·ln β.

## `caes.composants.compresseur.rendement`

Compression adiabatique à rendement : isentropique (Shi 2024) ou polytropique (Tola 2022).

### `comprimer_isentropique(air: 'Air', p_in_pa: 'float', T_in_K: 'float', beta: 'float', eta_s: 'float') -> 'ResultatEtage'`

Compression adiabatique à rendement isentropique (#F34).

### `comprimer_polytropique_rendement(air: 'Air', p_in_pa: 'float', T_in_K: 'float', beta: 'float', eta_p: 'float') -> 'ResultatEtage'`

Compression adiabatique à rendement polytropique (#F35).

## `caes.composants.detente`

Composant « détente » : ce qui se passe entre le réservoir et la turbine.

### classe `Detente`

Classe de base : nom, modèle, paramètres, provenance, avis.

- propriété `glissante` : 
- propriété `p_consigne_pa` : 
- propriété `p_arret_pa` : 
- `peut_fonctionner(self, p_reservoir_pa: 'float') -> 'bool'` : 
- `p_sortie_pour(self, p_reservoir_pa: 'float') -> 'float'` : Pression livrée à la turbine pour une pression de réservoir.
- `pas(self, etat: 'EtatAir', ctx: 'Contexte') -> 'tuple[EtatAir, Flux]'` : 
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).

## `caes.composants.humidite`

Air humide : teneur en eau, saturation, point de rosée, givre (phase 9, formules.md#F42 et #F43).

### classe `Equilibre`

Résultat d'une mise à l'équilibre vapeur / liquide.

### classe `HorsDomaineHumidite`

État hors du domaine de la formulation d'air humide.

### `enthalpie_condensation(T_K: 'float') -> 'float'`

Chaleur libérée par kg d'eau qui se condense à T [J/kg] : enthalpie de vaporisation (IAPWS-95 via CoolProp), plus l'enthalpie de fusion de la glace quand il se forme du givre (T < 0 °C).

### `equilibrer(T_K: 'float', p_abs_pa: 'float', w_vapeur: 'float', w_liquide: 'float') -> 'Equilibre'`

Répartit l'eau entre vapeur et liquide à (T, p) : la vapeur ne peut pas dépasser la saturation, le liquide s'évapore si l'air est sous-saturé (#F43).

### `hors_validite(p_abs_pa: 'float') -> 'bool'`

### `mettre_a_l_equilibre(etat: 'EtatAir', flux: 'Flux', composant: 'Composant | None' = None, etiquette: 'str' = '', avertir_condensation: 'bool' = True) -> 'EtatAir'`

Met l'eau de ``etat`` à l'équilibre à son (T, p), remplit les champs d'eau du flux et avertit (givre, condensation).

### `point_de_rosee(p_abs_pa: 'float', w_kg_kg: 'float') -> 'float'`

Température de rosée (ou de givre sous 0 °C) [K] à la pression p pour une teneur w en vapeur ; −inf pour un air sec.

### `sous_domaine_froid(T_K: 'float') -> 'bool'`

Vrai sous 130 K : la formulation RP-1485 ne s'applique plus ; la pression de vapeur de la glace y est négligeable (< 1e-6 Pa), toute l'eau est considérée gelée (teneur à saturation nulle).

### `w_de_humidite_relative(T_K: 'float', p_abs_pa: 'float', humidite_relative: 'float') -> 'float'`

Teneur en eau [kg/kg] d'un air à (T, p, φ).

### `w_saturation(T_K: 'float', p_abs_pa: 'float') -> 'float'`

Teneur en eau à saturation [kg/kg] (sur la glace sous 0 °C) ; infinie si l'eau ne peut pas condenser à cette pression. Mise en cache au 0,01 K et au 0,1 % de pression près (CoolProp est lent).

## `caes.composants.isolation`

Pertes à travers un isolant : coefficient global U (formules.md#F41).

### classe `Isolant`

Isolant(nom: 'str', epaisseur_m: 'float', conductivite_w_mk: 'float', h_ext_w_m2k: 'float')

- propriété `coefficient_global_w_m2k` : U = 1 / (e/k + 1/h_ext) (#F41).
- `description(self) -> 'str'` : 

### `isolant_depuis_bloc(bloc: 'dict', registre: 'Registre') -> 'Isolant'`

Construit l'isolant d'un bloc ``isolation: {materiau, epaisseur}``.

## `caes.composants.refroidisseur`

Composant « refroidisseur » (échangeur air / air ambiant).

### classe `Refroidisseur`

Classe de base : nom, modèle, paramètres, provenance, avis.

- `efficacite_a(self, p_refoulement_pa: 'float') -> 'float'` : 
- `pas(self, etat: 'EtatAir', ctx: 'Contexte') -> 'tuple[EtatAir, Flux]'` : Refroidissement isobare vers l'ambiant (#F09 ou #F37), puis perte de charge éventuelle.
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).

## `caes.composants.refroidisseur.pincement`

Refroidisseur à pincement (Tola 2022 : 20 K air/air, 10 K air/huile ; Shi 2024 : 10 K), formules.md#F37.

### `refroidir_pincement(air: 'Air', p_pa: 'float', T_in_K: 'float', T_froid_K: 'float', pincement_K: 'float', T_seuil_K: 'float') -> 'ResultatRefroidisseur'`

Refroidissement isobare jusqu'à T_froid + δ (#F37).

## `caes.composants.reservoir_air`

Composant « réservoir d'air » (bilans de masse et d'énergie).

### classe `ReservoirAir`

Classe de base : nom, modèle, paramètres, provenance, avis.

- `initialiser(self, air: 'Air', p_abs_pa: 'float', T_K: 'float', T_paroi_K: 'float | None' = None, w_kg_kg: 'float' = 0.0) -> 'None'` : 
- `plafonner_eau(self, w_max_kg_kg: 'float') -> 'None'` : Borne la vapeur de l'air initial à ``w_max`` (teneur de l'air que la chaîne de charge refoule) ; l'excès a été drainé avant l'instant initial et n'est pas compté comme condensation.
- propriété `w_vapeur_kg_kg` : 
- propriété `T_rosee_K` : 
- `reinitialiser(self) -> 'None'` : Remet l'état interne à zéro (composants avec mémoire).
- propriété `volume_m3` : 
- propriété `p_abs_pa` : 
- propriété `T_K` : 
- propriété `T_paroi_K` : 
- propriété `masse_kg` : 
- propriété `energie_interne_j` : 
- `etat_sortie(self, m_dot_kg_s: 'float') -> 'EtatAir'` : L'air qui sort : à l'état du réservoir, avec sa vapeur (l'eau condensée reste au fond).
- `remplir(self, ctx: 'Contexte', entree: 'EtatAir') -> 'dict[str, float]'` : Reçoit ``entree`` pendant ``dt`` (laminage implicite, #F12).
- `vider(self, ctx: 'Contexte', m_dot_kg_s: 'float') -> 'dict[str, float]'` : Soutire ``m_dot`` pendant ``dt`` (#F12).
- `attendre(self, ctx: 'Contexte') -> 'dict[str, float]'` : Pas sans débit : seules les pertes thermiques agissent (et l'eau se condense si le réservoir refroidit) ; avec ``fuite_par_jour``, une fraction de l'air s'échappe à l'état du réservoir (F12).
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).

## `caes.composants.secheur`

Composants « sécheur » et « perte de débit ».

### classe `PerteDebit`

Classe de base : nom, modèle, paramètres, provenance, avis.

- `pas(self, etat: 'EtatAir', ctx: 'Contexte') -> 'tuple[EtatAir, Flux]'` : 

### classe `Secheur`

Classe de base : nom, modèle, paramètres, provenance, avis.

- `pas(self, etat: 'EtatAir', ctx: 'Contexte') -> 'tuple[EtatAir, Flux]'` : Même p et T ; débit réduit (sécheur, F10) et eau retirée (point de rosée de sortie, séparateur ; F43).
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).

## `caes.composants.stockage_chaleur`

Composant « stockage de chaleur » : ce qui réchauffe l'air avant une turbine, et d'où vient cette chaleur.

### classe `StockageChaleur`

Classe de base : nom, modèle, paramètres, provenance, avis.

- `initialiser(self, T_K: 'float') -> 'None'` : 
- `reinitialiser(self) -> 'None'` : Remet l'état interne à zéro (composants avec mémoire).
- propriété `masse_gravier_kg` : 
- `energie_stockee_j(self, T_ref_K: 'float') -> 'float'` : Chaleur stockée au-dessus de T_ref [J].
- `exergie_j(self, T0_K: 'float') -> 'float'` : Exergie du stockage [J] (formules.md#F31).
- `profil_temperature_K(self) -> 'np.ndarray | None'` : 
- `pression_de_travail(self, p_air_pa: 'float', ctx: 'Contexte') -> 'float'` : 
- `deposer(self, Q_j: 'float') -> 'None'` : Reçoit de la chaleur d'un refroidisseur (huile idéale).
- `charger_air(self, etat: 'EtatAir', ctx: 'Contexte') -> 'tuple[EtatAir, Flux]'` : L'air chaud traverse le stockage (charge, formules.md#F30) ; l'eau est remise à l'équilibre à la sortie (F43).
- `rechauffer(self, etat: 'EtatAir', ctx: 'Contexte', T_cible_K: 'float | None') -> 'tuple[EtatAir, Flux]'` : Réchauffe l'air avant une turbine, au plus jusqu'à la cible ; l'eau entraînée (gouttelettes, givre) s'évapore si l'air réchauffé le permet (F43).
- `attendre(self, ctx: 'Contexte') -> 'float'` : Pas sans débit (conduction et pertes) ; retourne Q perdue [J].
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).
- `description(self) -> 'str'` : 

## `caes.composants.stockage_chaleur.deux_reservoirs`

Stockage de chaleur à deux réservoirs de liquide (formules.md#F40).

### classe `DeuxReservoirs`

DeuxReservoirs(fluide: 'Fluide', masse_totale_kg: 'float', pincement_K: 'float', coefficient_perte_w_m2k: 'float' = 0.0, surface_par_reservoir_m2: 'float' = 0.0, T_froid_maintenue_K: 'float | None' = None)

- `initialiser(self, T_K: 'float') -> 'None'` : 
- `energie_stockee_j(self, T_ref_K: 'float') -> 'float'` : 
- `exergie_j(self, T0_K: 'float') -> 'float'` : 
- propriété `T_plafond_K` : 
- `charger(self, air: 'Air', p_pa: 'float', T_in_K: 'float', m_dot_kg_s: 'float', dt_s: 'float') -> 'tuple[float, float, bool]'` : Retourne (T_air_out, Q_j stockée, plafond atteint).
- `rechauffer(self, air: 'Air', p_pa: 'float', T_avant_K: 'float', m_dot_kg_s: 'float', dt_s: 'float', T_cible_K: 'float | None') -> 'tuple[float, float]'` : Retourne (T_air_out, Q_j fournie).
- `attendre(self, dt_s: 'float', T_amb_K: 'float') -> 'float'` : Pertes des deux réservoirs [J] (relaxation exacte, #F41).

### classe `Fluide`

Fluide(nom: 'str', cp_j_kgk: 'float', T_max_K: 'float | None' = None)

### `fluide_eau(p_cuve_pa: 'float', marge_K: 'float', T_calcul_K: 'float') -> 'Fluide'`

Eau liquide à la pression de la cuve (CoolProp, IAPWS-95).

## `caes.composants.turbine`

Composant « turbine » : une machine à plusieurs étages de détente.

### classe `EtageTurbineMaillon`

Vue « maillon » de l'étage ``numero`` d'une turbine.

- propriété `nom` : 
- `pas(self, etat: 'EtatAir', ctx: 'Contexte') -> 'tuple[EtatAir, Flux]'` : Détente de l'étage puis laminage vers l'étage suivant.

### classe `ResultatDetenteEtage`

Grandeurs massiques d'un étage (sans le réchauffage amont).

- propriété `q_residuel` : Chaleur implicite [J/kg] : −dh − w_mec (> 0 = perdue).

### classe `Turbine`

Classe de base : nom, modèle, paramètres, provenance, avis.

- propriété `nb_etages` : 
- propriété `debit_variable` : 
- propriété `repartition_egale` : Tous les étages glissent avec un rapport commun (Tola).
- propriété `pression_entree_variable` : 
- `etage(self, numero: 'int') -> 'EtageTurbineMaillon'` : 
- `rendement_etage(self, numero: 'int') -> 'float'` : 
- `rendement_mecanique_etage(self, numero: 'int') -> 'float'` : 
- `rendement_electrique_etage(self, numero: 'int') -> 'float'` : 
- `preparer(self, p_disponible_pa: 'float') -> 'float'` : Fixe les pressions des étages pour ce pas et rend le débit [kg/s] : nominal, loi de l'ellipse (``flugel``, F39) ou répartition égale glissante (``pression_sortie_finale``).
- `debit(self, p_disponible_pa: 'float') -> 'float'` : Débit massique du pas [kg/s]. Nominal, sauf pour ``flugel`` où la loi de l'ellipse l'impose (formules.md#F39).
- `verifier_validite(self) -> 'list[str]'` : Vérifications statiques des paramètres (avant simulation).

## `caes.composants.turbine.flugel`

Turbine hors de son point nominal : formule de Flügel modifiée (Zhang S. et al. 2025, éq. 1 à 6), formules.md#F39.

### classe `PointNominal`

PointNominal(p_in0_pa: 'float', p_out0_pa: 'float', T0_K: 'float', G0_kg_s: 'float')

### `debit_reduit_relatif(pn: 'PointNominal', G_kg_s: 'float', p_in_pa: 'float', T_in_K: 'float') -> 'float'`

Ġ = (G√T/p_in) / (G√T/p_in)_0 (éq. 4 de Zhang).

### `debit_stodola(pn: 'PointNominal', p_in_pa: 'float', p_out_pa: 'float', T_in_K: 'float') -> 'float'`

Débit [kg/s] admis par l'étage (éq. 1 et 4 de Zhang, #F39).

### `p_entree_pour_debit(pn: 'PointNominal', G_kg_s: 'float', p_out_pa: 'float', T_in_K: 'float') -> 'float'`

Inverse de :func:`debit_stodola` : pression d'entrée [Pa].

### `rendement_relatif(G_red: 'float', n_red: 'float', t4: 'float') -> 'float'`

η/η0 selon l'éq. 2 de Zhang (formule de Flügel modifiée).

### `resoudre_debit_glissant(points: 'list[PointNominal]', T_in_K: 'list[float]', p_disponible_pa: 'float', p_sortie_finale_pa: 'float', iterations: 'int' = 80) -> 'tuple[float, list[float]]'`

Débit G et pressions d'entrée de chaque étage tels que la chaîne d'étages passe G avec p_in,1 = p_disponible (bissection sur G).

### `vitesse_reduite_relative(pn: 'PointNominal', T_in_K: 'float') -> 'float'`

ṅ = sqrt(T0/T_in) à vitesse de rotation constante (éq. 5).

## `caes.composants.turbine.rendement`

Détente adiabatique à rendement : isentropique (Shi 2024, Zhang S. 2025) ou polytropique (Tola 2022), formules.md#F34 et #F35.

### `detendre_isentropique(air: 'Air', p_in_pa: 'float', T_in_K: 'float', p_out_pa: 'float', eta_s: 'float') -> 'tuple[float, float, float]'`

Détente à rendement isentropique (#F34). Retourne (T_out, w, dh).

### `detendre_polytropique_rendement(air: 'Air', p_in_pa: 'float', T_in_K: 'float', p_out_pa: 'float', eta_p: 'float') -> 'tuple[float, float, float]'`

Détente à rendement polytropique (#F35). Retourne (T_out, w, dh).

## `caes.compresseur`

Compresseur volumétrique à plusieurs étages, modèle polytropique.

### classe `Compresseur`

Compresseur à ``len(indices_polytropiques)`` étages.

- propriété `nb_etages` : 
- `p_refoulement(self, p_reservoir_pa: 'float') -> 'float'` : Pression de refoulement : au moins la pression minimale.
- `debit_massique_aspire(self, air: 'Air', p_aspiration_pa: 'float', T_aspiration_K: 'float') -> 'float'` : Débit massique aspiré [kg/s] (formules.md#F06).
- `rapports_pression(self, p_aspiration_pa: 'float', p_refoulement_pa: 'float') -> 'tuple[float, ...]'` : Rapport de pression de chaque étage (formules.md#F07).
- `rendement_mecanique(self, p_refoulement_pa: 'float') -> 'float'` : Rendement mécanique selon la pression (formules.md#F07).
- `puissance_electrique(self, debit_massique_kg_s: 'float', travail_massique_total_j_kg: 'float', p_refoulement_pa: 'float') -> 'float'` : Puissance électrique absorbée [W] (éq. 5, formules.md#F08).

### classe `ResultatEtage`

Résultat de la compression d'un étage (grandeurs massiques).

### `comprimer_etage(air: 'Air', p_in_pa: 'float', T_in_K: 'float', rapport_pression: 'float', indice_polytropique: 'float') -> 'ResultatEtage'`

Compression polytropique d'un étage (formules.md#F04, #F05).

### `interpoler_lineaire(x: 'float', x0: 'float', x1: 'float', y0: 'float', y1: 'float') -> 'float'`

Interpolation linéaire bornée : y(x0) = y0, y(x1) = y1.

## `caes.detendeur`

Détendeur (régulateur de pression) en sortie des réservoirs.

### classe `CoefficientsCheayb`

Coefficients de l'éq. 15 (registre ``detendeur.cheayb.*``).

- `a(self, T_in_K: 'float') -> 'float'` : 
- `b(self, T_in_K: 'float') -> 'float'` : 

### classe `Detendeur`

Régulateur de pression à consigne fixe.

- propriété `p_arret_pa` : Pression de réservoir sous laquelle le détendeur s'arrête.
- `peut_fonctionner(self, p_reservoir_pa: 'float') -> 'bool'` : 
- `detendre(self, air: 'Air', p_reservoir_pa: 'float', T_reservoir_K: 'float') -> 'ResultatDetente'` : 

### classe `ResultatDetente`

État avant et après le détendeur.

- propriété `dh` : Écart d'enthalpie massique [J/kg] (0 pour l'isenthalpique).

### `detente_cheayb(air: 'Air', coef: 'CoefficientsCheayb', p_in_pa: 'float', T_in_K: 'float', p_out_pa: 'float') -> 'ResultatDetente'`

Détente selon Cheayb et al. (formules.md#F16).

### `detente_isenthalpique(air: 'Air', p_in_pa: 'float', T_in_K: 'float', p_out_pa: 'float') -> 'ResultatDetente'`

Laminage adiabatique sans travail : h constante (formules.md#F15).

### `temperature_cheayb(coef: 'CoefficientsCheayb', T_in_K: 'float', p_in_pa: 'float', p_out_pa: 'float') -> 'float'`

Température de sortie [K] selon l'éq. 15 (pression en bar).

## `caes.exergie`

Exergie : où se perd l'énergie **utile**.

### classe `BilanExergie`

Postes d'un bilan d'exergie [J], dans l'ordre du tableau.

- propriété `total_postes_j` : 
- propriété `residu_relatif` : (entrée − somme des postes) / entrée.

### classe `Exergie`

Fonctions d'exergie pour un état mort (T0, p0) donné.

- `flux(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Exergie massique d'un écoulement [J/kg] (formules.md#F21).
- `fermee_massique(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Exergie massique d'une masse enfermée [J/kg] (formules.md#F22).
- `fermee(self, masse_kg: 'float', p_abs_pa: 'float', T_K: 'float') -> 'float'` : Exergie d'un réservoir [J] : masse × exergie massique fermée.
- `chaleur(self, Q_j: 'float', T_K: 'float') -> 'float'` : Exergie d'une chaleur Q échangée à T [J] (formules.md#F23).
- `air_comprime_gaz_parfait(self, volume_m3: 'float', p_abs_pa: 'float') -> 'float'` : Éq. 22 de Baniamerian (2025) : gaz parfait à T0 (formules.md#F22).

### `bilan_exergie_charge(res: 'ResultatCharge', air: 'Air | None' = None) -> 'BilanExergie'`

Bilan d'exergie d'une charge, poste par poste [J].

### `bilan_exergie_decharge(res: 'ResultatDecharge', air: 'Air | None' = None) -> 'BilanExergie'`

Bilan d'exergie d'une décharge, poste par poste [J].

### `exergie_etage_compression(ex: 'Exergie', p_in_pa: 'float', T_in_K: 'float', p_out_pa: 'float', T_out_K: 'float', q_poly_j_kg: 'float') -> 'tuple[float, float]'`

Destruction et exergie de la chaleur rejetée, par kg (formules.md#F24).

### `temperature_log_moyenne(T1_K: 'float', T2_K: 'float') -> 'float'`

Température logarithmique moyenne entre T1 et T2 [K].

## `caes.flotte`

Répartition d'une flotte de modules identiques sur une demande variable, seconde par seconde (formules.md#F47).

### classe `CourbeModule`

Puissance électrique d'un module en décharge, P(τ) [W] depuis le démarrage, à pas constant ``dt_s``.

- propriété `duree_s` : 
- propriété `energie_j` : 
- propriété `P_nominale_w` : 

### classe `ResultatFlotte`

ResultatFlotte(nombre_modules: 'int', dt_s: 'float', demande_w: 'np.ndarray', fournie_w: 'np.ndarray', modules_en_marche: 'np.ndarray', energie_demandee_j: 'float', energie_fournie_j: 'float', energie_non_servie_j: 'float', energie_ecretee_j: 'float', modules_utilises: 'int', demarrages: 'int', duree_couverte_s: 'float', details: 'dict[str, float]' = <factory>)

- propriété `couverture` : Part de l'énergie demandée qui a été fournie.
- propriété `energie_restante_j` : 

### `modules_necessaires(courbe: 'CourbeModule', demande_w: 'np.ndarray', dt_s: 'float | None' = None, couverture_min: 'float' = 0.999, maximum: 'int' = 10000) -> 'tuple[int, ResultatFlotte]'`

Plus petit nombre de modules qui couvre la demande (part de l'énergie ≥ ``couverture_min``), par recherche dichotomique à partir de la borne énergétique E_demandée / E_module.

### `profil_jour_nuit(duree_s: 'float', P_moyenne_w: 'float', facteur_jour: 'float', facteur_nuit: 'float', dt_s: 'float' = 1.0, debut_jour_h: 'float' = 6.0, fin_jour_h: 'float' = 22.0) -> 'np.ndarray'`

Demande en créneaux jour / nuit, à partir de minuit [W].

### `repartir(courbe: 'CourbeModule', demande_w: 'np.ndarray', nombre_modules: 'int', dt_s: 'float | None' = None, marge_w: 'float | None' = None) -> 'ResultatFlotte'`

Fait suivre la demande par ``nombre_modules`` modules identiques.

## `caes.graphiques`

Style commun des graphiques de validation.

### `etiquette_fin(ax: 'plt.Axes', x: 'float', y: 'float', texte: 'str', couleur: 'str') -> 'None'`

### `nouvelle_figure(largeur: 'float' = 8.0, hauteur: 'float' = 4.5) -> 'tuple[plt.Figure, plt.Axes]'`

### `point_reference(ax: 'plt.Axes', x: 'float', y: 'float', texte: 'str') -> 'None'`

### `style_axes(ax: 'plt.Axes', titre: 'str', x: 'str', y: 'str') -> 'None'`

### `terminer(fig: 'plt.Figure', ax: 'plt.Axes', chemin: 'Path', legende: 'str | None' = 'best') -> 'str'`

## `caes.integre`

Système intégré : banc de Dormoy + cuves de gravier (phase 5).

### classe `ConfigCuves`

Réglages des cuves de gravier d'une architecture D ou E.

- `construire(self) -> 'list[LitGravier]'` : 

### classe `CouplageCuvesCharge`

Cuves traversées (D) ou alimentées par une boucle d'air (E).

- `preparer(self, m_dot: 'float', dt: 'float') -> 'None'` : 
- `apres_etage(self, i: 'int', p_pa: 'float', T_K: 'float') -> 'float'` : 
- `fin_de_pas(self, chaine: 'EtatChaine', m_dot: 'float', dt: 'float') -> 'dict[str, float]'` : 

### classe `CouplageHuileIdeale`

Architecture C : chaleur des refroidisseurs au-dessus du seuil mise de côté sans perte (hypothèse de Dormoy, § 3.3.5).

- `preparer(self, m_dot: 'float', dt: 'float') -> 'None'` : 
- `apres_etage(self, i: 'int', p_pa: 'float', T_K: 'float') -> 'float'` : 
- `fin_de_pas(self, chaine: 'EtatChaine', m_dot: 'float', dt: 'float') -> 'dict[str, float]'` : 

### classe `Cycle`

Cycle(numero: 'int', charge: 'ResultatCharge', decharge: 'ResultatDecharge', attente_h: 'float', chaleur_cuves_debut_kwh: 'float', chaleur_cuves_fin_kwh: 'float', pertes_attente_kwh: 'float')

### classe `RechauffeurCuves`

Réchauffage des turbines par les cuves (D, E) : turbine i ← cuve n − i. Un bypass limite la température à la cible ; sans appoint.

- `preparer(self, m_dot: 'float', dt: 'float') -> 'None'` : 
- `indice_cuve(self, i_turbine: 'int') -> 'int'` : 
- `chauffer(self, i: 'int', p_pa: 'float', T_avant_K: 'float', T_cible_K: 'float | None') -> 'tuple[float, str]'` : 

### classe `RechauffeurHuileIdeale`

Architecture C : puise dans la réserve, sinon source externe.

- `preparer(self, m_dot: 'float', dt: 'float') -> 'None'` : 
- `chauffer(self, i: 'int', p_pa: 'float', T_avant_K: 'float', T_cible_K: 'float | None') -> 'tuple[float, str]'` : 

### classe `ResultatIntegre`

ResultatIntegre(scenario: 'Scenario', architecture: 'str', cycles: 'list[Cycle]', cuves: 'list[LitGravier] | None', volumes_m3: 'list[float]', converge: 'bool')

- propriété `dernier` : 
- `resume(self) -> 'str'` : 

### `exergie_cuve(lit: 'LitGravier', T0_K: 'float') -> 'float'`

Exergie du gravier [J] : Σ C·[(T − T0) − T0·ln(T/T0)] (#F31).

### `simuler_cycles(scenario: 'Scenario | Path | str', registre: 'Registre | None' = None, air: 'Air | None' = None, volumes_m3: 'list[float] | None' = None) -> 'ResultatIntegre'`

Enchaîne des cycles charge → attente → décharge jusqu'au régime stable (variation de l'électricité produite < tolérance).

## `caes.lit_gravier`

Lit de gravier traversé par de l'air : modèle de Schumann 1D.

### classe `Correlations`

Constantes des corrélations (registre ``lit.*``).

- `nusselt(self, Re: 'float', Pr: 'float') -> 'float'` : Nu = a + b·Re^c·Pr^(1/3) (Wakao et al. 1979, formules.md#F27).
- `dans_validite(self, Re: 'float') -> 'bool'` : 

### classe `LitGravier`

Cuve cylindrique remplie de gravier, discrétisée en cellules.

- propriété `section_m2` : 
- propriété `volume_m3` : 
- propriété `dx_m` : 
- propriété `masse_gravier_kg` : 
- propriété `capacite_cellule_j_k` : Capacité thermique du solide d'une cellule [J/K].
- propriété `surface_laterale_cellule_m2` : 
- `initialiser(self, T_K: 'float | np.ndarray') -> 'None'` : Température initiale uniforme ou profil (haut → bas).
- `energie_stockee_j(self, T_ref_K: 'float') -> 'float'` : Chaleur du gravier au-dessus de T_ref [J].
- `energie_utile_j(self, T_seuil_K: 'float') -> 'float'` : Chaleur du gravier au-dessus d'un seuil (par exemple 130 °C).
- `sortie_instantanee(self, air: 'Air', debit_massique_kg_s: 'float', T_entree_K: 'float', p_abs_pa: 'float', sens: 'int' = 1) -> 'float'` : Température de sortie de l'air, solide figé (sans avancer).
- `pas(self, air: 'Air', dt_s: 'float', debit_massique_kg_s: 'float', T_entree_K: 'float', p_abs_pa: 'float', T_amb_K: 'float', sens: 'int' = 1) -> 'dict[str, float]'` : Avance d'un pas (formules.md#F25, #F26, #F29).
- `simuler(self, air: 'Air', dt_s: 'float', duree_s: 'float', debit_massique_kg_s: 'float', T_entree_K: 'float', p_abs_pa: 'float', T_amb_K: 'float', sens: 'int' = 1) -> 'dict[str, np.ndarray]'` : Enchaîne des pas à conditions constantes ; renvoie les séries.

### `coefficient_echange(air: 'Air', materiau: 'Materiau', corr: 'Correlations', p_abs_pa: 'float', T_K: 'float', vitesse_superficielle_m_s: 'float') -> 'tuple[float, float, float]'`

Coefficient d'échange air-particule h [W/m²K] (formules.md#F27).

### `perte_de_charge_ergun(air: 'Air', materiau: 'Materiau', corr: 'Correlations', p_abs_pa: 'float', T_K: 'float', vitesse_superficielle_m_s: 'float', longueur_m: 'float') -> 'float'`

Perte de charge d'Ergun [Pa] (formules.md#F28).

### `solution_schumann(xi: 'float', eta: 'np.ndarray') -> 'tuple[np.ndarray, np.ndarray]'`

Solution analytique de Schumann (1929) pour un échelon d'entrée.

## `caes.materiaux`

Matériaux de stockage de chaleur (gravier, roches).

### classe `Materiau`

Solide granulaire d'un lit de stockage.

- propriété `capacite_volumique_lit_j_m3k` : Capacité thermique du solide par m³ de lit [J/(m³·K)].
- propriété `surface_specifique_m2_m3` : Surface des particules par m³ de lit (sphères) [m²/m³].
- `avec(self, **modifications: 'float') -> 'Materiau'` : Copie avec des propriétés modifiées (expériences numériques).

### `charger_materiau(nom: 'str', registre: 'Registre | None' = None) -> 'Materiau'`

Construit un matériau à partir des entrées ``materiau.<nom>.*``.

## `caes.metriques`

Indicateurs d'écart entre simulation et référence.

### `comparer_sur_grille(t_sim: 'np.ndarray', y_sim: 'np.ndarray', t_ref: 'np.ndarray', y_ref: 'np.ndarray') -> 'dict[str, float]'`

Interpole la simulation aux instants de la référence, puis RMSE/MAPE.

### `ecart_relatif_pct(simule: 'float', reference: 'float') -> 'float'`

(simulé − référence) / référence, en pourcent.

### `lire_courbe_numerisee(chemin: 'Path | str') -> 'pd.DataFrame'`

Lit un CSV de ``data/validation/`` (lignes ``#`` ignorées).

### `mape(simule: 'np.ndarray', mesure: 'np.ndarray') -> 'float'`

Erreur absolue moyenne en pourcentage de la mesure.

### `rmse(simule: 'np.ndarray', mesure: 'np.ndarray') -> 'float'`

Racine de l'erreur quadratique moyenne (mêmes unités que y).

## `caes.proprietes`

Propriétés thermodynamiques de l'air sec.

### classe `Air`

Interface commune aux modèles d'air.

- `rho(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Masse volumique [kg/m3].
- `T_de_p_rho(self, p_abs_pa: 'float', rho: 'float') -> 'float'` : Température [K] à partir de la pression et de la masse volumique.
- `p_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Pression absolue [Pa] à partir de la masse volumique et de T.
- `h(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Enthalpie massique [J/kg].
- `u_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Énergie interne massique [J/kg].
- `cv_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Chaleur massique à volume constant [J/(kg·K)].
- `cp(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Chaleur massique à pression constante [J/(kg·K)].
- `s(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Entropie massique [J/(kg·K)].
- `T_de_p_h(self, p_abs_pa: 'float', h: 'float') -> 'float'` : Température [K] à partir de la pression et de l'enthalpie.
- `T_de_p_s(self, p_abs_pa: 'float', s: 'float') -> 'float'` : Température [K] à partir de la pression et de l'entropie.
- `gamma(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Rapport cp/cv à l'état (p, T) [-] (exposant isentropique du gaz parfait équivalent).
- `mu(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Viscosité dynamique [Pa·s].
- `k(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Conductivité thermique [W/(m·K)].
- `prandtl(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Nombre de Prandtl Pr = μ·cp/k [-].
- `etat(self, p_abs_pa: 'float', T_K: 'float') -> 'Etat'` : État complet à (p, T).
- `T_de_rho_u(self, rho: 'float', u: 'float', T_depart: 'float', tolerance_K: 'float' = 0.0001, iterations_max: 'int' = 50) -> 'float'` : Température [K] telle que u(rho, T) = u, par la méthode de Newton.

### classe `AirParfait`

Gaz parfait à chaleurs massiques constantes (voir formules.md#F03).

- `mu(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Loi de Sutherland (formules.md#F26).
- `k(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Conductivité thermique [W/(m·K)].
- `rho(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Masse volumique [kg/m3].
- `T_de_p_rho(self, p_abs_pa: 'float', rho: 'float') -> 'float'` : Température [K] à partir de la pression et de la masse volumique.
- `p_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Pression absolue [Pa] à partir de la masse volumique et de T.
- `h(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Enthalpie massique [J/kg].
- `u_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Énergie interne massique [J/kg].
- `cv_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Chaleur massique à volume constant [J/(kg·K)].
- `cp(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Chaleur massique à pression constante [J/(kg·K)].
- `s(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Entropie massique [J/(kg·K)].
- `T_de_p_h(self, p_abs_pa: 'float', h: 'float') -> 'float'` : Température [K] à partir de la pression et de l'enthalpie.
- `T_de_p_s(self, p_abs_pa: 'float', s: 'float') -> 'float'` : Température [K] à partir de la pression et de l'entropie.

### classe `AirReel`

Air réel (CoolProp, fluide « Air », équation de Lemmon 2000).

- `rho(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Masse volumique [kg/m3].
- `T_de_p_rho(self, p_abs_pa: 'float', rho: 'float') -> 'float'` : Température [K] à partir de la pression et de la masse volumique.
- `p_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Pression absolue [Pa] à partir de la masse volumique et de T.
- `h(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Enthalpie massique [J/kg].
- `u_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Énergie interne massique [J/kg].
- `cv_de_rho_T(self, rho: 'float', T_K: 'float') -> 'float'` : Chaleur massique à volume constant [J/(kg·K)].
- `cp(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Chaleur massique à pression constante [J/(kg·K)].
- `s(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Entropie massique [J/(kg·K)].
- `T_de_p_h(self, p_abs_pa: 'float', h: 'float') -> 'float'` : Température [K] à partir de la pression et de l'enthalpie.
- `T_de_p_s(self, p_abs_pa: 'float', s: 'float') -> 'float'` : Température [K] à partir de la pression et de l'entropie.
- `mu(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Viscosité dynamique [Pa·s].
- `k(self, p_abs_pa: 'float', T_K: 'float') -> 'float'` : Conductivité thermique [W/(m·K)].

### classe `Etat`

État thermodynamique d'une masse d'air.

### `air_par_defaut() -> 'Air'`

Le modèle d'air utilisé par le simulateur : l'air réel.

## `caes.refroidisseur`

Refroidisseurs intermédiaires, méthode de l'efficacité (NTU).

### classe `Refroidisseur`

Un refroidisseur d'efficacité fixe ou variable avec la pression.

- `efficacite_a(self, p_refoulement_pa: 'float') -> 'float'` : 
- `refroidir(self, air: 'Air', p_pa: 'float', T_in_K: 'float', T_froid_K: 'float', T_seuil_K: 'float', p_refoulement_pa: 'float') -> 'ResultatRefroidisseur'` : 

### classe `ResultatRefroidisseur`

Grandeurs massiques d'un passage dans un refroidisseur.

### `refroidir(air: 'Air', p_pa: 'float', T_in_K: 'float', T_froid_K: 'float', efficacite: 'float', T_seuil_K: 'float') -> 'ResultatRefroidisseur'`

Refroidissement à pression constante (formules.md#F09).

## `caes.registre`

Chargeur du registre scientifique.

### classe `ErreurRegistre`

Le registre est incohérent (identifiant, unité ou source).

### classe `Parametre`

Une valeur du registre, avec sa source et son unité.

- propriété `unite_si` : Unité SI correspondante.
- propriété `valeur_si` : Valeur convertie en SI. Erreur si seule une plage existe.
- propriété `valeur_min_si` : Borne basse convertie en SI, ou ``None``.
- propriété `valeur_max_si` : Borne haute convertie en SI, ou ``None``.
- propriété `est_plage` : Vrai si la source ne donne qu'une plage.

### classe `Reference`

Une source du registre (ligne de ``references.csv``).

- `citation(self) -> 'str'` : Citation courte, par exemple « Dormoy E. et al. (2024), ... ».

### classe `Registre`

Registre scientifique chargé en mémoire.

- `verifier(self) -> 'None'` : Lève :class:`ErreurRegistre` si le registre est incohérent.
- `si(self, id_: 'str') -> 'float'` : Raccourci : valeur SI du paramètre ``id_``.
- `source(self, id_: 'str') -> 'Reference'` : La référence d'où vient le paramètre ``id_``.
- `par_niveau(self, niveau: 'str') -> 'list[Parametre]'` : Tous les paramètres d'un niveau de preuve donné.
- `par_prefixe(self, prefixe: 'str') -> 'list[Parametre]'` : Tous les paramètres dont l'identifiant commence par ``prefixe``.

## `caes.reservoir`

Réservoir d'air comprimé équivalent : bilans de masse et d'énergie.

### classe `Reservoir`

Réservoir équivalent (état mutable : masse et énergie interne).

- `initialiser(self, air: 'Air', p_abs_pa: 'float', T_K: 'float', T_paroi_K: 'float | None' = None) -> 'None'` : Fixe l'état initial à (p, T) ; la paroi est à T_paroi ou T.
- propriété `rho` : 
- `pas(self, air: 'Air', dt_s: 'float', debit_entree_kg_s: 'float', h_entree_j_kg: 'float', T_amb_K: 'float', debit_sortie_kg_s: 'float' = 0.0) -> 'dict[str, float]'` : Avance d'un pas de temps (formules.md#F11, #F12).

## `caes.scenario`

Chargement des fichiers de scénario (YAML).

### classe `Scenario`

Scénario résolu : valeurs SI et provenance de chaque feuille.

- `get(self, cle: 'str', defaut: 'Any' = None) -> 'Any'` : 
- `avec(self, modifications: 'dict[str, Any]', suffixe: 'str') -> 'Scenario'` : Copie du scénario avec des feuilles remplacées (valeurs SI).

### `charger_scenario(chemin: 'Path | str', registre: 'Registre | None' = None) -> 'Scenario'`

Lit un fichier YAML et résout toutes ses valeurs en SI.

## `caes.secheur`

Sécheur d'air par adsorption.

### classe `EtatDebit`

Un débit d'air avec son état (humidité à venir en phase 8).

### classe `Secheur`

Sécheur à perte de débit constante (éq. 10 de Dormoy).

- `debit_sortie(self, debit_entree_kg_s: 'float') -> 'float'` : Débit massique sortant [kg/s] (formules.md#F10).
- `debit_rejete(self, debit_entree_kg_s: 'float') -> 'float'` : Débit perdu à la régénération [kg/s].
- `traiter(self, entree: 'EtatDebit') -> 'EtatDebit'` : Passage dans le sécheur : même p et T, débit réduit.

## `caes.sortie`

Écriture des résultats d'une simulation dans un dossier (phase 6).

### `ecrire_resultats(res: 'ResultatSimulation', dossier: 'Path | str', graphiques: 'bool' = True, commande: 'str' = 'python -m caes simuler') -> 'Path'`

Écrit tous les fichiers de résultats ; retourne le dossier.

## `caes.systeme`

Assemblage du système et simulation de la charge.

### classe `CouplageCharge`

Crochets pour brancher des cuves de chaleur sur la charge.

- `preparer(self, m_dot: 'float', dt: 'float') -> 'None'` : 
- `apres_etage(self, i: 'int', p_pa: 'float', T_K: 'float') -> 'float'` : 
- `fin_de_pas(self, chaine: "'EtatChaine'", m_dot: 'float', dt: 'float') -> 'dict[str, float]'` : 

### classe `EtatChaine`

Résultat stationnaire de la chaîne de compression à un instant.

### classe `RechauffeurDecharge`

Source de chaleur de réchauffage branchable sur la décharge.

- `preparer(self, m_dot: 'float', dt: 'float') -> 'None'` : 
- `chauffer(self, i: 'int', p_pa: 'float', T_avant_K: 'float', T_cible_K: 'float | None') -> 'tuple[float, str]'` : 

### classe `ResultatCharge`

Séries temporelles et totaux d'une simulation de charge.

- `resume(self) -> 'str'` : 

### classe `ResultatDecharge`

Séries temporelles et totaux d'une simulation de décharge.

- `resume(self) -> 'str'` : 

### `chaine_compression(air: 'Air', compresseur: 'Compresseur', refroidisseurs: 'list[Refroidisseur]', p_aspiration_pa: 'float', T_aspiration_K: 'float', T_froid_K: 'float', p_refoulement_pa: 'float', T_seuil_K: 'float', apres_etage: 'Callable[[int, float, float], float] | None' = None) -> 'EtatChaine'`

Chaîne compression / refroidissement en régime permanent.

### `construire_compresseur(sc: 'Scenario') -> 'Compresseur'`

### `construire_detendeur(sc: 'Scenario') -> 'Detendeur'`

### `construire_refroidisseurs(sc: 'Scenario') -> 'list[Refroidisseur]'`

### `construire_reservoir(sc: 'Scenario') -> 'Reservoir'`

### `construire_turbine(sc: 'Scenario') -> 'Turbine'`

### `rendements_aller_retour(charge: 'ResultatCharge', decharge: 'ResultatDecharge') -> 'dict[str, float]'`

Les deux définitions du rendement (formules.md#F20).

### `sauvegarder_series(resultat: 'ResultatCharge', chemin: 'Path | str') -> 'None'`

Écrit les séries temporelles en CSV (unités SI dans les en-têtes).

### `simuler_charge(scenario: 'Scenario | Path | str', registre: 'Registre | None' = None, air: 'Air | None' = None, couplage: 'CouplageCharge | None' = None, reservoir_initial: 'Reservoir | None' = None) -> 'ResultatCharge'`

Simule la charge décrite par le scénario jusqu'à la pression cible.

### `simuler_decharge(scenario: 'Scenario | Path | str', registre: 'Registre | None' = None, air: 'Air | None' = None, rechauffeur: 'RechauffeurDecharge | None' = None, reservoir_initial: 'Reservoir | None' = None) -> 'ResultatDecharge'`

Simule la décharge jusqu'à l'arrêt du détendeur.

### `totaux_en_dataframe(resultats: 'list[ResultatCharge] | list[ResultatDecharge]') -> 'pd.DataFrame'`

Tableau comparatif des totaux de plusieurs simulations.

## `caes.tableau_1000`

Tableau « 1000 unités » : où va l'énergie utile, étape par étape.

### classe `Cas`

Cas(code: 'str', titre: 'str', charge: 'ResultatCharge', decharge: 'ResultatDecharge', bilan_charge: 'BilanExergie', bilan_decharge: 'BilanExergie')

- propriété `unite_j` : 

### `cas_depuis_resultats(code: 'str', titre: 'str', charge: 'ResultatCharge', decharge: 'ResultatDecharge') -> 'Cas'`

Construit un cas (et ses bilans d'exergie) à partir des résultats.

### `cascade(cas: 'Cas', chemin: 'Path') -> 'str'`

Graphique en cascade de l'exergie (unités sur 1000).

### `lignes_tableau(cas: 'Cas') -> 'list[dict[str, object]]'`

Lignes du tableau : étape, exergie perdue, exergie restante, chaleur.

### `tableau_markdown(cas: 'Cas', generateur: 'str' = '`caes.tableau_1000`') -> 'str'`

### `u(cas: 'Cas', val_j: 'float') -> 'float'`

Convertit des joules en « unités sur 1000 ».

## `caes.turbine`

Turbine à air à plusieurs étages, avec réchauffage avant chaque étage.

### classe `EtageTurbine`

Un étage de détente et son réchauffeur amont.

### classe `ResultatEtageTurbine`

Grandeurs massiques d'un étage (réchauffage + détente).

- propriété `q_residuel` : Chaleur implicite [J/kg] : −dh − w_mec (> 0 = perdue).

### classe `Turbine`

Turbine à ``len(etages)`` étages, débit massique constant.

- propriété `p_entree_pa` : 
- propriété `p_sortie_pa` : 
- `produire(self, air: 'Air', T_entree_K: 'float', rechauffeur: 'Callable[[int, float, float, float | None], tuple[float, str]] | None' = None) -> 'tuple[ResultatEtageTurbine, ...]'` : Réchauffage et détente de chaque étage, à partir de T_entree.
- `puissance_electrique(self, resultats: 'tuple[ResultatEtageTurbine, ...]') -> 'float'` : Puissance électrique totale [W] (éq. 17, formules.md#F18).

### `detendre_etage(air: 'Air', p_in_pa: 'float', T_in_K: 'float', p_out_pa: 'float', indice_polytropique: 'float') -> 'tuple[float, float, float]'`

Détente polytropique (formules.md#F17).
