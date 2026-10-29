---
name: aws-radar
description: "Resume las novedades de AWS relevantes para un Solution Architect de IA (Bedrock, SageMaker, agentes, datos, analytics, seguridad, costos) y las cruza con los proyectos activos del harness. Usar cuando se pregunte qué hay de nuevo en AWS, lanzamientos recientes, si existe un servicio o feature nuevo para un caso de uso, o en la rutina semanal."
---

# aws-radar

Salida: `~/claude-workspace/research/aws-updates/AAAA-Www.md`. Es de la persona, no de un proyecto. El impacto en cada proyecto se anota en la sección de ese proyecto dentro del archivo.

## Fuentes, en orden

1. Conector **AWS MCP** (`claude_ai_AWS_MCP`), si está autenticado: documentación y novedades.
2. Web: "What's New with AWS" y el AWS News Blog, con WebSearch o WebFetch. **La política de DinoCloud limita el egress**: si un dominio no está permitido, no se insiste ni se busca otro camino. Se anota en el archivo que la fuente no estuvo disponible.
3. Si no hay ninguna fuente disponible, el archivo lo dice y termina ahí. No se completa con memoria del modelo.

## Contenido

- Ventana: desde el último archivo de `research/aws-updates/` (por defecto 7 días).
- Filtro base: IA generativa y ML (Bedrock, AgentCore, SageMaker, Q), datos y analytics (Glue, Athena, Redshift, OpenSearch, S3 Tables), integración, seguridad y gobierno, y costos o pricing.
- Filtro por proyecto: se suman los servicios de AWS que aparecen en los tags de `index.toon` y en `docs/00-overview.md` de cada proyecto activo.
- Lo demás se descarta.
- Por novedad: qué es, en una línea; qué cambia para un arquitecto; región o GA vs. preview; link oficial.
- **Cruce con proyectos:** para cada proyecto activo, leer `docs/00-overview.md` y los tags de `index.toon` (servicios mencionados). Si una novedad lo afecta, anotar en qué y proponer, si corresponde, una tarea como propuesta en ese proyecto (se escribe en el archivo del radar, no en el proyecto).
- Si una novedad es una oportunidad Data/AI para un cliente, se anota además en `docs/oportunidades-data-ai.md` del proyecto, solo en modo interactivo.

## Cierre

Commit en `claude-workspace`: `harness(aws-radar): AAAA-Www`.
