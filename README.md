# Codi-de-procesat-de-fitxers-de-temperatura
Aquest projecte conté un script Python per generar mapes de temperatura en format PNG i HTML interactiu a partir de fitxers CSV.

## Arxius
- `genera_mapes_temperatura.py`: script principal.
- `Entrada fitxers/`: carpeta on han d’estar els fitxers CSV d’entrada.
- `Mapes termics/`: carpeta de sortida per als resultats generats.

# genera_mapes_temperatura.py

Script per generar mapes de temperatura (PNG) i opcionalment HTML interactiu a partir de fitxers CSV.

## Estructura
- `genera_mapes_temperatura.py`: script principal.
- `Entrada fitxers/`: carpeta d’entrada amb els CSV.
- `Mapes termics/`: carpeta de sortida per als resultats.

## Què fa
- Llegeix fitxers CSV amb valors numèrics (separats per `;`) i valida la consistència de columnes.
- Genera PNG per cada mapa i opcionalment un HTML interactiu per explorar el mapa.
- Calcula la sèrie de valors màxims per fitxer i genera gràfiques i CSV resum.
- La gràfica de màxims utilitza un eix temporal relatiu en minuts; la posició dels punts és contínua (decimals), però les etiquetes es mostren en minuts enters.

## Dependències
- Python 3.8+ (recomanat 3.11)
- `matplotlib` (per generar PNG i gràfiques)

Instal·la dependències:

```bash
pip install matplotlib
```

## Ús
Executa l’script des del directori del projecte:

```bash
python genera_mapes_temperatura.py [opcions]
```

Opcions rellevants:
- `--entrada`: carpeta d’entrada amb CSV (per defecte `Entrada fitxers`).
- `--sortida`: carpeta de sortida (per defecte `Mapes termics`).
- `--cmap`: mapa de colors per als PNG (p. ex. `inferno`).
- `--interval-segons`: interval en segons entre imatges quan no es pot extreure el temps del nom del fitxer.
- `--retall`: retall en píxels `x1,y1,x2,y2` aplicat abans de cercar el màxim.
- `--retall-percent`: retall en percentatge `x1,y1,x2,y2`.
- `--suavitzat-punts`: punts per suavitzar la sèrie de màxims (imparell, per defecte 21).
- `--llindar-pic`: llindar en °C per considerar pics com a soroll (per defecte 1.0).
- `--escala-global`: usa la mateixa escala de colors per a tots els fitxers processats.
- `--no-html`: NO generar els fitxers HTML interactius (només PNG i CSV).

Exemples:

```bash
# Processar i generar tot (HTML + PNG)
python genera_mapes_temperatura.py

# Només PNG i CSV (sense HTML interactiu)
python genera_mapes_temperatura.py --no-html

# Quan no es pot obtenir temps del nom i vols fixar 10 s entre imatges
python genera_mapes_temperatura.py --interval-segons 10
```

## Sortida generada
- `Mapes termics/Imatges PNG/`: PNG dels mapes.
- `Mapes termics/HTML navegador/`: HTML interactiu per imatges i gràfiques (si no està deshabilitat).
- `Mapes termics/Dades CSV/`: CSV amb màxims i resum.

## Notes importants
- El script calcula un temps relatiu (en minuts) basat en la data/hora extreta del nom del fitxer si està disponible, o bé fa servir `--interval-segons` com a alternativa.
- La gràfica de màxims utilitza coordenades X contínues (minuts amb decimals) per traçar la línia suau; les etiquetes i el resum mostren minuts sencers.
- Els CSV han de tenir totes les files amb la mateixa longitud i valors numèrics vàlids. Si troba línies amb errors les ignora i continua.

## Contacte
Si trobes algun problema, envia un exemple del CSV i la sortida del script perquè pugui reproduir-ho.
