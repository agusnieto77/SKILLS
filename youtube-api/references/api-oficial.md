# API oficial de YouTube (Data API v3)

Ruta documentada por Google para datos de video y comentarios. Requiere proyecto en Google Cloud, habilitación de la API y una **API key** (o credenciales OAuth 2.0). Las respuestas históricas se registraron el 22-10-2026; la receta de inventario describe la ruta oficial, no una nueva ejecución.

## Qué resuelve y qué no

| Objetivo | Endpoint oficial | Notas |
|---|---|---|
| Metadatos de un video | `GET /youtube/v3/videos?part=snippet,statistics,contentDetails&id=VIDEO_ID` | `snippet` (título, descripción, etiquetas, `publishedAt`), `statistics` (vistas, likes), `contentDetails` (duración, `caption` = "true"/"false") |
| Buscar videos | `GET /youtube/v3/search?part=snippet&q=...&type=video` | Costo de cuota: **100 unidades** por llamada |
| Comentarios (hilos) | `GET /youtube/v3/commentThreads?part=snippet,replies&videoId=VIDEO_ID&maxResults=100` | Costo: **1 unidad** por llamada. `maxResults` admite hasta 100; paginar con `pageToken` |
| Respuestas a un comentario | `GET /youtube/v3/comments?part=snippet&parentId=...&maxResults=100` | Costo: **1 unidad**. Paginar con `pageToken`; `replies.comments` de `commentThreads` puede contener solo parte de las respuestas |
| Pistas de subtítulo | `GET /youtube/v3/captions?part=snippet&videoId=VIDEO_ID` | Costo: **50 unidades**. **Requiere OAuth** con `youtube.force-ssl` o `youtubepartner` |
| Descargar subtítulo | `GET /youtube/v3/captions/{CAPTION_ID}?tfmt=vtt` | Devuelve el archivo binario, no una URL timedtext. Costo: **200 unidades**, requiere permiso de edición; admite `tfmt=srt|vtt` y traducción automática con `tlang` |

Puntos que conviene distinguir:

- `captions.list` **solo funciona con el canal propietario o con OAuth autorizado**. Un atacante anónimo con API key propia no puede leer la transcripción de un video ajeno por esta vía.
- `commentThreads.list` devuelve texto y admite `searchTerms`, además de orden `time`/`relevance`. Filtrar por texto cambia el universo de comentarios observado; no presentarlo como cobertura total.
- `search.list` es la operación más cara: 100 unidades por llamada frente a 1 unidad por página de comentarios. Con la cuota por defecto de 10 000 unidades/día, 100 búsquedas agotan la cuota diaria.
- La cuota por defecto es **10 000 unidades/día**; se puede pedir aumento en la consola de Google Cloud.

## Autenticación

- **API key** (simple): suficiente para `videos.list`, `commentThreads.list`, `comments.list` y `search.list` sobre contenido público.
- **OAuth 2.0**: necesario para `captions.list`/`captions.download` y para recursos privados o del propio canal. Scope mínimo para subtítulos: `https://www.googleapis.com/auth/youtube.force-ssl`.

La API key viaja en el parámetro `key=` de la query. No pegarla en el chat ni en archivos versionados: va en variable de entorno (`YOUTUBE_API_KEY`) o en el gestor de secretos del entorno.

## Inventario de un canal o playlist

Para inventariar videos públicos de un canal sin usar `search.list` como catálogo:

1. Resolver el ID del canal y consultar `channels.list(part=contentDetails,id=CHANNEL_ID)` (o `forHandle=@CANAL`). Leer `items[].contentDetails.relatedPlaylists.uploads`: es el ID de su playlist de subidas.
2. Consultar `playlistItems.list(part=snippet,contentDetails,playlistId=UPLOADS_ID,maxResults=50)`. Para una playlist pública explícita, comenzar directamente aquí con su ID. Seguir `nextPageToken` mediante `pageToken` solo dentro del alcance acordado: para este CLI, detenerse al reunir 50 entradas. Conservar `snippet.position` y `contentDetails.videoId`; registrar elementos privados/eliminados en vez de inventar su ID.
3. Consultar `videos.list(part=snippet,statistics,contentDetails,id=ID1,ID2,...)` con **hasta 50 IDs por petición**. Unir por ID, no por posición: el servicio puede omitir videos no disponibles y el orden no es una clave. Registrar error/ausencia por elemento sin descartar los válidos.
4. Guardar el inventario y su fecha, playlist/canal fuente, posición, límite y continuación no recorrida si existe. Es una muestra acotada, no necesariamente el catálogo completo. Si se entrega al CLI anónimo, generar UTF-8 con un ID/URL por línea y usar `--archivo-ids`.

`channels.list`, `playlistItems.list` y `videos.list` cuestan 1 unidad por llamada cada uno; las páginas adicionales consumen cuota. Clave de proyecto propia mediante `YOUTUBE_API_KEY`, nunca pegada en chat/versionada. Esta receta oficial no cambia la vía del CLI incluido: el CLI sigue usando páginas públicas e InnerTube sin clave, secuencialmente y con máximo 50 entradas. No agregar SQLite, rotar claves ni dividir recolecciones para eludir cuotas o bloqueos.

Documentación primaria: [channels.list](https://developers.google.com/youtube/v3/docs/channels/list), [playlistItems.list](https://developers.google.com/youtube/v3/docs/playlistItems/list), [videos.list](https://developers.google.com/youtube/v3/docs/videos/list), [commentThreads.list](https://developers.google.com/youtube/v3/docs/commentThreads/list), [comments.list](https://developers.google.com/youtube/v3/docs/comments/list) y [captions.download](https://developers.google.com/youtube/v3/docs/captions/download).

## Comprobación rápida

Sin clave, la API responde 403 con un mensaje explícito:

```json
{
  "error": {
    "code": 403,
    "message": "Method doesn't allow unregistered callers (callers without established identity). Please use API Key or other form of API consumer identity to call this method."
  }
}
```

Ese 403 **no** significa que falten permisos sobre el video: significa que la llamada no está identificada. Con una clave válida, un video inexistente devuelve 404 `videoNotFound` y un video privado devuelve 403 `forbidden`.

## Comparación con la vía no oficial

| Aspecto | Data API v3 | InnerTube (`youtubei`) |
|---|---|---|
| Clave | Obligatoria | No: la clave pública se lee del propio HTML |
| Cuota | 10 000 unidades/día por defecto | Sin cuota documentada, pero sujeto a bloqueos por IP |
| Soporte | Sí (Google) | No: puede cambiar sin aviso |
| Comentarios | Sí, paginados | Sí, paginados |
| Transcripción de videos ajenos | No (`captions` exige OAuth del propietario) | Sí, por `timedtext` |

Para una clase o un análisis puntual, la vía no oficial es la práctica (es la que usa `yt-dlp`). Para un sistema en producción, la oficial. Lo que no corresponde es presentar la segunda como la primera.
