# Cómo se resolvieron los puntos 4 y 5, paso a paso

Este documento explica en detalle cómo se resolvieron los puntos 4 (Gran Nube de Magallanes) y 5
(Caja de Joyas) del taller *Astronomía para Todos – Taller de ejercicios sobre magnitudes*. Para cada
paso indica:
- de dónde salió cada dato;
- qué parámetros se usaron y por qué;
- todas las cuentas, con sus números;
- qué archivo del repositorio contiene el resultado.

Todas las rutas son relativas a la raíz del repositorio. Los scripts están en `resultados/scripts/` y
se ejecutan con el entorno virtual del proyecto (`.venv/bin/python resultados/scripts/<script>.py`).

---

## 0. Contexto: el CDS estuvo caído y hubo que usar alternativas

El taller está pensado para hacerse con **Aladin** y los servicios del **CDS** (Centro de Datos
Astronómicos de Estrasburgo): SIMBAD para los objetos, VizieR para los catálogos y los HiPS para las
imágenes del cielo. Durante todo el trabajo, del 28 de octubre al 3 de noviembre de 2026, esos
servidores no respondieron.

### Cómo comprobamos que el problema era del CDS y no de nuestra red

1. **Control:** `https://www.google.com` respondía en 0.3 s, así que la conexión a internet funcionaba.
2. **Nombres de dominio (DNS):** `simbad.cds.unistra.fr` resolvía bien a `130.79.128.4`.
3. **Conexión:** la conexión TCP al puerto 443 de los servidores del CDS nunca se establecía; daba
   timeout a los 20 s. Probamos SIMBAD, VizieR, MocServer, hips2fits (alasky y alaskybis), el portal
   `cds.unistra.fr` y Aladin web: los siete fallaban igual.
4. **Desde otras redes:** lo mismo desde la red de la casa (`192.168.1.x`) y desde un hotspot de
   celular (`172.20.10.x`). Desde un servidor externo, la conexión era **rechazada**
   (`ECONNREFUSED 130.79.128.4:443`).
5. **Otro usuario** reportó el mismo problema el 29/10/2026 en un issue público de GitHub.

### Alternativas usadas

| Lo que pide el taller | Fuente prevista | Alternativa usada | Por qué funciona |
|---|---|---|---|
| Datos de objetos (SIMBAD) | `simbad.cds.unistra.fr` | Espejo de la Universidad de Harvard, `simbad.harvard.edu` | Es una copia completa de la misma base de datos |
| Imágenes DSS, AKARI, Planck, Fermi | HiPS del CDS (Aladin / hips2fits) | NASA SkyView, `skyview.gsfc.nasa.gov` | Distribuye los mismos surveys desde la infraestructura de la NASA |
| Catálogo de Bonanos et al. (VizieR) | VizieR J/AJ/138/1003 | Tabla 3 en formato legible por máquina (MRT), publicada por la revista (IOP) | Es la tabla original que VizieR redistribuye |
| Tamaño RC3 de la LMC | — | NED (NASA/IPAC Extragalactic Database), `ned.ipac.caltech.edu` | Tiene los diámetros de RC3 por objeto |

El espejo de VizieR en Harvard (`vizier.cfa.harvard.edu`) no sirvió como alternativa: conectaba, pero
devolvía `504 Gateway Time-out` porque reenvía las consultas a Estrasburgo.

---

# Punto 4: la Gran Nube de Magallanes (LMC)

## 4.1 Datos de referencia

### SIMBAD (espejo de Harvard)

Se consultó el objeto `LMC`. Resultado guardado en `resultados/punto4/simbad_LMC.json`.

| Dato | Valor | Campo de SIMBAD |
|---|---|---|
| Nombre principal | NAME LMC | `main_id` |
| Tipo | Galaxia (G) | `otype` |
| Coordenadas (J2000) | AR 05h 23m 34.6s, Dec −69° 45′ 22″ (80.894167°, −69.756111°) | `ra`, `dec` |
| Tamaño angular | 322.8′ × 274.8′, ángulo de posición 170° | `galdim_majaxis`, `galdim_minaxis`, `galdim_angle` |
| Origen del tamaño | 2014MNRAS.445..881C, en óptico | `galdim_bibcode`, `galdim_wavelength` |
| Distancia | 50 kpc (varias mediciones, por ejemplo 2020ApJ...893...47D) | tabla `mesDistance` |

Conversión del tamaño a grados (1° = 60′):
- 322.8′ / 60 = **5.38°**
- 274.8′ / 60 = **4.58°**

Para la **Nebulosa de la Tarántula** se consultó `NAME 30 Dor Nebula`
(`resultados/punto4/simbad_30Dor_Nebula.json`): centro 84.65°, −69.0864°, tamaño **40′ × 25′**
(referencia 1976MmRAS..81...89D, en óptico). El nombre `30 Dor` a secas resuelve al cúmulo central
R136, que no tiene tamaño en SIMBAD.

### Una trampa de SIMBAD que encontramos

Si se piden las magnitudes (por ejemplo V) en la misma consulta que los datos básicos, la base hace
una unión estricta y **los objetos sin esa magnitud desaparecen del resultado**. NGC 4755 no tiene V en
SIMBAD y salía como "inexistente". Por eso los datos básicos, las magnitudes y las distancias se
consultaron por separado.

### RC3 en NED

En NED, la sección *Diameters* de la LMC trae, para RC3 (de Vaucouleurs et al. 1991, código
`1991RC3.9.C...0000d`):
- log D₂₅ = 3.81, en unidades de 0.1′: D₂₅ = 10^3.81 / 10 = 6457 / 10 = **645.7′**
- valores en segundos de arco de NED: 38 739.2″ × 32 967.06″
- 38 739.2″ / 60 = **645.7′ = 10.76°**; 32 967.06″ / 60 = **549.5′ = 9.16°**

D₂₅ se mide hasta la isofota de 25 mag/arcsec² en el filtro B, un nivel de brillo muy débil. Por eso
incluye el disco externo de la galaxia y es casi el doble que el tamaño de SIMBAD.

## 4.2 Descarga de las imágenes

Todas centradas en la LMC (80.894167°, −69.756111°), con proyección gnomónica (TAN), descargadas de
NASA SkyView con `astroquery.skyview`. Scripts: `p4_descargas_extra.py` (Mellinger, Fermi 1–4,
Planck 30 GHz) y la herramienta `get_survey_image` (AKARI, Planck 857 GHz, Fermi 5, DSS2 roja,
30 Doradus).

| Banda | Survey de SkyView | Campo | Píxeles | Escala | Archivo FITS (`resultados/punto4/`) |
|---|---|---|---|---|---|
| Óptico | Mellinger Red, Green y Blue | 20° | 600 × 600 | 0.0333°/px = 120″/px | `LMC_optico_Mellinger{Red,Green,Blue}_20deg.fits` y `..._luminancia_20deg.fits` |
| Óptico (descartado) | DSS2 Red | 20° | 800 × 800 | 0.025°/px = 90″/px | `LMC_optico_DSS2red_20deg.fits` |
| Infrarrojo lejano | AKARI WIDE-L (140 µm) | 20° | 600 × 600 | 120″/px | `LMC_infrarrojo_AKARI140um_20deg.fits` |
| Submilimétrico | Planck 857 I | 20° | 600 × 600 | 120″/px | `LMC_radio_Planck857GHz_20deg.fits` (MJy/sr) |
| Radio | Planck 030 I | 20° | 400 × 400 | 0.05°/px = 180″/px | `LMC_radio_Planck030GHz_20deg.fits` (K) |
| Rayos gamma | Fermi 5 (3–300 GeV) | 20° | 400 × 400 | 180″/px | `LMC_gamma_Fermi3-300GeV_20deg.fits` |
| Rayos gamma (pruebas) | Fermi 1, 2, 3, 4 | 20° | 400 × 400 | 180″/px | `LMC_gamma_Fermi{1,2,3,4}_20deg.fits` |
| 30 Doradus | DSS2 Red | 1.5° | 600 × 600 | 0.0025°/px = 9″/px | `30Dor_optico_DSS2red_1.5deg.fits` |

Por qué se eligió cada una:
- **20° de campo**: la LMC mide unos 10° en su parte débil (RC3), y hace falta cielo alrededor para medir
  el fondo. Con 20° el objeto ocupa como mucho la mitad del campo.
- **Mellinger en lugar de DSS**: el DSS2 de SkyView para un campo de 20° es un mosaico de placas
  fotográficas tomadas en noches distintas, pegadas sin igualar su fondo. Quedan escalones
  rectangulares de brillo (`LMC_optico_DSS2red_20deg.png`), y la medida automática siguió el borde de una
  placa en vez de la galaxia (dio 2.82°, que no corresponde a la LMC). Mellinger (Mellinger 2009) es un
  mosaico óptico de todo el cielo, continuo y en color, con 36″/px de resolución propia.
- **Imagen de luminancia de Mellinger**: para medir se usó el promedio de los tres canales (rojo, verde
  y azul), en un solo plano. La imagen en color (`LMC_optico_Mellinger_color_20deg.png`) es solo para
  mostrar.
- **Planck 30 GHz además de 857 GHz**: el enunciado dice "radio (PLANCK)". El canal de 857 GHz
  (≈ 350 µm) es submilimétrico y muestra emisión térmica de polvo, no radio. El de 30 GHz (≈ 1 cm) sí
  es radio: gas ionizado (emisión libre-libre) y electrones relativistas (sincrotrón).
- **Varias bandas de Fermi**: el mapa de 3–300 GeV sin procesar es casi solo ruido de fotones sueltos,
  así que se probaron las otras bandas (ver 4.3).

Detalle técnico: la cabecera FITS de Mellinger trae un tabulador dentro de un comentario, lo que no es
FITS válido, y astropy se negaba a guardarla. Se limpiaron esos caracteres de los comentarios antes de
guardar; los datos y las coordenadas no cambian.

## 4.3 (a) Diámetro angular: método 1, umbral automático

Script: `p4a_measure.py`, que usa la función `measure_size` de `aladin_mcp/imaging.py`. Resultados en
`resultados/punto4/medidas_diametro.json` y figuras `resultados/punto4/medida_<banda>_umbral<N>.png`.

### Paso a paso

1. **Leer la imagen.** Si tiene tres planos (color), se promedian. Los píxeles sin dato (NaN) se
   reemplazan por la mediana de la imagen.
2. **Suavizar** con un filtro gaussiano de desviación σ_s, para borrar estrellas sueltas y ruido y
   quedarse con la emisión extendida.
   - Por defecto σ_s = 1 % del lado menor de la imagen:
     - imágenes de 600 px: σ_s = 6 px = 6 × 0.0333° = **0.2°**;
     - imágenes de 400 px: σ_s = 4 px = 4 × 0.05° = **0.2°**;
     - 30 Doradus: σ_s = 6 px = 6 × 0.0025° = **0.015°** (0.9′).
   - En Fermi: **σ_s = 0.5° = 10 px**, comparable a la resolución del telescopio (ver más abajo).
3. **Estimar el fondo y su ruido** con estadística robusta: media, mediana y desviación estándar con
   *sigma-clipping* (se descartan iterativamente los píxeles a más de 3σ, hasta 10 veces). El fondo es
   la mediana resultante y el ruido σ, su desviación estándar.
4. **Umbral:** se marcan los píxeles con brillo > fondo + N·σ, con N = 2, 3 y 5. El valor principal es
   N = 3.
5. **Elegir la región:** se agrupan los píxeles marcados en regiones conectadas y se toma la que
   contiene el píxel central de la imagen. Si el centro queda bajo el umbral, se toma la región más
   grande, y esa medida se marca como no confiable porque podría ser otra fuente.
6. **Convertir a grados** con la escala del sistema de coordenadas (WCS) de la imagen:
   - **Diámetro equivalente** (el de un círculo con la misma área A, en píxeles):
     D_eq = 2·√(A/π) × escala.
   - **Ejes mayor y menor**: se calcula la matriz de covarianza de las posiciones (x, y) de los píxeles
     de la región y sus autovalores λ₁ ≥ λ₂. Para una elipse uniforme, la varianza a lo largo de un eje
     es (semieje)²/4, o sea semieje = 2√λ. Entonces:
     eje mayor = 4√λ₁ × escala y eje menor = 4√λ₂ × escala.

### Resultados

| Banda | D_eq 2σ | D_eq 3σ | D_eq 5σ | Ejes a 3σ | ¿Válida? |
|---|---|---|---|---|---|
| Óptico (Mellinger) | 4.454° | **3.249°** | 1.785° | 4.869° × 2.416° | Sí: a 3σ encierra la barra |
| Infrarrojo AKARI | 6.505° | **5.982°** | 4.924° | 6.977° × 5.511° | Sí |
| Submm Planck 857 | 5.595° | **4.506°** | 3.089° | 6.139° × 4.542° | Sí, con cautela (polvo de la Vía Láctea alrededor) |
| Radio Planck 30 GHz | 6.170° | **5.108°** | 3.783° | 5.659° × 5.388° | Sí |
| Gamma Fermi 3–300 GeV (σ_s = 0.5°) | 5.181° | **3.863°** | 2.968° | 5.103° × 3.085° | Cota superior |
| Óptico DSS2 roja | 4.677° | 2.824° | 0.598° | 5.378° × 1.996° | **No**: sigue los escalones entre placas |
| 30 Doradus (DSS2 roja) | 15.8′ | **13.7′** | 9.0′ | 15.5′ × 12.4′ | Solo el núcleo brillante |

Ojo con dos números que parecen contradecirse: para AKARI, el **5.98°** es el diámetro equivalente y el
**6.98°** es el eje mayor. Son dos medidas distintas de la misma región, y el diámetro equivalente
siempre queda entre el eje menor y el mayor.

### Cómo se trató Fermi

En el mapa sin procesar de 3–300 GeV, el contorno a 3σ seguía ruido. Se probaron dos cosas:
1. **Suavizar más:** con σ_s = 0.5° y σ_s = 1° aparece una mancha compacta en la LMC, con el máximo del
   lado de 30 Doradus.
2. **Otras bandas de energía.** Señal/ruido máxima a menos de 3° del centro de la LMC, con σ_s = 0.5°:

| Banda Fermi de SkyView | Energía | S/N | ¿Se detecta la LMC? |
|---|---|---|---|
| Fermi 1 | 30–100 MeV | ≤ 1.2 (1.2 es el máximo de toda la imagen) | No |
| Fermi 2 | 100–300 MeV | 3.6 | Apenas |
| Fermi 3 | 0.3–1 GeV | 8.5 | Sí |
| Fermi 4 | 1–3 GeV | 14.4 | Sí (D_eq 3σ = 4.06°) |
| Fermi 5 | 3–300 GeV | 15.9 | Sí (D_eq 3σ = 3.86°) |

Que la misma mancha aparezca en tres bandas independientes indica que es emisión real. A 5σ, en Fermi 3
y 4 el centro quedó bajo el umbral y el método eligió "la región más grande", así que esas medidas se
descartaron. Se adoptó Fermi 5 con σ_s = 0.5°.

### Sesgo del suavizado (medido con un disco de prueba)

Se probó el método con una imagen artificial: ruido de σ = 1 más un disco uniforme de radio 30 px y
brillo +50 (escala 0.05°/px, diámetro real 3.00°). El test está en `tests/test_core.py`.

| Suavizado σ_s | D_eq medido | Radio extra |
|---|---|---|
| 0 px | 2.997° | 0 |
| 1 px | 3.213° | +2.1 px = 2.13 σ_s |
| 2 px | 3.479° | +4.8 px = 2.39 σ_s |
| 4 px | 4.019° | +10.2 px = 2.55 σ_s |
| 8 px | 5.148° | +21.5 px = 2.68 σ_s |

Sin suavizado el método es exacto. Con suavizado, el borde de una fuente brillante se corre hacia
afuera entre 2 y 3 σ_s, porque el umbral (3σ del ruido ya suavizado) queda muy por debajo del brillo
del objeto. La teoría lo predice: un borde abrupto suavizado se desplaza σ_s·Φ⁻¹(1 − umbral/amplitud),
donde Φ⁻¹ es la inversa de la función de distribución normal; aquí da ≈ 2.4 σ_s, igual que lo medido.

Consecuencia: en Fermi (σ_s = 0.5°) el diámetro puede estar inflado hasta ~2.5° en el peor caso. Por
eso se reporta como cota superior.

## 4.4 (a) Diámetro angular: método 2, perfil a lo largo de los ejes

Este método imita la medida con la herramienta de distancia (regla) de Aladin, y es independiente del
anterior. Script: `p4_medidas_perfiles.py`. Resultados en `resultados/punto4/medidas_perfiles.json`,
perfiles en `medidas_perfiles.png` y capturas de Aladin con las reglas en
`resultados/capturas/aladin_regla_*.png`.

### Paso a paso

1. **Centro:** el de SIMBAD (LMC: 80.894167°, −69.756111°; 30 Doradus: 84.65°, −69.0864°), convertido a
   píxeles con el WCS.
2. **Dirección del eje mayor:** a partir de los momentos de brillo de los píxeles que superan el
   fondo + 2σ dentro de un radio de 4.75° (LMC) alrededor del centro. La imagen se filtra antes con una
   mediana de 3 × 3 px para quitar estrellas sueltas. El eje menor es la dirección perpendicular.
3. **Perfil:** a lo largo de cada dirección se toma una franja (largo: ±9.5° para la LMC y ±0.7° para
   30 Doradus; ancho: 0.6°, 1.0° en Fermi y 0.05° en 30 Doradus) y en cada punto se calcula la
   **mediana a través de la franja**, para que una estrella sola no cuente. No hay suavizado 2D.
4. **Cielo de cada lado:** la mediana del 20 % exterior de ese lado del perfil. El ruido sale de la
   desviación absoluta mediana (MAD × 1.4826). Cada lado usa su propio cielo porque la Vía Láctea
   agrega gradientes de fondo.
5. **Nivel de borde (criterio fijado antes de ver los resultados):**
   nivel = cielo + 10 % × (pico − cielo), donde el pico es el máximo del perfil en la mitad central.
6. **Borde:** desde el centro hacia afuera, el último punto por encima del nivel. Se ignoran los huecos
   internos más cortos que 0.5° (2′ en 30 Doradus), porque el ojo salta los huecos entre nubes. El
   perfil se filtra antes con una mediana de 5 puntos.
7. **Validez:** la medida vale si el pico supera al cielo en más de 5 veces el ruido y ambos bordes
   quedan dentro de la regla. Si no, el resultado es "sin borde definido".
8. **Sensibilidad:** se repitió todo con 5 % y 20 % de contraste.

### Por qué este criterio (y no otro)

Antes de fijar el 10 % se probaron tres criterios que fallaron:
- el primero cortaba en huecos internos de la galaxia;
- el segundo se estiraba con los gradientes del fondo;
- el tercero contaba el polvo de nuestra galaxia como parte de la LMC.

En lugar de seguir ajustando parámetros hasta obtener el número esperado (eso sería forzar el
resultado), se fijó un criterio de contraste y se reportó su sensibilidad.

### Resultados

| Banda | Eje mayor (5 % / **10 %** / 20 %) | Eje menor (5 % / **10 %** / 20 %) | Referencia |
|---|---|---|---|
| Óptico (Mellinger) | 13.10° / **11.33°** / 7.53° | 10.17° / **8.27°** / 6.10° | RC3: 10.76° × 9.16° |
| Infrarrojo AKARI | 6.73° / **6.43°** / 5.20° | 6.37° / **4.80°** / 3.23° | — |
| Submm Planck 857 | 6.83° / **6.53°** / 3.27° | 6.43° / **4.03°** / 3.43° (no confiable) | — |
| Radio Planck 30 GHz | 11.70° / **7.10°** / 4.40° | 7.15° / **5.60°** / 5.15° | — |
| Gamma Fermi (mapa crudo) | sin borde definido | sin borde definido | — |
| 30 Doradus | 47.1′ / **37.5′** / 23.9′ | 36.2′ / **30.0′** / 17.0′ | SIMBAD: 40′ × 25′ |

- **Eje menor de Planck 857:** no es confiable. De ese lado, el cielo vecino incluye cirros de polvo de
  la Vía Láctea, más brillantes que el cielo junto a la LMC, y el borde se cortó en un hueco interno.
  Se ve en `resultados/capturas/aladin_regla_planck857.png`.
- **Ejes intercambiados:** en Planck 857 y 30 GHz, el perfil perpendicular a la dirección de los
  momentos resultó más largo, así que se intercambiaron los nombres de los ejes.

### Comparación de los dos métodos

Script `comparar_medidas.py`; resultados en `resultados/punto4/comparacion_medidas.csv` y `.png`.

| Banda | Perfil (eje mayor) | Umbral 3σ (eje mayor) | Diferencia |
|---|---|---|---|
| Óptico | 11.33° | 4.87° | +133 % |
| AKARI | 6.43° | 6.98° | −8 % |
| Planck 857 | 6.53° | 6.14° | +6 % |
| Planck 30 GHz | 7.10° | 5.66° | +26 % |
| 30 Doradus | 37.5′ | 15.5′ | +142 % |

Diferencia = (perfil − umbral) / umbral × 100. Por ejemplo, para el óptico: (11.33 − 4.87) / 4.87 =
1.33, es decir +133 %.

**Lectura:**
- En las bandas con bordes nítidos (AKARI, Planck 857) los dos métodos coinciden dentro del 8 %.
- En el óptico y en 30 Doradus el perfil da más del doble y coincide con los catálogos (RC3 y SIMBAD).
  El umbral de 3σ corta el halo débil, sea el disco externo o los filamentos, y deja solo la barra o el
  núcleo.

### Sensibilidad al umbral en el método 1

Cambio del diámetro equivalente al pasar de 3σ a 2σ (o a 5σ): (D(2σ) / D(3σ) − 1) × 100.
- Óptico: 4.454 / 3.249 − 1 = **+37 %** (a 5σ: −45 %)
- AKARI: 6.505 / 5.982 − 1 = **+9 %** (−18 %)
- Planck 857: **+24 %** (−31 %)
- Planck 30 GHz: **+21 %** (−26 %)
- Fermi: **+34 %** (−23 %)
- 30 Doradus: **+15 %** (−34 %)

## 4.5 (a) Tamaño físico

Para ángulos pequeños, el tamaño físico es **D = d · θ**, con θ en radianes
(θ[rad] = θ[°] × π/180) y d = 50 kpc. Ejemplo completo con el óptico (perfil):
- θ = 11.33° × π/180 = 11.33 × 0.017453 = 0.19775 rad
- D = 50 kpc × 0.19775 = **9.89 kpc**

| Objeto | θ | θ (rad) | D |
|---|---|---|---|
| LMC, óptico, perfil (eje mayor) | 11.33° | 0.19775 | 9.89 kpc |
| LMC, RC3 (eje mayor) | 10.76° | 0.18780 | 9.39 kpc |
| LMC, AKARI, D_eq 3σ | 5.982° | 0.10441 | 5.22 kpc |
| LMC, AKARI, eje mayor 3σ | 6.977° | 0.12177 | 6.09 kpc |
| LMC, SIMBAD (eje mayor) | 5.38° | 0.09390 | 4.70 kpc |
| LMC, SIMBAD (eje menor) | 4.58° | 0.07994 | 4.00 kpc |
| LMC, Planck 30 GHz, D_eq 3σ | 5.108° | 0.08915 | 4.46 kpc |
| LMC, Fermi, D_eq 3σ (cota superior) | 3.863° | 0.06742 | 3.37 kpc |
| 30 Doradus, perfil (eje mayor) | 37.5′ = 0.625° | 0.01091 | 545 pc |
| 30 Doradus, SIMBAD | 40′ = 0.667° | 0.01164 | 582 pc |

## 4.6 (b) Estrellas masivas de Bonanos et al. (2009)

Script: `p4b_bonanos_cmd.py`.

### De dónde salieron los datos
- Artículo: Bonanos et al. 2009, *Spitzer SAGE Infrared Photometry of Massive Stars in the Large
  Magellanic Cloud*, AJ 138, 1003, DOI `10.1088/0004-6256/138/4/1003`. Es el catálogo VizieR
  J/AJ/138/1003.
- Tabla 3 en formato MRT, publicada por la revista:
  `https://content.cld.iop.org/journals/1538-3881/138/4/1003/revision1/aj318206t3_mrt.txt`
  Está guardada en `resultados/punto4/bonanos2009_original/aj318206t3_mrt.txt`.
- La tabla se leyó con `astropy.io.ascii.read(..., format="mrt")`.

### Columnas de la tabla 3 (1268 estrellas)

| Columnas | Contenido |
|---|---|
| `Name`, `IRAC`, `RAdeg`, `DEdeg` | Nombre, designación de Spitzer y coordenadas J2000 en grados |
| `Umag`, `Bmag`, `Vmag`, `Imag` y sus errores `e_…` | Fotometría óptica |
| `VOGLEmag`, `IOGLEmag` | V e I del sondeo OGLE |
| `Jmag`, `Hmag`, `Kmag`, `JIRSFmag`, `HIRSFmag`, `KIRSFmag` | Infrarrojo cercano (2MASS e IRSF) |
| `3.6mag`, `4.5mag`, `5.8mag`, `8.0mag`, `24mag` | Infrarrojo medio (Spitzer IRAC y MIPS) |
| `Ref`, `CandC` | Referencia y clasificación espectral |

### Pasos
1. **Índice de color:** no hay una columna B−V; se calcula **B−V = Bmag − Vmag**. Por ejemplo, para la
   estrella `Sk -69 1`: 13.364 − 13.446 = −0.082.
2. **Filtrar:** de las 1268 estrellas, **1135** tienen B y V.
3. **Control de calidad:** 35 estrellas (3 %) tienen B−V < −0.5 o > 2.5.
   - El color intrínseco más azul posible es B−V ≈ −0.33, así que valores de −2 son imposibles.
   - El corte se puso en −0.5 y no en −0.33 para dejar margen por los errores de medida. Calculando el
     error de B−V como √(e_Bmag² + e_Vmag²), la mediana es 0.05–0.07 mag y un 10 % de las estrellas
     supera 0.12–0.21 mag. El margen de 0.17 mag cubre esos casos.
   - Las 35 estrellas se marcaron con `BV_plausible = False` y se graficaron aparte; **no se borraron**.
     Quedan **1100** estrellas válidas.
4. **Clase espectral:** se tomó la primera letra de `CandC` (O, B, A, F, G, K, M, o los prefijos WN, WC,
   WO y LBV), y WN, WC y WO se agruparon como Wolf-Rayet (WR).
5. **Archivos generados** (`resultados/punto4/`):
   - `Bonanos2009_LMC_V_BV.csv`: nombre, coordenadas, B, V, B−V, calidad y clase.
   - `Bonanos2009_LMC_V_BV.xlsx`, con tres hojas: `datos` (1100), `descartadas_BV_implausible` (35) y
     `grafico`, un diagrama de dispersión de Excel con el eje V invertido.
   - `Bonanos2009_LMC_V_vs_BV.png`: el diagrama coloreado por clase.
   - `Bonanos2009_LMC_para_Aladin.xml`: VOTable para cargar en Aladin.
6. **Verificación del Excel:** se abrió con LibreOffice y se exportó a imagen
   (`resultados/capturas/excel_grafico_V_vs_BV.png`). Eso mostró dos defectos de la primera versión,
   ya corregidos:
   - los marcadores no tenían color definido y se dibujaban blancos sobre blanco;
   - al invertir V, el eje B−V se iba arriba. Se resolvió con `crosses = "max"`.
7. **Localización sobre la imagen:** el VOTable se cargó en Aladin sobre la imagen óptica y se exportó la
   vista (`resultados/capturas/aladin_Bonanos2009_sobre_LMC.png`). Las estrellas se concentran en la barra
   y en 30 Doradus.

## 4.7 (c) Estrellas frías y calientes

### B−V por clase (las 1100 estrellas válidas)

| Clase | N | B−V medio | Mínimo | Máximo |
|---|---|---|---|---|
| O | 316 | −0.05 | −0.48 | 1.62 |
| Wolf-Rayet | 78 | −0.06 | −0.46 | 1.03 |
| B | 582 | −0.03 | −0.50 | 2.30 |
| LBV | 1 | +1.07 | — | — |
| A | 8 | +0.34 | 0.02 | 1.62 |
| F | 3 | +0.06 | −0.27 | 0.60 |
| G | 1 | +1.50 | — | — |
| K | 18 | +1.66 | 1.15 | 2.01 |
| M | 86 | +1.76 | 0.55 | 2.41 |
| Sin clase | 7 | +1.20 | −0.24 | 1.97 |
| **Total** | **1100** | | | |

### Interpretación, con cuentas
- **B y V:** B mide la luz azul (~440 nm) y V la visual (~550 nm). Como la escala de magnitudes es
  inversa, B−V negativo significa que la estrella es más brillante en azul.
- **Ley de Wien:** λ_máx = b/T, con b = 2.898 × 10⁻³ m·K.
  - T = 40 000 K: λ_máx = 2.898 × 10⁻³ / 40 000 = 7.2 × 10⁻⁸ m = **72 nm**
  - T = 30 000 K: **97 nm**
  - T = 20 000 K: **145 nm** (todas en el ultravioleta: más luz en B que en V, B−V < 0)
  - T = 4500 K: **644 nm**
  - T = 3500 K: **828 nm** (rojo e infrarrojo cercano: más luz en V, B−V grande)
- **Magnitud aparente y luminosidad:** todas las estrellas de la LMC están a la misma distancia. El
  módulo de distancia es m − M = 5 log₁₀(d / 10 pc) = 5 log₁₀(50 000 / 10) = 5 × 3.699 = **18.49**. Una
  estrella con V = 11 tiene M_V = 11 − 18.49 ≈ **−7.5**, sin corregir por polvo.
- **Enrojecimiento (análisis complementario):** las estrellas O deberían tener (B−V)₀ ≈ −0.3, y su
  promedio observado es −0.05. El exceso de color es E(B−V) ≈ −0.05 − (−0.3) = **0.25 mag**, por el polvo
  de la Vía Láctea y de la propia LMC.

---

# Punto 5: la Caja de Joyas (NGC 4755)

## 5.1 Datos de SIMBAD

Consulta de `NGC 4755` en el espejo de Harvard (`resultados/punto5/simbad_NGC_4755.json`; captura de la
ficha en `resultados/capturas/simbad_NGC4755.jpg`):

| Dato | Valor |
|---|---|
| Tipo | Cúmulo abierto (OpC) |
| Coordenadas (J2000) | AR 12h 53m 39.6s, Dec −60° 22′ 16″ (193.415°, −60.371111°) |
| Tamaño angular | 10.3′ × 10.3′ |
| Paralaje | 0.462 ± 0.002 mas |
| Movimiento propio | −4.647, −1.134 mas/año |

**Distancias publicadas** (tabla `mesDistance`):
- 1887 ± 68 pc, por paralaje (2021MNRAS.504..356D);
- 1992 pc, por paralaje (2021A&A...651A.104P);
- 1971 pc (2018MNRAS.473..849D);
- 1978 pc (2017AstBu..72..257L);
- 1976 pc, por tipo espectral (2005A&A...438.1163K);
- un valor discrepante de 3436 pc (2010MNRAS.403.1491P).

**Distancia por paralaje directa:** d = 1/p = 1 / 0.000462″ = **2164 pc**. Es más que los valores
publicados porque invertir la paralaje ignora el error de punto cero de Gaia; por eso se prefieren las
distancias publicadas (~1.9–2.0 kpc).

## 5.2 Estrellas más brillantes del cúmulo

Consulta ADQL al servicio TAP de SIMBAD: estrellas con V < 9.5 a menos de 0.09° (5.4′) del centro
(`resultados/punto5/NGC4755_estrellas_brillantes_SIMBAD.csv`).

| Estrella | Tipo espectral | V | B | B−V | Paralaje (mas) |
|---|---|---|---|---|---|
| HD 111904 | B9 Iab | 5.77 | 6.05 | 0.28 | 0.44 |
| κ Cru | B5 I | 5.94 | 6.12 | 0.18 | 0.51 |
| HD 111990 | B1.5 I | 6.78 | 6.95 | 0.17 | 0.40 |
| BU Cru | B2 Ib | 6.84 | 7.04 | 0.20 | 0.49 |
| DU Cru | M2 Iab | 7.66 | 9.82 | 2.16 | 0.46 |
| CC Cru | B2 III | 7.83 | 8.00 | 0.17 | 0.47 |
| CPD −59 4552 | B1 III | 8.24 | 8.34 | 0.10 | 0.48 |
| CN Cru | B1 V | 8.58 | 8.69 | 0.11 | 0.07 |
| BV Cru | OB | 8.60 | 8.80 | 0.20 | 0.50 |

- **CN Cru no es miembro:** su paralaje (0.07 mas) indica una distancia de unos 14 kpc, mucho más lejos
  que el cúmulo (~0.46–0.50 mas). Es una estrella de fondo.
- **Identificación en la foto del taller:** la foto tiene la misma orientación que DSS, con el norte
  arriba (`resultados/punto5/NGC4755_DSS2red_estrellas_identificadas.png`):
  - la estrella naranja es DU Cru;
  - la azul justo debajo a la derecha es BU Cru;
  - el grupo de abajo a la izquierda es κ Cru con BV Cru;
  - los dos halos grandes de arriba son HD 111990 y HD 111904.

## 5.3 (1) Análisis de la foto de la página 2

Script: `p5_pagina2_analisis.py`. Entrada: `resultados/punto5/pagina2.jpg` (foto de la página 2,
1200 × 1600 px). Resultados en `pagina2_estimaciones.json` y `pagina2_tabla_estrellas_cuadrado.csv`.

### Calibración de las escalas de la hoja
- **Barra de color:** se muestreó el color promedio de cada recuadro a la altura y = 390–404 px. De
  izquierda a derecha: O (x 191–209), B (212–229), A (234–249), F1 (253–265), F2 (269–284), G (288–306),
  K1 (312–324), K2 (330–348) y M (352–368).
- **Problema:** en la foto impresa los halos de las estrellas quedan desaturados (el canal azul
  normalizado de una estrella "azul" es ≈ 0.41, mientras que el recuadro B impreso tiene ≈ 0.65), así que
  compararlos directamente con la barra no funcionaba. Se usó un **índice de azul t = b − r**, con los
  canales normalizados b = B/(R+G+B) y r = R/(R+G+B), y cortes según el color percibido:

| t | Color percibido | Clase asignada |
|---|---|---|
| ≥ 0.12 | Azul | B |
| 0.04 a 0.12 | Blanco azulado | A |
| −0.02 a 0.04 | Blanco | F1 |
| −0.06 a −0.02 | Amarillento | F2 |
| −0.09 a −0.06 | Amarillo | G |
| −0.11 a −0.09 | Naranja claro | K1 |
| −0.16 a −0.11 | Naranja | K2 |
| < −0.16 | Rojo | M |

### Detección de estrellas
1. Se recortó la zona de la foto del cúmulo (x 180–572, y 428–782). Se excluyó el doblez del papel en
   y ≈ 795: la primera vez, el doblez hizo que el "centro" cayera en el borde de la foto.
2. Para cada píxel se calculó la luminancia, el promedio de R, G y B, y se restó un fondo local, la
   mediana en una ventana de 25 × 25 px.
3. Se marcaron los píxeles con luminancia > fondo + 80. Con umbrales más bajos se detectaba el grano del
   papel.
4. Se agruparon los píxeles en regiones conectadas: **296 detecciones**.
5. El color de cada estrella se midió en su **halo**, no en el centro, porque en la impresión los centros
   brillantes quedan blancos.
6. **Brillo 1–10:** se ordenaron las estrellas por el área de su halo y se repartieron en 10 niveles con
   límites en progresión geométrica, entre la más grande (brillo 1) y la más chica (brillo 10).
7. Se fusionaron las detecciones que caían dentro del halo de una estrella más brillante (a menos de
   0.6·√área de su halo), porque eran pedazos de la misma estrella.

### Centro, límite y cuadrado
- **Tres candidatos para el centro:**
  - máximo de densidad de estrellas, contando cada una igual: (360, 653) px;
  - máximo de densidad pesado por brillo: (345, 644) px. Lo desplazan las detecciones falsas en el halo
    de una estrella saturada;
  - baricentro de las tres concentraciones brillantes del núcleo: DU Cru (379, 552), BU Cru (407, 581) y
    el grupo de κ Cru (325, 647). Da ((379 + 407 + 325)/3, (552 + 581 + 647)/3) = **(370, 593) px**.
- **Centro adoptado:** el tercero. Los otros dos quedan a menos de ~60 px, y coincide con el centro de
  SIMBAD, que está entre DU Cru y κ Cru.
- **Límite:** desde el centro hacia afuera, el primer radio donde la densidad de estrellas (suavizada
  con σ = 35 px) cae por debajo de 1.3 veces su mediana en la foto: **120 px**.
- **Escala aproximada de la foto:** HD 111990 y HD 111904 están separadas ~4.6′ en el cielo, medido sobre
  la imagen DSS, y ~295 px en la foto. Eso da ~64 px por minuto de arco, así que la foto cubre unos **6′**.
  El límite visible es el del núcleo brillante; el cúmulo completo mide 10.3′ (SIMBAD).
- **Cuadrado:** 130 px de lado (~2′ de cielo), centrado en la X.
- **Estrellas dentro del cuadrado:** **46**, después de fusionar los halos y descartar los niveles 9 y 10,
  que a esta resolución son ruido del papel.

### Estimación de brillo y color (46 estrellas)

| Brillo ↓ / Color → | B | A | F1 | F2 | K1 | K2 |
|---|---|---|---|---|---|---|
| 2 | | | | | | 1 |
| 3 | 1 | | | | | |
| 4 | | 1 | | | | |
| 5 | 5 | 2 | | | | |
| 6 | 2 | 1 | | 1 | | 1 |
| 7 | 3 | 7 | 7 | 1 | 1 | |
| 8 | | 3 | 8 | 1 | | |
| **Total** | **11** | **14** | **15** | **3** | **1** | **2** |

No hubo estrellas O, G ni M en el cuadrado, ni de brillo 1. La K2 de brillo 2 es DU Cru. La K2 de
brillo 6 probablemente es un pedazo de su halo anaranjado.

Figuras: `resultados/punto5/pagina2_cumulo_ampliado.png` (X, límite, cuadrado y estrellas numeradas) y
`hoja_de_trabajo_llena.png` (hoja de trabajo dibujada).

## 5.4 (2) Edad del cúmulo

### Comparación con los diagramas de referencia de la página 2

| Diagrama de referencia | Rasgo distintivo |
|---|---|
| Joven (< 100 millones de años) | Estrellas azules (O, B) muy brillantes arriba a la izquierda, y una secuencia que baja en diagonal |
| Edad intermedia (100–3000 millones) | Sin estrellas O/B brillantes; la secuencia empieza más abajo y hay gigantes rojas arriba a la derecha |
| Viejo (> 3000 millones) | Solo la parte baja de la secuencia y muchas gigantes rojas brillantes |

La hoja de la Caja de Joyas tiene estrellas **B de brillo 3 a 5 arriba a la izquierda**, una secuencia
hacia A y F en brillo 7–8, y **una sola** estrella roja brillante. Se parece al diagrama **joven**.

### Por qué la supergigante roja no contradice la conclusión
Las estrellas más masivas consumen su combustible más rápido. En un cúmulo de unas decenas de millones de
años, solo las más masivas ya agotaron el hidrógeno de su núcleo y se convirtieron en supergigantes
(DU Cru, M2 Iab). Las demás estrellas B, algo menos masivas, siguen en la secuencia principal.

### Edad en la literatura
Verificada en el texto completo de los artículos y en el registro de DOI (Crossref):
- Sanner et al. 2001, A&A 369, 511: **10 ± 5 millones de años** (su tabla 16, ajuste de isócronas).
- Bonatto et al. 2006, A&A 453, 121: **14 ± 2 millones de años** (isócronas de Padova, 2MASS). Es la que
  se cita en el documento final.
- Piskunov et al. 2004, MNRAS 349, 1449: **16 millones de años** (función de luminosidad).

**Conclusión:** la Caja de Joyas es un cúmulo joven, de menos de 100 millones de años; la literatura le da
entre 10 y 16 millones.

## 5.5 Comprobación con datos reales de Gaia DR3 (análisis complementario)

Este análisis no aparece en el documento final, pero respalda la conclusión. Script: `p5_gaia_cmd.py`.

1. **Consulta** al archivo de Gaia de la ESA (no depende del CDS): estrellas de Gaia DR3 a menos de 0.1°
   (6′) del centro de SIMBAD, con G < 18 y con color BP−RP y paralaje disponibles. Resultado:
   **2306 estrellas** (`resultados/punto5/NGC4755_GaiaDR3_cono6arcmin.csv`).
   - Trampa encontrada: la consulta normal (síncrona) corta en 2000 filas; hay que usar la asíncrona.
2. **Selección de miembros:**
   - punto de partida: paralaje entre 0.3 y 0.7 mas y error de paralaje < 0.1 mas;
   - tres iteraciones con la mediana de paralaje y de movimiento propio de los miembros: se conservan las
     estrellas con movimiento propio a menos de 0.5 mas/año de esa mediana y con paralaje a menos de
     3·√(error² + 0.03²) de la mediana.
   - Resultado: **553 miembros**, con paralaje mediana 0.470 mas y movimiento propio
     (−4.707, −1.077) mas/año, que coincide con el de SIMBAD (−4.647, −1.134).
3. **Lectura del diagrama** (`NGC4755_GaiaDR3_CMD.png`):
   - la secuencia principal sube casi vertical, con BP−RP ≈ 0.23 entre G = 8 y G = 11;
   - las 4 estrellas azules más brillantes (G = 5.6–6.8) están corridas a la derecha, con BP−RP de 0.35 a
     0.57: son supergigantes B saliendo de la secuencia principal. Ese es el **punto de giro**, en lo más
     alto del diagrama;
   - hay una única supergigante roja aislada (G = 6.10, BP−RP = 2.79), que es DU Cru.
   - Un punto de giro tan arriba corresponde a unos 10–15 millones de años.

---

## Cómo reproducir todo

Las imágenes de AKARI, Planck 857 GHz, Fermi 5, DSS2 roja y 30 Doradus se descargaron con la
herramienta `get_survey_image` del servidor (`aladin_mcp/imaging.py`). Los parámetros están en la
tabla de la sección 4.2: alias `AKARI`, `PLANCK`, `FERMI` y `DSS`, centro de la LMC o "30 Dor", campo de
20° o 1.5°. El resto se regenera con:

```bash
.venv/bin/python resultados/scripts/p4_descargas_extra.py
.venv/bin/python resultados/scripts/p4a_measure.py
.venv/bin/python resultados/scripts/p4_medidas_perfiles.py
.venv/bin/python resultados/scripts/comparar_medidas.py
.venv/bin/python resultados/scripts/p4b_bonanos_cmd.py
.venv/bin/python resultados/scripts/p4_imagenes_png.py
.venv/bin/python resultados/scripts/p5_pagina2_analisis.py
.venv/bin/python resultados/scripts/p5_hoja_sobre_foto.py
.venv/bin/python resultados/scripts/p5_ngc4755_identificadas.py
.venv/bin/python resultados/scripts/p5_gaia_cmd.py
```

Las capturas de Aladin (`p_capturas_aladin.py`) necesitan Aladin Desktop abierto con su hub SAMP.

## Referencias

- Wenger, M. et al. 2000, *The SIMBAD astronomical database*, A&AS 143, 9.
- Bonnarel, F. et al. 2000, *The ALADIN interactive sky atlas*, A&AS 143, 33.
- Bonanos, A. Z. et al. 2009, *Spitzer SAGE Infrared Photometry of Massive Stars in the Large Magellanic
  Cloud*, AJ 138, 1003.
- de Vaucouleurs, G. et al. 1991, *Third Reference Catalogue of Bright Galaxies* (RC3), Springer.
- Mellinger, A. 2009, *A Color All-Sky Panorama Image of the Milky Way*, PASP 121, 1180.
- Bonatto, C., Bica, E., Ortolani, S. & Barbuy, B. 2006, *Detection of Ks-excess stars in the 14 Myr open
  cluster NGC 4755*, A&A 453, 121.
- Sanner, J., Brunzendorf, J., Will, J.-M. & Geffert, M. 2001, *Photometric and kinematic studies of open
  star clusters. III*, A&A 369, 511.
- Piskunov, A. E. et al. 2004, *On the determination of age and mass functions of stars in young open
  star clusters from the analysis of their luminosity functions*, MNRAS 349, 1449.
- Gaia Collaboration, Vallenari, A. et al. 2023, *Gaia Data Release 3: Summary of the content and survey
  properties*, A&A 674, A1.
