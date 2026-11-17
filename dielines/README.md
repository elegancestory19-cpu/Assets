# L'Adresse — tracés de découpe (die-lines)

Six fichiers de découpe vectoriels à l'échelle 1:1 (unités : mm), noir #000000 sur fond blanc.

| # | Boîte | Dimensions (mm) | Format à plat (mm) |
|---|-------|-----------------|--------------------|
| 01 | Boîte longue cookies à fenêtre | 240 × 90 × 55 | 305 × 386 |
| 02 | Boîte carrée (postale auto-montante) | 240 × 240 × 140 | 806 × 818 |
| 03 | Boîte gable pâtisserie avec poignée | 220 × 160 × 150 (+ toit/poignée) | 775 × 465 |
| 04 | Boîte 3 verrines à fenêtre + cale 3 alvéoles | 270 × 110 × 85 | 405 × 484 (+ cale) |
| 05 | Boîte carrée basse pâtisserie | 180 × 180 × 75 | 486 × 542 |
| 06 | Porte-gobelets 2 cafés avec poignée + cale | 195 × 95 × 210 (+ toit/poignée) | 595 × 425 (+ cale) |

## Fichiers
- `NN_nom.svg` / `.pdf` : version complète avec 4 calques
  - **DECOUPE** : trait plein 0,25 mm, contours fermés et continus (courbes de Bézier cubiques)
  - **RAINAGE** : pointillés 0,25 mm (plis), fusionnés, sans doublons
  - **MARQUAGE** : logo + textes vectorisés (contours), repère visuel — **ne pas découper**
  - **INFOS** : cartouche, légende, barre d'échelle 100 mm — **ne pas découper**
- `NN_nom_production.svg` / `.pdf` : uniquement DECOUPE + RAINAGE, prêt pour la machine.
- `previews/` : aperçus PNG.
- `src/generate_dielines.py` : générateur paramétrique (modifier les cotes puis relancer).

Contrôle d'échelle : la barre « 100 mm » des fichiers complets doit mesurer exactement 100 mm à l'import.
