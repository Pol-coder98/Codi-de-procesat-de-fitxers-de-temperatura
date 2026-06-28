# Codi-de-procesat-de-fitxers-de-temperatura
Aquest projecte conté un script Python per generar mapes de temperatura en format PNG i HTML interactiu a partir de fitxers CSV.
## Arxius
- `genera_mapes_temperatura.py`: script principal.
- `Entrada fitxers/`: carpeta on han d’estar els fitxers CSV d’entrada.
- `Mapes termics/`: carpeta de sortida per als resultats generats.

## Funcionalitats
- Llegeix CSV amb valors de temperatura separats per `;`.
- Genera imatges PNG de cada mapa de temperatura.
- Crea HTML interactiu per explorar el mapa dels valors.
- Calcula la sèrie de màxims de temperatura per fitxer.
- Genera gràfiques de màxims amb l’eix temporal en minuts relatius.
- Exporta dades CSV amb les mètriques calculades.

## Dependències
- Python 3.8 o superior.
- `matplotlib` per generar les imatges PNG i gràfiques.

Instal·la les dependències amb pip si cal:

```bash
pip install matplotlib
```

## Ús
Executa l’script des del directori del projecte:

```bash
python genera_mapes_temperatura.py
```

Paràmetres importants:
- `--entrada`: carpeta d’entrada amb CSV (per defecte `Entrada fitxers`).
- `--sortida`: carpeta de sortida (per defecte `Mapes termics`).
- `--cmap`: mapa de colors per als PNG.
- `--interval-segons`: interval de temps quan no es pot inferir del nom del fitxer.
- `--retall`: retall en pixels amb format `x1,y1,x2,y2`.
- `--retall-percent`: retall percentual amb format `x1,y1,x2,y2`.
- `--suavitzat-punts`: punts de suavitzat per a la gràfica de màxims.
- `--llindar-pic`: llindar per eliminar pics sorollosos.
- `--escala-global`: aplica la mateixa escala de colors a tots els fitxers.

## Resultats
L’script crea a la carpeta de sortida:
- PNG dels mapes de temperatura.
- HTML interactiu per a cada mapa.
- CSV amb els màxims de temperatura.
- HTML i PNG de la gràfica de màxims.
- Resum de dades en CSV.

## Notes
Els fitxers CSV han de tenir totes les files amb la mateixa longitud i valors numèrics vàlids.
