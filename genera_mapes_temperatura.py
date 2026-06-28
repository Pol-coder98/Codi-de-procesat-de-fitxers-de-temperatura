import argparse
import base64
import csv
from datetime import datetime, timedelta
import html
import json
import os
from pathlib import Path
import re


# =========================
# CONFIGURACIO PER DEFECTE
# =========================

CARPETA_CSV = "Entrada fitxers"
CARPETA_SORTIDA = "Mapes termics"
ESCALA_COLORS = "inferno"

INFERNO_STOPS = [
    (0.000, (0, 0, 4)),
    (0.125, (31, 12, 72)),
    (0.250, (85, 15, 109)),
    (0.375, (136, 34, 106)),
    (0.500, (186, 54, 85)),
    (0.625, (227, 89, 51)),
    (0.750, (249, 140, 10)),
    (0.875, (249, 201, 50)),
    (1.000, (252, 255, 164)),
]


def llegir_csv_temperatures(fitxer):
    data = []

    with open(fitxer, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")

        for num_linia, fila in enumerate(reader, start=1):
            valors = []

            for valor in fila:
                valor = valor.strip()
                if not valor:
                    continue

                try:
                    valors.append(float(valor.replace(",", ".")))
                except ValueError:
                    print(f"Linia ignorada a {fitxer} (linia {num_linia}): {';'.join(fila)}")
                    valors = []
                    break

            if valors:
                data.append(valors)

    if not data:
        raise ValueError("No s'han trobat dades valides")

    amples = [len(fila) for fila in data]
    if len(set(amples)) != 1:
        raise ValueError("Les files no tenen totes la mateixa longitud")

    return data


def estadistiques(temp):
    valors = [valor for fila in temp for valor in fila]
    return min(valors), max(valors), sum(valors) / len(valors)


def punt_maxim(temp):
    millor_x = 0
    millor_y = 0
    millor_valor = temp[0][0]

    for y, fila in enumerate(temp):
        for x, valor in enumerate(fila):
            if valor > millor_valor:
                millor_x = x
                millor_y = y
                millor_valor = valor

    return millor_x, millor_y, millor_valor


def mida(temp):
    return len(temp[0]), len(temp)


def interpretar_retall(text):
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 4:
        raise ValueError("El retall ha de tenir el format x1,y1,x2,y2")

    try:
        x1, y1, x2, y2 = [int(part) for part in parts]
    except ValueError as exc:
        raise ValueError("Les coordenades del retall han de ser nombres enters") from exc

    return x1, y1, x2, y2


def interpretar_retall_percent(text, amplada, alcada):
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 4:
        raise ValueError("El retall percentual ha de tenir el format x1,y1,x2,y2")

    try:
        x1p, y1p, x2p, y2p = [float(part.replace(",", ".")) for part in parts]
    except ValueError as exc:
        raise ValueError("Les coordenades percentuals del retall han de ser numeriques") from exc

    return (
        round(amplada * x1p / 100),
        round(alcada * y1p / 100),
        round(amplada * x2p / 100),
        round(alcada * y2p / 100),
    )


def retallar_temperatures(temp, retall):
    amplada, alcada = mida(temp)
    x1, y1, x2, y2 = retall

    x1 = max(0, min(amplada, x1))
    x2 = max(0, min(amplada, x2))
    y1 = max(0, min(alcada, y1))
    y2 = max(0, min(alcada, y2))

    if x2 <= x1 or y2 <= y1:
        raise ValueError(
            f"Retall invalid per a una imatge de {amplada} x {alcada}: "
            f"{retall}. Usa x1,y1,x2,y2 amb x2>x1 i y2>y1."
        )

    return [fila[x1:x2] for fila in temp[y1:y2]], (x1, y1, x2, y2)


def paleta_inferno_256():
    colors = []

    for i in range(256):
        pos = i / 255

        for idx in range(len(INFERNO_STOPS) - 1):
            p0, c0 = INFERNO_STOPS[idx]
            p1, c1 = INFERNO_STOPS[idx + 1]

            if p0 <= pos <= p1:
                factor = (pos - p0) / (p1 - p0) if p1 != p0 else 0
                colors.append(
                    [
                        round(c0[canal] + (c1[canal] - c0[canal]) * factor)
                        for canal in range(3)
                    ]
                )
                break

    return colors


def guardar_png(temp, nom, carpeta_sortida, cmap, vmin=None, vmax=None):
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return None

    t_min, t_max, t_avg = estadistiques(temp)

    plt.figure(figsize=(10, 8))
    im = plt.imshow(temp, cmap=cmap, origin="upper", aspect="equal", vmin=vmin, vmax=vmax)
    plt.colorbar(im, label="Temperatura (C)")
    plt.title(f"{nom}\nMin={t_min:.1f} C  Mitjana={t_avg:.1f} C  Max={t_max:.1f} C")
    plt.xlabel("X (px)")
    plt.ylabel("Y (px)")
    plt.tight_layout()

    png_sortida = carpeta_sortida / f"{nom}.png"
    plt.savefig(png_sortida, dpi=140, bbox_inches="tight")
    plt.close()

    return png_sortida


def generar_html_interactiu(temp, nom, carpeta_sortida, cmap, vmin=None, vmax=None):
    t_min, t_max, t_avg = estadistiques(temp)
    escala_min = t_min if vmin is None else float(vmin)
    escala_max = t_max if vmax is None else float(vmax)
    amplada, alcada = mida(temp)

    colors = paleta_inferno_256()

    payload = {
        "nom": nom,
        "dades": [[round(valor, 4) for valor in fila] for fila in temp],
        "min": round(t_min, 4),
        "max": round(t_max, 4),
        "mitjana": round(t_avg, 4),
        "escalaMin": escala_min,
        "escalaMax": escala_max,
        "colors": colors,
    }

    payload_b64 = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")

    document = f"""<!doctype html>
<html lang="ca">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(nom)} - mapa de temperatures</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f5f5f2;
      color: #1c1c1a;
    }}

    body {{
      margin: 0;
      padding: 24px;
    }}

    main {{
      max-width: 1180px;
      margin: 0 auto;
    }}

    h1 {{
      margin: 0 0 10px;
      font-size: 26px;
      line-height: 1.2;
      font-weight: 700;
    }}

    .resum {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }}

    .resum span,
    .lectura {{
      border: 1px solid #d9d7cf;
      background: #ffffff;
      border-radius: 6px;
      padding: 9px 11px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}

    .eina {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 170px;
      gap: 16px;
      align-items: start;
    }}

    .mapa-wrap {{
      min-width: 0;
    }}

    canvas#mapa {{
      width: 100%;
      height: auto;
      display: block;
      background: #111;
      border: 1px solid #222;
      cursor: crosshair;
      image-rendering: pixelated;
    }}

    .lectura {{
      position: sticky;
      top: 16px;
      font-size: 15px;
      line-height: 1.45;
    }}

    .lectura strong {{
      display: block;
      margin-bottom: 8px;
      font-size: 16px;
    }}

    .valor {{
      font-size: 24px;
      font-weight: 700;
    }}

    .escala {{
      width: 32px;
      height: 360px;
      border: 1px solid #222;
      background: linear-gradient(to top, #000, #fff);
    }}

    .llegenda {{
      display: grid;
      grid-template-columns: 32px 1fr;
      gap: 8px;
      align-items: center;
      margin-top: 12px;
      font-size: 13px;
    }}

    .ticks {{
      height: 360px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    @media (max-width: 760px) {{
      body {{
        padding: 14px;
      }}

      .eina {{
        grid-template-columns: 1fr;
      }}

      .lectura {{
        position: static;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(nom)}</h1>
    <div class="resum">
      <span>Min: {t_min:.2f} C</span>
      <span>Mitjana: {t_avg:.2f} C</span>
      <span>Max: {t_max:.2f} C</span>
      <span>Mida: {amplada} x {alcada} px</span>
    </div>

    <div class="eina">
      <div class="mapa-wrap">
        <canvas id="mapa" aria-label="Mapa interactiu de temperatures"></canvas>
      </div>

      <aside class="lectura">
        <strong>Punt seleccionat</strong>
        <div>X: <span id="x">-</span></div>
        <div>Y: <span id="y">-</span></div>
        <div class="valor"><span id="temp">Mou el cursor</span></div>
        <div>Suavitzat: <span id="temp-suavitzada">-</span></div>
        <div class="llegenda">
          <div id="escala" class="escala"></div>
          <div class="ticks">
            <span>{escala_max:.2f} C</span>
            <span>{((escala_min + escala_max) / 2):.2f} C</span>
            <span>{escala_min:.2f} C</span>
          </div>
        </div>
      </aside>
    </div>
  </main>

  <script>
    const payload = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob("{payload_b64}"), c => c.charCodeAt(0))));
    const dades = payload.dades;
    const alt = dades.length;
    const ample = dades[0].length;
    const canvas = document.getElementById("mapa");
    const ctx = canvas.getContext("2d");
    const escala = document.getElementById("escala");
    const lecturaX = document.getElementById("x");
    const lecturaY = document.getElementById("y");
    const lecturaTemp = document.getElementById("temp");

    canvas.width = ample;
    canvas.height = alt;

    function colorPerTemperatura(valor) {{
      const rang = payload.escalaMax - payload.escalaMin || 1;
      const normalitzat = Math.max(0, Math.min(1, (valor - payload.escalaMin) / rang));
      return payload.colors[Math.round(normalitzat * 255)];
    }}

    function pintarMapa() {{
      const image = ctx.createImageData(ample, alt);

      for (let y = 0; y < alt; y += 1) {{
        for (let x = 0; x < ample; x += 1) {{
          const idx = (y * ample + x) * 4;
          const [r, g, b] = colorPerTemperatura(dades[y][x]);
          image.data[idx] = r;
          image.data[idx + 1] = g;
          image.data[idx + 2] = b;
          image.data[idx + 3] = 255;
        }}
      }}

      ctx.putImageData(image, 0, 0);
    }}

    function actualitzarLectura(event) {{
      const rect = canvas.getBoundingClientRect();
      const x = Math.max(0, Math.min(ample - 1, Math.floor((event.clientX - rect.left) * ample / rect.width)));
      const y = Math.max(0, Math.min(alt - 1, Math.floor((event.clientY - rect.top) * alt / rect.height)));
      const temperatura = dades[y][x];

      lecturaX.textContent = x;
      lecturaY.textContent = y;
      lecturaTemp.textContent = `${{temperatura.toFixed(2)}} C`;
    }}

    function pintarEscala() {{
      const stops = payload.colors
        .map((rgb, index) => `rgb(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}}) ${{(index / 255 * 100).toFixed(2)}}%`)
        .join(", ");
      escala.style.background = `linear-gradient(to top, ${{stops}})`;
    }}

    canvas.addEventListener("mousemove", actualitzarLectura);
    canvas.addEventListener("click", actualitzarLectura);

    pintarMapa();
    pintarEscala();
  </script>
</body>
</html>
"""

    html_sortida = carpeta_sortida / f"{nom}.html"
    html_sortida.write_text(document, encoding="utf-8")
    return html_sortida


def extreure_instant_del_nom(nom):
    text = nom.replace(" ", "_")

    patrons = [
        r"(?P<any>20\d{2})[-_\.]?(?P<mes>[01]\d)[-_\.]?(?P<dia>[0-3]\d).*?(?P<hora>[0-2]\d)[-_hH\.]?(?P<minut>[0-5]\d)(?:[-_\.]?(?P<segon>[0-5]\d))?",
        r"(?P<dia>[0-3]\d)[-_\.](?P<mes>[01]\d)[-_\.](?P<any>20\d{2}).*?(?P<hora>[0-2]\d)[-_hH\.]?(?P<minut>[0-5]\d)(?:[-_\.]?(?P<segon>[0-5]\d))?",
    ]

    for patro in patrons:
        coincidencia = re.search(patro, text)
        if not coincidencia:
            continue

        grups = coincidencia.groupdict()
        try:
            return datetime(
                int(grups["any"]),
                int(grups["mes"]),
                int(grups["dia"]),
                int(grups["hora"]),
                int(grups["minut"]),
                int(grups.get("segon") or 0),
            )
        except ValueError:
            continue

    return None


def construir_serie_maxims(dades_per_fitxer, interval_segons=None):
    instants = [extreure_instant_del_nom(fitxer.stem) for fitxer, _, _, _ in dades_per_fitxer]

    if all(instant is not None for instant in instants):
        combinat = sorted(zip(dades_per_fitxer, instants), key=lambda item: item[1])
        t0 = combinat[0][1]
    else:
        combinat = list(zip(dades_per_fitxer, instants))
        t0 = None

    serie = []

    for index, ((fitxer, temp, offset_x, offset_y), instant) in enumerate(combinat):
        max_x, max_y, max_temp = punt_maxim(temp)

        if instant is not None and t0 is not None:
            rel_minuts_float = (instant - t0).total_seconds() / 60
        elif interval_segons is not None:
            rel_minuts_float = index * interval_segons / 60
        else:
            rel_minuts_float = float(index)

        rel_minuts = round(rel_minuts_float)
        temps_label = str(rel_minuts)

        serie.append(
            {
                "fitxer": fitxer.name,
                "temps": temps_label,
                "temps_minuts": rel_minuts,
                "temps_relatius_minuts": rel_minuts_float,
                "max_C": round(max_temp, 4),
                "x_max": max_x,
                "y_max": max_y,
                "x_max_original": max_x + offset_x,
                "y_max_original": max_y + offset_y,
            }
        )

    serie.sort(key=lambda punt: punt["temps_relatius_minuts"])

    return serie


def guardar_serie_maxims_csv(serie, carpeta_sortida):
    sortida = carpeta_sortida / "maxims_temperatura.csv"

    with open(sortida, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["fitxer", "temps", "max_C", "x_max_retall", "y_max_retall", "x_max_original", "y_max_original"])

        for punt in serie:
            writer.writerow(
                [
                    punt["fitxer"],
                    punt["temps"],
                    f"{punt['max_C']:.4f}".replace(".", ","),
                    punt["x_max"],
                    punt["y_max"],
                    punt["x_max_original"],
                    punt["y_max_original"],
                ]
            )

    return sortida


def mediana(valors):
    ordenats = sorted(valors)
    mig = len(ordenats) // 2

    if len(ordenats) % 2 == 1:
        return ordenats[mig]

    return (ordenats[mig - 1] + ordenats[mig]) / 2


def valors_suavitzats(valors, finestra=21, llindar_pic=1.0):
    if not valors:
        return []

    finestra = max(1, int(finestra))
    if finestra % 2 == 0:
        finestra += 1

    radi = finestra // 2
    sense_pics = []

    for index, valor in enumerate(valors):
        inici = max(0, index - radi)
        final = min(len(valors), index + radi + 1)
        finestra_local = valors[inici:final]
        mediana_local = mediana(finestra_local)

        if llindar_pic is not None and abs(valor - mediana_local) > llindar_pic:
            sense_pics.append(mediana_local)
        else:
            sense_pics.append(valor)

    suavitzats = []

    for index in range(len(sense_pics)):
        inici = max(0, index - radi)
        final = min(len(sense_pics), index + radi + 1)
        finestra_local = sense_pics[inici:final]
        suavitzats.append(sum(finestra_local) / len(finestra_local))

    return suavitzats


def enriquir_serie_amb_suavitzat(serie, finestra=21, llindar_pic=1.0):
    valors = [punt["max_C"] for punt in serie]
    suavitzats = valors_suavitzats(valors, finestra=finestra, llindar_pic=llindar_pic)

    for punt, valor_suavitzat in zip(serie, suavitzats):
        punt["max_suavitzat_C"] = round(valor_suavitzat, 4)

    return serie


def guardar_serie_suavitzada_csv(serie, carpeta_sortida):
    sortida = carpeta_sortida / "maxims_temperatura_suavitzats.csv"

    with open(sortida, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["fitxer", "temps", "max_C_original", "max_C_suavitzat"])

        for punt in serie:
            writer.writerow(
                [
                    punt["fitxer"],
                    punt["temps"],
                    f"{punt['max_C']:.4f}".replace(".", ","),
                    f"{punt['max_suavitzat_C']:.4f}".replace(".", ","),
                ]
            )

    return sortida


def generar_html_grafica_maxims(serie, carpeta_sortida):
    payload_b64 = base64.b64encode(json.dumps(serie, ensure_ascii=False).encode("utf-8")).decode("ascii")

    document = f"""<!doctype html>
<html lang="ca">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Temperatura maxima en funcio del temps</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f5f5f2;
      color: #1c1c1a;
    }}

    body {{
      margin: 0;
      padding: 24px;
    }}

    main {{
      max-width: 1180px;
      margin: 0 auto;
    }}

    h1 {{
      margin: 0 0 14px;
      font-size: 26px;
      line-height: 1.2;
    }}

    .resum {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }}

    .resum span,
    .lectura {{
      border: 1px solid #d9d7cf;
      background: #fff;
      border-radius: 6px;
      padding: 9px 11px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}

    .eina {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 230px;
      gap: 16px;
      align-items: start;
    }}

    canvas {{
      width: 100%;
      height: 520px;
      display: block;
      background: #fff;
      border: 1px solid #cfcac0;
      cursor: crosshair;
    }}

    .lectura {{
      position: sticky;
      top: 16px;
      font-size: 14px;
      line-height: 1.45;
    }}

    .lectura strong {{
      display: block;
      margin-bottom: 8px;
      font-size: 16px;
    }}

    .valor {{
      margin: 8px 0;
      font-size: 24px;
      font-weight: 700;
    }}

    table {{
      width: 100%;
      margin-top: 18px;
      border-collapse: collapse;
      font-size: 13px;
      background: #fff;
      border: 1px solid #d9d7cf;
    }}

    th,
    td {{
      padding: 7px 8px;
      border-bottom: 1px solid #ece9e1;
      text-align: left;
    }}

    th {{
      background: #ece9e1;
    }}

    @media (max-width: 760px) {{
      body {{
        padding: 14px;
      }}

      .eina {{
        grid-template-columns: 1fr;
      }}

      canvas {{
        height: 380px;
      }}

      .lectura {{
        position: static;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Temperatura maxima en funcio del temps</h1>
    <div class="resum">
      <span id="num-punts"></span>
      <span id="rang-temp"></span>
    </div>

    <div class="eina">
      <canvas id="grafica" aria-label="Grafica de temperatura maxima en funcio del temps"></canvas>
      <aside class="lectura">
        <strong>Punt seleccionat</strong>
        <div>Temps: <span id="temps">-</span></div>
        <div class="valor"><span id="temp">Mou el cursor</span></div>
        <div>Fitxer: <span id="fitxer">-</span></div>
        <div>Max retallat a X=<span id="x">-</span>, Y=<span id="y">-</span></div>
        <div>Max original a X=<span id="x-original">-</span>, Y=<span id="y-original">-</span></div>
      </aside>
    </div>

    <table>
      <thead>
        <tr>
          <th>Temps</th>
          <th>Max C original</th>
          <th>Max C suavitzat</th>
          <th>Fitxer</th>
          <th>X max retall</th>
          <th>Y max retall</th>
          <th>X max original</th>
          <th>Y max original</th>
        </tr>
      </thead>
      <tbody id="taula"></tbody>
    </table>
  </main>

  <script>
    const serie = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob("{payload_b64}"), c => c.charCodeAt(0))));
    const canvas = document.getElementById("grafica");
    const ctx = canvas.getContext("2d");
    const lecturaTemps = document.getElementById("temps");
    const lecturaTemp = document.getElementById("temp");
    const lecturaTempSuavitzada = document.getElementById("temp-suavitzada");
    const lecturaFitxer = document.getElementById("fitxer");
    const lecturaX = document.getElementById("x");
    const lecturaY = document.getElementById("y");
    const lecturaXOriginal = document.getElementById("x-original");
    const lecturaYOriginal = document.getElementById("y-original");
    const puntsGrafics = [];

    function ajustarCanvas() {{
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * ratio);
      canvas.height = Math.round(rect.height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }}

    function dibuixar() {{
      ajustarCanvas();
      puntsGrafics.length = 0;

      const w = canvas.getBoundingClientRect().width;
      const h = canvas.getBoundingClientRect().height;
      const marge = {{ esquerra: 62, dreta: 24, superior: 28, inferior: 82 }};
      const valors = serie.flatMap(p => [p.max_C, p.max_suavitzat_C ?? p.max_C]);
      const min = Math.min(...valors);
      const max = Math.max(...valors);
      const rang = max - min || 1;
      const yMin = min - rang * 0.08;
      const yMax = max + rang * 0.08;
      const yRang = yMax - yMin || 1;
      const xValors = serie.map(p => Number(p.temps_minuts));
      const xMin = Math.min(...xValors);
      const xMax = Math.max(...xValors);
      const xRang = Math.max(1, xMax - xMin);
      const ampladaPlot = w - marge.esquerra - marge.dreta;
      const alcadaPlot = h - marge.superior - marge.inferior;

      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, w, h);

      ctx.strokeStyle = "#d9d7cf";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(marge.esquerra, marge.superior);
      ctx.lineTo(marge.esquerra, h - marge.inferior);
      ctx.lineTo(w - marge.dreta, h - marge.inferior);
      ctx.stroke();

      ctx.fillStyle = "#333";
      ctx.font = "12px Arial";
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";

      for (let i = 0; i <= 5; i += 1) {{
        const valor = yMin + yRang * i / 5;
        const y = h - marge.inferior - (valor - yMin) / yRang * alcadaPlot;
        ctx.strokeStyle = "#ece9e1";
        ctx.beginPath();
        ctx.moveTo(marge.esquerra, y);
        ctx.lineTo(w - marge.dreta, y);
        ctx.stroke();
        ctx.fillText(`${{valor.toFixed(1)}} C`, marge.esquerra - 8, y);
      }}

      serie.forEach((punt) => {{
        const xValue = Number(punt.temps_minuts);
        const x = marge.esquerra + (xValue - xMin) / xRang * ampladaPlot;
        const y = h - marge.inferior - (punt.max_C - yMin) / yRang * alcadaPlot;
        const ySuau = h - marge.inferior - ((punt.max_suavitzat_C ?? punt.max_C) - yMin) / yRang * alcadaPlot;
        puntsGrafics.push({{ x, y, punt }});
        punt.ySuau = ySuau;
      }});

      puntsGrafics.forEach(({{ x, y }}) => {{
        ctx.fillStyle = "rgba(70, 70, 70, 0.30)";
        ctx.beginPath();
        ctx.arc(x, y, 2.2, 0, Math.PI * 2);
        ctx.fill();
      }});

      ctx.strokeStyle = "#b83f2d";
      ctx.lineWidth = 3;
      ctx.beginPath();
      puntsGrafics.forEach((punt, index) => {{
        if (index === 0) ctx.moveTo(punt.x, punt.punt.ySuau);
        else ctx.lineTo(punt.x, punt.punt.ySuau);
      }});
      ctx.stroke();

      puntsGrafics.forEach(({{ x, punt }}) => {{
        const y = punt.ySuau;
        ctx.fillStyle = "#b83f2d";
        ctx.beginPath();
        ctx.arc(x, y, 3.2, 0, Math.PI * 2);
        ctx.fill();
      }});

      ctx.fillStyle = "#333";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      const saltEtiquetes = Math.max(1, Math.ceil(serie.length / 10));

      puntsGrafics.forEach(({{ x, punt }}, index) => {{
        if (index % saltEtiquetes !== 0 && index !== serie.length - 1) return;
        ctx.save();
        ctx.translate(x, h - marge.inferior + 10);
        ctx.rotate(-Math.PI / 4);
        ctx.textAlign = "right";
        ctx.fillText(`${{punt.temps}} min`, 0, 0);
        ctx.restore();
      }});
    }}

    function seleccionarMesProper(event) {{
      if (!puntsGrafics.length) return;

      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      let millor = puntsGrafics[0];
      let millorDistancia = Infinity;

      puntsGrafics.forEach(punt => {{
        const distancia = Math.hypot(punt.x - x, punt.y - y);
        if (distancia < millorDistancia) {{
          millor = punt;
          millorDistancia = distancia;
        }}
      }});

      lecturaTemps.textContent = `${{millor.punt.temps}} min`;
      lecturaTemp.textContent = `${{millor.punt.max_C.toFixed(2)}} C`;
      lecturaTempSuavitzada.textContent = `${{(millor.punt.max_suavitzat_C ?? millor.punt.max_C).toFixed(2)}} C`;
      lecturaFitxer.textContent = millor.punt.fitxer;
      lecturaX.textContent = millor.punt.x_max;
      lecturaY.textContent = millor.punt.y_max;
      lecturaXOriginal.textContent = millor.punt.x_max_original;
      lecturaYOriginal.textContent = millor.punt.y_max_original;
    }}

    function omplirTaula() {{
      const tbody = document.getElementById("taula");
      tbody.innerHTML = serie.map(punt => `
        <tr>
          <td>${{punt.temps}}</td>
          <td>${{punt.max_C.toFixed(2)}}</td>
          <td>${{(punt.max_suavitzat_C ?? punt.max_C).toFixed(2)}}</td>
          <td>${{punt.fitxer}}</td>
          <td>${{punt.x_max}}</td>
          <td>${{punt.y_max}}</td>
          <td>${{punt.x_max_original}}</td>
          <td>${{punt.y_max_original}}</td>
        </tr>
      `).join("");
    }}

    document.getElementById("num-punts").textContent = `${{serie.length}} imatges processades`;
    document.getElementById("rang-temp").textContent = `Maxims: ${{Math.min(...serie.map(p => p.max_C)).toFixed(2)}} - ${{Math.max(...serie.map(p => p.max_C)).toFixed(2)}} C`;

    canvas.addEventListener("mousemove", seleccionarMesProper);
    canvas.addEventListener("click", seleccionarMesProper);
    window.addEventListener("resize", dibuixar);

    omplirTaula();
    dibuixar();
  </script>
</body>
</html>
"""

    sortida = carpeta_sortida / "grafica_maxims_temperatura.html"
    sortida.write_text(document, encoding="utf-8")
    return sortida


def guardar_png_grafica_maxims(serie, carpeta_sortida):
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return None

    sortida = carpeta_sortida / "grafica_maxims_temperatura.png"
    x = [punt["temps_relatius_minuts"] for punt in serie]
    y_original = [punt["max_C"] for punt in serie]
    y_suau = [punt.get("max_suavitzat_C", punt["max_C"]) for punt in serie]
    etiquetes = [f"{round(punt['temps_relatius_minuts'])} min" for punt in serie]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.scatter(x, y_original, s=12, color="#777777", alpha=0.28, label="Valors originals")
    ax.plot(x, y_suau, color="#b83f2d", linewidth=2.8, label="Tendencia suavitzada")

    max_ticks = 8
    if len(x) <= max_ticks:
        tick_posicions = x
    else:
        tick_posicions = sorted(
            set(
                round(x[0] + index * (x[-1] - x[0]) / (max_ticks - 1))
                for index in range(max_ticks)
            )
        )

    tick_etiquetes = [f"{posicio} min" for posicio in tick_posicions]

    ax.set_title("Temperatura maxima en funcio del temps")
    ax.set_xlabel("Temps relatiu (minuts)")
    ax.set_ylabel("Temperatura maxima (C)")
    ax.set_xticks(tick_posicions)
    ax.set_xticklabels(tick_etiquetes, rotation=25, ha="right")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    fig.savefig(sortida, dpi=140, bbox_inches="tight")
    plt.close(fig)

    return sortida


def guardar_png_grafica_maxims_original(serie, carpeta_sortida):
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return None

    sortida = carpeta_sortida / "grafica_maxims_temperatura_original.png"
    x = list(range(1, len(serie) + 1))
    y = [punt["max_C"] for punt in serie]

    plt.figure(figsize=(11, 6))
    plt.plot(x, y, marker=".", linewidth=1, color="#777777", alpha=0.65)
    plt.title("Temperatura maxima original")
    plt.xlabel("Temps")
    plt.ylabel("Temperatura maxima (C)")
    plt.grid(axis="y", alpha=0.25)
    plt.xticks([])
    plt.tight_layout()
    plt.savefig(sortida, dpi=140, bbox_inches="tight")
    plt.close()

    return sortida


def ruta_relativa(fitxer, carpeta_base):
    try:
        return str(fitxer.relative_to(carpeta_base))
    except ValueError:
        return fitxer.name


def main():
    parser = argparse.ArgumentParser(
        description="Genera mapes de temperatura PNG i HTML interactius per a tots els CSV d'una carpeta."
    )
    parser.add_argument("--entrada", default=CARPETA_CSV, help="Carpeta on hi ha els fitxers .csv")
    parser.add_argument("--sortida", default=CARPETA_SORTIDA, help="Carpeta on es guardaran els mapes")
    parser.add_argument("--cmap", default=ESCALA_COLORS, help="Mapa de colors de matplotlib")
    parser.add_argument(
        "--interval-segons",
        type=float,
        default=None,
        help="Interval entre imatges si el temps no es pot extreure del nom del fitxer",
    )
    parser.add_argument(
        "--retall",
        default=None,
        help="Zona util en pixels amb format x1,y1,x2,y2. El maxim es calcula nomes dins aquesta zona.",
    )
    parser.add_argument(
        "--retall-percent",
        default=None,
        help="Zona util en percentatge amb format x1,y1,x2,y2. Exemple: 10,20,90,85",
    )
    parser.add_argument(
        "--suavitzat-punts",
        type=int,
        default=21,
        help="Nombre de punts per suavitzar la grafica de maxims. Ha de ser imparell; per defecte 21.",
    )
    parser.add_argument(
        "--llindar-pic",
        type=float,
        default=1.0,
        help="Diferencia en C respecte la mediana local per considerar un pic com a soroll. Per defecte 1.0.",
    )
    parser.add_argument(
        "--escala-global",
        action="store_true",
        help="Fes servir la mateixa escala de colors per a tots els fitxers processats",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="No generar els fitxers HTML interactius",
    )
    args = parser.parse_args()

    carpeta_csv = Path(args.entrada)
    carpeta_sortida = Path(args.sortida)
    carpeta_html = carpeta_sortida / "HTML navegador"
    carpeta_imatges = carpeta_sortida / "Imatges PNG"
    carpeta_dades = carpeta_sortida / "Dades CSV"

    carpeta_sortida.mkdir(parents=True, exist_ok=True)
    if not args.no_html:
        carpeta_html.mkdir(parents=True, exist_ok=True)
    carpeta_imatges.mkdir(parents=True, exist_ok=True)
    carpeta_dades.mkdir(parents=True, exist_ok=True)

    fitxers = sorted(carpeta_csv.glob("*.csv"))
    print(f"S'han trobat {len(fitxers)} fitxers CSV")

    if not fitxers:
        print(f"Posa els CSV dins la carpeta: {carpeta_csv.resolve()}")
        return

    dades_per_fitxer = []

    for fitxer in fitxers:
        try:
            temp = llegir_csv_temperatures(fitxer)
            offset_x = 0
            offset_y = 0

            if args.retall and args.retall_percent:
                raise ValueError("Fes servir --retall o --retall-percent, pero no tots dos alhora")

            if args.retall:
                temp, retall_aplicat = retallar_temperatures(temp, interpretar_retall(args.retall))
                offset_x, offset_y = retall_aplicat[0], retall_aplicat[1]
            elif args.retall_percent:
                amplada, alcada = mida(temp)
                retall = interpretar_retall_percent(args.retall_percent, amplada, alcada)
                temp, retall_aplicat = retallar_temperatures(temp, retall)
                offset_x, offset_y = retall_aplicat[0], retall_aplicat[1]

            dades_per_fitxer.append((fitxer, temp, offset_x, offset_y))
        except Exception as e:
            print(f"Error llegint {fitxer}: {e}")

    if not dades_per_fitxer:
        print("No s'ha pogut processar cap fitxer.")
        return

    vmin = vmax = None
    if args.escala_global:
        vmin = min(estadistiques(temp)[0] for _, temp, _, _ in dades_per_fitxer)
        vmax = max(estadistiques(temp)[1] for _, temp, _, _ in dades_per_fitxer)

    serie_maxims = construir_serie_maxims(dades_per_fitxer, interval_segons=args.interval_segons)
    serie_maxims = enriquir_serie_amb_suavitzat(
        serie_maxims,
        finestra=args.suavitzat_punts,
        llindar_pic=args.llindar_pic,
    )
    maxims_csv = guardar_serie_maxims_csv(serie_maxims, carpeta_dades)
    maxims_suavitzats_csv = guardar_serie_suavitzada_csv(serie_maxims, carpeta_dades)
    grafica_html = None
    if not args.no_html:
        grafica_html = generar_html_grafica_maxims(serie_maxims, carpeta_html)
    grafica_png = guardar_png_grafica_maxims(serie_maxims, carpeta_imatges)

    resum_sortida = carpeta_dades / "resum_temperatures.csv"
    with open(resum_sortida, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "fitxer",
                "amplada_px",
                "alcada_px",
                "x_origen_retall",
                "y_origen_retall",
                "min_C",
                "mitjana_C",
                "max_C",
                "html",
                "png",
            ]
        )

        for fitxer, temp, offset_x, offset_y in dades_per_fitxer:
            try:
                nom = fitxer.stem
                t_min, t_max, t_avg = estadistiques(temp)
                amplada, alcada = mida(temp)

                png_sortida = guardar_png(temp, nom, carpeta_imatges, args.cmap, vmin=vmin, vmax=vmax)
                html_sortida = ""
                if not args.no_html:
                    html_sortida = generar_html_interactiu(temp, nom, carpeta_html, args.cmap, vmin=vmin, vmax=vmax)

                writer.writerow(
                    [
                        fitxer.name,
                        amplada,
                        alcada,
                        offset_x,
                        offset_y,
                        f"{t_min:.4f}".replace(".", ","),
                        f"{t_avg:.4f}".replace(".", ","),
                        f"{t_max:.4f}".replace(".", ","),
                        ruta_relativa(html_sortida, carpeta_sortida),
                        ruta_relativa(png_sortida, carpeta_sortida) if png_sortida else "",
                    ]
                )

                if args.no_html:
                    print(
                        f"{nom}: Min={t_min:.2f} C Max={t_max:.2f} C "
                        f"Mitjana={t_avg:.2f} C -> {ruta_relativa(png_sortida, carpeta_sortida) if png_sortida else ''}"
                    )
                else:
                    print(
                        f"{nom}: Min={t_min:.2f} C Max={t_max:.2f} C "
                        f"Mitjana={t_avg:.2f} C -> {html_sortida}"
                    )
            except Exception as e:
                print(f"Error generant mapa per {fitxer}: {e}")

    print(f"Serie de maxims: {maxims_csv}")
    print(f"Serie de maxims suavitzats: {maxims_suavitzats_csv}")
    if not args.no_html:
        print(f"Grafica interactiva de maxims: {grafica_html}")
    if grafica_png:
        print(f"Grafica PNG de maxims: {grafica_png}")
    if not args.no_html:
        print(f"HTML per obrir al navegador: {carpeta_html.resolve()}")
    print(f"Imatges PNG: {carpeta_imatges.resolve()}")
    print(f"Dades CSV: {carpeta_dades.resolve()}")
    print(f"Proces finalitzat. Resultats a: {carpeta_sortida.resolve()}")


if __name__ == "__main__":
    main()
