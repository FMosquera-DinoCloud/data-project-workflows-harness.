> **DinoCloud Internal - Confidential**

# `project.toml`: esquema

Es lo único que describe a un proyecto. Las skills no tienen nada propio de un proyecto: todo lo leen de acá. Una sección que el proyecto no usa se deja fuera o vacía.

```toml
[project]
name        = "slug-del-proyecto"        # igual al nombre del directorio
client      = "Nombre del cliente"
description = "Una línea: qué se construye y para qué"
stage       = "F1 Descubrimiento"         # fase actual; debe coincidir con una de [[phases]]
owner       = "Nombre del TL"
started     = "AAAA-MM-DD"
scope_confirmed = false                   # true cuando está confirmado el alcance autorizado para procesar material del cliente

[[phases]]                                # hitos y camino crítico
id       = "F1"
name     = "Descubrimiento"
end      = "AAAA-MM-DD"
critical = ["T-001", "T-003"]             # ids del backlog que están en el camino crítico

[[team]]                                  # equipo interno del proyecto
name    = "Nombre Apellido"
role    = "Data Engineer"
aliases = ["Nombre", "nombre.apellido"]   # cómo aparece en Slack, Meet o ClickUp

[[client_people]]                         # personas del cliente: solo nombre y rol
name = "Nombre Apellido"
role = "Product Owner"

[drive]
folder_id = ""                            # carpeta raíz del proyecto en Drive; vacío = sin espejo
exclude   = []                            # subcarpetas o patrones de nombre que no se espejan

[clickup]
space     = ""
folder_id = ""                            # se prefiere folder a list: cubre todos los sprints
list_id   = ""                            # opcional: lista del sprint vigente

[calendar]
match = ["NOMBRE-PROYECTO", "Cliente"]    # un evento es del proyecto si su título contiene alguno
exclude = ["Almuerzo"]

[gmail]
query = ""                                # consulta Gmail para hilos del proyecto; vacío = no se lee Gmail
exclude_senders = ["notifications@clickup.com", "calendar-notification@google.com", "drive-shares-dm-noreply@google.com"]

[[internal]]                              # canales internos del equipo
type = "slack"                            # slack | gchat
id   = ""                                 # id del canal o espacio
name = "#proyecto-internal"
ingest = true

[[client_channels]]                       # un bloque por canal con el cliente
type   = "slack-connect"                  # slack-connect | teams | gmail | gchat | whatsapp
id     = ""                               # id de canal, query de Gmail o nombre del grupo
name   = ""
people = []                               # quiénes participan (nombre y rol)
ingest = true                             # whatsapp: siempre false (figura solo para saber que existe)
notes  = ""                               # para qué se usa, horario, quién responde

[github]
repos = []                                # "org/repo"; se leen PRs e issues abiertos para el status

```

## Reglas

- `scope_confirmed = false` → `project-ingest` solo procesa fuentes internas y lo avisa en el status. Material del cliente solo con `true`.
- Canales `whatsapp`, o con `ingest = false`: no se leen. Se nombran en el overview para saber que existen.
- Si un tipo de canal no tiene conector disponible (hoy: `gchat`, y `teams` hasta autenticar Microsoft 365), se saltea y se anota en "Pendientes" del status.
