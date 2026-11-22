# -*- coding: utf-8 -*-
"""Génère references.csv et parametres.csv à partir des valeurs extraites
de Dormoy et al. (2024) et de ses données supplémentaires (phase 0).

Ce script est la « source de vérité » lisible du registre : pour
ajouter ou corriger une valeur, modifier ce fichier puis le relancer
depuis la racine du projet :

    python data/registre/generer_registre_phase0.py

Les CSV générés sont versionnés eux aussi, pour qu'un lecteur sans
Python puisse les ouvrir dans un tableur.
"""
import csv
import math
import pathlib

D = "dormoy2024"
S = "dormoy2024supp"

references = [
    # id, auteurs, annee, titre, revue, doi_ou_url, type, acces,
    # fichier_local, notes
    (D, "Dormoy E., Le Lostec B., Haillot D.", 2024,
     "Aboveground compressed air energy storage systems: Experimental and "
     "numerical approach",
     "Energy Conversion and Management, 321, 119073",
     "https://doi.org/10.1016/j.enconman.2024.119073", "article_revise",
     "libre (CC BY-NC)", "../Études/études/dormoy.pdf",
     "Banc ÉTS / Hydro-Québec, 190 bar. Cas de référence du simulateur. "
     "Les auteurs ne partagent pas les données brutes."),
    (S, "Dormoy E., Le Lostec B., Haillot D.", 2024,
     "Supplementary Materials (tableaux 7, 8 et 9) de l'article Dormoy 2024",
     "Energy Conversion and Management, 321, 119073, annexe A",
     "https://ars.els-cdn.com/content/image/1-s2.0-S0196890424010148-mmc1.pdf",
     "donnees_supplementaires", "libre (CC BY-NC)",
     "data/sources/dormoy-supplementaire/dormoy2024-supplementaire-mmc1.pdf",
     "Téléchargé le 2 nov. 2026. Transcription dans "
     "data/sources/dormoy-supplementaire/tableaux-7-8-9.md."),
    ("tola2022", "Tola V., Marcello F.C., Cocco D., Cau G.", 2022,
     "Performance Assessment of Low-Temperature A-CAES (Adiabatic Compressed "
     "Air Energy Storage) Plants",
     "Journal of Thermal Science, 31(5), 1279-1292",
     "https://doi.org/10.1007/s11630-022-1632-7", "article_revise",
     "PDF disponible", "../Études/études/tola2022.pdf",
     "Simulation seulement (pas de mesures). Cas A, B, C ; lit de gravier. "
     "Vérification croisée du module gravier."),
    ("baniamerian2025",
     "Baniamerian Z., Garvey S., Rouse J., Mehdipour R., Cárdenas B.", 2025,
     "Integrated energy storage and transmission solutions: Evaluating "
     "hydrogen, ammonia, and compressed air for offshore wind power delivery",
     "Journal of Energy Storage, 118, 116254",
     "https://doi.org/10.1016/j.est.2025.116254", "article_revise",
     "libre (CC BY)",
     "../Études/études/others/offshore/"
     "offshore-energy-1-s2.0-S2352152X25009673-main.pdf",
     "Formule d'exergie (éq. 22), règle du bilan de chaleur. "
     "Modèle sans mesures."),
    ("zhangS2025", "Zhang S. et al.", 2025,
     "Dynamic performance of CAES based on an ON/OFF valve, buffer tank and "
     "regulating valve (titre abrégé, voir le PDF)",
     "Carbon Neutrality, 4, 24",
     "https://doi.org/10.1007/s43979-025-00140-z", "article_revise",
     "PDF disponible",
     "../Études/études/others/caes-perfo/"
     "Dynamic performance of CAES based.pdf",
     "Modèle du détendeur (vanne ON/OFF + tampon). Cite l'essai de Luo et "
     "al. (90 L, 50-100 bar) comme second jeu de validation."),
    ("shi2024", "Shi, Liang, Ding, Su, Lin, Wang", 2024,
     "Prépublication SSRN 5042640 : centrale A-CAES de 100 MW, 4 "
     "compresseurs, 3 turbines, eau chaude à 190 °C (titre complet dans le "
     "PDF)",
     "SSRN (prépublication non révisée par les pairs)",
     "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5042640",
     "prepublication", "PDF disponible",
     "../Études/études/others/aa-caes/aa-caes.pdf",
     "NON RÉVISÉE : à signaler à chaque usage. Turbine à pression glissante "
     "sans détendeur. Peut-être le « Shi et al. 2026 » de ChatGPT (non "
     "confirmé)."),
    ("bazdar2022", "Bazdar E. et al.", 2022,
     "Compressed air energy storage in integrated energy systems: A review",
     "Renewable and Sustainable Energy Reviews, 167, 112701",
     "https://doi.org/10.1016/j.rser.2022.112701", "revue_litterature",
     "PDF disponible",
     "../Études/études/others/bazdar-2022-revue-caes-systemes-integres/"
     "Compressed-air-energy-storage-in-integrated-energy-systems-A-review.pdf",
     "Carte de références et ordres de grandeur. Tableau comparatif avec "
     "des erreurs : vérifier chaque chiffre."),
    ("zhangZ2021", "Zhang Z. et al.", 2021,
     "A review of technologies and applications on versatile energy storage "
     "systems",
     "Renewable and Sustainable Energy Reviews, 148, 111263",
     "https://doi.org/10.1016/j.rser.2021.111263", "revue_litterature",
     "PDF disponible",
     "../Études/études/others/zhang-2021-revue-stockage-energie/"
     "A review of technologies and applications on versatile energy storage "
     "systems.pdf",
     "Source principale du tableau 1 de Dormoy. Comparaison des "
     "technologies de stockage."),
    ("schumann1929", "Schumann T.E.W.", 1929,
     "Heat transfer: a liquid flowing through a porous prism",
     "Journal of the Franklin Institute, 208(3), 405-416",
     "https://doi.org/10.1016/S0016-0032(29)91186-8", "article_revise",
     "payant", "",
     "Modèle à deux équations (fluide et solide) du lit de particules, "
     "avec solution analytique pour un échelon d'entrée. Réf. [30] de "
     "Tola 2022."),
    ("wakao1979", "Wakao N., Kaguei S., Funazkri T.", 1979,
     "Effect of fluid dispersion coefficients on particle-to-fluid heat "
     "transfer coefficients in packed beds",
     "Chemical Engineering Science, 34(3), 325-336",
     "https://doi.org/10.1016/0009-2509(79)85064-2", "article_revise",
     "payant", "",
     "Corrélation Nu = 2 + 1,1 Re^0,6 Pr^(1/3), valide pour 15 < Re < "
     "8500 ; corrélation de référence des lits de particules."),
    ("ergun1949", "Ergun S., Orning A.A.", 1949,
     "Fluid flow through randomly packed columns and fluidized beds",
     "Industrial & Engineering Chemistry, 41(6), 1179-1184",
     "https://doi.org/10.1021/ie50474a011", "article_revise", "payant", "",
     "Équation d'Ergun pour la perte de charge dans un lit de particules "
     "(constantes 150 et 1,75 fixées dans Ergun 1952, Chem. Eng. Prog. "
     "48:89-94)."),
    ("jeffreson1972", "Jeffreson C.P.", 1972,
     "Prediction of breakthrough curves in packed beds: I. Applicability "
     "of single parameter models",
     "AIChE Journal, 18(2), 409-416",
     "https://doi.org/10.1002/aic.690180225", "article_revise", "payant",
     "", "Correction du coefficient d'échange pour le gradient interne "
     "des particules : h_eff = h / (1 + Bi/5)."),
    ("sutherland1893", "Sutherland W.", 1893,
     "The viscosity of gases and molecular force",
     "Philosophical Magazine, Series 5, 36(223), 507-531",
     "https://doi.org/10.1080/14786449308620508", "article_revise",
     "payant", "", "Loi de Sutherland pour la viscosité de l'air (modèle "
     "gaz parfait de comparaison)."),
    ("robertson1988", "Robertson E.C.", 1988,
     "Thermal properties of rocks",
     "U.S. Geological Survey, Open-File Report 88-441",
     "https://doi.org/10.3133/ofr88441", "rapport", "libre", "",
     "Conductivité thermique des roches (granite, gneiss, calcaire : "
     "environ 2 à 3,5 W/m·K). Sert à l'hypothèse sur le gravier."),
    ("cascetta2018", "Cascetta M., Serra F., Cau G., Puddu P.", 2018,
     "Comparison between experimental and numerical results of a "
     "packed-bed thermal energy storage system in continuous operation",
     "Energy Procedia, 148, 234-241",
     "https://doi.org/10.1016/j.egypro.2018.08.073", "article_revise",
     "libre (CC BY-NC-ND), PDF non récupéré (site bloqué aux robots)", "",
     "Réf. [31] de Tola 2022 : validation expérimentale du modèle de "
     "cuve. À télécharger à la main depuis ScienceDirect et à déposer "
     "dans data/sources/cascetta2018/."),
    ("barbour2015", "Barbour E., Mignard D., Ding Y., Li Y.", 2015,
     "Adiabatic Compressed Air Energy Storage with packed bed thermal "
     "energy storage",
     "Applied Energy, 155, 804-815",
     "https://doi.org/10.1016/j.apenergy.2015.06.019", "article_revise",
     "libre (CC BY), PDF non récupéré (site bloqué aux robots)", "",
     "Réf. [21] de Tola 2022. Modèle de lit compact en A-CAES. À "
     "télécharger à la main."),
    ("wolfbudt2014", "Wolf D., Budt M.", 2014,
     "LTA-CAES - A low-temperature approach to Adiabatic Compressed Air "
     "Energy Storage",
     "Applied Energy, 125, 158-164",
     "https://doi.org/10.1016/j.apenergy.2014.03.013", "article_revise",
     "payant ; DOI vérifié via Crossref le 21 nov. 2026 ; PDF non "
     "récupéré", "",
     "Concept du stockage de chaleur à deux réservoirs de liquide (huile) "
     "à basse température. Valeurs reprises via Bazdar 2022 (tableau 3) "
     "et Tola 2022 (cas B)."),
    ("ablaoui2023",
     "Ablaoui E.M., Malendowski M., Szymkuc W., Pozorski Z.", 2023,
     "Determination of Thermal Properties of Mineral Wool Required for the "
     "Safety Analysis of Sandwich Panels Subjected to Fire Loads",
     "Materials, 16(17), 5852",
     "https://doi.org/10.3390/ma16175852", "article_revise",
     "libre (CC BY) ; texte lu sur PMC (PMC10488771) le 21 nov. 2026", "",
     "Tableau 1 : conductivité et chaleur massique de la laine minérale "
     "(densité > 26 kg/m3) selon un projet d'Eurocode ; plage ambiante "
     "0,030-0,046 W/m·K citée à sa réf. [13]."),
    ("wagner2002", "Wagner W., Pruß A.", 2002,
     "The IAPWS Formulation 1995 for the Thermodynamic Properties of "
     "Ordinary Water Substance for General and Scientific Use",
     "Journal of Physical and Chemical Reference Data, 31(2), 387-535",
     "https://doi.org/10.1063/1.1461829", "article_revise",
     "payant ; DOI vérifié via Crossref le 21 nov. 2026 ; équation "
     "implémentée dans CoolProp (fluide « Water »)", "",
     "Propriétés de l'eau liquide (cp, température de saturation) pour "
     "le stockage à eau sous pression (phase 7)."),
    ("herrmann2009", "Herrmann S., Kretzschmar H.-J., Gatley D.P.", 2009,
     "Thermodynamic Properties of Real Moist Air, Dry Air, Steam, Water, "
     "and Ice (RP-1485)",
     "HVAC&R Research, 15(5), 961-986",
     "https://doi.org/10.1080/10789669.2009.10390874", "article_revise",
     "payant ; DOI vérifié via Crossref le 21 nov. 2026 ; formulation "
     "implémentée dans CoolProp (HumidAir, HAPropsSI)", "",
     "Air humide réel avec facteur d'augmentation de la solubilité de "
     "l'eau ; domaine 10 Pa à 10 MPa, −143 à 350 °C."),
    ("tesla2020", "Tesla Inc.", 2020,
     "Megapack Datasheet (active), rev. 2.1",
     "fiche technique du fabricant, 10 décembre 2020",
     "https://www.fes-group.co.uk/wp-content/uploads/2021/02/"
     "Megapack-Datasheet.pdf", "fiche_fabricant",
     "PDF vérifié le 22 nov. 2026 (copie publique chez un intégrateur) ; "
     "les fiches plus récentes (Megapack 2 XL, 2025) sont chiffrées et "
     "n'ont pas pu être lues",
     "data/sources/tesla2020_megapack/"
     "Megapack_datasheet_rev2.1_2020-12-10.pdf",
     "Batterie lithium-ion en conteneur : énergie, puissance, masse, "
     "rendement aller-retour ; sert de comparaison au centre d'urgence."),
    ("caterpillar2020", "Caterpillar Inc.", 2020,
     "Cat D100 GC Diesel Generator Sets, Standby 60 Hz (LEHE2663-02)",
     "fiche technique du fabricant, décembre 2020",
     "https://csdieselgenerators.com/Images/Generators/2954/"
     "CAT-D100GC-spec-sheet.pdf", "fiche_fabricant",
     "PDF vérifié le 22 nov. 2026 (copie publique chez un distributeur)",
     "data/sources/caterpillar2020_d100gc/LEHE2663-02_D100GC.pdf",
     "Génératrice diesel de 100 kW : consommation à 50, 75 et 100 % de "
     "charge, masse ; sert de comparaison au centre d'urgence."),
    ("nrel2023", "Cole W., Karmakar A.", 2023,
     "Cost Projections for Utility-Scale Battery Storage: 2023 Update "
     "(NREL/TP-6A40-85332)",
     "National Renewable Energy Laboratory, Golden (Colorado)",
     "https://doi.org/10.2172/1984976", "rapport",
     "DOI vérifié le 22 nov. 2026 (notice OSTI 1984976) ; le PDF chez NREL "
     "n'a pas pu être téléchargé (DNS) : valeurs prises au résumé de la "
     "notice", "",
     "Projections de coût (bas, moyen, haut) des batteries lithium-ion "
     "de 4 h, en dollars américains de 2022, pour 2030 et 2050."),
    ("asm1990", "ASM Handbook Committee", 1990,
     "Properties and Selection: Nonferrous Alloys and Special-Purpose "
     "Materials (ASM Handbook, Volume 2)",
     "ASM International, Materials Park (Ohio)",
     "https://doi.org/10.31399/asm.hb.v02.9781627081627", "livre",
     "payant ; DOI vérifié le 21 nov. 2026 (redirige vers la fiche du "
     "volume chez ASM) ; même source [28] que Dormoy pour l'aluminium "
     "6061-T6 ; chapitres réservés aux abonnés, valeurs typiques "
     "reproduites par les fiches des fournisseurs", "",
     "Propriétés mécaniques typiques des alliages d'aluminium."),
    ("feistel2006", "Feistel R., Wagner W.", 2006,
     "A New Equation of State for H2O Ice Ih",
     "Journal of Physical and Chemical Reference Data, 35(2), 1021-1047",
     "https://doi.org/10.1063/1.2183324", "article_revise",
     "payant ; DOI vérifié via Crossref le 21 nov. 2026", "",
     "Équation d'état IAPWS de la glace Ih : enthalpie de fusion au point "
     "triple."),
    ("lemmon2000",
     "Lemmon E.W., Jacobsen R.T., Penoncello S.G., Friend D.G.", 2000,
     "Thermodynamic Properties of Air and Mixtures of Nitrogen, Argon, and "
     "Oxygen From 60 to 2000 K at Pressures to 2000 MPa",
     "Journal of Physical and Chemical Reference Data, 29(3), 331-385",
     "https://doi.org/10.1063/1.1285884", "article_revise",
     "payant ; équation implémentée dans CoolProp (fluide « Air »)", "",
     "Équation d'état de l'air réel utilisée par Dormoy [38] et par le "
     "simulateur via CoolProp."),
]

# (id, nom, valeur, vmin, vmax, unite, source, localisation, conditions,
#  niveau, notes)
P = []


def p(id_, nom, valeur, unite, source, loc, niveau, conditions="", notes="",
      vmin="", vmax=""):
    P.append((id_, nom, valeur, vmin, vmax, unite, source, loc, conditions,
              niveau, notes))


# --- Compresseur (Sauer WP4351 Basic) ---------------------------------
p("compresseur.marque_modele", "Compresseur : marque et modèle",
  "Sauer WP4351 Basic", "texte", S, "tableau 7", "fabricant")
p("compresseur.puissance_arbre",
  "Puissance nominale à l'arbre du compresseur", 45, "kW", S,
  "tableau 7 ; §2.1", "fabricant")
p("compresseur.nb_etages", "Nombre d'étages de compression", 4, "-", S,
  "tableau 7 ; §2.1", "fabricant")
p("compresseur.pression_max_conception",
  "Pression maximale de conception du compresseur", 350, "bar", S,
  "tableau 7 ; §2.1", "fabricant",
  notes="Pression absolue supposée (l'article ne précise pas abs/relative ; "
        "à 350 bar la différence est négligeable).")
p("compresseur.vitesse_rotation", "Vitesse de rotation du vilebrequin",
  1782, "rpm", S, "tableau 7 ; §2.1", "fabricant",
  "constante pendant la charge")
p("compresseur.cylindree_piston1",
  "Volume déplacé par le premier piston à chaque tour", 1.609e-3, "m3/tr",
  S, "tableau 7", "fabricant",
  notes="L'article (§2.1) arrondit à 1,61e-3 m3.")
p("compresseur.debit_volumique_entree",
  "Débit volumique aspiré par l'étage 1", 172.4, "m3/h", D, "§2.1 ; §3.1",
  "fabricant", "conditions d'aspiration",
  "1,609e-3 × 1782 × 60 = 172,0 m3/h ; l'article donne 172,4. "
  "Écart de 0,2 % non expliqué.")
p("compresseur.debit_volumique_reel_115bar",
  "Débit volumique réel annoncé à 115 bar", 129.2, "m3/h", S, "tableau 7",
  "fabricant", "refoulement à 115 bar")
p("compresseur.debit_volumique_reel_200bar",
  "Débit volumique réel annoncé à 200 bar", 125.4, "m3/h", S, "tableau 7",
  "fabricant", "refoulement à 200 bar")
p("compresseur.rendement_electrique",
  "Rendement électrique du moteur du compresseur (plage)", "", "%", S,
  "tableau 7", "fabricant",
  notes="Résout le point d'attention de la phase 1 : le rendement "
        "mécanique calibré (69-74 %) ne contient PAS le rendement "
        "électrique. Éq. 5 : W_el = W_pol / (eta_mec × eta_el).",
  vmin=94, vmax=95)
p("compresseur.rendement_volumetrique",
  "Rendement volumétrique moyen du compresseur", 83, "%", D,
  "§3.1 ; tableau 7 (supp.)", "calcul_personnel", "charge 1 → 190 bar",
  "0,043 / 0,052 = 0,83. Calculé par Dormoy à partir du débit fabricant et "
  "du débit d'entrée mesuré.")
p("compresseur.debit_massique_entree_moyen",
  "Débit massique moyen à l'entrée du compresseur (point 1)", 0.052,
  "kg/s", D, "§3.1", "mesure", "charge 1 → 190 bar, état ambiant mesuré",
  "Déduit de l'état mesuré de l'air et du débit volumique de 172,4 m3/h.")
p("compresseur.debit_massique_sortie",
  "Débit massique à la sortie du compresseur (point 9)", 0.043, "kg/s", D,
  "§3.1", "fabricant", "valeur annoncée par le fabricant, pas mesurée")
p("compresseur.rapport_compression_etage1",
  "Rapport de compression moyen, étage 1", 3.25, "-", D,
  "§3.1 ; fig. 8 ; tableau 7 (supp.)", "mesure", "stable pendant la charge",
  "Moyenne des mesures.")
p("compresseur.rapport_compression_etage2",
  "Rapport de compression moyen, étage 2", 3.75, "-", D,
  "§3.1 ; fig. 8 ; tableau 7 (supp.)", "mesure", "stable pendant la charge",
  "Moyenne des mesures.")
p("compresseur.rapport_compression_etage3",
  "Rapport de compression, étage 3 (plage)", "", "-", D,
  "§3.1 ; fig. 8 ; tableau 7 (supp.)", "mesure",
  "croît linéairement avec la pression du réservoir au-dessus de 60 bar",
  "Courbe à numériser (fig. 8).", vmin=3.54, vmax=4.44)
p("compresseur.rapport_compression_etage4",
  "Rapport de compression, étage 4 (plage)", "", "-", D, "§3.1 ; fig. 8",
  "mesure",
  "croît linéairement avec la pression du réservoir au-dessus de 60 bar",
  "Le texte donne 1,52-3,5 ; le tableau 7 des données supplémentaires "
  "donne 1,63-3,50. Incohérence de la source. Courbe à numériser (fig. 8).",
  vmin=1.52, vmax=3.5)
for i, (n0, n1) in enumerate(
        [(1.35, 1.35), (1.37, 1.38), (1.44, 1.44), (1.59, 1.52)], start=1):
    p(f"compresseur.indice_polytropique_etage{i}",
      f"Indice polytropique calibré, étage {i}", n1, "-", D, "tableau 2",
      "calibration", "charge 1 → 190 bar",
      f"Valeur initiale avant calibration : {n0} (étage 4 : 1,59 déduit des "
      "mesures, puis calibré à 1,52).")
p("compresseur.rendement_mecanique",
  "Rendement mécanique calibré du compresseur (plage)", "", "%", D,
  "tableau 2 ; §3.2", "calibration", "varie avec la pression du réservoir",
  "Valeur initiale 85 % (littérature). La loi de variation avec la "
  "pression n'est pas donnée : hypothèse à poser en phase 1 et à marquer "
  "comme telle.", vmin=69, vmax=74)

# --- Refroidisseurs ---------------------------------------------------
p("refroidisseur.nb_etages", "Nombre d'étages de refroidissement", 4, "-",
  S, "tableau 7", "fabricant")
p("refroidisseur.debit_volumique_air_froid",
  "Débit volumique de la source froide (air ambiant) du refroidisseur",
  11000, "m3/h", S, "tableau 7", "fabricant",
  notes="Air de refroidissement tiré de l'ambiant (§3.3.1).")
for i, (e0, e1) in enumerate([(83, 82), (86, 85), (86, 88)], start=1):
    p(f"refroidisseur.efficacite_etage{i}",
      f"Efficacité NTU calibrée du refroidisseur, étage {i}", e1, "%", D,
      "tableau 2", "calibration", "charge 1 → 190 bar",
      f"Valeur initiale : {e0} %.")
p("refroidisseur.efficacite_etage4",
  "Efficacité NTU calibrée du refroidisseur, étage 4 (plage)", "", "%", D,
  "tableau 2 ; §3.2", "calibration", "croît avec la pression du réservoir",
  "Valeur initiale constante 76 %. Modèle transitoire : efficacité qui "
  "augmente avec la pression. Loi exacte non donnée : hypothèse en phase 1.",
  vmin=74, vmax=85)

# --- Sécheur ----------------------------------------------------------
p("secheur.efficacite",
  "Efficacité massique du sécheur par adsorption (débit sortant / entrant)",
  81, "%", D, "§2.2.3 ; éq. 10", "mesure", "charge",
  "Le fabricant annonce une perte de 20-25 % (soit 75-80 %).")
p("secheur.perte_debit_fabricant",
  "Perte de débit annoncée par le fabricant du sécheur (plage)", "", "%",
  D, "§2.1 ; §2.2.3", "fabricant", vmin=20, vmax=25)
p("secheur.debit_massique_sortie",
  "Débit massique moyen à la sortie du sécheur (point 10), entrant dans "
  "les réservoirs", 0.032, "kg/s", D, "§3.1", "mesure",
  "charge 1 → 190 bar",
  "Perte cumulée compresseur + sécheur : 0,020 kg/s, soit 38 %.")

# --- Réservoirs -------------------------------------------------------
p("reservoir.nb_320L", "Nombre de réservoirs de 320 L", 8, "-", D,
  "§1 (contributions) ; éq. 11-12", "fabricant")
p("reservoir.nb_270L", "Nombre de réservoirs de 270 L", 12, "-", D,
  "§1 (contributions) ; éq. 11-12", "fabricant",
  notes="L'article dit 0,27 m3 ; la nomenclature et les éq. 11-12 parlent "
        "de 275 L. Voir reservoir.volume_total.")
p("reservoir.volume_unitaire_320L",
  "Volume intérieur d'un réservoir de 320 L", 0.32, "m3", S, "tableau 8",
  "fabricant")
p("reservoir.volume_unitaire_270L",
  "Volume intérieur d'un réservoir de 270 L", 0.27, "m3", S, "tableau 8",
  "fabricant",
  notes="8 × 0,32 + 12 × 0,27 = 5,80 m3, mais l'article annonce 5,86 m3, "
        "ce qui correspond à 0,275 m3 (275 L). Incohérence de 1 % dans la "
        "source.")
p("reservoir.volume_total",
  "Volume total du système de réservoirs (réservoir équivalent)", 5.86,
  "m3", D, "§2.1 ; §3.1 ; §3.3", "fabricant",
  notes="Valeur utilisée par Dormoy pour toutes les simulations. Préférer "
        "cette valeur au produit des volumes unitaires (5,80).")
p("reservoir.diametre_interieur",
  "Diamètre intérieur d'un réservoir (les deux modèles)", 0.372, "m", S,
  "tableau 8", "fabricant")
p("reservoir.surface_interieure_320L",
  "Surface intérieure d'un réservoir de 320 L", 3.6, "m2", S, "tableau 8",
  "fabricant")
p("reservoir.surface_interieure_270L",
  "Surface intérieure d'un réservoir de 270 L", 3.06, "m2", S, "tableau 8",
  "fabricant")
p("reservoir.surface_equivalente_totale",
  "Surface d'échange du réservoir équivalent (éq. 12)", 65.52, "m2", D,
  "éq. 12 ; tableau 8 (supp.)", "calcul_personnel",
  notes="8 × 3,6 + 12 × 3,06 = 65,52 m2.")
p("reservoir.masse_320L", "Masse d'un réservoir de 320 L", 107, "kg", S,
  "tableau 8", "fabricant")
p("reservoir.masse_270L", "Masse d'un réservoir de 270 L", 95, "kg", S,
  "tableau 8", "fabricant")
p("reservoir.alu.epaisseur",
  "Épaisseur de la couche intérieure en aluminium 6061-T6", 0.005, "m", S,
  "tableau 8", "fabricant")
p("reservoir.alu.conductivite",
  "Conductivité thermique de l'aluminium 6061-T6", 167, "W/mK", S,
  "tableau 8", "mesure", "20 °C", "ASM Handbook [28] cité par Dormoy.")
p("reservoir.alu.cp", "Chaleur massique de l'aluminium 6061-T6", 869,
  "J/kgK", S, "tableau 8", "mesure", "20 °C",
  "ASM Handbook [28] cité par Dormoy.")
p("reservoir.alu.masse_volumique",
  "Masse volumique de l'aluminium 6061-T6", 2700, "kg/m3", S, "tableau 8",
  "mesure", "20 °C", "ASM Handbook [28] cité par Dormoy.")
p("reservoir.alu.masse_320L",
  "Masse de la couche d'aluminium, réservoir de 320 L", 53, "kg", S,
  "tableau 8", "fabricant")
p("reservoir.alu.masse_270L",
  "Masse de la couche d'aluminium, réservoir de 270 L", 45, "kg", S,
  "tableau 8", "fabricant")
p("reservoir.fibre.epaisseur",
  "Épaisseur de la couche extérieure en fibre de carbone", 0.011, "m", S,
  "tableau 8", "fabricant")
p("reservoir.fibre.conductivite",
  "Conductivité thermique de la fibre de carbone (composite)", 0.60,
  "W/mK", S, "tableau 8", "hypothese", "20 °C",
  "Estimation de Dormoy d'après Ou et al. [29] et Khan et al. [30] ; "
  "composition exacte non divulguée par le fournisseur.")
p("reservoir.fibre.cp",
  "Chaleur massique de la fibre de carbone (composite)", 900, "J/kgK", S,
  "tableau 8", "hypothese", "20 °C",
  "Estimation de Dormoy d'après [29,30].")
p("reservoir.fibre.masse_volumique",
  "Masse volumique de la fibre de carbone (composite)", 1400, "kg/m3", S,
  "tableau 8", "hypothese", "20 °C",
  "Estimation de Dormoy d'après [29,30].")
p("reservoir.fibre.masse_320L",
  "Masse de la couche de fibre de carbone, réservoir de 320 L", 54, "kg",
  S, "tableau 8", "fabricant")
p("reservoir.fibre.masse_270L",
  "Masse de la couche de fibre de carbone, réservoir de 270 L", 50, "kg",
  S, "tableau 8", "fabricant")
p("reservoir.K_global",
  "Coefficient de transfert thermique global du réservoir équivalent "
  "(éq. 14)", 8.8, "W/m2K", D, "tableau 2 ; §3.2", "calibration", "charge",
  "Valeur initiale 13,9 W/m2K (Chen et al. [25]).")
p("reservoir.h_conv_ext",
  "Coefficient de convection extérieur paroi-ambiant (éq. 21)", 2.47,
  "W/m2K", D, "§3.2", "calibration", "décharge",
  "Température de la structure supposée uniforme.")
p("reservoir.h_conv_int",
  "Coefficient de convection intérieur air-paroi (éq. 21)", 25.42,
  "W/m2K", D, "§3.2", "calibration", "décharge",
  "Température de la structure supposée uniforme.")

# --- Détendeur --------------------------------------------------------
p("detendeur.pression_sortie_min",
  "Pression de sortie minimale réglable du détendeur", 17, "bar", D,
  "§2.1", "fabricant")
p("detendeur.pression_sortie_max",
  "Pression de sortie maximale réglable du détendeur", 275, "bar", D,
  "§2.1", "fabricant")
p("detendeur.ecart_pression_min",
  "Écart de pression minimal entrée-sortie pour une sortie stable ; arrêt "
  "automatique sous ce seuil", 15, "bar", D, "§2.1", "mesure",
  "observation sur le banc")
p("detendeur.cheayb.pression_min_validite",
  "Borne basse de validité du modèle de Cheayb et al. (éq. 15)", 25,
  "bar", D, "§2.2.5", "simulation_publiee",
  notes="Dormoy l'utilise jusqu'à 190 bar et observe un MAPE de 0,21 % "
        "(tableau 4).")
p("detendeur.cheayb.pression_max_validite",
  "Borne haute de validité du modèle de Cheayb et al. (éq. 15)", 150,
  "bar", D, "§2.2.5", "simulation_publiee")

# --- Essai de charge mesuré -------------------------------------------
p("essai_charge.pression_initiale",
  "Pression initiale du réservoir, essai de charge", 1.01325, "bar", D,
  "§3.1", "mesure", "« atmospheric pressure »",
  "Valeur exacte non donnée ; pression atmosphérique normale supposée.")
p("essai_charge.pression_finale",
  "Pression finale du réservoir, essai de charge", 190, "bar", D, "§3.1",
  "mesure")
p("essai_charge.duree", "Durée de l'essai de charge complet", 10, "h", D,
  "§3.1", "mesure", "1 → 190 bar",
  "« almost 10 h » : valeur approximative ; courbe fig. 10 à numériser.")
p("essai_charge.energie_consommee",
  "Énergie électrique consommée, essai de charge", 396, "kWh", D, "§3.1",
  "mesure", "1 → 190 bar, 5,86 m3")
p("essai_charge.puissance_moyenne",
  "Puissance électrique moyenne, essai de charge", 39, "kW", D, "§3.1",
  "mesure", "1 → 190 bar")
p("essai_charge.pas_acquisition",
  "Pas de temps d'acquisition des mesures", 1, "s", D, "§3.1", "mesure")

# --- Essai de décharge mesuré -----------------------------------------
p("essai_decharge.volume",
  "Volume de réservoir utilisé, essai de décharge", 2.56, "m3", D, "§3.1",
  "mesure", "capacité partielle (8 × 0,32 m3)")
p("essai_decharge.pression_initiale",
  "Pression initiale, essai de décharge", 190, "bar", D, "§3.1", "mesure")
p("essai_decharge.pression_consigne_detendeur",
  "Pression de consigne en sortie du détendeur, essai de décharge", 35,
  "bar", D, "§3.1", "mesure")
p("essai_decharge.pression_arret",
  "Pression du réservoir à l'arrêt de l'essai de décharge", 50, "bar", D,
  "§3.1", "mesure", notes="35 + 15 bar d'écart minimal.")
p("essai_decharge.temperature_initiale",
  "Température moyenne initiale de l'air dans le réservoir, essai de "
  "décharge", 55, "degC", D, "§3.1", "mesure")
p("essai_decharge.duree", "Durée de l'essai de décharge", 38, "min", D,
  "§3.1", "mesure", "190 → 50 bar")
p("essai_decharge.debit_massique",
  "Débit massique moyen mesuré au débitmètre, essai de décharge", 0.148,
  "kg/s", D, "§3.1", "mesure")

# --- Erreurs du modèle de Dormoy --------------------------------------
p("dormoy_modele.charge.MAPE_max",
  "MAPE maximal du modèle de Dormoy sur la charge (tous paramètres)",
  3.58, "%", D, "tableau 3", "simulation_publiee",
  notes="Tolérance à viser en phase 1.")
p("dormoy_modele.charge.T_etage4.RMSE_calibre",
  "RMSE de la température de sortie de l'étage 4 après calibration", 2.83,
  "degC", D, "§3.2 ; fig. 9", "simulation_publiee",
  notes="Différence de températures (ne pas convertir en K absolu) : "
        "10,39 °C avant calibration.")
p("dormoy_modele.charge.T_etage4.MAPE_calibre",
  "MAPE de la température de sortie de l'étage 4 après calibration", 1.90,
  "%", D, "§3.2 ; fig. 9", "simulation_publiee",
  notes="5,49 % avant calibration.")
p("dormoy_modele.decharge.MAPE_max_reservoir",
  "MAPE maximal du modèle de Dormoy sur la décharge (réservoir)", 1.10,
  "%", D, "tableau 4", "simulation_publiee")
p("dormoy_modele.decharge.MAPE_detendeur_isenthalpique",
  "MAPE de la température de sortie du détendeur, modèle isenthalpique",
  0.39, "%", D, "tableau 4", "simulation_publiee", notes="RMSE 1,17 °C.")
p("dormoy_modele.decharge.MAPE_detendeur_cheayb",
  "MAPE de la température de sortie du détendeur, modèle de Cheayb", 0.21,
  "%", D, "tableau 4", "simulation_publiee", notes="RMSE 0,98 °C.")

# --- Cas simulés par Dormoy -------------------------------------------
p("cas_base.energie_produite",
  "Énergie produite, cas de base simulé (1 étage, sans réchauffage, "
  "190 bar, 5,86 m3)", 16.93, "kWh", D, "§3.3", "simulation_publiee")
p("cas_base.energie_consommee",
  "Énergie consommée, cas de base simulé", 366.75, "kWh", D, "§3.3",
  "simulation_publiee",
  notes="Simulée, à ne pas confondre avec les 396 kWh mesurés.")
p("cas_base.rte_annonce",
  "Rendement aller-retour annoncé pour le cas de base", 4.3, "%", D,
  "§3.3", "simulation_publiee",
  notes="16,93 / 396 = 4,3 % (consommation mesurée).")
p("cas_base.rte_recalcule",
  "Rendement aller-retour recalculé pour le cas de base", 4.6, "%", D,
  "§3.3", "calcul_personnel",
  notes="16,93 / 366,75 = 4,6 % (consommation simulée). L'article mélange "
        "les deux.")
p("cas_Tamb.plage_min",
  "Température ambiante minimale de l'analyse paramétrique", -15, "degC",
  D, "§3.3.1", "simulation_publiee")
p("cas_Tamb.plage_max",
  "Température ambiante maximale de l'analyse paramétrique", 25, "degC",
  D, "§3.3.1", "simulation_publiee")
p("cas_Tamb.debit_massique_-15C", "Débit massique de charge à -15 °C",
  0.065, "kg/s", D, "§3.3.1 ; fig. 11", "simulation_publiee")
p("cas_Tamb.debit_massique_25C", "Débit massique de charge à 25 °C",
  0.056, "kg/s", D, "§3.3.1 ; fig. 11", "simulation_publiee")
p("cas_Tamb.duree_charge_25C", "Durée de charge à 25 °C", 595, "min", D,
  "§3.3.1", "simulation_publiee")
p("cas_Tamb.energie_produite_prechauffe_-15C",
  "Énergie produite avec réchauffage à -15 °C", 27, "kWh", D,
  "§3.3.1 ; fig. 12", "simulation_publiee")
p("cas_Tamb.energie_produite_prechauffe_25C",
  "Énergie produite avec réchauffage à 25 °C", 22, "kWh", D,
  "§3.3.1 ; fig. 12", "simulation_publiee")
p("cas_Tamb.rte_prechauffe_-15C", "RTE avec réchauffage à -15 °C", 6.3,
  "%", D, "§3.3.1 ; fig. 12", "simulation_publiee")
p("cas_Tamb.rte_prechauffe_25C", "RTE avec réchauffage à 25 °C", 5.4, "%",
  D, "§3.3.1 ; fig. 12", "simulation_publiee")
p("cas_pmax.plage_min",
  "Pression maximale de stockage, borne basse de l'analyse", 75, "bar", D,
  "§3.3.2", "simulation_publiee")
p("cas_pmax.plage_max",
  "Pression maximale de stockage, borne haute de l'analyse", 300, "bar", D,
  "§3.3.2", "simulation_publiee")
p("cas_pmax.puissance_compresseur_300bar",
  "Puissance du compresseur à 300 bar", 48, "kW", D, "§3.3.2",
  "simulation_publiee", notes="39 kW à 190 bar.")
p("cas_pmax.optimum_prechauffe",
  "Pression maximale optimale, système avec réchauffage", 150, "bar", D,
  "§3.3.2 ; fig. 13", "simulation_publiee",
  notes="RTE 5,3 % à l'optimum, 5,1 % au-delà.")
p("cas_pmax.optimum_sans_prechauffage",
  "Pression maximale optimale, système sans réchauffage", 125, "bar", D,
  "§3.3.2 ; fig. 13", "simulation_publiee",
  notes="RTE 4,2 % à l'optimum, 3,8 % au-delà.")
p("cas_n.energie_produite_n1_sans",
  "Énergie produite avec indice polytropique 1 (isotherme), sans "
  "réchauffage", 17.9, "kWh", D, "§3.3.3 ; fig. 15", "simulation_publiee")
p("cas_n.energie_produite_n1_avec",
  "Énergie produite avec indice polytropique 1, avec réchauffage", 22.8,
  "kWh", D, "§3.3.3 ; fig. 15", "simulation_publiee")
p("cas_n.rte_n1_avec", "RTE avec indice polytropique 1 et réchauffage",
  7.5, "%", D, "§3.3.3", "simulation_publiee")
p("cas_n.puissance_compresseur_n1",
  "Puissance du compresseur avec indice polytropique 1 (borne haute)", 36,
  "kW", D, "§3.3.3 ; fig. 14", "simulation_publiee",
  notes="« less than 36 kW ».")
p("cas_etages.energie_consommee_1etage",
  "Énergie de charge avec turbine à 1 étage (pression de travail minimale "
  "basse)", 380, "kWh", D, "§3.3.4", "simulation_publiee",
  notes="« nearly 380 kWh ».")
p("cas_etages.energie_consommee_3etages",
  "Énergie de charge avec turbine à 3 étages (recharge depuis ~55 bar)",
  290, "kWh", D, "§3.3.4", "simulation_publiee")
p("cas_etages.rte_1etage_prechauffe", "RTE avec 1 étage et réchauffage",
  5.5, "%", D, "§3.3.4 ; fig. 16", "simulation_publiee")
p("cas_etages.rte_3etages_prechauffe", "RTE avec 3 étages et réchauffage",
  16.0, "%", D, "§3.3.4 ; fig. 16 ; §4", "simulation_publiee",
  notes="La chaleur de réchauffage (46,2 kWh) n'est pas comptée dans ce "
        "rendement.")

# --- Turbine DEPRAG (tableau 9) ---------------------------------------
T9 = {
    "pression_entree": ([40, 11, 3], "bar", "Pression d'entrée"),
    "pression_sortie": ([11.5, 3.5, 1.0], "bar", "Pression de sortie"),
    "temperature_entree": ([130, 90, 90], "degC",
                           "Température d'entrée (réchauffage requis)"),
    "temperature_sortie": ([59.2, 20.7, 16.0], "degC",
                           "Température de sortie"),
    "rapport_detente": ([0.29, 0.32, 0.34], "-",
                        "Rapport de détente (p_sortie / p_entrée)"),
    "indice_polytropique": ([1.19, 1.23, 1.27], "-",
                            "Indice polytropique calculé"),
    "debit_massique": ([0.321, 0.321, 0.321], "kg/s",
                       "Débit massique nominal"),
    "rendement_mecanique": ([53, 64, 73], "%", "Rendement mécanique"),
    "rendement_electrique": ([90, 91, 92], "%",
                             "Rendement électrique de la génératrice"),
    "puissance_mecanique": ([22.1, 22.0, 23.7], "kW", "Puissance mécanique"),
    "puissance_electrique": ([20.0, 20.1, 21.8], "kW",
                             "Puissance électrique"),
}
for key, (vals, unite, nom) in T9.items():
    for i, v in enumerate(vals, start=1):
        p(f"turbine.etage{i}.{key}", f"Turbine DEPRAG, étage {i} : {nom}", v,
          unite, S, "tableau 9", "fabricant", "conditions nominales",
          "Turbine non installée sur le banc : utilisée en simulation "
          "seulement.")
p("turbine.puissance_electrique_totale",
  "Puissance électrique totale des 3 étages de turbine", 62, "kW", D,
  "§2.1", "fabricant", "avec réchauffage 130/90/90 °C",
  "20,0 + 20,1 + 21,8 = 61,9 kW.")
p("turbine.nb_etages_max",
  "Nombre d'étages de turbine (configuration simulée)", 3, "-", D, "§2.1",
  "simulation_publiee")

# --- Chaleur (tableaux 5 et 6) ----------------------------------------
p("turbine.etage1.puissance_chaleur_requise",
  "Puissance thermique requise pour réchauffer l'air avant la turbine 1 "
  "(plage)", "", "kW", D, "tableau 5", "simulation_publiee",
  "190 → 55 bar, 3 étages, 0,321 kg/s", "ΔT maximal de 115 °C.",
  vmin=33.5, vmax=38.0)
for i, q in [(2, 9.6), (3, 22.5)]:
    p(f"turbine.etage{i}.puissance_chaleur_requise",
      f"Puissance thermique requise pour réchauffer l'air avant la turbine "
      f"{i}", q, "kW", D, "tableau 5", "simulation_publiee",
      "190 → 55 bar, 3 étages, 0,321 kg/s")
for i, e in [(1, 24.8), (2, 6.4), (3, 15.0)]:
    p(f"turbine.etage{i}.energie_chaleur_requise",
      f"Énergie thermique requise avant la turbine {i}, sur la décharge", e,
      "kWh", D, "tableau 5", "simulation_publiee",
      "décharge de 40 min, 190 → 55 bar")
p("turbine.energie_chaleur_requise_totale",
  "Énergie thermique totale requise par la turbine à 3 étages", 46.2,
  "kWh", D, "tableau 5 ; §3.3.5", "simulation_publiee",
  "décharge de 40 min, 190 → 55 bar")
p("decharge_3etages.duree",
  "Durée de la décharge simulée avec 3 étages", 40, "min", D, "§3.3.5",
  "simulation_publiee", "190 → 55 bar")
for i, (q, e) in enumerate(
        [(1.9, 12.5), (3.8, 23.4), (5.0, 30.0), (3.5, 6.3)], start=1):
    p(f"refroidisseur.etage{i}.puissance_chaleur_sup130",
      f"Puissance thermique récupérable au-dessus de 130 °C, "
      f"refroidisseur {i}", q, "kW", D, "tableau 6", "simulation_publiee",
      "charge 55 → 190 bar, 0,052 kg/s")
    p(f"refroidisseur.etage{i}.energie_chaleur_sup130",
      f"Énergie thermique récupérable au-dessus de 130 °C, "
      f"refroidisseur {i}", e, "kWh", D, "tableau 6", "simulation_publiee",
      "charge 55 → 190 bar sur 6,8 h")
p("refroidisseur.energie_chaleur_sup130_totale",
  "Énergie thermique totale récupérable au-dessus de 130 °C "
  "(4 refroidisseurs)", 72.2, "kWh", D, "tableau 6 ; §3.3.5",
  "simulation_publiee", "charge 55 → 190 bar sur 6,8 h")
p("refroidisseur.energie_chaleur_totale",
  "Énergie thermique totale rejetée par les 4 refroidisseurs (toutes "
  "températures)", 189.2, "kWh", D, "§3.3.5", "simulation_publiee",
  "charge 55 → 190 bar sur 6,8 h",
  "143 kWh resteraient disponibles après réchauffage de la turbine.")
p("charge_55_190.duree", "Durée de la charge simulée de 55 à 190 bar",
  6.8, "h", D, "§3.3.5", "simulation_publiee")
p("charge_55_190.pression_min",
  "Pression minimale de travail du banc avec turbine à 3 étages", 55,
  "bar", D, "§3.3.5", "simulation_publiee",
  notes="Pression d'entrée turbine 1 (40 bar) + écart minimal du détendeur "
        "(15 bar).")

# --- Températures lues sur les figures (approximatives) ---------------
p("fig18.T_sortie_etage3_max",
  "Température maximale de sortie de l'étage 3 (lecture de la fig. 18)",
  200, "degC", D, "§3.3.5 ; fig. 18", "mesure", "après 3 h de charge",
  "« exceeding 200 °C » : borne basse. Courbe à numériser.")
p("fig18.T_sortie_etages1a3_min",
  "Température de sortie des étages 1 à 3 (lecture de la fig. 18, borne "
  "basse)", 150, "degC", D, "§3.3.5 ; fig. 18", "mesure", "charge",
  "« surpassing 150 °C ». Courbe à numériser.")


# --- Ajouts de la phase 1 (modèle de charge) --------------------------
p("air.R_specifique", "Constante spécifique de l'air sec (R / M)", 287.05,
  "J/kgK", "lemmon2000", "§2 (M = 28,9586 g/mol)", "mesure",
  notes="8,314462618 / 0,0289586 = 287,10 ; CoolProp donne 287,05 avec "
        "M = 28,9647 g/mol. Sert au modèle « gaz parfait » de comparaison.")
p("air.cp_1bar_20C", "Chaleur massique à pression constante de l'air",
  1006.1, "J/kgK", "lemmon2000", "équation d'état, via CoolProp", "mesure",
  "1,013 bar, 20 °C",
  "Valeur constante du modèle « gaz parfait » de comparaison.")
p("ambiance.T_amb_essai_charge",
  "Température ambiante pendant l'essai de charge", 20, "degC", D, "§3.1",
  "hypothese", "non donnée par l'article",
  "Hypothèse du projet. Le débit aspiré mesuré (0,052 kg/s) "
  "correspondrait à ≈ 52 °C à 1,013 bar avec 172,4 m3/h : l'air aspiré "
  "est sans doute plus chaud que l'ambiant, ou la mesure inclut autre "
  "chose. Voir rapports/phase1/validation_charge.md.")
p("ambiance.p_amb_essai",
  "Pression atmosphérique pendant les essais", 1.01325, "bar", D, "§3.1",
  "hypothese", "non donnée par l'article",
  "Pression normale supposée (Shawinigan, ≈ 100 m d'altitude : "
  "≈ 1,00 bar en moyenne).")
p("ambiance.humidite_relative_essai",
  "Humidité relative de l'air ambiant pendant les essais", 50, "%", D,
  "§3.1", "hypothese", "non donnée par l'article",
  "Hypothèse du projet (valeur moyenne intérieure). Sert au bloc "
  "« ambiance » obligatoire des scénarios (phase 6) ; le module humidité "
  "(phase 9) l'utilisera pour le point de rosée.")
p("compresseur.pression_refoulement_max",
  "Pression de refoulement maximale du compresseur pendant les essais "
  "(borne haute des lois calibrées)", 190, "bar", D, "§3.1 ; fig. 8 ; fig. 10",
  "calcul_personnel",
  "borne haute des lois linéaires en pression (rapport de l'étage 3, "
  "rendement mécanique, efficacité du refroidisseur 4)",
  "Égale à la pression finale de l'essai de charge "
  "(essai_charge.pression_finale) : les lois « varie avec la pression » "
  "de Dormoy (formules.md#F07) sont calibrées entre 66 et 190 bar.")
p("compresseur.pression_refoulement_min",
  "Pression de refoulement minimale du compresseur (soupape de pression "
  "minimale avant le sécheur)", 66, "bar", D, "§3.1 ; fig. 8",
  "calcul_personnel",
  "pression de réservoir sous laquelle les rapports des étages 3 et 4 "
  "restent constants",
  "1,01325 × 3,25 × 3,75 × 3,54 × 1,52 = 66,4 bar, avec les rapports "
  "minimaux des étages 3 et 4. Dormoy parle d'un seuil de 60 bar. À "
  "vérifier sur la fig. 8 numérisée.")
p("compresseur.loi_rapport_etage3",
  "Loi de variation du rapport de pression de l'étage 3",
  "linéaire en pression de refoulement, de 3,54 à p_refoulement_min "
  "jusqu'à 4,44 à 190 bar", "texte", D, "§3.1 ; fig. 8", "hypothese",
  notes="Dormoy dit « linear increase beyond the 60-bar threshold ». La "
        "pente exacte sera lue sur la fig. 8 numérisée. L'étage 4 prend "
        "le reste du rapport total.")
p("compresseur.loi_rendement_mecanique",
  "Loi de variation du rendement mécanique du compresseur",
  "linéaire en pression de refoulement, de 69 % à p_refoulement_min "
  "jusqu'à 74 % à 190 bar", "texte", D, "tableau 2 ; §3.2", "hypothese",
  notes="Dormoy donne seulement la plage 69-74 % « depending on reservoir "
        "pressure », sans le sens de variation. Hypothèse : croissant "
        "(meilleur rendement à forte charge). À confronter à la fig. 10.")
p("refroidisseur.loi_efficacite_etage4",
  "Loi de variation de l'efficacité du refroidisseur 4",
  "linéaire en pression de refoulement, de 74 % à p_refoulement_min "
  "jusqu'à 85 % à 190 bar", "texte", D, "§3.2", "hypothese",
  notes="Dormoy : « efficiency scaling alongside reservoir pressure », "
        "sans la loi exacte.")
p("reservoir.capacite_thermique_paroi",
  "Capacité thermique totale des parois des 20 réservoirs", 1.767e6, "J/K",
  S, "tableau 8", "calcul_personnel",
  notes="Aluminium : (8 × 53 + 12 × 45) kg × 869 J/kgK = 837,7 kJ/K ; "
        "fibre : (8 × 54 + 12 × 50) kg × 900 J/kgK = 928,8 kJ/K. Total "
        "1 766,5 kJ/K. Sert au modèle thermique « paroi » (décharge).")

# --- Ajouts de la phase 2 (modèle de décharge) ------------------------
for nom_c, val, desc in [
    ("a1", 0.0297, "a : terme en 1/T_in"),
    ("a2", 1.674, "a : terme en 1/T_in^2 (soustrait)"),
    ("a3", 19093, "a : terme en 1/T_in^3 (soustrait)"),
    ("a4", 0.0000157, "a : constante (ajoutée)"),
    ("b1", 50.1, "b : terme en 1/T_in"),
    ("b2", 14830, "b : terme en 1/T_in^2"),
    ("b3", 366000, "b : terme en 1/T_in^3"),
    ("b4", 0.122, "b : constante (soustraite)"),
]:
    p(f"detendeur.cheayb.{nom_c}",
      f"Coefficient de l'éq. 15 (modèle de Cheayb et al.), {desc}", val,
      "-", D, "§2.2.5, éq. 15", "simulation_publiee",
      "pression en bar, température en K ; validé de 25 à 150 bar",
      "T(P) = a·P² + b·P + c ; a = ½(a1/T − a2/T² − a3/T³ + a4) ; "
      "b = b1/T + b2/T² + b3/T³ − b4 ; c = T_in − a·P_in² − b·P_in. "
      "Relation semi-empirique d'après Hoxton, reprise par Cheayb et al. "
      "[27]. Lue sur l'image de la page 8 (extraction texte illisible).")
p("essai_decharge.surface",
  "Surface d'échange des 8 réservoirs de 320 L utilisés à la décharge",
  28.8, "m2", S, "tableau 8", "calcul_personnel",
  notes="8 × 3,6 m2. Dormoy dit « 2,56 m3 », soit exactement 8 × 0,32.")
p("essai_decharge.capacite_thermique_paroi",
  "Capacité thermique des parois des 8 réservoirs de 320 L", 7.574e5,
  "J/K", S, "tableau 8", "calcul_personnel",
  notes="8 × (53 kg × 869 + 54 kg × 900) J/K = 757,4 kJ/K.")
p("essai_decharge.temperature_paroi_initiale",
  "Température initiale de la structure des réservoirs, essai de "
  "décharge", 55, "degC", D, "§3.1 ; §3.2", "hypothese",
  "égale à celle de l'air",
  "Non mesurée. Dormoy note que la chaleur accumulée dans la structure "
  "pendant la charge influence la température de l'air en décharge.")
p("cas_base.turbine",
  "Détendeur du cas de base (1 étage, sans réchauffage)",
  "étage 3 de la turbine DEPRAG (3 → 1 bar, n = 1,27, 0,321 kg/s)",
  "texte", D, "§3.3", "simulation_publiee",
  notes="« a single-stage expansion device represented by the last stage "
        "of the selected turbine (Table 9) ». Le détendeur est donc réglé "
        "à 3 bar et la décharge s'arrête à 18 bar, pas à 50 bar comme dans "
        "l'essai mesuré.")
p("cas_base.pression_arret",
  "Pression d'arrêt de la décharge, cas de base (3 bar + 15 bar d'écart)",
  18, "bar", D, "§2.1 ; §3.3 ; tableau 9 (supp.)", "calcul_personnel",
  notes="Pression d'entrée de l'étage 3 (3 bar) + écart minimal du "
        "détendeur (15 bar).")
p("cas_2etages.pression_arret",
  "Pression d'arrêt de la décharge avec 2 étages (étages 2 et 3)", 26,
  "bar", D, "§3.3.4 ; tableau 9 (supp.)", "calcul_personnel",
  notes="11 bar + 15 bar. Hypothèse : les 2 étages sont les étages 2 et 3 "
        "de la turbine DEPRAG.")
p("cas_base.temperature_initiale_decharge",
  "Température initiale de l'air et des parois pour les cas de décharge "
  "simulés", 55, "degC", D, "§3.1 ; §3.3 ; tableau 5", "hypothese",
  "non donnée par l'article pour les cas simulés",
  "Valeur mesurée au début de l'essai de décharge (§3.1). Retenue parce "
  "qu'elle reproduit le tableau 5 (chaleur de réchauffage 24,8 / 6,4 / "
  "15,0 kWh) et les températures d'entrée de turbine qu'il implique "
  "(13-27 °C). Variantes testées : 20 °C (air revenu à l'ambiant) et "
  "29 °C (fin de la charge simulée en phase 1). Voir "
  "rapports/phase2/validation_decharge.md.")
p("turbine.rechauffage.source",
  "Source de la chaleur de réchauffage dans les simulations de Dormoy",
  "externe, non comptée dans le rendement", "texte", D, "§2.4 ; §3.3.4",
  "simulation_publiee",
  notes="Dormoy impose 130/90/90 °C sans modéliser la source. Le "
        "simulateur marque cette chaleur « externe » et calcule aussi le "
        "rendement qui la compte.")

# --- Ajouts de la phase 4 (lit de gravier) ----------------------------
T_ = "tola2022"
p("materiau.gravier_tola.masse_volumique", "Masse volumique du gravier",
  2750, "kg/m3", T_, "tableau 3", "simulation_publiee",
  notes="Valeur adoptée par Tola d'après sa réf. [28].")
p("materiau.gravier_tola.cp", "Chaleur massique du gravier", 900, "J/kgK",
  T_, "tableau 3", "simulation_publiee")
p("materiau.gravier_tola.diametre_particule",
  "Diamètre moyen des particules de gravier", 0.03, "m", T_, "tableau 3",
  "simulation_publiee")
p("materiau.gravier_tola.porosite", "Fraction de vide du lit de gravier",
  0.3, "-", T_, "tableau 3 ; §2.3", "simulation_publiee",
  notes="Tola : granulométrie variée, d'où 0,3 (plus compact que 0,38 "
        "pour des sphères).")
p("materiau.gravier_tola.conductivite",
  "Conductivité thermique des particules de gravier", 2.5, "W/mK",
  "robertson1988", "tableaux granite / gneiss", "hypothese",
  "roche silicatée, 20 °C",
  "Tola ne la donne pas. 2 à 3,5 W/m·K selon la roche (USGS). Sert à la "
  "correction de Jeffreson (gradient interne) et à la conduction axiale.")
p("lit.wakao.a", "Corrélation de Wakao : Nu = a + b Re^c Pr^(1/3), a", 2.0,
  "-", "wakao1979", "éq. 11", "simulation_publiee",
  "15 < Re < 8500, Re sur la vitesse superficielle et le diamètre des "
  "particules")
p("lit.wakao.b", "Corrélation de Wakao : b", 1.1, "-", "wakao1979",
  "éq. 11", "simulation_publiee")
p("lit.wakao.c", "Corrélation de Wakao : exposant de Re", 0.6, "-",
  "wakao1979", "éq. 11", "simulation_publiee")
p("lit.wakao.Re_min", "Borne basse de validité de Wakao", 15, "-",
  "wakao1979", "§ résultats", "simulation_publiee")
p("lit.wakao.Re_max", "Borne haute de validité de Wakao", 8500, "-",
  "wakao1979", "§ résultats", "simulation_publiee")
p("lit.ergun.A", "Équation d'Ergun : terme visqueux", 150, "-",
  "ergun1949", "éq. 6 (constantes de 1952)", "simulation_publiee",
  "Re_p de 1 à environ 2500")
p("lit.ergun.B", "Équation d'Ergun : terme inertiel", 1.75, "-",
  "ergun1949", "éq. 6 (constantes de 1952)", "simulation_publiee")
p("lit.jeffreson.facteur",
  "Correction de Jeffreson : h_eff = h / (1 + Bi / facteur)", 5, "-",
  "jeffreson1972", "éq. 9", "simulation_publiee",
  notes="Bi = h d / (2 k_s). Négligeable si Bi < 0,1.")
p("air.sutherland.mu_ref",
  "Viscosité de référence de l'air (loi de Sutherland)", 1.716e-5,
  "Pa.s", "sutherland1893", "constantes usuelles pour l'air", "mesure",
  "273,15 K", "Modèle gaz parfait seulement ; CoolProp sinon.")
p("air.sutherland.T_ref", "Température de référence de Sutherland",
  273.15, "K", "sutherland1893", "constantes usuelles", "mesure")
p("air.sutherland.S", "Constante de Sutherland pour l'air", 110.4, "K",
  "sutherland1893", "constantes usuelles", "mesure")
p("air.prandtl", "Nombre de Prandtl de l'air (modèle gaz parfait)", 0.71,
  "-", "lemmon2000", "propriétés de transport via CoolProp", "mesure",
  "0 à 300 °C, 1 bar", "Varie de 0,70 à 0,72.")
# Cuves de Tola (cas C) pour la vérification croisée
p("tola.tes_lp.diametre", "Cuve TES-LP (cas C) : diamètre", 5.2, "m", T_,
  "tableau 8", "simulation_publiee",
  notes="Même diamètre pour TES-IP et TES-HP. Vérification : π/4 × 5,2² "
        "× 10,4 = 220,8 m3.")
p("tola.tes_lp.rapport_hauteur_diametre",
  "Cuve TES-LP : rapport hauteur / diamètre", 2.0, "-", T_,
  "tableau 8 ; §3.3 (« an aspect ratio of 2 was set »)",
  "simulation_publiee", notes="Hauteur 10,4 m ; volume 220,8 m3 pour "
  "chacune des trois cuves du cas C.")
p("tola.tes_lp.volume", "Cuve TES-LP : volume", 220.8, "m3", T_,
  "tableau 8", "simulation_publiee")
p("tola.tes_lp.pression_charge", "Cuve TES-LP : pression en charge", 3.9,
  "bar", T_, "tableau 4", "simulation_publiee",
  notes="0,39 MPa ; décharge 0,40-0,53 MPa.")
p("tola.tes_ip.pression_charge", "Cuve TES-IP : pression en charge", 11.9,
  "bar", T_, "tableau 4", "simulation_publiee",
  notes="1,19 MPa ; décharge 1,74-2,24 MPa.")
p("tola.tes_hp.pression_charge", "Cuve TES-HP : pression en charge", 36.8,
  "bar", T_, "tableau 4", "simulation_publiee",
  notes="3,68 MPa ; décharge 6,40-10,0 MPa.")
p("tola.tes.debit_charge", "Cuves du cas C : débit d'air en charge", 12.3,
  "kg/s", T_, "tableau 8 ; §3.3", "simulation_publiee")
p("tola.tes.debit_decharge", "Cuves du cas C : débit d'air en décharge",
  24.5, "kg/s", T_, "tableau 8 ; §3.3", "simulation_publiee")
p("tola.tes.T_entree_charge",
  "Cuves du cas C : température d'entrée en charge", 170, "degC", T_,
  "tableau 4 et 8", "simulation_publiee")
p("tola.tes.T_entree_decharge",
  "Cuves du cas C : température d'entrée en décharge", 35, "degC", T_,
  "tableau 4 et 8", "simulation_publiee")
p("tola.tes.duree_charge", "Durée de la charge", 6, "h", T_, "§3.3",
  "simulation_publiee")
p("tola.tes.duree_decharge", "Durée de la décharge", 3, "h", T_, "§3.3",
  "simulation_publiee")
p("tola.tes.T_sortie_min_decharge",
  "Température minimale de sortie imposée en décharge (1er cycle)", 100,
  "degC", T_, "§3.3", "simulation_publiee")
p("tola.tes_lp.energie_stockee", "Cuve TES-LP : énergie stockée", 9.60,
  "MWh", T_, "tableau 8", "simulation_publiee")
p("tola.tes_ip.energie_stockee", "Cuve TES-IP : énergie stockée", 9.54,
  "MWh", T_, "tableau 8", "simulation_publiee")
p("tola.tes_hp.energie_stockee", "Cuve TES-HP : énergie stockée", 9.54,
  "MWh", T_, "tableau 8", "simulation_publiee")
p("tola.tes.nb_cycles_stabilisation",
  "Nombre de cycles simulés jusqu'au régime stable", 20, "-", T_, "§3.3",
  "simulation_publiee",
  notes="« full operational regime is reached » en moins de 20 cycles ; "
        "l'air converge plus vite que l'huile.")
p("tola.tes.fraction_sortie_constante",
  "Fraction de la charge ou de la décharge pendant laquelle la "
  "température de sortie reste constante", 0.67, "-", T_, "§3.3 ; fig. 4",
  "simulation_publiee", notes="« about two thirds ».")


# --- Ajouts de la phase 7 (bibliothèque de composants) ----------------
SH = "shi2024"
ZS = "zhangS2025"
BA = "baniamerian2025"
BZ = "bazdar2022"
WB = "wolfbudt2014"
AB = "ablaoui2023"
NOTE_SHI = ("Prépublication SSRN non révisée par les pairs : à signaler à "
            "chaque usage.")
# Tola 2022 : machines et échangeurs
p("tola.compresseur.rendement_polytropique",
  "Rendement polytropique des compresseurs (CLP, CIP, CHP, CVHP au "
  "point nominal)", 0.88, "-", T_, "tableau 1 ; §2.1", "simulation_publiee",
  "turbomachines commerciales (réf. [21] de Tola)")
p("tola.turbine.rendement_polytropique",
  "Rendement polytropique des trois turbines", 0.86, "-", T_, "tableau 6",
  "simulation_publiee")
p("tola.rendement_moteur_generateur",
  "Rendement du moteur et de la génératrice (mécanique → électrique)",
  0.97, "-", T_, "§4", "simulation_publiee")
p("tola.compresseur.T_sortie", "Température de sortie imposée des "
  "compresseurs CLP, CIP, CHP", 170, "degC", T_, "tableau 1",
  "simulation_publiee", "les rapports de pression en découlent")
p("tola.compresseur.T_entree", "Température d'entrée des compresseurs "
  "après refroidissement", 35, "degC", T_, "tableau 1 ; §2.1",
  "simulation_publiee")
p("tola.pincement_air", "Écart minimal de température des échangeurs "
  "air / air (cas A)", 20, "K", T_, "tableau 2 ; §2.1", "simulation_publiee",
  notes="Différence de température : pas de décalage de 273,15.")
p("tola.pincement_huile", "Écart minimal de température des échangeurs "
  "air / huile (cas B)", 10, "K", T_, "tableau 2 ; §2.1", "simulation_publiee",
  notes="Différence de température : pas de décalage de 273,15.")
p("tola.huile.cp", "Chaleur massique de l'huile thermique Therminol 66 "
  "(conditions ambiantes)", 1494, "J/kgK", T_, "tableau 2",
  "simulation_publiee", "à l'ambiant ; croît avec la température")
p("tola.turbine.T_sortie_min", "Température minimale de sortie de chaque "
  "turbine (vanne de laminage sinon)", 15, "degC", T_, "tableau 6",
  "simulation_publiee")
p("tola.cave.pression_min", "Pression minimale de la caverne", 64, "bar",
  T_, "§2.2", "simulation_publiee")
p("tola.cave.pression_max", "Pression maximale de la caverne", 100, "bar",
  T_, "§2.2", "simulation_publiee")
p("tola.rte.cas_A", "Rendement aller-retour, cas A (air)", 0.566, "-", T_,
  "tableau 10", "simulation_publiee")
p("tola.rte.cas_B", "Rendement aller-retour, cas B (huile)", 0.635, "-",
  T_, "tableau 10", "simulation_publiee")
p("tola.rte.cas_C", "Rendement aller-retour, cas C (gravier direct)",
  0.674, "-", T_, "tableau 10", "simulation_publiee",
  notes="La conclusion dit « légèrement inférieur à 0,65 » : incohérence.")
# Shi 2024 : centrale de 100 MW
p("shi.compresseur.rendement_isentropique",
  "Rendement isentropique des compresseurs", 0.86, "-", SH, "tableau 4",
  "simulation_publiee", notes=NOTE_SHI + " Réf. [27] de Shi.")
p("shi.turbine.rendement_isentropique",
  "Rendement isentropique des turbines", 0.90, "-", SH, "tableau 4",
  "simulation_publiee", notes=NOTE_SHI + " Réf. [27] de Shi.")
p("shi.rendement_mecanique", "Rendement mécanique des compresseurs et "
  "des turbines", 0.99, "-", SH, "tableau 4", "simulation_publiee",
  notes=NOTE_SHI)
p("shi.rendement_electrique", "Rendement électrique des moteurs et des "
  "génératrices", 0.98, "-", SH, "tableau 4", "simulation_publiee",
  notes=NOTE_SHI)
p("shi.pincement", "Écart minimal de température (PPTD) des "
  "réchauffeurs et des refroidisseurs", 10, "K", SH, "tableau 4",
  "simulation_publiee",
  notes=NOTE_SHI + " Différence de température : pas de décalage.")
p("shi.perte_charge_echangeur", "Perte de charge dans chaque échangeur",
  0.4, "bar", SH, "tableau 4", "simulation_publiee",
  notes=NOTE_SHI + " 0,04 MPa.")
p("shi.perte_charge_entree_reservoir", "Surpression requise à l'entrée du "
  "réservoir d'air", 2, "bar", SH, "tableau 4 ; §4", "simulation_publiee",
  notes=NOTE_SHI + " 0,2 MPa.")
p("shi.compresseur.T_sortie", "Température de sortie imposée des "
  "compresseurs 1 à 3", 200, "degC", SH, "tableau 4", "simulation_publiee",
  notes=NOTE_SHI)
p("shi.T_eau_froide", "Température de l'eau froide à l'entrée des "
  "refroidisseurs", 30, "degC", SH, "tableau 4", "simulation_publiee",
  notes=NOTE_SHI)
p("shi.T_amb", "Température ambiante", 25, "degC", SH, "tableau 4",
  "simulation_publiee", notes=NOTE_SHI)
p("shi.reservoir.pression_min", "Pression minimale du réservoir d'air "
  "(réservoir isochore adiabatique)", 40, "bar", SH, "tableau 4",
  "simulation_publiee", notes=NOTE_SHI)
p("shi.reservoir.pression_max", "Pression maximale du réservoir d'air",
  100, "bar", SH, "tableau 4", "simulation_publiee", notes=NOTE_SHI)
p("shi.puissance_decharge", "Puissance de décharge", 100000, "kW", SH,
  "tableau 4", "simulation_publiee", notes=NOTE_SHI)
p("shi.duree_decharge", "Durée de décharge", 6, "h", SH, "tableau 4",
  "simulation_publiee", notes=NOTE_SHI)
p("shi.duree_charge", "Durée de charge", 8, "h", SH, "tableau 4",
  "simulation_publiee", notes=NOTE_SHI)
p("shi.rte", "Rendement aller-retour au point de conception", 0.6764, "-",
  SH, "tableau 5 ; §5", "simulation_publiee",
  notes=NOTE_SHI + " 600 / 887,05 MWh.")
p("shi.eau.pression", "Pression des réservoirs d'eau chaude et froide",
  18, "bar", SH, "figure 7", "simulation_publiee",
  notes=NOTE_SHI + " 1,8 MPa ; eau chaude à 190 °C, eau froide à 30 °C.")
p("shi.eau.T_chaud", "Température de l'eau chaude stockée", 190, "degC",
  SH, "figure 7", "simulation_publiee", notes=NOTE_SHI)
p("eau.cp_source", "Chaleur massique et saturation de l'eau liquide : "
  "équation d'état IAPWS-95 via CoolProp", "IAPWS-95 (CoolProp, Water)",
  "texte", "wagner2002", "équation d'état", "mesure",
  notes="Utilisée par le modèle eau_sous_pression (formules.md#F40).")
p("shi.eau.volume_chaud", "Volume du réservoir d'eau chaude", 4783.5,
  "m3", SH, "tableau 5", "simulation_publiee", notes=NOTE_SHI)
# Zhang S. 2025 : Flügel, vanne
p("zhangS.flugel.t4", "Coefficient t4 de la formule de Flügel modifiée "
  "(chute de rendement hors du point nominal)", 0.3, "-", ZS, "éq. 3",
  "simulation_publiee",
  "turbines de grande taille ; à vérifier pour une petite turbine",
  "Valeur de la littérature reprise par Zhang (réf. [40], [41]).")
p("zhangS.turbine.rendement_isentropique",
  "Rendement isentropique de la turbine au point nominal", 0.88, "-", ZS,
  "§4.1.1", "simulation_publiee", "turbine de 10 MW",
  "Trop optimiste pour une petite turbine DEPRAG (53-73 % mécanique).")
p("zhangS.vanne.Cq", "Coefficient de débit des vannes ON/OFF et de "
  "réglage", 0.95, "-", ZS, "§4.1.1 (tableau des paramètres)",
  "simulation_publiee")
p("zhangS.turbine.T_entree", "Température d'entrée de la turbine au "
  "point nominal", 336.88, "K", ZS, "§4.1.1", "simulation_publiee")
p("zhangS.turbine.pression_entree", "Pression d'entrée de la turbine au "
  "point nominal", 70, "bar", ZS, "§4.1.1 ; §4.1.2", "simulation_publiee")
p("zhangS.reservoir.pression_max", "Pression maximale de la caverne", 100,
  "bar", ZS, "§4.1.1", "simulation_publiee")
# Wolf & Budt 2014 (via Bazdar 2022, tableau 3)
p("wolfbudt.rte", "Rendement aller-retour attendu d'un LTA-CAES (deux "
  "réservoirs de liquide, basse température)", None, "-", BZ,
  "tableau 3 (d'après Wolf & Budt 2014, réf. [110])", "simulation_publiee",
  notes="Plage 52-60 %. Source primaire : wolfbudt2014 (DOI vérifié, PDF "
        "non récupéré).", vmin=0.52, vmax=0.60)
p("wolfbudt.demarrage", "Temps de démarrage d'un LTA-CAES", 5, "min", BZ,
  "tableau 3 (d'après Wolf & Budt 2014)", "simulation_publiee",
  notes="« < 5 min » ; stockage chaud (gravier) : 10-15 min.")
# Laine minérale (Ablaoui 2023, tableau 1)
p("materiau.laine_minerale.conductivite", "Conductivité thermique de la "
  "laine minérale à 20 °C (densité > 26 kg/m3)", 0.036, "W/mK", AB,
  "tableau 1 (projet d'Eurocode, réf. [19] d'Ablaoui)", "fabricant",
  "20 °C, sec",
  "Valeur tabulée d'un projet de norme, pas une mesure des auteurs. Plage "
  "ambiante 0,030-0,046 W/m·K (réf. [13] d'Ablaoui).",
  vmin=0.030, vmax=0.046)
p("materiau.laine_minerale.conductivite_100C", "Conductivité thermique "
  "de la laine minérale à 100 °C", 0.047, "W/mK", AB, "tableau 1",
  "fabricant", "100 °C",
  "Interpolation linéaire admise entre 20 et 100 °C (note du tableau).")
p("materiau.laine_minerale.cp", "Chaleur massique de la laine minérale à "
  "20 °C", 880, "J/kgK", AB, "tableau 1", "fabricant", "20 °C")
p("materiau.laine_minerale.masse_volumique", "Masse volumique de la laine "
  "minérale testée par Ablaoui", 114, "kg/m3", AB, "§4 ; tableau 4",
  "mesure", "échantillons testés", "Le tableau 1 vaut pour > 26 kg/m3.")
p("isolation.h_ext", "Coefficient d'échange convectif extérieur d'une "
  "cuve isolée (air calme)", 2.5, "W/m2K", D, "§2.2.5 (h_conv,ext des "
  "réservoirs)", "calibration",
  "même valeur que les réservoirs d'air de Dormoy (air calme, extérieur "
  "du conteneur)",
  "Réutilisation de reservoir.h_conv_ext pour la face externe de l'isolant "
  "d'une cuve : hypothèse de même convection naturelle.")
# Zhang Z. 2021 : autodécharge
p("zhangZ.autodecharge_tes", "Autodécharge d'un stockage de chaleur "
  "(grandes installations)", None, "%", "zhangZ2021", "tableau 11",
  "simulation_publiee", "par jour", "Plage 0,05-1 % par jour ; valeur "
  "générique de revue, sans source par ligne.", vmin=0.05, vmax=1.0)


# --- Ajouts de la phase 8 (tableau de bord de validation) --------------
# Tola 2022 : tableaux 1, 6, 7, 9, 10 et § 3.2 (caverne)
p("tola.T_amb", "Température ambiante (entrée du compresseur basse "
  "pression)", 15, "degC", T_, "tableau 1", "simulation_publiee")
p("tola.p_amb", "Pression ambiante (entrée du compresseur basse pression)",
  1.01, "bar", T_, "tableau 1", "simulation_publiee", notes="0,101 MPa.")
p("tola.compresseur.debit_entree", "Débit massique d'air à l'entrée du "
  "compresseur basse pression", 12.35, "kg/s", T_, "tableau 7 ; tableau 10",
  "simulation_publiee", notes="Décroît légèrement le long de la chaîne "
  "(condensation) : 12,35 / 12,35 / 12,31 / 12,28 kg/s.")
p("tola.compresseur.CLP.rapport", "Rapport de pression du compresseur "
  "basse pression (CLP)", 3.8, "-", T_, "tableau 1", "simulation_publiee")
p("tola.compresseur.CIP.rapport", "Rapport de pression du compresseur "
  "moyenne pression (CIP)", 3.1, "-", T_, "tableau 1", "simulation_publiee")
p("tola.compresseur.CHP.rapport", "Rapport de pression du compresseur "
  "haute pression (CHP)", 3.1, "-", T_, "tableau 1", "simulation_publiee")
for nom, P_, E_ in (("CLP", 1980, 11.90), ("CIP", 1730, 10.38),
                    ("CHP", 1720, 10.31)):
    p(f"tola.compresseur.{nom}.puissance", f"Puissance électrique du "
      f"compresseur {nom} (constante pendant la charge)", P_, "kW", T_,
      "tableau 7", "simulation_publiee",
      notes="Électrique : 1,98 MW × 6 h = 11,9 MWh (tableau 7), rendement "
            "moteur 0,97 compris.")
    p(f"tola.compresseur.{nom}.energie", f"Énergie électrique du "
      f"compresseur {nom} sur la charge de 6 h", E_, "MWh", T_, "tableau 7",
      "simulation_publiee")
p("tola.compresseur.CVHP.puissance", "Puissance électrique du compresseur "
  "très haute pression (CVHP), de 6,4 à 10 MPa", None, "kW", T_,
  "tableau 7", "simulation_publiee", vmin=790, vmax=1550)
p("tola.compresseur.CVHP.energie", "Énergie électrique du compresseur CVHP "
  "sur la charge", 7.16, "MWh", T_, "tableau 7", "simulation_publiee")
p("tola.compresseur.energie_totale", "Énergie électrique totale de la "
  "chaîne de compression (6 h)", 39.76, "MWh", T_, "tableau 7 ; tableau 10",
  "simulation_publiee", notes="39,8 MWh au tableau 10.")
p("tola.turbine.debit", "Débit massique d'air des turbines", 24.5, "kg/s",
  T_, "tableau 10", "simulation_publiee")
for cas, T_in, E_, P_ in (("A", 130, 23.92, 8300), ("B", 150, 26.82, 9500),
                          ("C", 170, 28.48, 10000)):
    p(f"tola.turbine.T_entree_cas_{cas}", f"Température d'entrée nominale "
      f"des turbines, cas {cas}", T_in, "degC", T_, "tableau 6",
      "simulation_publiee")
    p(f"tola.turbine.energie_cas_{cas}", f"Énergie électrique produite par "
      f"les trois turbines sur 3 h, cas {cas}", E_, "MWh", T_,
      "tableau 9 ; tableau 10", "simulation_publiee")
    p(f"tola.turbine.puissance_max_cas_{cas}", f"Puissance électrique "
      f"maximale des trois turbines (début de décharge), cas {cas}", P_,
      "kW", T_, "tableau 9 ; tableau 10", "simulation_publiee")
for nom, E_ in (("THP", 9.41), ("TIP", 9.53), ("TLP", 9.54)):
    p(f"tola.turbine.{nom}.energie_cas_C", f"Énergie produite par la "
      f"turbine {nom}, cas C", E_, "MWh", T_, "tableau 9",
      "simulation_publiee")
p("tola.cave.volume", "Volume de la caverne", 6500, "m3", T_, "§3.2",
  "simulation_publiee", notes="Calculé par Tola avec l'hypothèse du gaz "
  "parfait pour 264,6 t d'air de décharge.")
p("tola.cave.masse_min", "Masse d'air dans la caverne à la pression "
  "minimale", 470, "t", T_, "§3.2", "simulation_publiee")
p("tola.cave.masse_max", "Masse d'air dans la caverne en fin de charge",
  735, "t", T_, "§3.2", "simulation_publiee")
p("tola.cave.T_min", "Température minimale de l'air dans la caverne", 15,
  "degC", T_, "§2.2", "simulation_publiee",
  notes="Plage 15-55 °C imposée « to avoid structural issues ».")
p("tola.cave.T_max", "Température maximale de l'air dans la caverne", 55,
  "degC", T_, "§2.2", "simulation_publiee")
p("tola.rte.energie_decharge_cas_C", "Énergie produite, cas C (tableau 10)",
  28.5, "MWh", T_, "tableau 10", "simulation_publiee")
# Shi 2024 : figure 7 (états à 7 MPa), § 5, tableau 5
p("shi.p_amb", "Pression ambiante", 1, "bar", SH, "figure 7",
  "simulation_publiee", notes=NOTE_SHI + " 0,1 MPa.")
p("shi.debit_charge", "Débit massique d'air pendant la charge", 198.35,
  "kg/s", SH, "figure 7 ; §5", "simulation_publiee", notes=NOTE_SHI)
p("shi.debit_decharge", "Débit massique d'air pendant la décharge", 260.15,
  "kg/s", SH, "figure 7 ; §5", "simulation_publiee", notes=NOTE_SHI)
for i, P_ in ((1, 36230), (2, 33140), (3, 33150), (4, 10270)):
    p(f"shi.compresseur.puissance_{i}", f"Puissance électrique du "
      f"compresseur {i} quand le réservoir est à 7 MPa", P_, "kW", SH,
      "§5 ; figure 7", "simulation_publiee", "réservoir à 7 MPa",
      NOTE_SHI)
for i, P_ in ((1, 20440), (2, 39800), (3, 39770)):
    p(f"shi.turbine.puissance_{i}", f"Puissance électrique de la turbine "
      f"{i} quand le réservoir est à 7 MPa", P_, "kW", SH, "§5 ; figure 7",
      "simulation_publiee", "réservoir à 7 MPa", NOTE_SHI)
for i, pp in ((1, 4.3), (2, 14.0), (3, 48.6)):
    p(f"shi.compresseur.p_sortie_{i}", f"Pression de sortie du compresseur "
      f"{i}", pp, "bar", SH, "figure 7", "simulation_publiee",
      "réservoir à 7 MPa", NOTE_SHI)
p("shi.compresseur.p_sortie_4", "Pression de sortie du compresseur 4 "
  "(réservoir à 7 MPa)", 75.5, "bar", SH, "figure 7", "simulation_publiee",
  "réservoir à 7 MPa", NOTE_SHI)
p("shi.compresseur.T_sortie_4", "Température de sortie du compresseur 4 "
  "(réservoir à 7 MPa)", 90, "degC", SH, "figure 7", "simulation_publiee",
  "réservoir à 7 MPa", NOTE_SHI)
p("shi.refroidisseur.T_sortie_air", "Température de l'air à la sortie des "
  "refroidisseurs", 40, "degC", SH, "figure 7", "simulation_publiee",
  notes=NOTE_SHI)
p("shi.turbine.T_entree", "Température d'entrée des turbines (eau à "
  "190 °C, pincement 10 K)", 180, "degC", SH, "figure 7",
  "simulation_publiee", notes=NOTE_SHI)
p("shi.turbine.p_sortie_1", "Pression de sortie de la turbine 1", 32.6,
  "bar", SH, "figure 7", "simulation_publiee", "réservoir à 7 MPa", NOTE_SHI)
p("shi.turbine.p_entree_2", "Pression d'entrée de la turbine 2 (après le "
  "réchauffeur, 0,04 MPa de perte)", 32.2, "bar", SH, "figure 7",
  "simulation_publiee", notes=NOTE_SHI)
p("shi.turbine.p_sortie_2", "Pression de sortie de la turbine 2", 5.9,
  "bar", SH, "figure 7", "simulation_publiee", notes=NOTE_SHI)
p("shi.turbine.p_entree_3", "Pression d'entrée de la turbine 3", 5.5, "bar",
  SH, "figure 7", "simulation_publiee", notes=NOTE_SHI)
p("shi.turbine.p_sortie_3", "Pression de sortie de la turbine 3", 1, "bar",
  SH, "figure 7", "simulation_publiee", notes=NOTE_SHI)
for i, T_ in ((1, 100), (2, 24), (3, 24)):
    p(f"shi.turbine.T_sortie_{i}", f"Température de sortie de la turbine "
      f"{i} (réservoir à 7 MPa)", T_, "degC", SH, "figure 7",
      "simulation_publiee", "réservoir à 7 MPa", NOTE_SHI)
p("shi.reservoir.volume", "Volume du réservoir d'air", 118000, "m3", SH,
  "tableau 5 ; §5", "simulation_publiee", notes=NOTE_SHI + " 1,18 × 10^5 m3.")
p("shi.masse_air", "Masse d'air stockée par cycle", 5712.5, "t", SH,
  "tableau 5", "simulation_publiee", notes=NOTE_SHI + " 198,35 kg/s × 8 h.")
p("shi.masse_eau", "Masse d'eau stockée par cycle", 4193.7, "t", SH,
  "tableau 5", "simulation_publiee", notes=NOTE_SHI)
p("shi.eau.volume_froid", "Volume du réservoir d'eau froide", 4208.8, "m3",
  SH, "tableau 5", "simulation_publiee", notes=NOTE_SHI)
p("shi.compresseur4.duree_fonctionnement", "Durée de fonctionnement du "
  "compresseur 4 pendant la charge de 8 h", 7.04, "h", SH, "tableau 5 ; §5",
  "simulation_publiee", notes=NOTE_SHI + " Inactif tant que la sortie du "
  "compresseur 3 dépasse la pression du réservoir.")
p("shi.energie_charge", "Énergie électrique consommée par cycle", 887.05,
  "MWh", SH, "tableau 5 ; §5", "simulation_publiee", notes=NOTE_SHI)
p("shi.energie_decharge", "Énergie électrique produite par cycle", 600,
  "MWh", SH, "tableau 5", "simulation_publiee", notes=NOTE_SHI)
p("shi.reservoir.T_min", "Température de l'air dans le réservoir en début "
  "de charge", 2.78, "degC", SH, "§4 (texte) ; figure 7", "simulation_publiee",
  notes=NOTE_SHI + " Plage 3-70 °C sur la figure 7.")
p("shi.reservoir.T_max", "Température de l'air dans le réservoir en fin "
  "de charge", 70, "degC", SH, "figure 7", "simulation_publiee",
  notes=NOTE_SHI)


# --- Ajouts de la phase 9 (humidité et sécheur) --------------------------
HE = "herrmann2009"
p("humidite.formulation", "Propriétés de l'air humide : formulation ASHRAE "
  "RP-1485 via CoolProp (HAPropsSI)", "RP-1485 (CoolProp HumidAir)",
  "texte", HE, "article entier", "mesure",
  notes="Inclut le facteur d'augmentation f(T, p) de la solubilité de "
        "l'eau dans l'air comprimé (formules.md#F42).")
p("humidite.pression_max_validite", "Pression maximale de validité de la "
  "formulation d'air humide", 100, "bar", HE, "résumé ; §2",
  "simulation_publiee", "10 Pa à 10 MPa, −143 à 350 °C",
  "Au-delà (réservoir de Dormoy à 190 bar), le simulateur extrapole à "
  "pression partielle de vapeur constante et le signale.")
p("eau.enthalpie_fusion", "Enthalpie de fusion de la glace Ih au point "
  "triple", 333.4, "kJ/kg", "feistel2006", "tableau des propriétés au "
  "point triple", "mesure", "273,16 K, 611,657 Pa",
  "Sert à la chaleur libérée par le givre (formules.md#F43).")
p("secheur.point_de_rosee_sortie", "Point de rosée sous pression à la "
  "sortie d'un sécheur par adsorption", -40, "degC", D, "§2.1 (sécheur "
  "par adsorption, non spécifié)", "hypothese",
  "valeur usuelle des sécheurs par adsorption sans chaleur (classe ISO "
  "8573-1 : 2)",
  "Dormoy ne donne pas le point de rosée de son sécheur : hypothèse du "
  "projet, à remplacer par la fiche technique.")
p("separateur.efficacite", "Fraction de l'eau liquide entraînée retenue "
  "par un séparateur cyclonique ou à coalescence", 0.98, "-", D,
  "§2.1 (non décrit)", "hypothese", "gouttelettes après un refroidisseur",
  "Hypothèse du projet (ordre de grandeur des séparateurs industriels) ; "
  "aucune donnée dans les études lues.")
p("secheur.appoint.efficacite", "Fraction du débit conservée par un petit "
  "sécheur d'appoint (purge réduite)", 0.95, "-", D, "§2.1 (non décrit)",
  "hypothese", "après un séparateur, air déjà proche de la saturation à "
  "basse teneur", "Hypothèse du projet : purge de 5 % au lieu de 19 % "
  "pour un sécheur dimensionné sur une charge en eau bien plus faible.")

# --- Phase 10 : masse des réservoirs (paroi mince, formules.md#F44) ------
p("reservoir.alu.limite_elastique",
  "Limite d'élasticité de l'aluminium 6061-T6 (valeur typique)", 276,
  "MPa", "asm1990", "propriétés typiques de l'alliage 6061-T6", "fabricant",
  "20 °C", "Valeur typique (40 ksi) ; résistance à la traction 310 MPa. "
  "Sert de borne « tout aluminium » dans le calcul de masse F44.")
p("reservoir.pression_service", "Pression de service des réservoirs "
  "composites de Dormoy", 300, "bar", D, "§3.3.2 (cas à 300 bar)",
  "hypothese", "", "L'article simule une charge à 300 bar avec les mêmes "
  "réservoirs ; leur pression nominale n'est pas publiée.")
p("reservoir.coefficient_securite", "Coefficient de sécurité (rapport "
  "pression d'éclatement / pression de service) retenu pour un réservoir "
  "composite", 2.25, "-", D, "non publié", "hypothese", "",
  "Hypothèse du projet : rapport d'éclatement courant des bouteilles "
  "composites à liner métallique (ordre de grandeur de l'industrie, "
  "aucune source à DOI lue) ; à remplacer par la norme applicable.")
_r = 0.372 / 2
_v_fond = 4.0 / 3.0 * math.pi * _r**3
_rs = []
for _v, _m in ((0.32, 107.0), (0.27, 95.0)):
    _rs.append(2.25 * 300e5 * (2 * (_v - _v_fond) + 1.5 * _v_fond) / _m)
p("reservoir.resistance_specifique_equivalente",
  "Résistance spécifique équivalente (σ_adm / ρ) de la paroi composite "
  "des réservoirs de Dormoy, déduite de leur masse", round(sum(_rs) / 2
  / 1e3, 0), "kJ/kg", S, "tableau 8 (masse, diamètre, volume)",
  "calibration", "paroi mince, pression de service 300 bar, coefficient "
  "2,25", "Calcul personnel F44 : (σ/ρ) = S · p · (2 V_cyl + 1,5 V_fonds)"
  " / m, pour les bouteilles de 320 L (107 kg) et 270 L (95 kg) ; "
  "l'aluminium 6061-T6 seul donne 102 kJ/kg (276 MPa / 2700 kg/m3).",
  vmin=round(min(_rs) / 1e3, 0), vmax=round(max(_rs) / 1e3, 0))

# --- Phase 11 : scénarios d'exemple -------------------------------------
p("reservoir.fuite_par_jour", "Fraction de la masse d'air perdue par jour "
  "par fuites lentes pendant une attente", 0.5, "%", D,
  "non publié (l'essai de 10 h ne montre pas de fuite)", "hypothese", "",
  "Ordre de grandeur choisi par le projet pour les scénarios de "
  "transport ; 0 par défaut dans les composants. À remplacer par une "
  "mesure d'étanchéité.")
TE = "tesla2020"
p("megapack.energie", "Énergie disponible d'un Megapack « 4-Hour Standard »",
  3080.4, "kWh", TE, "page 2, Standard System Specifications",
  "fabricant", "25 °C, jour 1, pertes thermiques incluses")
p("megapack.puissance", "Puissance d'un Megapack « 4-Hour Standard »",
  770.1, "kW", TE, "page 2", "fabricant")
p("megapack.rendement_aller_retour", "Rendement aller-retour d'un Megapack "
  "4 h", 90, "%", TE, "page 2", "fabricant", "25 °C, jour 1")
p("megapack.masse", "Masse maximale à l'expédition d'un Megapack standard",
  25400, "kg", TE, "page 2, Mechanical and Mounting", "fabricant")
p("megapack.longueur", "Longueur de l'enveloppe d'un Megapack", 7.168, "m",
  TE, "page 2", "fabricant")
p("megapack.largeur", "Profondeur de l'enveloppe d'un Megapack", 1.659, "m",
  TE, "page 2", "fabricant")
p("megapack.hauteur", "Hauteur de l'enveloppe d'un Megapack", 2.522, "m",
  TE, "page 2", "fabricant")
p("megapack.T_min", "Température ambiante minimale de fonctionnement d'un "
  "Megapack", -30, "degC", TE, "page 2", "fabricant")
CA = "caterpillar2020"
p("groupe_diesel.puissance", "Puissance électrique de secours (standby) de "
  "la génératrice Cat D100 GC, 60 Hz", 100, "kW", CA, "page 1", "fabricant")
p("groupe_diesel.conso_100", "Consommation de carburant à 100 % de charge "
  "(triphasé, avec ventilateur)", 27.9, "L/h", CA, "page 1, Fuel "
  "Consumption", "fabricant")
p("groupe_diesel.conso_75", "Consommation à 75 % de charge", 22.5, "L/h",
  CA, "page 1", "fabricant")
p("groupe_diesel.conso_50", "Consommation à 50 % de charge", 16.7, "L/h",
  CA, "page 1", "fabricant")
p("groupe_diesel.masse", "Masse à sec de la génératrice D100 GC", 1008,
  "kg", CA, "page 2, Weights & Dimensions", "fabricant")
p("groupe_diesel.pci", "Pouvoir calorifique inférieur du diesel n° 2 "
  "(18 390 BTU/lb)", 42.78, "MJ/kg", CA, "page 2, note 2",
  "calcul_personnel", "", "18 390 BTU/lb × 2,326 kJ/kg par BTU/lb.")
p("groupe_diesel.masse_volumique", "Masse volumique du diesel n° 2 à "
  "35° API", 850, "kg/m3", CA, "page 2, note 2", "calcul_personnel", "",
  "Densité = 141,5 / (131,5 + 35) = 0,850.")
NR = "nrel2023"
for _nom, _v in (("bas", 245), ("moyen", 326), ("haut", 403)):
    p(f"batterie.cout_2030_{_nom}", f"Coût projeté ({_nom}) d'une batterie "
      "lithium-ion de 4 h en 2030, dollars américains de 2022", _v, "$/kWh",
      NR, "résumé (notice OSTI)", "simulation_publiee", "",
      "Coût du système installé par kWh de capacité.")
p("caes.cout_reservoir_hors_sol", "Coût du stockage d'air hors sol "
  "(réservoirs) par kWh", None, "$/kWh", D, "tableau 1 (d'après Bazdar "
  "et al. 2022)", "simulation_publiee", "", "Fourchette citée par Dormoy "
  "pour un CAES à réservoirs hors sol.", vmin=200, vmax=250)
p("centre_urgence.puissance_moyenne", "Puissance moyenne d'un centre "
  "d'urgence", 100, "kW", D, "plan v2 du projet (scénario 3)", "hypothese",
  "", "Choix du projet ; 7,2 MWh sur 72 h.")
p("centre_urgence.duree", "Autonomie visée d'un centre d'urgence", 72, "h",
  D, "plan v2 du projet (scénario 3)", "hypothese")
p("centre_urgence.facteur_jour", "Multiplicateur de la demande de jour "
  "(6 h à 22 h)", 1.2, "-", D, "non publié", "hypothese", "",
  "Profil jour/nuit de moyenne 1 : (16 × 1,2 + 8 × 0,6) / 24 = 1. À "
  "remplacer par un profil mesuré (données ouvertes d'un bâtiment).")
p("centre_urgence.facteur_nuit", "Multiplicateur de la demande de nuit "
  "(22 h à 6 h)", 0.6, "-", D, "non publié", "hypothese")
p("meteo.amplitude_journaliere", "Demi-amplitude de la variation "
  "journalière de la température extérieure dans les profils d'exemple",
  5, "K", D, "non publié", "hypothese", "",
  "Sinusoïde de 24 h autour de la moyenne (−20 °C en hiver, 30 °C en "
  "été) ; à remplacer par des normales climatiques.")


def main() -> None:
    out = pathlib.Path(__file__).resolve().parent
    with open(out / "references.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "auteurs", "annee", "titre", "revue", "doi_ou_url",
                    "type", "acces", "fichier_local", "notes"])
        w.writerows(references)
    with open(out / "parametres.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "nom", "valeur", "valeur_min", "valeur_max",
                    "unite", "source_id", "localisation", "conditions",
                    "niveau_preuve", "notes"])
        w.writerows(P)
    ids = [x[0] for x in P]
    doublons = {i for i in ids if ids.count(i) > 1}
    print(f"{len(references)} références ; {len(P)} paramètres ; "
          f"doublons : {doublons or 'aucun'}")


if __name__ == "__main__":
    main()
