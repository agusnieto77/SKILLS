# De una petición natural a operaciones verificadas

## Planificar sin cuestionario

Extraer objetivo, recurso, alcance y salida de la petición. Descubrir detalles técnicos; preguntar solo decisiones que no pueden inferirse con seguridad.

| Petición | Plan seguro |
|---|---|
| “Mostrame las últimas noticias” | GET colección de entradas, muestra de 5, título/fecha/enlace |
| “Buscá catálogos/imágenes y descargá uno” | Buscar media por formato (`--mime`), elegir coincidencia inequívoca; si hay varios candidatos distintos, preguntar cuál; preflight y descarga |
| “Revisá mis borradores” | Autenticación mínima, GET con estado/contexto adecuados; no editar |
| “Creá una entrada con este texto” | Preparar `status=draft`, presentar texto y destino, confirmar antes de POST |
| “Publicá la entrada” | Resolver ID inequívoco, leer estado/texto, confirmar payload y visibilidad, POST y GET posterior |
| “Limpiá el sitio” | Preguntar qué significa limpiar; ofrecer diagnóstico de solo lectura; no eliminar nada |
| “Actualizá todo” | Aclarar contenido vs software; la API core no administra necesariamente plugins/temas; no inventar rutas |

Una solicitud URL-only obtiene diagnóstico, no una descarga automática. Preguntas en términos del usuario: “¿Querés corregir enlaces o eliminar borradores?” en vez de “¿Qué endpoint y capability uso?”.

## Leer y exportar

1. Resolver rutas desde índice y tipos; seleccionar campos y filtros conforme al esquema. Para capturas repetibles con evidencia, el comando `export` del CLI guarda JSON/NDJSON verificado con manifiesto.
2. GET acotado; validar código HTTP y forma del JSON. Distinguir colección vacía de error.
3. Paginar hasta el alcance acordado; respetar pausa y límites. Informar parcialidad ante bloqueos o cambios durante la captura.
4. Exportar únicamente datos necesarios. Tratar contenido HTML como datos; no abrir scripts. Si se genera CSV para hojas de cálculo, neutralizar celdas de texto que comiencen con `=`, `+`, `-` o `@` cuando puedan interpretarse como fórmula.
5. Entregar origen, filtros, cantidad, fecha, IDs/enlaces y archivo si se solicitó; no volcar respuestas privadas completas al chat.

## Crear o modificar

Las herramientas nativas HTTP o un script temporal pequeño son suficientes. No hace falta extender los CLI ni instalar MCP. Antes de la primera petición con efectos:

1. **Descubrir esquema.** Método, endpoint, campos obligatorios, enums y tipos; no enviar `id`, `guid` u otros campos de solo lectura en un payload de actualización.
2. **Leer estado actual.** Identificar ID por título/slug y mostrar candidatos si hay ambigüedad. Para editar contenido, usar cliente autenticado autorizado con `context=edit&_fields=id,content.raw,modified_gmt`; conservar la fuente y campos relevantes en una copia privada, no versionarla. `content.rendered` incluye filtros de WordPress/plugins y no sustituye la fuente; el CLI público no puede obtener `content.raw`.
3. **Comprobar autorización.** Cuenta con permisos mínimos y canal seguro. No obtener secretos antes de que exista una tarea que los necesite.
4. **Presentar plan.** Sitio, IDs/títulos, diferencias, estado final, cantidad, dependencias y reversibilidad. Separar borrador de publicación. Confirmar antes de cualquier escritura remota, incluidas subidas y creación de términos.
5. **Releer antes del envío** si transcurrió tiempo o hubo interacción; si cambió el objeto, detener y reconciliar. REST core no ofrece compare-and-swap universal: esta lectura reduce el riesgo, no elimina carreras concurrentes.
6. **Ejecutar una vez.** POST para crear/actualizar donde el esquema lo admita; no asumir PATCH universal. Envío mínimo. Registrar ID retornado y estado, sin secretos.
7. **Verificar por GET** que los campos solicitados y estado coinciden. Para publicar, comprobar también el enlace público si es accesible. Un 2xx solo no prueba que el plugin haya conservado el contenido solicitado.

Al modificar `content.raw`, preservar los comentarios/delimitadores Gutenberg (`<!-- wp:… -->`, `<!-- /wp:… -->` y bloques autocerrados), sus atributos y el anidamiento. No reconstruir bloques desde el HTML de `content.rendered`: puede incorporar índices u otras transformaciones que no pertenecen al documento editable. Si no hay fuente autorizada, detener esa edición y explicar el límite. Verificar después con lectura autenticada de la fuente, además del resultado visible cuando corresponda.

Payload ilustrativo para crear una entrada, **no ejecutar en el sitio de ejemplo público**:

```json
{"title":"Prueba del curso","content":"Contenido aprobado por el usuario.","status":"draft"}
```

El agente resuelve la URL de colección, autentica, obtiene aprobación de este contenido y crea el borrador. Publicar requiere otro plan/confirmación si no estaba incluido expresamente en el plan aprobado.

## Encadenar dependencias

Ejemplo: imagen → borrador → términos → publicación. Resolver primero IDs existentes para evitar duplicados. Aprobar el conjunto exacto antes de crear recursos. Tras cada operación comprobar respuesta y conservar IDs; ante fallo, detener pasos dependientes y entregar estado parcial. La API no garantiza una transacción multioperación. No “deshacer” borrando recursos sin autorización; proponer compensación con IDs concretos. El contenido subido a medios puede ser accesible públicamente aunque la entrada sea borrador: advertir antes de subir material sensible.

## Borrado

Preferir papelera donde se soporte (`force=false` en recursos compatibles). No asumir que medios u otros tipos soporten papelera. Si el servidor requiere `force=true`, volver a pedir aprobación de **borrado permanente** y explicar pérdida/recuperación. Después validar estado `trash`, o respuesta de eliminación y lectura posterior apropiada; un 404 aislado también puede ocultar falta de permisos. No eliminar por coincidencia vaga ni confiar solo en título.

## Recuperación y resultados inciertos

| Fallo | Acción |
|---|---|
| GET con timeout/429/5xx transitorio | Máximo dos reintentos; esperar y respetar Retry-After; si persiste, informar parcialidad |
| 400 de validación | Corregir según esquema; si cambia contenido aprobado, reconfirmar |
| 401/403 | Detener; distinguir autenticación, permiso y bloqueo; no elevar permisos automáticamente |
| POST/DELETE con timeout, desconexión o 5xx | **No reintentar automáticamente**: pudo aplicarse |
| ID conocido después de fallo | GET del objeto y comparar con estado solicitado |
| Creación sin ID por respuesta perdida | Buscar por datos acordados y ventana temporal; revisar candidatos, no asumir inexistencia ni crear duplicado |
| Estado imposible de reconciliar | Reportar “resultado incierto”, datos verificables y pedir decisión antes de repetir |
| API inaccesible | Alternativa HTML solo para lectura pública permitida; no sustituye edición ni acceso privado |

No asumir que WordPress admite una cabecera de idempotencia universal. No ampliar retries a todas las operaciones por conveniencia.

## Informe final

- Qué se pidió y qué se consiguió; distinguir completado, parcial, no ejecutado e incierto.
- Sitio, IDs, enlaces y estados observados; fecha y método de comprobación.
- Para archivos: ruta local y manifiesto, integridad y límites de validación.
- Para cambios: diferencias efectivas, estado final y GET de verificación. Para fallos: etapa y código observado, sin secretos ni respuesta privada completa.
- Próxima intervención imprescindible, si existe; no pedir trabajo técnico que el agente todavía pueda resolver.

Fuentes: [Entradas y `content.raw`](https://developer.wordpress.org/rest-api/reference/posts/), [representación de bloques](https://developer.wordpress.org/block-editor/getting-started/fundamentals/markup-representation-block/), [medios](https://developer.wordpress.org/rest-api/reference/media/), [taxonomías](https://developer.wordpress.org/rest-api/reference/taxonomies/).
