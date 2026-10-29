---
name: estimate
description: "Estima esfuerzo de tareas, épicas o propuestas con rango de tres puntos, supuestos explícitos y ajuste por trabajo asistido por IA, y guarda la estimación en el proyecto. Usar cuando se pida estimar, dimensionar, cuántas horas o días lleva algo, armar un plan de horas por rol, o revisar una estimación existente."
---

# estimate

Plantilla de datos: `estimations/<slug>.toon` → `items[N]{id,title,role,optimistic_h,likely_h,pessimistic_h,expected_h,ai_factor,final_h,assumptions}`. Complemento en prosa: `estimations/<slug>.md`.

## Método

1. **Descomponer** en ítems de 4 a 24 h, con resultado verificable. Si el ítem viene del backlog, se usa su `T-NNN` y sus criterios de aceptación (`task-writer`). Si algo no se puede descomponer por falta de información, es un **spike** con time-box y va así en la estimación.
2. **Tres puntos por ítem y rol:** optimista, probable y pesimista. `expected_h = (O + 4P + Pe) / 6`.
3. **Ajuste IA** (`ai_factor`): aplicar los criterios de trabajo asistido de `clickup-time-logging` y los descuentos por rol de `sow-evaluator`, según el tipo de tarea. Por defecto: código y documentación 0.4 a 0.6; diseño, arquitectura, reuniones y validación con el cliente 1.0. `final_h = expected_h × ai_factor`.
4. **Supuestos** en una línea por ítem. Si cambian, la estimación cambia.
5. **Riesgo:** sumar contingencia solo a nivel total (10 a 25 % según la incertidumbre), nunca escondida en los ítems.
6. **Salida:**
   - Tabla por rol: horas finales, rango y la contingencia aparte.
   - Supuestos globales.
   - Qué información reduciría más el rango.

## Reglas

- No inventar productividad ni datos históricos. Si hay horas reales de tareas parecidas en `time/*.toon` o en ClickUp, usarlas y citarlas; si no, decirlo.
- Estimar el objetivo, no una implementación elegida. Si la estimación depende de una decisión técnica abierta, se estiman las dos alternativas o se deja como spike.
- Cuando la estimación es para un SOW o propuesta, se valida después con `sow-evaluator`.
- Actualizar `index.toon` (`type=estimation`) y hacer commit.
