---
nombre: "tipos_internos_items"
version: "1.0.0"
descripcion: "Catálogo completo de ID_INTERNAL_TYPE de items de PeopleNet (M4RDC_LU_INTERNFLD). Clasifica semánticamente los 111 tipos en 13 grupos funcionales con conteos reales de la BD."
---

## Documentación de la Skill: `tipos_internos_items`

### Propósito
`ID_INTERNAL_TYPE` es un clasificador semántico de segundo nivel para los items de PeopleNet. Complementa `ID_ITEM_TYPE` (Method=1 / Property=2 / Block=3) indicando el **rol funcional específico** que el motor de PeopleNet atribuye a ese item.

El catálogo oficial está en la tabla `M4RDC_LU_INTERNFLD`. Hay **111 tipos** definidos (IDs 1–113).

---

### Dónde se usa

- `M4RCH_ITEMS.ID_INTERNAL_TYPE` — campo de cada item en el repositorio de metadatos.
- El motor lo usa para localizar automáticamente items clave en un canal sin depender del nombre del item. Por ejemplo, al ejecutar `Load_Blk()` busca el item con `ID_INTERNAL_TYPE=20` para saber el `SYS_SENTENCE` activo.
- Permite patrones polimórficos: si un canal declara un item de tipo 41 (System Load), el motor lo invoca automáticamente en el ciclo de carga.

### Relación con el binding BD

`ID_INTERNAL_TYPE` es un clasificador **semántico** — indica el rol funcional del item para el motor. Es **ortogonal** al binding de base de datos:

- El **binding BD** (si el item lee o escribe en la BD, y dónde) se determina por los campos `ID_READ_OBJECT`, `ID_WRITE_OBJECT`, `ID_READ_FIELD`, `ID_WRITE_FIELD` de `M4RCH_ITEMS`.
- Un item puede tener cualquier `ID_INTERNAL_TYPE` y también tener o no binding BD — son dimensiones independientes.
- Por ejemplo, un item `SYS_SENTENCE` (`ID_INTERNAL_TYPE=20`) casi nunca tiene `ID_WRITE_OBJECT` (no persiste en BD); pero un item de tipo "Ninguno" (`ID_INTERNAL_TYPE=1`) puede tanto escribir como no escribir dependiendo de su configuración.

Ver skill `binding_bd_items` para la documentación completa del mecanismo de binding.

---

### Grupo A — Fechas de Vigencia (~10.000 items)

El motor de PeopleNet trabaja con vigencias temporales. Estos tipos marcan qué item de un bloque contiene cada fecha del rango de validez.

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 1 | Ninguno | None | 142.912 | Tipo por defecto — 75% de todos los items |
| 2 | Fecha inicio aplicación | Application Start Date | 4.754 | Inicio de vigencia del registro |
| 3 | Fecha fin aplicación | Application End Date | 4.477 | Fin de vigencia del registro |
| 4 | Fecha inicio corrección | Correction Start Date | 154 | Inicio de corrección histórica |
| 5 | Fecha fin corrección | Correction End Date | 143 | Fin de corrección histórica |
| 6 | Fecha transacción | Transaction Date | 164 | Fecha de la transacción |
| 7 | Proyección | Projection | 1 | |
| 10 | Fecha inicio aplicación para filtro | App. Filter Start Date | 711 | Variante de filtro de la fecha 2 |
| 11 | Fecha fin aplicación para filtro | App. Filter End Date | 712 | Variante de filtro de la fecha 3 |
| 12 | Fecha inicio corrección para filtro | Corr. Filter Init. Date | 6 | |
| 13 | Fecha fin corrección para filtro | Corr. Filter End Date | 5 | |

**Nota**: Los tipos 2/3 son los más frecuentes después de "Ninguno". Prácticamente todos los bloques de datos llevan estas fechas, lo que define el modelo de vigencias temporales del motor.

---

### Grupo B — Traducción Multiidioma (~9.600 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 8 | Columna virtual traducción | Virtual Translation Column | 8.559 | Campo calculado que devuelve el texto en el idioma activo |
| 9 | Columna traducción | Translation Column | 1.034 | Campo físico con el texto en un idioma concreto |

---

### Grupo C — Moneda / Divisa (~13.900 items)

Permiten al motor gestionar automáticamente la conversión de divisas en los bloques de datos.

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 14 | Tipo moneda | Currency Type | 1.864 | Código de divisa del registro |
| 15 | Valor moneda | Currency Value | 8.441 | Importe en la divisa del registro |
| 16 | Fecha de cambio de moneda | Currency Exchange Date | 1.802 | Fecha para obtener la tasa de cambio |
| 29 | Tipo de cambio de moneda | Currency Exchange Rate | 1.805 | Tasa de cambio aplicada |

---

### Grupo D — Loading SQL: SYS_SENTENCE / SYS_PARAM / DYN_FILTER (~11.660 items)

El núcleo del sistema de filtrado declarativo en tiempo de ejecución. Ver skill `describir_sentence_apisql` para el ciclo de vida completo.

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 20 | Sentencia lógica SQL | Logical SQL Statement | 7.636 | `SYS_SENTENCE` — filtro declarativo para `Load_Blk`/`Load_Prg`. Puede ser un ID de sentence o APISQL inline |
| 33 | Parámetros de la sentencia lógica | Logical Statement Param. | 3.937 | `SYS_PARAM` — valores para los `?(type,size,prec)` del APISQL, en orden posicional |
| 34 | Sentencia lógica del filtro dinámico | Dynamic Filter Logical Statem. | 86 | `DYN_FILTER` — anula los SYS_SENTENCE cuando está activo (Query Builder del usuario) |
| 69 | Tabla de lectura del filtro dinámico | Dynamic Filter Read Table | 1 | Variante de DYN_FILTER |
| 81 | Hint de la sentencia lógica | Logical Statement Hint | 1 | SQL optimizer hint del APISQL |
| 110 | Método sentencia en ejecución | Runtime Statement Method | 0 | Reservado |
| 111 | Campo sentencia en ejecución | Runtime Statement Field | 0 | Reservado |

**Patrón LN4 típico** (tipo 20 y 33):
```ln4
TI.SYS_SENTENCE = "FROM &OBJETO A WHERE A.CAMPO = ?(2,30,0)"
TI.SYS_PARAM = valor_parametro
TI.Load_Blk()
```

---

### Grupo E — Métodos del Ciclo de Vida del Motor (~130 items)

Estos tipos marcan items que son **puntos de extensión del motor**. Todos son `ID_ITEM_TYPE=1` (Method). El motor los invoca automáticamente en determinados momentos del ciclo de vida del canal.

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 41 | Carga del sistema | System Load | 34 | Invocado por el motor durante `Load_Blk`/`Load_Prg` |
| 42 | Grabación del sistema | System Save | 65 | Invocado por el motor durante `Save_Blk`/`Save_Prg` |
| 43 | Navegación del sistema | System Navigation | 11 | Invocado durante navegación entre nodos |
| 44 | Navegación del sistema | System Navigation | 8 | Variante de navegación |
| 45 | Ejecución | Execution | 16 | Punto de extensión de ejecución genérica |
| 52 | Ejecución de informe Odbc | Execute Report ODBC | 3 | Lanzamiento de informe ODBC |

---

### Grupo F — Dominio DMD y Tipos Variant (~575 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 17 | Razón de cambio DM | Domain Change Reason | 21 | Motivo del cambio de dominio |
| 18 | Componente DM | Domain Component | 198 | Componente de un dominio |
| 19 | Valor DMD | DMD Value | 0 | |
| 21 | Tipo de dato del variant | Variant Data Type | 274 | Tipo del valor variant (`_ID_M4_TYPE`) |
| 23 | Tipo variant | Variant Value | 282 | Valor del tipo variant (`CME_VALOR`) |

---

### Grupo G — Nómina y Pago (~339 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 24 | Fecha de asignación | Allocation Date | 86 | |
| 25 | Fecha de pago | Payment Date | 70 | |
| 26 | Tipo de pago | Payment Type | 31 | |
| 27 | Frecuencia de pago | Payment Frequency | 47 | |
| 36 | Tipo de asignación de paga | Pay Allocation Type | 31 | |
| 37 | Fecha de asignación de paga | Allocation Pay Date | 46 | |
| 74 | Fecha de nómina | Payroll Date | 47 | |

---

### Grupo H — Fechas y Moneda Específicas de M4Object (~98 items)

Variantes de los tipos de divisa y fecha para el contexto específico de operaciones sobre m4objects (no sobre BDL directamente).

| ID | Nombre (ESP) | Nombre (ENG) | #Items |
|---|---|---|---|
| 53 | Fecha de imputación de un m4object | Meta4Object Allocation Date | 13 |
| 54 | Fecha de pago de un m4object | Meta4Object Payment Date | 13 |
| 55 | Moneda de un m4object | Meta4Object Currency | 15 |
| 56 | Tipo de cambio de un m4object | Meta4Object Exchange Rate | 14 |
| 57 | Fecha de cambio de un m4object | Meta4Object Change Date | 14 |
| 58 | Fecha de inicio de imputación | Allocation Start Date | 13 |
| 59 | Fecha fin de imputación | Allocation End Date | 13 |
| 60 | Modo de tramo | Slice Mode | 14 |

---

### Grupo I — Operaciones y Workflow de Tramitación (~5.580 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 46 | Orden | Order | 11 | |
| 47 | Operación | Operation | 11 | |
| 48 | Momento de la actualización | Upon Update | 10 | |
| 49 | Fecha de operación | Operation Date | 12 | |
| 50 | Información adicional | Additional Information | 21 | |
| 70 | Elemento de operación | Operation Item | 5.494 | El tipo más frecuente después de fechas y moneda |
| 86 | Operación de tramitación | Processing Operation | 23 | |
| 87 | Fecha última modificación tramitación | Last Processing Change Date | 22 | |
| 88 | Fecha inicio tramitación | Processing Start Date | 22 | |

---

### Grupo J — UI y Presentación (~340 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 61 | Consulta actual en plantillas de acumulado | Current Query in Cumulative Templates | 12 | |
| 62 | Ordenación en memoria | Sort in Memory | 171 | Item que define la clave de ordenación en RAM |
| 76 | No visualizar en informes de Consulta | Do Not View in Query Report | 126 | Oculta el item en los reports |
| 77 | Columna valor en nodo pivote | Value Column in Pivot Node | 27 | |
| 78 | Columna nombre concepto en crosstab | Concept Name Column in Crosstab | 1 | |
| 79 | Columna valor concepto en crosstab | Concept Value Column in Crosstab | 1 | |
| 80 | Columna total concepto en crosstab | Concept Total Column in Crosstab | 1 | |
| 84 | Icono para la lista | List Icon | 12 | Icono del registro en listas |
| 90 | Multi selección | Multiselection | 2 | |

---

### Grupo K — Seguridad y Multi-Sociedad (~1.600 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 30 | Usuario de aplicación de la transacción | Transaction Application User | 59 | |
| 31 | Role de aplicación de la transacción | Transaction App. Role | 33 | |
| 64 | Identificador de la Sociedad | Company ID | 1.445 | Clave de la sociedad en arquitectura multi-company |
| 67 | Operación de herencia | Inheritance Operation | 3 | |

---

### Grupo L — Web / SOAP / JavaScript (~255 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 83 | Método SOAP | SOAP Method | 250 | Items que exponen métodos SOAP del canal |
| 104 | JS token de elevación | Elevation Token JS | 1 | |
| 105 | JS role de elevación | Elevation Role JS | 1 | |
| 106 | JS sociedad de elevación | Elevation Company JS | 1 | |
| 107 | JS ID Meta4Object elevado | Elevated Meta4Object ID JS | 1 | |
| 108 | JS RSM de elevación | Elevation RSM JS | 1 | |

---

### Grupo M — Técnicos y Miscelánea (~440 items)

| ID | Nombre (ESP) | Nombre (ENG) | #Items | Notas |
|---|---|---|---|---|
| 22 | Prioridad | Priority | 10 | |
| 35 | Ejecución de informe | Run ODBC Report | 634 | Item que lanza un informe ODBC |
| 51 | Chequeos de BDL | LDB Checks | 59 | Validaciones contra la BDL |
| 63 | Cambio de moneda | Exchange Currency | 1 | |
| 71 | Borrar todas instancias L2 en servidor | Delete all L2 instances in server | 294 | |
| 82 | Elemento no utilizado | Item not used | 33 | Items marcados como obsoletos |
| 94 | Test unitario | Unit Test | 21 | Items de test unitario del motor |

---

### Tipos sin uso real en BD (0 items)

Tipos definidos en el catálogo pero sin items asociados en esta instalación:

`19, 28, 32, 38, 39, 40, 65, 66, 72, 73, 85, 89, 91, 92, 93, 95, 96, 97, 98, 99, 100, 101, 102, 103, 109, 112, 113`

---

### Consulta de referencia

Para buscar items de un tipo interno específico en la BD:

```sql
-- Todos los items de un tipo interno con su TI contenedor
SELECT
    i.ID_ITEM,
    i.ID_ITEM_TYPE,
    i.ID_T3,
    n.ID_NODE,
    lu.N_INTERN_FIELDESP
FROM M4RCH_ITEMS i
JOIN M4RDC_LU_INTERNFLD lu ON lu.ID_INTERNAL_FIELD = i.ID_INTERNAL_TYPE
LEFT JOIN M4RCH_NODES n ON n.ID_NODE = i.ID_NODE
WHERE i.ID_INTERNAL_TYPE = 20  -- SYS_SENTENCE
ORDER BY i.ID_T3, i.ID_ITEM
```

```sql
-- Conteo de items por tipo interno (top 20)
SELECT TOP 20
    i.ID_INTERNAL_TYPE,
    lu.N_INTERN_FIELDESP,
    COUNT(*) AS num_items
FROM M4RCH_ITEMS i
JOIN M4RDC_LU_INTERNFLD lu ON lu.ID_INTERNAL_FIELD = i.ID_INTERNAL_TYPE
GROUP BY i.ID_INTERNAL_TYPE, lu.N_INTERN_FIELDESP
ORDER BY num_items DESC
```
