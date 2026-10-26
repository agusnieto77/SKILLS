# sigeva-bd

Carga asistida y verificada del **Banco de Datos de Actividades de Ciencia y Tecnología** de SIGEVA CONICET (`si.conicet.gov.ar`), con un mapa del sitio que se mantiene al día solo.

- Convierte un BibTeX en registros, los valida y descarta lo que ya está cargado.
- Llena los formularios con un navegador real (Playwright), en seco por defecto, y **verifica cada alta en la lista** releyendo sus fechas.
- Cubre artículos, trabajos en eventos, libros y partes de libro con autores, compiladores y filiaciones, y cualquier otro rubro (premios, financiamiento, RRHH, redes…) relevando su formulario con `inspeccionar`.
- Releva en solo lectura las ~120 pantallas del Banco de Datos, documenta sus campos y detecta cualquier cambio: campos nuevos o eliminados, tipos, obligatoriedad, opciones, tablas, navegación, y sobre todo lo que rompería la carga.

Probado contra SIGEVA CONICET 14.11.24.6 (mapa en solo lectura) y contra un SIGEVA simulado que reproduce sus trampas (pruebas automáticas). Lo que se carga es una declaración jurada: la responsabilidad de revisar los datos es de quien firma.

## Instalación

```bash
python -m pip install -r assets/requirements.txt
python -m playwright install chromium
python assets/sigeva_bd.py doctor
```

## Configuración

Copiar `assets/config.ejemplo.json` a la carpeta de trabajo como `config.json`:

| Clave | Qué es |
|---|---|
| `base` | Instancia de SIGEVA. Solo se probó la del CONICET |
| `rol_banco_datos` | Id del rol en la intranet (`redirect(96)`) |
| `persona_id` | Tu id de persona: marca al autor declarante. `catalogo` sugiere candidatos; confirmalo vos |
| `declarante` | Tu apellido tal como figura en las citas (para marcar al declarante desde BibTeX) |
| `idioma_defecto` | Idioma si el `.bib` no trae `langid` |
| `area_conocimiento` | `campo` (value del combo) y `subcampo` (value o parte de su etiqueta) |
| `tablas` | Ids displaytag de las tablas de publicaciones; `verificar` avisa si cambian |

Credenciales: por defecto se abre Chromium y las tipeás vos. Para corridas desatendidas, `--env-file ruta/.env` (con `USER` y `PASS`) o las variables `SIGEVA_USER`/`SIGEVA_PASS`. Se usan solo para autenticar: nunca se escriben en disco.

## Uso

```bash
cd mi-carpeta-de-trabajo            # fuera del repositorio
S=ruta/a/sigeva-bd/assets/sigeva_bd.py

python $S inventario --config config.json        # qué hay cargado (solo lectura)
python $S catalogo   --config config.json        # ids de revistas, instituciones y persona
python $S bib --bib cv.bib --salida registros.json --config config.json
#   completar a mano en registros.json lo que el .bib no trae (archivo, resumen, editorial…)
python $S preparar --registros registros.json --config config.json
python $S cargar --registros sigeva-trabajo/listos.json --config config.json --limite 3   # en seco
python $S cargar --registros sigeva-trabajo/listos.json --config config.json --limite 5 --guardar
```

| Comando | Hace | Escribe en SIGEVA |
|---|---|---|
| `doctor` | Verifica Python, Playwright y Chromium | no |
| `bib` | BibTeX → `registros.json` (artículos y eventos) | no |
| `inventario` | Lee las listas de publicaciones y el índice con los conteos | no |
| `catalogo` | Abre registros existentes y junta ids de revistas, instituciones y persona | no |
| `inspeccionar` | Releva los campos de cualquier formulario (para registros `generico`) | no |
| `institucion` | Busca una institución en el catálogo oficial de SIGEVA y devuelve id, nombre y dependencia | no |
| `cv` | Cruza un CV (.docx/.pdf/.txt) con el inventario y lista qué falta cargar | no |
| `pdf` | Recorta (créditos + trabajo) y/o comprime un PDF para usarlo como full text | no |
| `preparar` | Resuelve ids (solo coincidencia exacta), valida y descarta lo ya cargado | no |
| `cargar` | Llena formularios y saca capturas; con `--guardar`, guarda y verifica | solo con `--guardar` |
| `modificar` | Corrige campos de un registro existente sin dejar duplicados (protocolo por ids de la lista) | solo con `--guardar` |
| `mapear` | Recorre el Banco de Datos y documenta su estructura | no |
| `verificar` | Compara el sitio real con la línea base y con el contrato del cargador | no |

`cargar` lleva un log append-only (`sigeva-trabajo/estado.jsonl`) para no repetir altas, deja un recibo por tanda y capturas de cada formulario. Para corregir un registro existente está `modificar` (ver abajo); ningún comando borra registros salvo el duplicado que pueda dejar un `modificar`, y solo con `--borrar-duplicado`.

```bash
# Corregir el año de una parte de libro: en seco primero, después con --guardar
python $S modificar --tipo capitulo --titulo "Historia del trabajo en el puerto" --campo anioPublica=2022
python $S modificar --tipo capitulo --titulo "Historia del trabajo en el puerto" --campo anioPublica=2022 --guardar --borrar-duplicado
```

Los nombres de campo salen del [mapa](references/mapa-sitio.md) o de `inspeccionar`. Para un `select`, el valor puede ir como JSON: `--campo 'idioma={"etiqueta":"Español"}'`.

El formato de los registros, incluido el `generico`, está en [references/registros.md](references/registros.md).

## Monitoreo de cambios

Todo trabajo contra SIGEVA (`inventario`, `catalogo`, `inspeccionar`, `cargar`) empieza con `verificar --auto` en la misma sesión: si SIGEVA cambió en algo que usa la skill, el comando no arranca; si el cambio no es crítico, actualiza la documentación y sigue. Una verificación aprobada se reutiliza durante 6 horas (`--vigencia-horas 0` para repetirla siempre). A mano:

```bash
python $S mapear    --env-file .env --headless --aceptar   # línea base + documentación (primera vez)
python $S verificar --env-file .env --headless --auto      # lo mismo que corre al inicio de cada trabajo
```

Detalle y severidades: [references/monitoreo.md](references/monitoreo.md). El mapa vigente está en [references/mapa-sitio.md](references/mapa-sitio.md).

## Pruebas

```bash
python validation/test_sigeva_bd.py
```

Sin red ni credenciales. Las unitarias corren siempre; las de punta a punta levantan un SIGEVA simulado (`validation/sigeva_simulado.py`) y se saltean si Chromium no está instalado. El simulador reproduce el datepicker que pisa fechas, el subcampo por AJAX, el guardado silencioso, el error que vacía el archivo y la paginación displaytag, y registra cada petición para probar que el mapeo no envía formularios.

## Errores frecuentes

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `preparar` bloquea por `institucion_id` | El catálogo no tiene la institución | Cargar a mano un registro con esa institución y volver a correr `catalogo` |
| `no-guardado` | SIGEVA volvió sin error y el registro no está | Mirar la captura; revisar tamaño del PDF (≤ 35 MB) y la lista antes de reintentar |
| `cargar` sale con código 2 y `contrato` | SIGEVA cambió un formulario que usa el cargador | `verificar`, corregir el código, probar, `verificar --aceptar` |
| `corte de tanda: guardado-con-diferencias` | El registro entró con otra fecha | Corregirlo a mano en SIGEVA; la tanda se detiene para no repetir el error |
| No detecta la sesión | Login no completado en 10 minutos | Volver a correr; con `.env`, revisar la captura `login-fallido.png` antes de reintentar |

## Créditos

El conocimiento sobre el funcionamiento interno de SIGEVA se apoya en [carga-sigeva](https://github.com/juanfraire/carga-sigeva) de Juan A. Fraire y en [SIGEVA-JSON](https://github.com/indirivacua/SIGEVA-JSON). Esta skill es una implementación propia; las técnicas de fijar fechas con `setDate` e inyectar filiaciones como inputs ocultos están adaptadas de carga-sigeva, publicado bajo licencia MIT:

> Copyright (c) 2026 Juan A. Fraire. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

Sin relación con el CONICET ni con el equipo de SIGEVA.
