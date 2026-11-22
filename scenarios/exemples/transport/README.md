# Scénario 2 : transport et conservation de la chaleur

**La question.** On charge l'installation D (air à 190 bar, cuves de gravier chaudes) à un endroit, on la transporte pendant 7 à 56 jours, et on la décharge à l'arrivée. Combien de chaleur reste-t-il dans les cuves, combien d'électricité, et à partir de quand le gravier ne sert plus ? Que changent l'épaisseur d'isolant, l'hiver québécois, la taille des cuves, les fuites d'air ? Et si la chaleur ne suffit plus, que coûte une chaudière d'appoint ?

**Les fichiers** (générés par `../generer_exemples.py`, ne pas éditer à la main) :

| Fichier | Contenu |
|---|---|
| `transport.yaml` | D avec 20 cm de laine minérale (Ablaoui 2023) autour de chaque cuve, attente de 14 jours à 20 °C, un cycle ; `fuite_par_jour` à 0 |
| `transport_appoint.yaml` | le même avec une source externe après chaque cuve (solution de repli, chaleur comptée « externe ») |
| `meteo_hiver.csv`, `meteo_ete.csv` | température extérieure sur 60 jours : sinusoïde journalière de ± 5 K (hypothèse `meteo.amplitude_journaliere`) autour de −20 °C et de 30 °C ; à remplacer par des normales climatiques |

L'ambiance est explicite : 20 °C constant, ou le profil (`--modifier ambiance.profil=meteo_hiver.csv`), avec l'air aspiré 32 K au-dessus de l'extérieur (conteneur du compresseur, phase 1). Les balayages du rapport se font par `--modifier` (durée d'attente, épaisseur, volume des cuves, `fuite_par_jour`), jamais par des copies du fichier.

**Régénérer.**

```
python rapports/scenarios_transport.py --procs 8   # → rapports/scenarios/transport.md, deux figures (≈ 3 min)
python -m caes simuler scenarios/exemples/transport/transport.yaml --modifier composants.attente.duree=28j --modifier ambiance.profil=meteo_hiver.csv
```

**Comment lire la réponse.** « Chaleur après charge » est ce que les cuves contiennent au-dessus de l'ambiant au départ ; « restante » après l'attente ; une cuve isolée perd sa chaleur comme e^(−t/τ), et le rapport calcule τ à la main (≈ 23 jours pour 2 m³ sous 20 cm). L'électricité livrée baisse quand les cuves ne tiennent plus leurs cibles ; l'air rejeté descend alors sous 0 °C (givre, phase 9) : regarder la colonne « air rejeté min ». Les fuites d'air sont une hypothèse (`reservoir.fuite_par_jour`, 0,5 %/j au registre, 0 dans le fichier). Le rendement avec chaudière d'appoint est donné avec et sans la chaleur externe.
