# aladin-mcp — Servidor MCP para Aladin / CDS

Servidor MCP en Python que permite a Claude (Claude Code o Claude Desktop) trabajar con el
ecosistema del CDS de Estrasburgo: SIMBAD, VizieR, imágenes HiPS y Aladin Desktop (vía SAMP).
Pensado para un taller de astronomía (Gran Nube de Magallanes y cúmulo NGC 4755).

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `simbad_query(nombre)` | Coordenadas, tipo de objeto, magnitudes, paralaje, distancias publicadas y tamaño angular. |
| `vizier_query(catalogo, columnas, filtros, max_filas, exportar_csv)` | Consulta un catálogo de VizieR y exporta cada tabla a CSV. |
| `get_survey_image(objetivo_o_coordenadas, hips_id, fov_grados, ancho_px, ...)` | Descarga un recorte con hips2fits y lo guarda como FITS y PNG. |
| `measure_angular_size(fits, umbral, ...)` | Estimación aproximada del diámetro angular de la emisión principal. |
| `plot_cmd(csv, col_mag, col_color, titulo)` | Diagrama color-magnitud con el eje de magnitud invertido. |
| `aladin_send(comandos)` | Envía un script a Aladin Desktop por SAMP (`script.aladin.send`). |
| `hips_search(palabra)` | Busca IDs HiPS en el MocServer (o en el Registro IVOA si el MocServer no responde). |

Todos los archivos generados quedan en `output/` (`images/`, `vizier/`, `plots/`). Los cachés
de astropy, astroquery y matplotlib se guardan en `.cache/` y `.config/` dentro de esta carpeta.

### Alias de surveys

| Alias | ID HiPS | Banda | Respaldo en NASA SkyView |
|---|---|---|---|
| `DSS` | `CDS/P/DSS2/color` | óptico | `DSS2 Red` |
| `AKARI` | `CDS/P/AKARI/FIS/Color` | infrarrojo lejano (65–140 µm) | `AKARI WIDE-L` |
| `PLANCK` | `CDS/P/PLANCK/R2/HFI/color` | submilimétrico/radio (353–857 GHz) | `Planck 857 I` |
| `FERMI` | `CDS/P/Fermi/color` | rayos gamma (0.3–300 GeV) | `Fermi 5` |

Cómo se verificaron (28/10/2026, con el MocServer del CDS sin responder):
- `CDS/P/DSS2/color` y `CDS/P/Fermi/color`: `creator_did` leído del archivo `properties` del
  HiPS en el espejo de ESA (skies.esac.esa.int).
- AKARI y Planck: existen en el Registro IVOA como `ivo://cds/p/akari/fis/color` y
  `ivo://cds/p/planck/r2/hfi/color`. El registro pasa los IDs a minúsculas, así que las
  mayúsculas de la tabla siguen la convención del CDS. Cuando el CDS responda, confirmalo con
  `hips_search("AKARI")` y `hips_search("PLANCK")`.

También podés pasar cualquier otro ID HiPS directamente en `hips_id`.

## Instalación

Probado en Ubuntu 24.04 con Python 3.12 y [uv](https://docs.astral.sh/uv/).

```bash
cd <RUTA_DEL_REPO>
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

Sin uv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Comprobación rápida (debe listar las 7 herramientas):

```bash
.venv/bin/python -c "import asyncio; from aladin_mcp.server import mcp; print([t.name for t in asyncio.run(mcp.list_tools())])"
```

Notas de versiones:
- `mcp` 2.x renombró `FastMCP` a `MCPServer` (`from mcp.server.mcpserver import MCPServer`).
  Es la misma API de decoradores `@mcp.tool()`.
- astropy 8 marca `astropy.samp` como obsoleto (el reemplazo es `pyvo.samp`). Sigue
  funcionando; el aviso se silencia.
- `scipy` se agregó a las dependencias pedidas: lo usa `measure_angular_size` (suavizado y
  regiones conectadas).

## Registro en Claude

### Claude Code

```bash
claude mcp add aladin --scope project -- <RUTA_DEL_REPO>/.venv/bin/python -m aladin_mcp.server
```

Con `--scope project` la configuración queda en `.mcp.json` dentro de esta carpeta; Claude
Code pide aprobarla la primera vez que abrís el proyecto. Verificá con `claude mcp list`.

Alternativa sin el comando: copie `.mcp.json.example` como `.mcp.json` y reemplace
`<RUTA_DEL_REPO>` por la ruta absoluta del repositorio en su máquina. `.mcp.json` no se versiona
porque contiene rutas propias de cada computadora.

### Claude Desktop

Agregá esto en `~/.config/Claude/claude_desktop_config.json` (Linux),
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) o
`%APPDATA%\Claude\claude_desktop_config.json` (Windows), y reiniciá Claude Desktop:

```json
{
  "mcpServers": {
    "aladin": {
      "command": "<RUTA_DEL_REPO>/.venv/bin/python",
      "args": ["-m", "aladin_mcp.server"],
      "cwd": "<RUTA_DEL_REPO>"
    }
  }
}
```

## Abrir Aladin Desktop con SAMP activo

1. Descargá Aladin Desktop desde https://aladin.cds.unistra.fr/AladinDesktop/ (requiere Java).
2. Abrilo (`java -jar Aladin.jar` o el lanzador instalado). Si no hay ningún hub SAMP
   corriendo, Aladin arranca su propio hub interno.
3. Si no se conecta solo: menú **Interop** → iniciar o conectar al hub SAMP. El ícono de
   SAMP abajo en la ventana se pone verde al conectarse.
4. Alternativa: abrí TOPCAT (que también trae un hub) y conectá Aladin a ese hub.

`aladin_send` no recibe confirmación de que Aladin ejecutó el script (usa una notificación
SAMP): mirá la ventana de Aladin, y si un comando falla aparece en su consola.

## Ejemplos para el taller

Escribile a Claude en lenguaje natural; él elige las herramientas. Estos son pedidos de ejemplo
con las llamadas que deberían resultar.

### Punto 4 — Gran Nube de Magallanes

> Buscá la LMC en SIMBAD y decime su tamaño angular y su distancia.

`simbad_query("LMC")` → galaxia, V = 0.4, eje mayor 322.8′ × 274.8′, distancias publicadas
de unos 50 kpc.

> Bajá imágenes de la LMC de 16 grados en DSS, AKARI, PLANCK y FERMI, y medí el diámetro
> angular en cada una suponiendo 50 kpc.

```
get_survey_image("LMC", "DSS",    fov_grados=16, ancho_px=800)
get_survey_image("LMC", "AKARI",  fov_grados=16, ancho_px=600)
get_survey_image("LMC", "PLANCK", fov_grados=16, ancho_px=600)
get_survey_image("LMC", "FERMI",  fov_grados=20, ancho_px=400)
measure_angular_size("output/images/<archivo>.fits", umbral=3, distancia_kpc=50)
```

Prueba real con AKARI (SkyView, 16°, 400 px): diámetro equivalente ≈ 5.9° (ejes de 6.9° × 5.4°),
unos 5.1 kpc a 50 kpc. Probá también `umbral=2` y `umbral=5` para ver cuánto depende el
resultado del umbral.

> Cargá el catálogo J/AJ/138/1003 con todas sus filas y graficá V contra B-V.

```
vizier_query("J/AJ/138/1003", max_filas=10000)
plot_cmd("output/vizier/<tabla>.csv", col_mag="Vmag", col_color="B-V", titulo="LMC massive stars (Bonanos+ 2009)")
```

Los nombres de columna exactos salen en la respuesta de `vizier_query` (campo `columnas`). Si
el catálogo trae `Bmag` y `Vmag` en vez de `B-V`, usá `col_color="Bmag-Vmag"`.

> Mostrame todo eso en Aladin.

```
aladin_send("get hips(CDS/P/AKARI/FIS/Color); LMC; zoom 15deg")
aladin_send("get VizieR(J/AJ/138/1003) LMC 5deg")
```

### Punto 5 — Caja de Joyas (NGC 4755)

> Consultá NGC 4755 en SIMBAD.

`simbad_query("NGC 4755")` → cúmulo abierto (OpC) en 12:53:39.6 −60:22:16, tamaño 10.3′,
paralaje 0.462 mas, distancias publicadas de unos 1.9–2.0 kpc. SIMBAD no tiene magnitudes
integradas para el cúmulo, así que el diagrama color-magnitud necesita un catálogo de sus
estrellas.

> Buscá fotometría UBV de las estrellas de NGC 4755 en VizieR y hacé el diagrama
> color-magnitud para estimar la edad.

Claude debe elegir un catálogo fotométrico del cúmulo (por ejemplo, buscándolo en VizieR por
nombre del objeto), descargarlo con `vizier_query` y graficarlo con `plot_cmd`. Para estimar la
edad se mira el punto de desvío (*turn-off*) de la secuencia principal: en un cúmulo joven
como NGC 4755 (10–16 millones de años según la literatura) el punto de giro está en lo más alto
del diagrama. Las estrellas más brillantes son supergigantes azules, como κ Crucis (B5 I), que
recién salen de la secuencia principal, y hay una sola supergigante roja, DU Cru (M2 Iab).

> Centrá Aladin en el cúmulo.

```
aladin_send("get hips(CDS/P/DSS2/color); NGC 4755; zoom 30arcmin")
```

## Cómo mide `measure_angular_size` (y por qué es aproximado)

Método:
1. Si la imagen es de color (R, G, B), se promedian los tres planos.
2. Suavizado gaussiano (por defecto σ = 1 % del tamaño de la imagen) para borrar estrellas y
   ruido y quedarse con la emisión extendida.
3. Fondo y ruido con estadística *sigma-clipped* (3σ) de todo el campo.
4. Umbral = fondo + `umbral` × ruido.
5. Se elige la región conectada que contiene el centro de la imagen (o la más grande).
6. Con la escala de píxel del WCS: diámetro del círculo de igual área, 2·√(área/π), y ejes
   mayor y menor de la elipse con los mismos momentos de segundo orden.

Limitaciones:
- **El resultado depende del umbral**: bajarlo agranda el diámetro. No hay un "diámetro
  verdadero"; es una medida operativa.
- Si el objeto llena el campo, el "fondo" incluye la propia galaxia y el tamaño sale menor.
  Usá un campo 2–3 veces mayor que el tamaño esperado.
- Si la región toca el borde, el número es solo un **límite inferior** (la herramienta avisa).
- Los surveys de baja resolución (Planck, de unos 5′; Fermi, con una PSF de alrededor de 1°)
  borronean y agrandan las fuentes, y en Planck o Fermi la emisión de la Vía Láctea puede
  unirse con el objeto.
- Cada longitud de onda traza otra cosa (estrellas, polvo, gas, rayos cósmicos): es esperable
  que los diámetros no coincidan entre surveys. Esa diferencia es justamente lo interesante.
- **Siempre mirá el PNG de diagnóstico** (`png_diagnostico`, con el contorno en cian). En la
  prueba real, la imagen DSS de respaldo de SkyView dio 1.9° porque el contorno siguió el borde
  de una placa fotográfica, no la galaxia. El número no sirve sin la imagen.

## Solución de problemas

**"no mirror answered" / timeouts.** El servidor prueba los espejos en orden y recuerda el
último que funcionó:
- SIMBAD: `simbad.cds.unistra.fr` → `simbad.harvard.edu` (independiente; funciona aunque
  Estrasburgo esté caído).
- VizieR: `vizier.cds.unistra.fr` → `vizier.cfa.harvard.edu` → `vizier.iucaa.in` →
  `vizier.nao.ac.jp`. Ojo: el espejo de CfA hace de **gateway** hacia Estrasburgo; si el CDS no
  responde, CfA devuelve `504 Gateway Time-out`.
- Imágenes: `alasky` → `alaskybis` (hips2fits) → NASA SkyView como respaldo.
- Timeout por intento: 30 s. Se cambia con la variable de entorno `ALADIN_MCP_TIMEOUT` (en la
  configuración de Claude Desktop, agregá `"env": {"ALADIN_MCP_TIMEOUT": "60"}`).

Para saber si el problema es el CDS o tu red:

```bash
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" -m 15 https://simbad.cds.unistra.fr/simbad/
```

`000` después de 15 s significa que no hubo conexión. Si al mismo tiempo
`https://www.google.com` responde, el problema está entre tu red y el CDS.

**La primera consulta tarda ~30 s.** Es el tiempo de espera al servidor principal caído antes
de pasar al espejo. Las siguientes van directo al espejo que funcionó.

**Las imágenes DSS de respaldo tienen escalones.** SkyView arma el mosaico con placas
fotográficas sin igualar el fondo. El HiPS del CDS (`CDS/P/DSS2/color`) no tiene ese problema;
reintentá cuando hips2fits responda.

**Un objeto de SIMBAD "no existe" pero en la web sí aparece.** Probá otro nombre
(`"Jewel Box"`, `"NGC4755"`). Internamente, las magnitudes se consultan aparte porque pedirlas
junto con los datos básicos hace que astroquery descarte objetos sin esa magnitud (NGC 4755 no
tiene V en SIMBAD).

**`aladin_send` dice que no hay hub SAMP.** Abrí Aladin Desktop y conectalo al hub (ver la
sección de Aladin). Si hay un hub pero ningún cliente acepta `script.aladin.send`, es que
Aladin no está conectado a ese hub.

**`plot_cmd` dice que la columna no existe.** El mensaje lista las columnas del CSV. Usá
`"A-B"` para graficar la diferencia de dos columnas.

## Estructura

```
aladin_mcp/
  __init__.py   # redirige los cachés a esta carpeta (antes de importar astropy)
  config.py     # espejos, timeouts, alias de surveys verificados
  mirrors.py    # reintento por espejos y mensajes de error legibles
  cds.py        # SIMBAD, VizieR, búsqueda de HiPS
  imaging.py    # hips2fits / SkyView, PNG, medición de tamaño
  plotting.py   # diagrama color-magnitud
  samp.py       # envío de scripts a Aladin
  server.py     # definición de las herramientas MCP
```
