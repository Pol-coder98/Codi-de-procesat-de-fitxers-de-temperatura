# Processament de Mapes Tèrmics i Sèries Temporals (`Python_temperatura.py`)

Aquest script en Python està dissenyat per automatitzar l'anàlisi de matrius de temperatura guardades en format CSV (delimitat per punt i coma). Genera mapes gràfics (PNG), visualitzacions interactives per al navegador (HTML) i extreu la tendència de la temperatura màxima al llarg del temps en format de gràfica i taula de dades.

---

## 🚀 Característiques Principals

*   **Generació Automàtica de Mapes:** Transforma matrius numèriques en imatges PNG utilitzant l'escala de colors *Inferno* (o qualsevol altra de *matplotlib*).
*   **Visor HTML Interactiu:** Crea fitxers HTML autònoms on, al passar el cursor per sobre de cada píxel, es mostra la coordenada exacta i la seva temperatura.
*   **Anàlisi Temporal de Màxims:** Sincronitza els fitxers cronològicament (detectant la data/hora al nom o per intervals) i genera una gràfica evolutiva dels punts més calents.
*   **Suavitzat de Dades i Filtre de Soroll:** Aplica un filtre de mitjana mòbil i eliminació de pics anòmals per netejar les gràfiques temporals.
*   **Sistema de Cache Integrat:** Detecta si un fitxer ja s'ha processat prèviament mitjançant un hash SHA-256 per estalviar temps en futures rutes.

---

## 🎯 Regla de Retall de Cerca Automàtica (Nou)

L'script incorpora una lògica intel·ligent durant la **Fase 1** d'anàlisi per restringir la zona on es busca la temperatura màxima segons el nom del fitxer:

*   📂 **Fitxers que contenen `MECO` al nom:** La cerca de la temperatura màxima queda limitada exclusivament a la zona superior esquerra del component:
    *   **Eix X:** De l'origen al **43%** de l'amplada total `[0, 43]`.
    *   **Eix Y:** De l'origen al **80%** de l'alçada total `[0, 80]`.
*   🌐 **Resta de fitxers:** S'analitza de manera estàndard el **100%** de l'àrea disponible.

> ⚠️ *Nota: Aquesta regla s'aplica automàticament sobre la matriu de treball (estigui o no retallada prèviament pels arguments globals) i serveix per evitar falsos positius d'elements externs en els informes de màxims.*

---

## 🛠️ Requisits i Dependències

L'script pot funcionar en mode bàsic sense llibreries externes, però per disposar del 100% de les seves funcions es recomana instal·lar:

```bash
pip install numpy pillow matplotlib
💻 Com s'Utilitza
Per defecte, només cal col·locar els fitxers .csv dins de la carpeta Entrada fitxers (al costat de l'script) i executar:

Bash
python Python_temperatura.py
Arguments de l'Línia de Comandes més Comuns:
--entrada "ruta": Especifica una carpeta d'origen diferent per als CSV.

--sortida "ruta": Especifica on desar els resultats.

--html: Activa la generació de mapes interactius HTML per a cada imatge i la gràfica web interactiva.

--nomes-grafica: Omet la creació de les imatges individuals (PNG/HTML) per processar centenars de fitxers en pocs segons, generant només els resums i les gràfiques.

--reutilitzar: En lloc de crear una carpeta nova tipus Resultats 3, sobreescriu els fitxers de l'última carpeta generada (ideal per a proves).

--suavitzat-punts 21: Modifica la finestra del filtre mòbil (per defecte 21 punts).

--llindar-pic 1.5: Canvia la tolerància en graus per descartar un pic com a soroll.

📁 Estructura de Sortida
Cada vegada que executes l'script (tret que usis --reutilitzar), es crea una nova carpeta numerada (Resultats 1, Resultats 2, etc.) per protegir les teves dades prèvies:

Plaintext
Mapes termics/
└── Resultats N/
    ├── .cache_processat
    ├── Imatges PNG/
    │   ├── grafica_maxims_temperatura.png   <-- Evolució temporal visual
    │   └── [Nom_Fitxer].png                 <-- Mapes tèrmics individuals
    ├── HTML navegador/                      <-- (Només amb --html)
    │   ├── grafica_maxims_temperatura.html  <-- Gràfica interactiva amb taula
    │   └── [Nom_Fitxer].html                <-- Visor de píxels interactiu
    └── Dades CSV/                           
        ├── maxims_temperatura.csv           <-- Coordenades i màxims en brut
        ├── maxims_temperatura_suavitzats.csv<-- Màxims filtrats per a informes
        └── resum_temperatures.csv           <-- Mides i estadístiques globals
