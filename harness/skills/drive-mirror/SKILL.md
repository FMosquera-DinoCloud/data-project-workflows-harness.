---
name: drive-mirror
description: "Mantiene drive/ como espejo local de solo lectura de la carpeta de Drive del proyecto y sube cambios a Drive solo con aprobación. Usar cuando se pida traer, sincronizar, actualizar o buscar documentos de Drive del proyecto, ver qué cambió en Drive, o actualizar/subir un documento a Drive. Use to mirror a project's Google Drive folder locally, or to push an approved change back to Drive."
---

# drive-mirror

Reglas comunes: `~/claude-workspace/harness/reference/conventions.md`. Configuración: `project.toml [drive]` y `config.toml [policy].drive_max_mb`. Manifest: `drive/.manifest.toon` (`files[N]{file_id,path,mime,modified,local_hash,status,link}`).

## Bajar de Drive a local (automático; único modo desatendido)

1. Listar la carpeta en forma recursiva: `search_files` con `parentId = '<folder_id>'`, y repetir en cada subcarpeta. Saltear lo que matchee `exclude`. Los accesos directos (`application/vnd.google-apps.shortcut`) se registran con `status=shortcut` y no se siguen.
2. Por archivo, comparar `modifiedTime` con el manifest. Solo se procesa lo nuevo o modificado.
3. **Conflicto**: si el archivo local existe y su `shasum -a 256` no coincide con `local_hash`, alguien lo editó localmente. No se pisa. Marcar `status=conflict` y listarlo en el resumen.
4. Qué se guarda, en `drive/<ruta relativa en Drive>/`:

   | Tipo | Archivo local | Cómo |
   |---|---|---|
   | Google Doc | `<nombre>.md` | `read_file_content`. |
   | Google Sheet | `<nombre>.md` | `read_file_content` (todas las hojas). Si hace falta la tabla exacta de la primera hoja, `download_file_content` con `text/csv`: devuelve base64, que se escribe a un archivo temporal y se decodifica con `base64 -d`. |
   | Google Slides | `<nombre>.md` | `read_file_content`. |
   | PDF, docx, xlsx, pptx | `<nombre>.<ext>.md` | `read_file_content`: representación en texto. |
   | Imagen, video, zip, binario, o más de `drive_max_mb` | no se baja | Solo la fila del manifest con `status=link-only` y el link. |

   Cada archivo `.md` generado empieza con: `> Espejo de Drive · [original](link) · modificado <fecha>. No editar acá: usar drive-mirror para cambiar Drive.`

5. Archivo borrado en Drive: se mueve a `drive/.deleted/`, queda `status=deleted` y se avisa. No se borra.
6. Actualizar el manifest (`modified`, `local_hash`, `status=ok`), `index.toon` (`type=drive`, un resumen de una línea sacado del contenido) y `[last].drive` en `state.toml`.
7. Commit `harness(drive): <N> nuevos, <M> actualizados, <K> conflictos`.

## Subir un cambio a Drive (solo interactivo y con OK)

1. Se hace únicamente cuando el usuario lo pide. Nunca como efecto de otra skill.
2. Mostrar el diff entre la versión de Drive (volver a leerla, por si cambió) y la propuesta, y el archivo de destino (nombre y link). El contenido va sin referencias internas (ver "Texto que sale del repo" en `conventions.md`).
3. Esperar un OK explícito para ese archivo. Un OK no vale para otros archivos.
4. Aplicar con los scripts de la skill `drive-sync` (`gdoc_update`, `edit_docx`, `upload_to_drive`), o con el conector de Docs si está disponible.
5. Volver a bajar el archivo para actualizar el espejo y el manifest. Commit `harness(drive): subido <nombre> con aprobación`.

## Resolver conflictos (interactivo)

Mostrar la diferencia entre lo local y Drive y preguntar qué hacer: descartar lo local (se vuelve a bajar), subir lo local (flujo de arriba, con OK) o guardar lo local como `<nombre>.local.md` fuera del espejo.
