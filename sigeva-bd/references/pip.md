# Módulo de convocatorias: presentación/solicitud (PIP y similares)

El trámite de una convocatoria (PIP, PICT…) vive en el rol **"Usuario presentación/solicitud"**
(`redirect(72)`), distinto del Banco de Datos (`redirect(96)`). Es la solicitud que termina en el
botón **ENVIAR PRESENTACIÓN** (irreversible): cada ítem de la carátula muestra estado **"Ok"** o
**"Sin Datos"** y el objetivo del módulo es dejar todo en "Ok" y recién entonces habilitar el envío.

```
CARÁTULA:        Datos del proyecto / Aspectos éticos / Seguridad / Recusación
ANTECEDENTES:    Grupo de Investigación / Financiamiento Básico / Financiamiento Adicional /
                 Otras Fuentes de Financiamiento
ARCHIVOS:        Plan de trabajo (PDF) / Aval de la autoridad máxima (PDF firmado)
PRESENTACIÓN:    botón ENVIAR PRESENTACIÓN (irreversible)
```

La cantidad exacta de ítems la da la tabla de estados del trámite: **nada se hardcodea**;
`pip-cargar` lee y relee la tabla.

## Línea base: primero mapear, siempre

```bash
# Una vez por instancia (el simulador y el sitio real tienen líneas base separadas):
python assets/sigeva_bd.py pip-mapear --env-file G:/.sigeva/.env --headless --tramite 11220260100119CO --aceptar
```

- Genera `references/mapa-pip-base.json` (con `origen: real|simulador`) y `references/mapa-pip-sitio.md`.
- El recorrido es **solo lectura**: visita pantallas, no envía formularios, no aprieta ENVIAR.
- En el módulo, `tramiteId` es estructura (se conserva) y las altas usan acciones propias
  (`alta`, `cargar`, `verificar`…), excepciones que `pip-mapear` declara al recorrido.
- Una línea base de origen `simulador` **no habilita** trabajos contra el sitio real:
  `pip-verificar`/`pip-cargar`/`pip-estados`/`pip-enviar` se niegan (`_chequear_origen`).
- El contrato PIP fija: pantalla del trámite (`tramite_pantalla`), tabla de estados
  (`estados_tabla_id`, columna ESTADO) y presencia del botón ENVIAR (`_chequear_enviar`;
  su desaparición es "alto": trámite enviado, vencido o cambiado).

## El trámite y sus estados

```bash
python assets/sigeva_bd.py pip-estados --config config.json --env-file .env --headless
# -> {"estados": {"Datos del proyecto": "Ok", ...}, "con_enlace": [...]}
```

Reglas de lectura:

- `leer_estados` recorre las tablas del trámite y arma `{seccion, estado, enlace}`.
- Sección "Sin Datos" **con enlace**: se puede completar desde el módulo.
- Sección "Sin Datos" **sin enlace**: depende del Banco de Datos (p. ej. integrantes que deben
  estar declarados allí). `pip-cargar` la informa como `error` con ese motivo y sigue; se
  resuelve en el Banco de Datos, no a los golpes en el trámite.
- El código del trámite (p. ej. `11220260100119CO`) identifica el trámite; si solo hay uno, no
  hace falta pasarlo.

## pip.json: los datos los declara la persona

```json
{
  "tramite": "11220260100119CO",
  "secciones": [
    {"clave": "datos-proyecto", "seccion": "Datos del proyecto",
     "campos": {"tituloProyecto": "…", "granAreaConocimiento": {"valor": "KS"},
                "disciplinaA": {"valor": "KS4"}, "disciplinaDesagregadaA": {"valor": "61"}}},
    {"clave": "finbasico", "seccion": "Financiamiento Básico",
     "grilla": {"1": {"2026": "6500000,00", "2027": "2000000,00", "2028": "0,00"}}},
    {"clave": "grupo", "seccion": "Grupo de Investigación",
     "miembros": [{"nombre": "Nieto, Alejandro Agustín", "dedicacion": "100"}]},
    {"clave": "plan", "seccion": "Plan de trabajo (PDF)",
     "archivo": {"ruta": "plan.pdf", "tipo": "1"}}
  ]
}
```

- `seccion` es el nombre **tal como figura en la tabla de estados** (se empareja exacto;
  si no figura, `pip-cargar` corta la tanda mostrando las secciones vistas).
- `campos`: cada entrada por `name` del control real, según el mapa (`mapa-pip-sitio.md`) o
  `inspeccionar --url <enlace de la sección>`. Mismos valores que `generico`:
  texto, `{"etiqueta": …}` o `{"valor": …}` para select, `{"fecha": "mm/aaaa"}` para datepicker,
  radios/checkbox por valor. Los nombres reales de cada pantalla se relevan, nunca se inventan.
  Los combos dependientes (p. ej. disciplina desagregada) se resuelven con espera AJAX.
- `grilla`: para las grillas de montos `{codigo: {año: "monto"}}` con formato argentino
  (`6500000,00`). Las claves son los códigos internos de `ubicaciones`
  (`codigo-año-…`), que **no** siempre coinciden con el número visible del rubro: en el
  Financiamiento Básico son 1–8 (Equipamiento, Licencias, Bibliografía, Bienes de
  consumo, Viajes y viáticos, Difusión, Servicios de terceros, Otros gastos); en el
  Adicional son solo 1, 4, 5, 7 y 8 (mismos nombres, etiquetas visibles (1), (2), (3),
  (4) y (5)). Si la grilla real no trae una celda única por código/año, o el código
  trae etiquetas inconsistentes entre años, se informa y no se toca nada.
- `miembros`: `[{nombre, dedicacion, [rol]}]` para la grilla del grupo. Se empareja por
  nombre normalizado contra las filas reales (el nombre tiene que estar contenido en el de
  la grilla: "RABINO, Daniel Nicolás", no "RABINO, Nicolás"); rol opcional (`Titular`,
  `Co-titular`, `Investigador`, `Becario`, `Prof técnico`). Cada declarado se **habilita**
  (casilla HAB, `seleccionadas`): quien se incorpora con el código del trámite aparece sin
  rol y sin habilitar, y así no integra el proyecto. Los que no figuran en la grilla
  se informan como avisos (se incorporan desde su Banco de Datos con el código del trámite:
  la pantalla no ofrece alta). Los extranjeros pueden figurar solo en el plan (instructivo).
- `filas`: `[{columna: valor, ...}]` para grillas de filas repetidas, como la recusación
  (`apellido`, `nombre`, `observacion`). Se escriben en orden y se vacían las sobrantes: la
  lista declarada es la completa. Ninguna columna puede quedar vacía. El instructivo pide
  listar a quienes no deban evaluar **y/o hayan colaborado con el titular en los últimos 5
  años**; el Guardar vacío no marca "Ok".
- `seleccion`: `{"campo": "otrosFinanciamientos", "valores": [ids]}` para listas paginadas
  de casillas (Otras fuentes de financiamiento: se tildan los subsidios del titular y del
  grupo). En SIGEVA **cada clic en una casilla envía el formulario y guarda**
  (`actualizar()`): en seco solo se recorren las páginas y se informa cuántas faltan; con
  `--guardar`, primero un recorrido de solo lectura valida que existan todos los valores
  (si falta uno, no se toca nada) y recién después se hace clic. Nunca destilda.
- `archivo`: subida en dos pasos (lista de adjuntos → Adjuntar del slot → página de
  subida). `tipo` es el valor de `tipoArchivo` del slot en la página de adjuntos;
  `seccion` es el nombre tal como figura en la tabla de estados (en el trámite real:
  "Plan de trabajo" y "Aval de la autoridad máxima del LT del titular", sin "(PDF)").
  Se valida que exista, que sea PDF y que entre en el límite del módulo
  (35 MB por defecto, configurable con `limite_adjunto_mb` en config).
- `guardar_vacio`: guarda el formulario sin tocar nada. En el sitio real **no** sirve para
  recusación ni otras fuentes (el Guardar vacío no marca "Ok"): usar `filas` y `seleccion`.
- Declaración jurada: campo vacío o faltante → `pip-preparar` bloquea y se le pide el dato a la
  persona; nada se completa con algo plausible.

```bash
python assets/sigeva_bd.py pip-preparar --datos pip.json     # -> pip-listos.json (o errores)
```

## Cargar y verificar

```bash
python assets/sigeva_bd.py pip-cargar --datos pip-listos.json --config config.json \
    --env-file .env --headless --claves datos-proyecto          # en seco, con capturas
python assets/sigeva_bd.py pip-cargar --datos pip-listos.json --config config.json \
    --env-file .env --headless --guardar                        # guarda y verifica
```

- Toda la disciplina del Banco de Datos aplica: `pip-verificar --auto` al inicio de la sesión
  (reutiliza una aprobada de 6 h), tandas cortas, en seco primero, `--guardar` solo con
  autorización explícita para esa tanda, después de que la persona revise las capturas.
- **Éxito = la sección vuelve a "Ok" en la tabla de estados** y, para `campos`, `filas`,
  `seleccion` y `miembros`, **lo releído coincide con lo pedido**. Después de cada Guardar se
  reabre el trámite, se relee la tabla (con reintentos) y se vuelve a abrir el formulario.
- **"Ok" no significa "al día".** Una sección en "Ok" con esos tipos se reabre y se compara
  campo por campo: si coincide, `ya-estaba` sin guardar; si difiere, se corrige y el recibo
  dice qué (`difiere`). Así un título o un resumen viejos no quedan cargados porque la
  sección ya estaba completa. Grillas de montos y adjuntos en "Ok" se dan por hechos.
- Resultados por clave: `guardado`, `ya-estaba`, `en-seco`, `rechazado` (mensaje de validación de
  SIGEVA), `no-guardado` (volvió sin error y sin guardar, o lo releído no coincide), `error`,
  `corte`. Recibo `recibo-pip-cargar-*.json` y log append-only `estado-pip.jsonl`, con la
  `huella` del contenido: si cambian los datos de una sección, deja de darse por hecha.
- El formulario de la sección se llena con las mismas primitivas que el Banco de Datos:
  fechas con `setDate` (el datepicker pisa lo escrito), selects con eventos reales, archivos con
  `set_input_files`.

## ENVIAR PRESENTACIÓN

- `pip-cargar` **nunca** lo aprieta: al terminar informa qué quedó pendiente y, si todo está en
  "Ok", lo dice en el log para que la persona lo aprete a mano (vía preferida).
- Existe `pip-enviar --tramite <código> --confirmo-enviar`: comando aparte, que se niega si falta
  la confirmación explícita o si alguna sección no está en "Ok"; aprieta el botón, acepta el
  diálogo de confirmación de SIGEVA y reporta la pantalla de comprobante.

## Estado actual y límites

- La línea base PIP en `references/` es del **sitio real** (`origen: "real"`), trámite
  PIP 2026-2028 GI 11220260100119CO (`index.do?tramiteid=752068`), 19 pantallas.
  El simulador genera la suya propia en cada corrida de tests.
- Tipos de ítem soportados además de `campos`: `grilla` (montos por rubro/año, formato
  `6500000,00`, emparejada contra `ubicaciones` y la etiqueta de la fila), `miembros`
  (dedicación/rol por fila de la grilla del grupo, emparejados por nombre; los ausentes
  se informan como avisos), `archivo` con `tipo` (slot tipoArchivo de la página de
  adjuntos; flujo en dos pasos: lista -> Adjuntar -> subida), `guardar_vacio`
  (declaración explícita de que no hay nada que declarar, p. ej. sin recusados),
  `dependientes` (selects con opciones por AJAX).
- Pendiente: agregar por UI de SIGEVA a los integrantes que no figuran en la grilla del
  grupo (la pantalla solo permite editar/borrar los presentes); los slots de adjunto se
  identifican por tipoArchivo (hipótesis por orden: 1 = plan, 105 = aval; confirmar en
  la primera carga real).
