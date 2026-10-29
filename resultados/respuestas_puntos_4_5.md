# Astronomía para Todos – Taller de magnitudes: puntos 4 y 5

Fechas de los datos: 28 y 29 de octubre de 2026. Todas las figuras y tablas citadas están en esta carpeta
(`resultados/`). Los scripts que las generan están en `resultados/scripts/`.

## Estado de los servicios y fuentes de datos (léase primero)

Durante todo el trabajo **los servidores del CDS de Estrasburgo no respondieron**: SIMBAD, VizieR,
Aladin/alasky y MocServer daban tiempo de espera agotado, también el 29/10. Por eso:

| Dato | Fuente prevista | Fuente usada |
|---|---|---|
| SIMBAD (LMC, 30 Dor, NGC 4755) | simbad.cds.unistra.fr | Espejo de Harvard (simbad.harvard.edu): misma base de datos |
| Imágenes | HiPS del CDS (hips2fits) | NASA SkyView: Mellinger R/G/B (óptico), AKARI WIDE-L (140 µm), Planck 857 GHz y 30 GHz, Fermi bandas 1–5 |
| Catálogo J/AJ/138/1003 | VizieR | Tabla 3 legible por máquina del artículo original en *The Astronomical Journal* (es la misma tabla que publica VizieR) |
| Tamaño RC3 de la LMC | — | NED (NASA/IPAC Extragalactic Database) |
| Fotometría del cúmulo NGC 4755 | VizieR | Gaia DR3 directamente desde el archivo de la ESA |

Ningún valor de este documento fue inventado: cada número sale de un archivo de esta carpeta o de una
referencia citada con su código bibliográfico (*bibcode*).

---

## Punto 4. La Gran Nube de Magallanes (LMC)

### 4.0 Datos de referencia

| Propiedad | Valor | Fuente |
|---|---|---|
| Nombre en SIMBAD | NAME LMC (tipo: galaxia) | `punto4/simbad_LMC.json` |
| Coordenadas (J2000) | AR 05h 23m 34.6s, Dec −69° 45′ 22″ | SIMBAD |
| Tamaño angular (SIMBAD) | 322.8′ × 274.8′ = **5.38° × 4.58°** | SIMBAD (2014MNRAS.445..881C, óptico) |
| Tamaño angular (RC3, D₂₅) | 645.7′ × 549.5′ = **10.76° × 9.16°** | RC3, de Vaucouleurs et al. 1991 (1991RC3.9.C...0000d), consultado en NED |
| Magnitud V integrada | 0.4 ± 0.1 | SIMBAD |
| Distancia | 50 kpc (varias mediciones: Cefeidas, etc.) | SIMBAD (p. ej. 2020ApJ...893...47D) |
| Nebulosa de la Tarántula (NAME 30 Dor Nebula) | 40′ × 25′, centro AR 05h 38m 36s, Dec −69° 05′ 11″ | SIMBAD (1976MmRAS..81...89D, óptico) |

¿Por qué dos tamaños tan distintos? El de RC3 (D₂₅) se mide hasta donde el brillo superficial cae a
**25 magnitudes por segundo de arco cuadrado** en el filtro B: una isofota muy débil que incluye el
**disco externo tenue** de la LMC. El de SIMBAD corresponde a la parte brillante (barra y disco interno).

### 4.1 Imágenes en cuatro bandas (más radio de verdad)

Campo de 20° × 20° centrado en la LMC (proyección TAN):

| Banda | Archivo | Qué traza |
|---|---|---|
| Óptico (Mellinger, color) | `punto4/LMC_optico_Mellinger_color_20deg.png` | Luz de estrellas: se ve la **barra** alargada y el disco |
| Infrarrojo lejano (AKARI, 140 µm) | `punto4/LMC_infrarrojo_AKARI140um_20deg.png` | Polvo frío (~20–30 K) calentado por estrellas |
| Submilimétrico (Planck, 857 GHz ≈ 350 µm) | `punto4/LMC_radio_Planck857GHz_20deg.png` | Polvo aún más frío; también polvo de nuestra galaxia en primer plano |
| Radio (Planck, 30 GHz ≈ 1 cm) | `punto4/LMC_radio_Planck030GHz_20deg.png` | Gas ionizado (emisión libre-libre) y electrones relativistas (sincrotrón) |
| Rayos gamma (Fermi, 3–300 GeV) | `punto4/LMC_gamma_Fermi3-300GeV_20deg.png` | Rayos cósmicos que chocan con el gas interestelar |

**Nota sobre "radio (PLANCK)":** el canal de 857 GHz de Planck no es radio sino **submilimétrico**: lo
que se ve es emisión térmica de polvo. Por eso también se descargó el canal de **30 GHz** del
instrumento LFI, que sí es radio; en él la LMC se ve claramente, dominada por 30 Doradus.

La imagen DSS2 roja de SkyView (`punto4/LMC_optico_DSS2red_20deg.png`) se conserva solo como ejemplo:
es un mosaico de placas fotográficas con escalones de brillo y no sirve para medir.

Los FITS para abrir en Aladin están en `punto4/` (por ejemplo,
`LMC_optico_Mellinger_luminancia_20deg.fits` para la medida óptica manual).

**Cómo hacerlo a mano en Aladin Desktop** (cuando el CDS responda):
1. Escriba `LMC` en el campo de comando de la parte superior y presione Enter.
2. En el árbol de datos de la izquierda busque el survey y haga doble clic: "DSS2 color" o
   "Mellinger color", "AKARI FIS color", "PLANCK R2 HFI color" (y "PLANCK R2 LFI" para 30 GHz) y
   "Fermi color".
3. Haga zoom hasta un campo de unos 20° (rueda del ratón o comando `zoom 20deg`).
4. Si el CDS no responde, use **File → Open** y abra los `.fits` de `resultados/punto4/`.

### 4.2 (a) Diámetro angular en cada imagen

#### Método automático (herramienta `measure_angular_size`)
1. Se suaviza la imagen con un filtro gaussiano para borrar estrellas individuales y ruido. Por
   defecto, σ = 1 % del ancho de la imagen; en Fermi, **σ = 0.5°**, comparable a la resolución (PSF)
   del telescopio.
2. Se estiman el **fondo** y el **ruido** (σ) del cielo con estadística robusta (*sigma-clipping* a 3σ).
3. Se define un **umbral** = fondo + N·σ (aquí N = 2, 3 y 5) y se marcan los píxeles que lo superan.
4. Se elige la región conectada que contiene el centro de la imagen: ese es el **contorno** (cian en
   las figuras `punto4/medida_*.png`).
5. Con la escala de píxel del sistema de coordenadas (WCS) se calcula:
   - el **diámetro equivalente**: el de un círculo de igual área, D = 2·√(área/π);
   - los **ejes mayor y menor** de la elipse que tiene la misma distribución de píxeles.

#### Resultados (umbral 3σ como valor principal)

| Banda | D equiv. 2σ | **D equiv. 3σ** | D equiv. 5σ | Ejes a 3σ | Comentario |
|---|---|---|---|---|---|
| Óptico (Mellinger) | 4.45° | **3.25°** | 1.78° | 4.87° × 2.42° | A 3σ encierra la barra; a 2σ, barra + disco interno |
| Infrarrojo AKARI 140 µm | 6.50° | **5.98°** | 4.92° | 6.98° × 5.51° | El contorno abraza toda la galaxia |
| Submm Planck 857 GHz | 5.59° | **4.51°** | 3.09° | 6.14° × 4.54° | Con cautela: hay polvo de la Vía Láctea alrededor |
| Radio Planck 30 GHz | 6.17° | **5.11°** | 3.78° | 5.66° × 5.39° | Dominado por 30 Doradus y regiones HII |
| Gamma Fermi 3–300 GeV (σ = 0.5°) | 5.18° | **3.86°** | 2.97° | 5.10° × 3.08° | **Cota superior**: el suavizado ensancha la mancha |
| Referencia SIMBAD (óptico) | — | 5.38° × 4.58° | — | — | Parte brillante |
| Referencia RC3 D₂₅ (óptico, B) | — | 10.76° × 9.16° | — | — | Incluye el disco externo débil |

Figura resumen: `punto4/panel_medidas_umbral3.png`. Datos completos: `punto4/medidas_diametro.json`.

**Sensibilidad al umbral (datos reales de la tabla):** bajar de 3σ a 2σ agranda el diámetro entre
**+9 % (AKARI) y +37 % (óptico)**: +21 % en Planck 30 GHz, +24 % en Planck 857 GHz y +34 % en Fermi.
Subir a 5σ lo achica entre −18 % y −45 %.

**Sobre Fermi.** Sin suavizar, el mapa de 3–300 GeV es casi todo ruido de fotones y el contorno a 3σ
no seguía a la galaxia: esa medida se descartó. Se probaron dos cosas:
- **Suavizado de σ = 0.5° y 1°.** La LMC aparece como una mancha compacta, con señal/ruido de 16 en
  3–300 GeV y de 14 en 1–3 GeV.
- **Otras bandas de energía.** En 30–100 MeV y 100–300 MeV (Fermi 1 y 2) la LMC **no se detecta**: la
  resolución es peor y domina el fondo de la Vía Láctea. En 0.3–1 GeV y 1–3 GeV sí aparece con la misma
  forma, y en 1–3 GeV el diámetro a 3σ es 4.06°, muy cercano a 3.86°.

Que la mancha aparezca en tres bandas independientes indica que es emisión real. Aun así, el diámetro
gamma es una **cota superior aproximada**: el suavizado lo ensancha (σ = 0.5° equivale a un ancho a
media altura de 1.2°).

**Nebulosa de la Tarántula (30 Doradus)**, imagen DSS2 roja de 1.5°:

| Umbral | D equivalente | Ejes |
|---|---|---|
| 2σ | 15.8′ | 18′ × 14′ |
| **3σ** | **13.7′** | 16′ × 13′ |
| 5σ | 9.0′ | 10′ × 8′ |
| Referencia SIMBAD | 40′ × 25′ | — |

La medida automática capta el **núcleo brillante** de 30 Dor (~14′); los filamentos externos que dan
los 40′ de SIMBAD son más débiles. Además, una costura entre placas fotográficas cruza la imagen justo a
la derecha de la nebulosa. Para 30 Dor es mejor la medida manual en Aladin.

#### Tamaño físico (aproximación de ángulo pequeño)

Para ángulos pequeños, **D = d · θ**, con θ en radianes (θ[rad] = θ[°] · π/180) y d = 50 kpc:

| Objeto | θ | θ en radianes | D = 50 kpc · θ |
|---|---|---|---|
| LMC, AKARI 3σ | 5.98° | 5.98 × π/180 = 0.1044 | **5.2 kpc** |
| LMC, Planck 30 GHz 3σ | 5.11° | 0.0892 | **4.5 kpc** |
| LMC, Planck 857 GHz 3σ | 4.51° | 0.0787 | **3.9 kpc** |
| LMC, Fermi 3σ (cota superior) | 3.86° | 0.0674 | **3.4 kpc** |
| LMC, óptico Mellinger 3σ (barra) | 3.25° | 0.0567 | **2.8 kpc** |
| LMC, SIMBAD (eje mayor) | 5.38° | 0.0939 | **4.7 kpc** |
| LMC, RC3 D₂₅ (eje mayor) | 10.76° | 0.1878 | **9.4 kpc** |
| 30 Dor, SIMBAD | 40′ = 0.667° | 0.01164 | **0.58 kpc** (≈ 580 pc) |
| 30 Dor, núcleo medido 3σ | 13.7′ = 0.228° | 0.00399 | **0.20 kpc** (≈ 200 pc) |

(1 kpc ≈ 3260 años luz.)

#### ¿Por qué el tamaño cambia con la longitud de onda?

Porque **cada banda ve un componente distinto de la galaxia**:
- **Óptico**: luz de estrellas. Domina la **barra** central; el disco externo es débil y se pierde
  contra el fondo de estrellas de la Vía Láctea, por eso el diámetro óptico depende tanto del umbral
  (de 3.3° a 10.8° según dónde se corte).
- **Infrarrojo lejano (AKARI)**: **polvo frío** calentado por estrellas jóvenes, repartido por todo el
  disco y las regiones de formación estelar. Es la banda donde la LMC se ve **más grande** (~6°).
- **Submilimétrico (Planck 857 GHz)**: polvo **aún más frío**. Sigue la misma estructura, pero los
  **cirros de polvo de nuestra galaxia** en primer plano obligan a un umbral más alto y achican el
  contorno (~4.5°).
- **Radio (Planck 30 GHz)**: gas ionizado alrededor de estrellas jóvenes masivas y electrones de alta
  energía. Concentrado en las regiones de formación estelar, sobre todo 30 Doradus (~5.1°).
- **Rayos gamma (Fermi)**: rayos cósmicos (acelerados por supernovas) que chocan con el gas. Pocos
  fotones y mala resolución: se ve una mancha más compacta (~3.9°, cota superior), con el máximo cerca
  de 30 Doradus.

Conclusión: **no existe un único "diámetro de la LMC"**. Depende de qué componente se mire y de dónde se
corte (el umbral).

#### Procedimiento manual en Aladin (para verificar)
1. Cargue la imagen (survey o FITS) y centre en la LMC.
2. Ajuste el contraste con la herramienta **Pixel** (o el histograma) para que el borde de la galaxia
   se vea nítido contra el fondo; anote qué corte usó.
3. Elija la herramienta **Dist** (regla) de la barra de herramientas de la derecha.
4. Haga clic en un borde de la emisión y arrastre hasta el borde opuesto a lo largo del **eje mayor**:
   Aladin muestra la distancia angular (en ° o ′).
5. Repita a lo largo del **eje menor** (perpendicular).
6. Haga lo mismo en todas las bandas **con el mismo criterio de borde**, y para 30 Dor con un campo de
   ~1.5°.
7. Anote los valores en `punto4/medidas_manuales.csv` y ejecute
   `python resultados/scripts/comparar_medidas.py`: genera una tabla y una figura que comparan sus
   medidas con las automáticas y con SIMBAD.

### 4.3 (b) Estrellas masivas de Bonanos et al. (2009) y diagrama V vs B−V

#### El catálogo
"Spitzer SAGE Infrared Photometry of Massive Stars in the Large Magellanic Cloud", Bonanos et al.
2009, AJ 138, 1003 (VizieR J/AJ/138/1003). La **Tabla 3** contiene la fotometría de 0.3 a 24 µm de
**1268 estrellas masivas**. Sus columnas son:

| Columnas | Contenido |
|---|---|
| `Name`, `IRAC`, `RAdeg`, `DEdeg` | Nombre, designación de Spitzer, coordenadas J2000 |
| `Umag`, `Bmag`, **`Vmag`**, `Imag` (+ errores `e_…`) | Fotometría óptica U, B, V, I |
| `VOGLEmag`, `IOGLEmag` | V e I del sondeo OGLE |
| `Jmag`, `Hmag`, `Kmag`, `JIRSFmag`… | Infrarrojo cercano (2MASS, IRSF) |
| `3.6mag` … `24mag` | Infrarrojo medio (Spitzer IRAC y MIPS) |
| `Ref`, `CandC` | Referencia y **clasificación espectral** |

**No existe una columna B−V**: se calcula como **B−V = Bmag − Vmag**. Hay 1135 estrellas con B y V.

**Control de calidad.** 35 estrellas (3 %) tienen B−V < −0.5 o > 2.5. Ni una estrella muy caliente baja
de un color intrínseco de B−V ≈ −0.33. El corte se puso en −0.5 y no en −0.33 para dejar un **margen
por los errores fotométricos**: en este catálogo el error de B−V (errores de B y V sumados en
cuadratura) tiene una mediana de 0.05–0.07 mag y un 10 % de las estrellas supera 0.12–0.21 mag. El margen
de ~0.17 mag evita descartar estrellas reales por un error de medida. Más allá de ese margen, lo más probable es que B y
V vengan de mediciones o épocas distintas, o de estrellas mezcladas en campos poblados. Se marcaron
con `BV_plausible = False` y se graficaron aparte (cruces grises); **no se borraron**.

#### Archivos
- `punto4/Bonanos2009_LMC_V_BV.csv`: nombre, coordenadas, B, V, B−V, calidad y clase espectral.
- `punto4/Bonanos2009_LMC_V_BV.xlsx`: hoja `datos` (1100 estrellas válidas), hoja
  `descartadas_BV_implausible` (35) y hoja `grafico` con un gráfico de dispersión de Excel y el
  **eje V invertido**.
- `punto4/Bonanos2009_LMC_V_vs_BV.png`: diagrama V vs B−V coloreado por clase espectral, con las
  zonas caliente y fría señaladas.
- `punto4/Bonanos2009_sobre_optico.png` y `Bonanos2009_sobre_AKARI.png`: las estrellas sobre las imágenes.
- `punto4/Bonanos2009_LMC_para_Aladin.xml`: VOTable para cargar en Aladin.

#### Cómo hacerlo a mano en Aladin
1. Con la imagen óptica de la LMC abierta, vaya a **File → Load catalog → VizieR** (o escriba en la
   consola de Aladin `get VizieR(J/AJ/138/1003) LMC 5deg`).
2. Elija la tabla 3 (fotometría). Las estrellas aparecen como símbolos sobre la imagen.
3. Seleccione el plano del catálogo y abra la tabla de mediciones (abajo). Desde ahí puede exportar a
   CSV, o abrir la herramienta de gráficos de Aladin y poner Vmag en el eje Y y una columna calculada
   Bmag − Vmag en el eje X. Los nombres exactos de los menús cambian entre versiones de Aladin;
   verifíquelos en la suya.
4. Si VizieR no responde: **File → Open** y elija `punto4/Bonanos2009_LMC_para_Aladin.xml`.

#### Dónde están las estrellas (figura `Bonanos2009_sobre_optico.png`)
Las 1100 estrellas se concentran en la **barra** y en las regiones de formación estelar del disco,
sobre todo en **30 Doradus**, donde hay una densa agrupación de estrellas azules y también rojas.

### 4.4 (c) ¿Dónde están las estrellas más frías y las más calientes?

Valores medidos en el diagrama (`punto4/Bonanos2009_resumen_por_clase.csv`):

| Clase espectral | N | B−V medio | Rango B−V |
|---|---|---|---|
| O | 316 | −0.05 | −0.48 a 1.62 |
| Wolf-Rayet | 78 | −0.06 | −0.46 a 1.03 |
| B | 582 | −0.03 | −0.50 a 2.30 |
| LBV (variable luminosa azul) | 1 | +1.07 | — |
| A | 8 | +0.34 | 0.02 a 1.62 |
| F | 3 | +0.06 | −0.27 a 0.60 |
| G | 1 | +1.50 | — |
| K | 18 | +1.66 | 1.15 a 2.01 |
| M | 86 | +1.76 | 0.55 a 2.41 |
| Sin clase en el catálogo | 7 | +1.20 | −0.24 a 1.97 |
| **Total** | **1100** | | |

**a) Las estrellas de superficie más fría están a la DERECHA del diagrama** (B−V grande, entre +1.2 y
+2.4). Son **supergigantes rojas** de tipo K y M. Aparecen arriba, entre V = 11 y 14, porque son
enormes y muy luminosas aunque su superficie esté a solo ~3500–4500 K.

**b) Las más calientes están a la IZQUIERDA** (B−V ≈ 0 o negativo). Son estrellas **O, B tempranas y
Wolf-Rayet**, con superficies de 20 000 a más de 40 000 K. Entre las más brillantes hay **supergigantes
azules**.

**¿Por qué?**
1. **B−V mide el color.** B es el brillo en el filtro azul (~440 nm) y V en el visual o verde-amarillo
   (~550 nm). Como la escala de magnitudes es "al revés" (más brillante = número menor):
   - si la estrella emite **más en azul** que en V, Bmag < Vmag → **B−V negativo** → estrella azul;
   - si emite **más en V (rojo)**, Bmag > Vmag → **B−V grande** → estrella roja.
2. **Ley de Wien**: el máximo de emisión de un cuerpo negro está en λ_max = b/T, con
   b = 2.898 × 10⁻³ m·K.
   - Para T = 30 000 K: λ_max = 2.898 × 10⁻³ / 30 000 = 9.7 × 10⁻⁸ m = **97 nm** (ultravioleta).
     La estrella brilla más en B que en V → B−V < 0.
   - Para T = 3 500 K: λ_max = 2.898 × 10⁻³ / 3 500 = 8.3 × 10⁻⁷ m = **828 nm** (infrarrojo
     cercano). Brilla mucho más en V que en B → B−V grande.
3. **Magnitud aparente ≈ luminosidad.** Todas las estrellas están a la misma distancia (50 kpc), así
   que el eje V ordena por **luminosidad real**: el módulo de distancia es
   m − M = 5·log₁₀(d / 10 pc) = 5·log₁₀(5000) = 18.5. Una estrella con V = 11 tiene M_V ≈ −7.5 (sin
   corregir por polvo): son estrellas decenas de miles de veces más luminosas que el Sol.

**Efecto del enrojecimiento por polvo.** El polvo interestelar absorbe más la luz azul que la roja,
así que **aumenta B−V**: las estrellas se ven más rojas de lo que son. En el diagrama se ve: las
estrellas O deberían tener un color intrínseco cercano a (B−V)₀ ≈ −0.3, pero su promedio observado es
−0.05. La diferencia, un **exceso de color E(B−V) ≈ 0.25 mag**, se debe al polvo de la Vía Láctea en la
línea de visión y al polvo propio de la LMC. Por eso hay estrellas O y B dispersas hacia B−V > 0.5:
están detrás de mucho polvo, no son "frías".

---

## Punto 5. La edad de los cúmulos abiertos: la Caja de Joyas (NGC 4755)

### 5.0 Datos de SIMBAD y de la literatura

| Propiedad | Valor | Fuente |
|---|---|---|
| Tipo | Cúmulo abierto (OpC) | SIMBAD |
| Coordenadas (J2000) | AR 12h 53m 39.6s, Dec −60° 22′ 16″ (Cruz del Sur) | SIMBAD |
| Tamaño angular | **10.3′** | SIMBAD |
| Paralaje (Gaia) | 0.462 ± 0.002 mas | SIMBAD |
| Distancia | **1.89 ± 0.07 kpc** (2021MNRAS.504..356D); 1.97–1.99 kpc (otros estudios) | SIMBAD |

La paralaje invertida (1/0.462 mas = 2.16 kpc) es una estimación ingenua que ignora el error de punto
cero de Gaia; se prefieren las distancias publicadas.

**Edad según la literatura** (SIMBAD no registra edades). Las tres referencias se verificaron en el
texto completo y en Crossref:

| Referencia | Bibcode | Edad | Método |
|---|---|---|---|
| Sanner, Brunzendorf, Will & Geffert 2001, *Photometric and kinematic studies of open star clusters. III. NGC 4103, NGC 5281, and NGC 4755*, A&A 369, 511–526 | 2001A&A...369..511S | **10 ± 5 Ma** | Ajuste de isócronas a la secuencia principal superior (su tabla 16) |
| Bonatto, Bica, Ortolani & Barbuy 2006, *Detection of Ks-excess stars in the 14 Myr open cluster NGC 4755*, A&A 453, 121–132 | 2006A&A...453..121B | **14 ± 2 Ma** | Isócronas de Padova, fotometría 2MASS |
| Piskunov, Belikov, Kharchenko, Sagar, Subramaniam et al. 2004, *On the determination of age and mass functions of stars in young open star clusters from the analysis of their luminosity functions*, MNRAS 349, 1449–1463 | 2004MNRAS.349.1449P | **16 Ma** (log t = 7.2 ± 0.2) | Ajuste de la función de luminosidad (edad de "encendido") |

(Ma = millones de años.)

**Estrellas más brillantes** (SIMBAD, a menos de 5.4′ del centro; `punto5/NGC4755_estrellas_brillantes_SIMBAD.csv`):

| Estrella | Tipo espectral (SIMBAD) | V | B−V |
|---|---|---|---|
| HD 111904 | B9 Iab (supergigante azul) | 5.77 | 0.28 |
| κ Cru (Kappa Crucis) | B5 I (supergigante azul) | 5.94 | 0.18 |
| HD 111990 | B1.5 I (supergigante azul) | 6.78 | 0.17 |
| BU Cru | B2 Ib (supergigante azul) | 6.84 | 0.20 |
| **DU Cru** | **M2 Iab (supergigante ROJA)** | 7.66 | **2.16** |
| CC Cru | B2 III (gigante azul) | 7.83 | 0.17 |
| CPD −59 4552 | B1 III | 8.24 | 0.10 |
| CN Cru | B1 V | 8.58 | 0.11 (paralaje 0.07 mas: estrella de fondo, **no** es miembro) |
| BV Cru | OB | 8.60 | 0.20 |

Figura: `punto5/NGC4755_DSS2red_estrellas_identificadas.png` (imagen DSS2 roja de 20′ con cada estrella
marcada). Comparada con la foto del taller, la orientación coincide (norte arriba):
- la **estrella naranja** de la foto es **DU Cru**;
- la azul brillante justo debajo a la derecha es **BU Cru**;
- el grupo azul de abajo a la izquierda es **κ Cru** con BV Cru;
- los dos halos grandes de arriba son HD 111990 y HD 111904.

### 5.1 (1) Centro, límite y cuadrado en la foto de la página 2

Figura: `punto5/pagina2_con_X_y_cuadrado.jpg` (ampliada en `punto5/pagina2_cumulo_ampliado.png`).

- **Centro (X roja):** se colocó en el baricentro de las tres concentraciones brillantes del núcleo:
  la estrella naranja (DU Cru), la azul que está debajo (BU Cru) y el grupo de abajo a la izquierda
  (κ Cru). Dos comprobaciones independientes lo respaldan:
  1. el máximo de densidad de estrellas detectadas en la foto queda a ~60 px (≈ 1′) de la X;
  2. el centro que da SIMBAD está justamente entre DU Cru y κ Cru.
- **Límite (círculo amarillo):** radio donde la densidad de estrellas baja al nivel del fondo, ~120 px.
  **Atención:** al comparar distancias entre estrellas conocidas, la foto cubre solo ~6′ de cielo,
  mientras que SIMBAD da 10.3′ para el cúmulo. El límite visible en la foto es el del **núcleo
  brillante**, no el del cúmulo completo.
- **Cuadrado (verde):** lado de 130 px (≈ 2′ de cielo), centrado en la X; contiene el núcleo con DU Cru,
  BU Cru y κ Cru.

**Estimación de color y brillo de las 46 estrellas dentro del cuadrado**
(`punto5/pagina2_tabla_estrellas_cuadrado.csv`, estrellas numeradas en la figura):

| Brillo ↓ / Color → | O | B | A | F1 | F2 | G | K1 | K2 | M |
|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | |
| 2 | | | | | | | | **1** | |
| 3 | | 1 | | | | | | | |
| 4 | | | 1 | | | | | | |
| 5 | | 5 | 2 | | | | | | |
| 6 | | 2 | 1 | | 1 | | | 1 | |
| 7 | | 3 | 7 | 7 | 1 | | 1 | | |
| 8 | | | 3 | 8 | 1 | | | | |
| 9–10 | (no se estimaron: a esta resolución son ruido del papel) | | | | | | | | |

La estrella K2 de brillo 2 es la supergigante roja DU Cru. La K2 de brillo 6 probablemente es un trozo
de su halo anaranjado, no una estrella aparte.

Hoja de trabajo llena: `punto5/hoja_de_trabajo_llena.png` (brillo 1 arriba, 10 abajo; colores O → M).

**Cómo hacer las estimaciones a mano en su hoja:**
1. Coloque una hoja transparente (o papel cebolla) sobre la foto. Marque la X en el centro del grupo
   formado por la estrella naranja y las estrellas azules más brillantes que la rodean.
2. Dibuje un cuadrado de unos 2–2.5 cm de lado centrado en la X (con la foto impresa a este tamaño).
3. Para cada estrella dentro del cuadrado:
   - **Brillo:** compare el tamaño del punto (incluido su halo) con los círculos de la escala 1–10.
     Elija el más parecido. Si duda entre dos, use el número mayor (más débil).
   - **Color:** compare el tono del halo, no del centro, porque en la impresión los centros de las
     estrellas brillantes quedan blancos. Azul intenso → B (u O); blanco azulado → A; blanco → F1;
     amarillento → F2/G; naranja → K; rojo → M.
4. Ponga un punto en la casilla (color, brillo) correspondiente. Las estrellas muy pequeñas se ven
   blancas solo porque la impresión pierde su color: anótelas como "A/F, dudoso" o déjelas fuera.

**Limitaciones:** la foto impresa y fotografiada desatura los colores, las estrellas brillantes se
saturan (sus halos se agrandan) y los colores reales de Gaia muestran que muchas estrellas "blancas"
de la foto son en realidad estrellas B enrojecidas por polvo. Es una estimación **cualitativa**, como
pide el ejercicio.

### 5.2 (2) Edad: comparación con los tres diagramas de referencia

Rasgos de los diagramas de referencia de la página 2:

| Diagrama | Rasgo distintivo |
|---|---|
| Joven (< 100 Ma) | Hay estrellas **muy brillantes y azules** (O, B) arriba a la izquierda; la secuencia principal baja en diagonal hacia la derecha; casi no hay gigantes rojas |
| Intermedio (100–3000 Ma) | La parte superior izquierda está **vacía**: las O/B ya se apagaron. La secuencia principal empieza más abajo (punto de giro en A/F) y aparecen **gigantes rojas** arriba a la derecha |
| Viejo (> 3000 Ma) | Solo queda la parte baja de la secuencia (estrellas G/K débiles) y hay muchas **gigantes rojas** brillantes arriba a la derecha; ninguna estrella azul brillante |

**Nuestro diagrama** (`hoja_de_trabajo_llena.png`) tiene **estrellas B brillantes** (brillo 3–5) arriba
a la izquierda y una secuencia que baja hacia A y F. Se parece al diagrama **joven**. La única estrella
roja brillante (DU Cru) no contradice esto: en un cúmulo de ~10–15 Ma las estrellas **más masivas**
(que evolucionan más rápido) ya agotaron el hidrógeno del núcleo y se volvieron supergigantes. Las demás
estrellas B, algo menos masivas, siguen en la secuencia principal.

**Conclusión: la Caja de Joyas es un cúmulo JOVEN (< 100 millones de años).** La literatura da 10–16
millones de años, de acuerdo con nuestra clasificación.

#### Respaldo con datos reales: diagrama color-magnitud de Gaia DR3

Figura: `punto5/NGC4755_GaiaDR3_CMD.png` (datos en `punto5/NGC4755_GaiaDR3_miembros.csv`).

- Se consultaron 2306 estrellas con G < 18 en un radio de 6′ y se seleccionaron **553 miembros
  probables**: paralaje 0.470 mas (≈ 2.1 kpc) y movimiento propio común (μ_α* = −4.71,
  μ_δ = −1.08 mas/año).
- La **secuencia principal** sube casi vertical, con BP−RP ≈ 0.23 entre G = 8 y G = 11: estrellas B,
  azules en realidad, pero algo enrojecidas por el polvo.
- **El punto de giro está en lo más alto del diagrama.** Las 4 estrellas azules más brillantes
  (G = 5.6–6.8) están **corridas a la derecha**, con BP−RP = 0.35–0.57, y una quinta en G = 7.9 lo está
  levemente (0.33). SIMBAD las clasifica como supergigantes (clase de luminosidad I): son las estrellas
  B más masivas, que **ya están saliendo de la secuencia principal**. Esa zona está marcada en la figura.
- Hay **una sola supergigante roja**, aislada: G = 6.1, BP−RP = 2.79. Es DU Cru, la siguiente etapa de
  esa evolución.

Que el punto de giro esté en estrellas B tan masivas significa que el cúmulo es muy joven: solo las
estrellas más masivas, que viven unos pocos millones de años, han tenido tiempo de evolucionar. Esto
corresponde a **unos 10–15 millones de años** y confirma la conclusión del ejercicio con la foto.

---

## Lista de verificación en Aladin Desktop (lo que usted debe hacer)

Capturas de pantalla sugeridas para el informe:

1. [ ] **LMC en cada banda**: abra los FITS de `resultados/punto4/` (File → Open). Si el CDS ya
   responde, repita con los HiPS en color "DSS2 color" o "Mellinger color", "AKARI FIS Color",
   "PLANCK R2 HFI color", "PLANCK R2 LFI" y "Fermi color".
2. [ ] **Medida manual con la herramienta Dist** de la LMC en cada banda: una captura con la regla sobre
   el eje mayor. Anote los valores en `punto4/medidas_manuales.csv` y ejecute `comparar_medidas.py`.
3. [ ] **Óptico**: mida en `LMC_optico_Mellinger_luminancia_20deg.fits` y compare con SIMBAD (5.38°) y
   RC3 (10.76°). ¿Hasta dónde llega el borde que usted ve?
4. [ ] **30 Doradus**: zoom a ~1.5° y medida con Dist de la nebulosa completa, filamentos incluidos.
   Compare con 40′ × 25′.
5. [ ] **Catálogo de Bonanos sobre la imagen** (`Bonanos2009_LMC_para_Aladin.xml`): captura mostrando
   dónde están las estrellas, sobre todo en la barra y en 30 Dor.
6. [ ] **Gráfico V vs B−V** en la herramienta de gráficos de Aladin, si su versión la tiene. Si no,
   use el Excel `Bonanos2009_LMC_V_BV.xlsx`.
7. [ ] **NGC 4755** en "DSS2 color" con un campo de ~20′: compare con la foto del taller e identifique
   DU Cru (la roja) y κ Cru.
8. [ ] **SIMBAD**: captura de la página de NGC 4755 (coordenadas, tipo OpC, tamaño 10.3′).
9. [ ] **Hoja de trabajo en papel**: hágala usted a mano con el método de 5.1 y compárela con
   `hoja_de_trabajo_llena.png`. Es normal que difiera en una o dos casillas.

## Qué no se pudo hacer o verificar

- Los HiPS del CDS (DSS2 color, Mellinger color, AKARI color, Planck color, Fermi color) no estuvieron
  disponibles: se usaron las versiones de NASA SkyView.
- El diámetro gamma (Fermi) es una cota superior aproximada, porque el suavizado necesario para ver la
  LMC ensancha la mancha.
- VizieR no respondió: el catálogo de Bonanos se tomó del artículo original. Es la misma tabla, pero no
  se pudo comparar fila por fila con la versión de VizieR.
- Los comandos enviados a Aladin por SAMP no devuelven confirmación de que se ejecutaron.
