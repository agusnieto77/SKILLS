# Monitoreo de cambios en SIGEVA

SIGEVA cambia sin aviso: aparecen campos obligatorios, cambian ids de tablas, un campo deja de ser datepicker. El cargador depende de esa estructura, así que la skill la releva, la documenta y la vigila.

## Piezas

| Pieza | Qué es | Dónde |
|---|---|---|
| Mapa | Recorrido de solo lectura del rol Banco de Datos: menús, listas y formularios de alta vacíos | `sigeva-trabajo/mapas/` (completo, local) |
| Línea base | Mapa saneado y aceptado: nombres, tipos, etiquetas, obligatoriedad, datepickers, valores de radios/checkbox, conteo y hash de opciones, tablas, navegación | [`mapa-base.json`](mapa-base.json) |
| Documento | Markdown generado de la línea base: índice de pantallas y campos | [`mapa-sitio.md`](mapa-sitio.md) |
| Contrato | Pantallas, campos, botones y tablas que usa `cargar` | `CONTRATO` en `assets/sigeva_bd.py` |
| Historial | Cada verificación con cambios, la más reciente arriba | [`historial-cambios.md`](historial-cambios.md) (se crea con el primer cambio) |
| Informe | JSON de cada verificación | `sigeva-trabajo/verificaciones/` (local) |

## Qué no hace el recorrido

Solo visita enlaces dentro de `/eva/` sin acción o con acción `nuevo`. Nunca: editar, borrar, importar, sincronizar, descargar, imprimir, salir, ni páginas de un registro (`id`, `produccionId`… se generalizan a `N`). El único submit es *Omitir* en la precarga de artículos, que abre un formulario vacío. No guarda valores: en pantallas de datos propios (datos personales, experticia, CV, roles, compartir) ni siquiera el conteo de opciones. Antes de escribir la línea base, aborta si el contenido incluye las credenciales del entorno.

## Comandos

```bash
# Relevar y adoptar como línea base (primera vez, o tras revisar un cambio)
python assets/sigeva_bd.py mapear --env-file G:/.sigeva/.env --headless --aceptar

# Comparar el sitio real con la línea base y el contrato
python assets/sigeva_bd.py verificar --env-file G:/.sigeva/.env --headless

# Lo mismo que corre solo al inicio de cada trabajo: adopta lo no crítico y registra todo
python assets/sigeva_bd.py verificar --auto --env-file G:/.sigeva/.env --headless
```

El recorrido completo tarda unos 3 a 4 minutos (≈120 pantallas, 1 s de pausa entre cada una).

Códigos de salida de `verificar`: `0` sin cambios (o, con `--auto`, solo cambios no críticos ya adoptados); `1` recorrido incompleto (sesión caída, error de pantalla; no se adopta nada); `2` hay cambios sin adoptar o, con `--auto`, alguno crítico.

## Severidades

| Severidad | Ejemplos | Qué hacer |
|---|---|---|
| crítico | Falta un campo, botón o tabla del contrato; cambió el id de paginación; un valor de radio que usa el cargador ya no existe | `cargar` se niega a guardar. Corregir `assets/sigeva_bd.py` (y `CONTRATO`), probar contra el simulador, luego `verificar --aceptar` |
| alto | Pantalla o campo eliminado, campo nuevo obligatorio, cambio de tipo, de `action` o de valores de radio/checkbox | Revisar si afecta registros `generico` y la documentación de [registros](registros.md) |
| medio | Pantalla o campo nuevo opcional, versión de SIGEVA, botón nuevo, navegación eliminada | Informativo; aceptar |
| bajo | Cambio en las opciones de un combo, etiquetas, navegación nueva | Informativo; aceptar |

## Al inicio de cada trabajo

No hay tarea programada: la verificación es el primer paso de cualquier trabajo contra SIGEVA. `inventario`, `catalogo`, `inspeccionar` y `cargar` corren `verificar --auto` dentro de su propia sesión, antes de hacer nada:

1. Si en `sigeva-trabajo/ultima-verificacion.json` hay una verificación aprobada (código 0, misma línea base) de menos de `--vigencia-horas` (6 por defecto), se reutiliza: varios comandos de una misma jornada no repiten el recorrido. `--vigencia-horas 0` lo fuerza siempre.
2. Si no, recorre el sitio y compara. Cambios no críticos: se adoptan, se regenera `mapa-sitio.md` y se anotan en el historial; el trabajo sigue.
3. Cambio crítico o recorrido incompleto: no se adopta nada y el comando termina sin empezar el trabajo, con el detalle y la ruta del informe.

`cargar` además repasa el contrato justo antes de la primera alta (solo las 4 pantallas del contrato, segundos), como última barrera aunque se haya reutilizado una verificación.

Después de un trabajo en el que la verificación actualizó `references/`: revisar `historial-cambios.md`, correr las pruebas y commitear `references/` para que la documentación del repositorio refleje el sitio.

## El `.env`

Dos líneas, fuera del repositorio:

```
USER=<usuario de la intranet>
PASS=<contraseña>
```

También se aceptan `SIGEVA_USER`/`SIGEVA_PASS`. Se cargan solo en el entorno del proceso y no se escriben en ningún archivo.
