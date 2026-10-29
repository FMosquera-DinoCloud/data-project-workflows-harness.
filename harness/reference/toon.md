# TOON en el harness

TOON (Token-Oriented Object Notation) sirve para listas uniformes: los campos se declaran una sola vez y cada fila lleva los valores en ese orden.

```toon
backlog[2]{id,title,status,priority,due,blocks,owner,phase,clickup_id,updated}:
  T-001,Acordar criterio de éxito del piloto,doing,P1,2026-10-03,T-004,Ana,F1,86abc123,2026-09-30
  T-002,"Relevar restricciones: seguridad, costos y plazos",todo,P3,,,,F1,,2026-09-30
```

## Reglas

- La cabecera es `nombre[N]{campo1,campo2,...}:`. `N` es la cantidad de filas y **se actualiza siempre** al agregar o quitar una fila.
- Cada fila va con dos espacios de sangría, con los valores separados por coma y en el orden de la cabecera.
- Un valor vacío queda como nada entre dos comas (`,,`).
- Un valor con coma, dos puntos, comillas o espacios al inicio o al final va entre comillas dobles; las comillas internas se escapan con `\"`.
- Las listas dentro de un campo (tags, `blocks`) se separan con `;`, sin espacios.
- Sin comentarios dentro del bloque. Las notas van en el Markdown asociado.
- Al editar, se reescribe la fila completa. No se reordenan filas ajenas al cambio.

## Esquemas

| Archivo | Cabecera |
|---|---|
| `index.toon` | `index[N]{path,type,date,summary,tags}` |
| `backlog/backlog.toon` | `backlog[N]{id,title,status,priority,due,blocks,owner,phase,clickup_id,updated}` |
| `drive/.manifest.toon` | `files[N]{file_id,path,mime,modified,local_hash,status,link}` |
| `time/AAAA-Www.toon` | `entries[N]{date,task_ref,source,minutes,evidence}` |
| `estimations/<slug>.toon` | `items[N]{id,title,role,optimistic_h,likely_h,pessimistic_h,expected_h,ai_factor,final_h,assumptions}` |
| `~/claude-workspace/projects.toon` | `projects[N]{name,path,active}` |

`type` en `index.toon` puede ser `overview`, `decision`, `meeting`, `digest`, `status`, `memory`, `backlog`, `drive`, `architecture`, `estimation`, `research`, `time` o `other`.
