---
name: session-close
description: "Cierre de una sesión de trabajo en un proyecto del harness: resumen de lo hecho y lo que queda en status/<fecha>-cierre.md, horas sin registrar, commit y push. Usar cuando el usuario diga que cierra ('cerramos por hoy', 'cierro la sesión', 'terminamos', '/session-close') o cuando el aviso del harness al arrancar diga que hay sesiones que terminaron sin cierre."
---

# session-close

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`. Script de apoyo: `harness/scripts/session_close.py` (correr con `py -X utf8` o el python del venv del harness).

## Qué sesión se cierra

- **La sesión en curso:** lo que pasó está en la conversación. El id sale de `session_close.py current <raíz del proyecto>`.
- **Sesiones que terminaron sin cierre** (el hook de salida las anota en `.harness/local/`; el de inicio las lista): por cada una, `session_close.py digest <transcript> --since <fecha del último cierre>` da los pedidos, la última respuesta de cada turno, los commits y las escrituras en ClickUp. Una sesión puede durar varios días: `--since` deja solo lo que no entró en un cierre anterior. Se trabaja sobre ese resumen; el transcript completo solo se abre para confirmar algo puntual. Si son varias del mismo día, van en el mismo cierre.

## Pasos

1. **Juntar lo hecho**, además de la conversación o el digest:
   - `git log --since=<inicio de la sesión> --oneline` en el repo del proyecto y en `~/claude-workspace`;
   - decisiones nuevas en `docs/decisions/decisions.md`, reuniones en `context/meetings/`, cambios en ClickUp.
2. **Escribir `status/AAAA-MM-DD-cierre.md`** (fecha de la sesión, no de hoy). Si ya existe, sumar una sección `## Sesión HH:MM` en lugar de pisarlo.

   ```markdown
   > **DinoCloud Internal - Confidential**

   # Cierre de sesión — AAAA-MM-DD

   ## Hecho
   - viñetas por tema: revisiones, documentos publicados, decisiones (D-NNN), reuniones, cambios en ClickUp, horas

   ## Para el próximo día hábil
   - lo que vence o espera a alguien, con responsable

   ## Pendiente del usuario
   - decisiones o acciones que le quedaron al usuario
   ```

   Corto: es lo que lee la próxima sesión y la daily. Sin copiar comentarios ni texto largo; los links a ClickUp o Drive valen.
3. **Horas:** si hubo trabajo que no está en `time/AAAA-Www.toon`, agregar las filas (`source=session`, minutos aproximados, tarea de ClickUp) **sin cargarlas**; la carga es de `weekly-hours` con OK.
4. **Commit y push** en el repo del proyecto: `harness(status): cierre del dd/mm`. Solo los archivos del cierre y las horas; lo que haya sin commitear de otra sesión se deja como está y se avisa.
5. **Marcar como cerradas:** `session_close.py mark <raíz> <session_id>...` con la sesión en curso y las que se cerraron desde el aviso.
6. Responder en 4 a 6 líneas: dónde quedó el cierre y lo del próximo día hábil.

## Lo que no hace

- No publica en ClickUp, Drive, Slack ni mail; no cambia estados ni carga horas.
- No cierra sesiones que no son de un proyecto del harness ni las de rutinas desatendidas.
