# Astronomía para Todos – Taller de magnitudes: puntos 1 a 3

Los cálculos usan los datos del enunciado. Al final de cada punto se comparan con los valores
actuales de SIMBAD (consultados el 29/10/2026 en el espejo de Harvard).

Constantes: 1 pc = 3.0857 × 10¹³ km = 3.2616 años luz; 1 año = 365.25 días = 8766 h.

---

## Punto 1. Un tren a α Centauri

**Datos:** velocidad v = 100 km/h; paralaje de α Cen p = 0.760″.

1. **Distancia.** Con la paralaje en segundos de arco, la distancia en parsecs es d = 1/p:
   d = 1 / 0.760 = **1.316 pc** = 1.316 × 3.0857 × 10¹³ km = **4.060 × 10¹³ km** (≈ 4.29 años luz).
2. **Tiempo de viaje:** t = d / v = 4.060 × 10¹³ km / 100 km/h = 4.060 × 10¹¹ h.
3. **En años:** t = 4.060 × 10¹¹ h / 8766 h/año = **4.63 × 10⁷ años**.

**Respuesta: unos 46 millones de años.** Para comparar: hace 46 millones de años ya se habían extinguido
los dinosaurios no avianos (hace 66 millones de años), pero todavía no existían los homínidos.

*Comparación:* SIMBAD da hoy p = 750.8 mas para el sistema α Cen, es decir d = 1.332 pc, y el viaje
duraría 46.9 millones de años. La conclusión no cambia.

---

## Punto 2. ¿Se puede ver Venus de día desde el fondo de un pozo?

**Datos:** el ojo distingue un contraste del 5 %; el cielo diurno tiene magnitud aparente −5.2.

### Criterio de brillo

Para que Venus se distinga, su flujo debe ser al menos el 5 % del flujo del cielo de fondo:
F_Venus / F_cielo ≥ 0.05.

En magnitudes, m₁ − m₂ = −2.5 log₁₀(F₁/F₂), así que el objeto más débil detectable tiene

m_límite = m_cielo + 2.5 log₁₀(1/0.05) = −5.2 + 2.5 × 1.301 = −5.2 + 3.25 = **−1.95**.

Cualquier objeto más brillante que magnitud −1.95 supera el umbral. Venus, en su máximo brillo,
llega a magnitud −4.4 a −4.6 (NAOJ; EarthSky). Su razón de flujos con el cielo es

F_Venus / F_cielo = 10^(−0.4 × (−4.6 + 5.2)) = 10^(−0.24) = **0.58** (58 %), y 0.48 (48 %) con −4.4.

Eso es diez veces más que el 5 % necesario. **Por brillo, Venus sí se puede ver de día**, y de hecho
se ve a simple vista si uno sabe dónde mirar.

### ¿Y el pozo?

- **El pozo no oscurece el cielo.** Las paredes tapan la mayor parte del cielo, pero el trozo que
  queda a la vista tiene el mismo brillo por unidad de área. El contraste entre Venus y el cielo es el
  mismo que fuera del pozo. Es un mito que desde un pozo se vean estrellas de día.
- **Pero sí limita hacia dónde se mira.** Desde el fondo de un pozo profundo solo se ve una zona
  pequeña alrededor del cenit. Venus nunca se aleja más de unos 27–28° del ecuador celeste: la
  eclíptica está inclinada 23.4° y la órbita de Venus otros 3.4°. En Albania, a unos 41° de latitud
  norte, Venus pasa como mínimo a unos 13° del cenit. Un pozo de 1 m de diámetro y 20 m de
  profundidad muestra solo un círculo de unos 1.4° de radio alrededor del cenit. **Venus no puede
  pasar por ahí.**

**Conclusión:** la afirmación **no merece crédito tal como está contada**. Que Venus sea visible de día
es cierto, y no por estar en un pozo. Pero desde el fondo de un pozo profundo en Albania, Venus nunca
entra en el pedazo de cielo visible.

---

## Punto 3. ¿Cuántas veces más brillante es Rigel que el Sol?

**Datos:** paralaje de Rigel p = 0.0069″; magnitud aparente m = 0.34; magnitud absoluta visual del
Sol M_☉ = 4.83.

1. **Distancia:** d = 1/p = 1/0.0069 = **144.9 pc**.
2. **Magnitud absoluta** (módulo de distancia): M = m − 5 log₁₀(d / 10 pc)
   = 0.34 − 5 log₁₀(14.49) = 0.34 − 5 × 1.161 = **−5.47**.
3. **Cociente de luminosidades** en la banda V:
   L_Rigel / L_☉ = 10^(0.4 × (M_☉ − M_Rigel)) = 10^(0.4 × (4.83 + 5.47)) = 10^(4.12) ≈ **1.3 × 10⁴**.

**Respuesta: Rigel emite unas 13 000 veces más luz visible que el Sol.**

*Comparación con datos actuales:* SIMBAD da para Rigel una paralaje de 3.78 ± 0.34 mas (no 6.9 mas)
y V = 0.13. Con esos valores, d ≈ 265 pc, M_V ≈ −6.98 y L/L_☉ ≈ **5.3 × 10⁴** en la banda visual. Rigel
es una supergigante azul (B8 Ia) y emite gran parte de su energía en el ultravioleta, así que su
luminosidad total (bolométrica) es mayor aún que la visual.
