# tweetscraper — columnas

Mismos nombres y orden que TweetScraperR. Fechas: texto ISO 8601 UTC
(`2026-06-12T21:22:33Z`). Ids: texto (superan la precisión de un número).
Ausente = `null`. Listas: arrays en JSON/JSONL; en CSV, valores unidos con ` | `.

## Tweets (31)

| Columna | Tipo | Contenido |
|---|---|---|
| `fecha` | fecha | Publicación (UTC). |
| `user` | texto | Autorx con `@`. |
| `texto` | texto | Texto completo (también en tweets largos, vía `note_tweet`). |
| `idioma` | texto | Código detectado por X. |
| `respuestas`, `retweets`, `citas`, `megustas`, `views` | entero | Métricas al momento de la recolección. |
| `emoticones` | lista | Emojis del texto, uno por aparición. |
| `hashtags` | lista | Sin `#` (entidades de X). |
| `menciones` | lista | Cuentas mencionadas, sin `@`. |
| `urls_externas` | lista | URLs expandidas. |
| `media` | lista | URLs de fotos; para video/gif, el mp4 de mayor bitrate. |
| `media_tipo` | lista | `photo`, `video`, `animated_gif` (alineada con `media`). |
| `es_retweet`, `es_cita` | lógico | |
| `tweet_citado_id` | texto | Id del tweet citado. |
| `conversation_id` | texto | Id del hilo. |
| `url` | texto | `https://x.com/<cuenta>/status/<id>`. |
| `tweet_id`, `user_id` | texto | |
| `respuesta_a_id`, `respuesta_a_user` | texto | Tweet y cuenta (con `@`) a la que responde. |
| `retweet_id` | texto | Tweet original de un retweet. |
| `guardados` | entero | Bookmarks. |
| `fuente` | texto | App de publicación ("Twitter for iPhone"). |
| `sensible`, `editado` | lógico | |
| `lugar`, `pais` | texto | Geoetiqueta, si la hay. |

## Hilos (`thread`)

Las 31 columnas de tweets permanecen intactas; solo este comando agrega `rol`:
`antecedente` (cadena de padres del focal), `focal` (ID solicitado),
`continuacion` (autorrespuestas conectadas del autor focal) o `respuesta`
(otras respuestas recolectadas). Filas deduplicadas por `tweet_id` y ordenadas
por `fecha`, con ID como desempate. En stdout: `requested_id`, `root_id`,
`truncated`, `details` y `warnings`. La raíz conocida no implica cuerpo completo.

## Articles (`article`, entidad separada)

| Campo | Contenido |
|---|---|
| `article_id`, `tweet_id` | ID del Article y tweet asociado si se conoce. |
| `user`, `url`, `fecha` | Autor, URL canónica del Article y fecha UTC si está disponible. |
| `titulo`, `portada` | Título y URL de portada. |
| `texto` | Cuerpo completo extraído de bloques o `plain_text`; `null` si solo hay preview. |
| `preview`, `estado_cuerpo` | Adelanto separado y `completo` / `preview`. |
| `bloques`, `entidades` | Bloques Draft.js y `entityMap` normalizado a objeto (acepta lista de entidades o pares key/value). |
| `enlaces` | URLs de entidades LINK. |
| `media` | Lista de `{id, url, tipo}` del cuerpo; no es la columna `media` de tweets. |

El exportador Markdown renderiza los bloques; no transforma `preview` en cuerpo.
La falta de contenido accesible genera aviso, no una ampliación de permisos.
Los 31 campos de tweets públicos también conservan su orden: información no
publicada por el proveedor queda en `null`, sin inventar ceros ni métricas.

## Usuarixs (18)

`user` (con `@`), `nombre`, `user_id`, `descripcion`, `seguidores`,
`siguiendo`, `tweets`, `favoritos`, `verificado` (azul, tipo de verificación
o legacy), `ubicacion`, `sitio_web`, `imagen_perfil`, `banner`,
`fecha_creacion`, `url`, `tweets_media`, `protegida`, `tipo_verificacion`
(`Business`, `Government`... o `null`).

## Acerca de la cuenta (13)

`user`, `nombre`, `user_id`, `pais_cuenta`, `ubicacion_precisa` (lógico),
`cambios_usuario` (entero), `ultimo_cambio_usuario` (fecha),
`afiliada_a`, `origen_cuenta` (p. ej. tienda de apps de registro),
`identidad_verificada` (lógico), `verificada_desde` (fecha), `fecha_creacion`,
`url`. X no publica todos los campos para todas las cuentas (`null`) y oculta
algunas fechas con valores negativos (también `null`).

## Sentimiento (`sentiment`)

`tweet_id`, `url` (si vienen del dataset), `tweet`, `tono` (Alegría, Tristeza,
Ira, Sorpresa, Disgusto, Miedo, Humor, Sarcasmo, Entusiasmo, Enojo,
Informativo, Otros), `sentimiento` (Positivo, Negativo, Neutral),
`expresiones_de_odio`, `direccionado`, `llama_a_accion` (lógicos),
`explicacion`; `error` si falló.

## Imágenes (`images`)

`clasificacion` (Foto, Meme, Captura de pantalla, Dibujo, Pintura, Viñeta,
Caricatura, Comic o historieta, Gráfico, Infografía, Flyer, Poster o cartel,
Placa de texto, Arte digital, Mapa, Collage, Fotomontaje, Otro),
`contiene_texto`, `texto_contenido`, `contenido_discriminatorio`,
`contenido_violento`, `contenido_pornografico`, `contenido_inapropiado`,
`descripcion`, `palabras_clave` (separadas por `;`), `img` (URL o ruta
absoluta), `tweet_url` (si vienen del dataset); `error` si falló.

## Pool (`accounts list`)

`cuenta`, `usuario_x`, `activa`, `pausas` ("Operacion until HH:MM:SS; ..."),
`requests`, `requests_por_endpoint`, `ultimo_uso`, `proxy` (clave oculta), `error`.
