# Generador de Mapes Tèrmics i Gràfiques (Python_temperatura.py)

Aquest script processa imatges tèrmiques exportades en format `.csv` per generar gràfiques d'evolució de temperatura (suavitzades i processades), i recrear els mapes tèrmics en format `PNG` i visualitzadors `HTML` interactius.

## Requisits del sistema

Perquè l'script funcioni correctament necessites instal·lar els següents paquets de Python:
```bash
pip install matplotlib Pillow numpy
Funcionament general
L'script busca tots els arxius .csv ubicats a la carpeta d'entrada Entrada fitxers. Per cada execució:

Analitzarà la matriu de temperatures de cada imatge.

Cercarà el pic de temperatura dins de la imatge descartant soroll gràcies al sistema de retall per zones.

Crearà una gràfica amb l'evolució temporal de les temperatures.

Generarà exportacions individuals visuals.

Tot el contingut processat es desarà automàticament en una subcarpeta nova anomenada Mapes termics / Resultats N per no sobreescriure dades anteriors.

Sistema de Coordenades (Molt Important)
En processament d'imatge i matrius, l'origen de coordenades no és el clàssic cartesià, sinó que s'ubica a DALT A L'ESQUERRA (0, 0):

Eix X (Horitzontal): 0% és el límit ESQUERRE i 100% és el límit DRET.

Eix Y (Vertical): 0% és el límit SUPERIOR i 100% és el límit INFERIOR.

Regles Automàtiques de Retall
L'script està programat per ignorar automàticament certes parts de la imatge per evitar llegir zones calentes no desitjades (ex. focus superiors). Això es fa directament des de la funció main().

Peces MECO:
Com que presenten focus de calor a la zona dreta i superior, l'script buscarà el punt màxim de temperatura només dins del següent marge operatiu:

X = [0, 55] (Descarta el 45% dret de la imatge).

Y = [20, 100] (Descarta el 20% de dalt de la imatge).

Altres peces:
S'analitzen al 100%, és a dir: X = [0, 100] i Y = [0, 100].

Arguments de Consola (Opcional)
Si executes l'script des del Terminal/CMD, pots personalitzar-ne el comportament:

--entrada [ruta]: Especifica una carpeta d'entrada diferent per als CSV.

--sortida [ruta]: Especifica una carpeta de destí diferent.

--html: Genera els mapes interactius individuals de cada fotografia.

--nomes-grafica: Ignora la generació dels PNG individuals (molt útil per estalviar temps si només vols veure la gràfica d'evolució d'un gran volum de fitxers).

--reutilitzar: Evita crear carpetes Resultats N i sobreescriu la darrera carpeta generada.

--interval-segons [valor]: Força un interval manual de segons per ordenar temporalment les fotografies si els fitxers no tenen timestamp al nom.

Exemple d'ús:

Bash
python Python_temperatura.py --html --nomes-grafica --reutilitzar
