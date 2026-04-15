---
nombre: "describir_salida_papel"
version: "1.0.0"
descripcion: "Consulta el layout de salida a papel (recibo de nomina) de PeopleNet desde M4SCO_ROWS, M4SCO_ROW_COL_DEF y M4SCO_ROWS_DETAIL."
herramienta: "tools.nomina.get_payslip_layout"
parametros:
  - nombre: "mode"
    tipo: "string"
    descripcion: "Modo de operacion: --list-reports, --list-rows, --row, --list-cells."
    requerido: true
  - nombre: "report"
    tipo: "string"
    descripcion: "ID del informe (SCO_ID_REPORT). Requerido para --row y --list-cells."
    requerido: false
  - nombre: "body"
    tipo: "string"
    descripcion: "ID del cuerpo/seccion (SCO_ID_BODY). Requerido para --row y --list-cells."
    requerido: false
  - nombre: "row_id"
    tipo: "integer"
    descripcion: "ID numerico de la fila (SCO_ID_ROW). Requerido para --row; opcional en --list-cells."
    requerido: false
  - nombre: "search"
    tipo: "string"
    descripcion: "Buscar por texto en nombre, etiqueta, nodo o ID de concepto."
    requerido: false
---

## Documentacion de la Skill: `describir_salida_papel`

### Proposito

Expone las tres tablas que definen el layout del **recibo de nomina (salida a papel)** en PeopleNet:

| Tabla fisica | Objeto BDL logico | Descripcion |
|---|---|---|
| `M4SCO_ROWS` | `SCO_ROWS` | Filas del recibo: una por concepto/grupo de conceptos a imprimir |
| `M4SCO_ROW_COL_DEF` | `SCO_ROW_COL_DEFINITION` | Definicion celda fila x columna: que valor/nodo/etiqueta aparece en cada celda |
| `M4SCO_ROWS_DETAIL` | `SCO_ROWS_DETAIL` | Configuracion de totalizacion por fila (registros y tramos) |

Estas tablas son parte del modulo BDL `SCO_PAY_SLIP` (Recibo de nomina) y conectan el layout
visual del recibo con los conceptos calculados por el motor de nomina.

### Modelo de datos

#### Jerarquia del recibo

```
SCO_REPORTS               <- Definicion del informe/recibo
  SCO_BODIES              <- Secciones del recibo (cabecera, cuerpo, pie, etc.)
    SCO_COLUMNS           <- Definicion de columnas (etiqueta, importe, etc.)
    SCO_ROWS              <- Filas del recibo  <-- TABLA CLAVE 1
      SCO_ROW_COL_DEF     <- Contenido de cada celda fila x columna  <-- TABLA CLAVE 2
      SCO_ROWS_DETAIL     <- Config. totalizacion de la fila  <-- TABLA CLAVE 3
```

#### Campos clave de `M4SCO_ROWS`

| Campo | Descripcion |
|---|---|
| `SCO_ID_REPORT`, `SCO_ID_BODY`, `SCO_ID_ROW` | Clave primaria |
| `SCO_NM_ROWESP` / `SCO_NM_ROWENG` / `SCO_NM_ROW` | Nombre de la fila (por idioma / generico) |
| `SCO_ORDER` | Orden de aparicion en el cuerpo |
| `SCO_RECORDS` | Mostrar todos los registros (check) |
| `SCO_SLICES` | Mostrar todos los tramos (check) |
| `SCO_ID_NODE` | Nodo destino del calculo (canal de nomina) |
| `ID_T3_PI` | ID del M4Object/canal concepto final |
| `ID_PAYROLL_ITEM` | ID del concepto de nomina (enlaza con M4RCH_PAYROLL_ITEM) |

> **Nota:** El campo logico `ID_APP_USER` se almacena fisicamente como `ID_SECUSER` en SQL Server.

#### Campos clave de `M4SCO_ROW_COL_DEF`

| Campo | Descripcion |
|---|---|
| `SCO_ID_REPORT`, `SCO_ID_BODY`, `SCO_ID_ROW`, `SCO_ID_COLUMN` | Clave primaria |
| `SCO_ID_NODE` | Nodo de calculo origen |
| `SCO_ID_ITEM` | Item/campo origen del valor |
| `SCO_LABELESP` / `SCO_LABELENG` / `SCO_LABEL` | Etiqueta de la celda (por idioma / generica) |
| `SCO_CONSTANT` | Valor constante a imprimir (si no hay nodo/item) |
| `SCO_BEF_AFT` | Posicion: antes (B) o despues (A) del valor |
| `SCO_CANCEL_ROW` | Si esta celda anula la fila completa |
| `SFR_ID_SOURCE_NODE` / `SFR_ID_SOURCE_ITEM` | Nodo/item origen alternativo (sfr = source for row) |

> **Nota:** El campo logico `SCO_ID_PRINTING_ITEM` se almacena fisicamente como `SCO_ID_PRT_ITEM`.

#### Campos clave de `M4SCO_ROWS_DETAIL`

| Campo | Descripcion |
|---|---|
| `SCO_ALL_RECORDS` | Mostrar todos los registros |
| `SCO_TOT_RECORDS` | Totalizar registros |
| `SCO_TOT_REC_FUNC` | Funcion de totalizacion para registros (lookup SCO_X_TOT_FUNC) |
| `SCO_ALL_SLICES` | Mostrar todos los tramos |
| `SCO_TOT_SLICES` | Totalizar tramos |
| `SCO_TOT_SLI_FUNC` | Funcion de totalizacion para tramos (lookup SCO_X_TOT_FUNC) |

### Flujo de trabajo

1. **Descubrir informes disponibles**: Usar `--list-reports` para obtener los IDs de informes (`SCO_ID_REPORT`) configurados en el sistema.
2. **Explorar filas**: Usar `--list-rows --report "..."` para ver todas las filas de un recibo con sus conceptos vinculados.
3. **Detallar una fila**: Usar `--row --report "..." --body "..." --row-id N` para obtener la fila completa incluyendo su configuracion de totalizacion y todas sus celdas.
4. **Explorar celdas**: Usar `--list-cells --report "..." --body "..."` para ver todas las celdas de un cuerpo, opcionalmente filtrando por fila o texto.

### Ejemplos de uso

**Listar todos los informes/recibos:**
```bash
python -m tools.nomina.get_payslip_layout --list-reports
```

**Listar filas de un informe especifico:**
```bash
python -m tools.nomina.get_payslip_layout --list-rows --report "RECIBO_PNET"
```

**Buscar filas que incluyan un concepto especifico:**
```bash
python -m tools.nomina.get_payslip_layout --list-rows --search "BIENESTAR"
```

**Obtener el detalle completo de la fila 10 (incluye celdas y config. de totalizacion):**
```bash
python -m tools.nomina.get_payslip_layout --row --report "RECIBO_PNET" --body "CUERPO_PRINCIPAL" --row-id 10
```

**Listar todas las celdas de un cuerpo filtrando por texto:**
```bash
python -m tools.nomina.get_payslip_layout --list-cells --report "RECIBO_PNET" --body "CUERPO_PRINCIPAL" --search "SUELDO"
```

### Relacion con otras herramientas

- `describir_payroll_item` (`tools.m4object.get_payroll_item`): describe los conceptos de nomina en `M4RCH_PAYROLL_ITEM`. La columna `ID_PAYROLL_ITEM` de `M4SCO_ROWS` enlaza directamente con esa tabla.
- `describir_m4object` (`tools.m4object.get_m4object`): describe el canal de nomina (`ID_T3_PI`) vinculado a una fila del recibo.
- `verificar_concepto_nomina`: realiza una verificacion cruzada completa de un concepto. Puede complementarse con esta skill para comprobar si el concepto tambien tiene representacion en el recibo.
- `describir_bdl_object` (`tools.bdl`): puede usarse para inspeccionar el modulo BDL `SCO_PAY_SLIP` y sus 20 objetos relacionados.
