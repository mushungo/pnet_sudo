---
# Metadata estructurada de la Skill
nombre: "describir_m4object"
version: "2.0.0"
descripcion: "Obtiene la definición completa de un m4object (canal) de PeopleNet, incluyendo su herencia, nodos, TIs, items con argumentos de métodos, conceptos de nómina, y reglas con código fuente LN4."
parametros:
  - nombre: "id_t3"
    tipo: "string"
    descripcion: "El identificador del m4object (canal) a describir. Ej: ABC, SCO_MNG_DEV_PRODUCT."
    requerido: true
  - nombre: "include_rules"
    tipo: "boolean"
    descripcion: "Si true, incluye el detalle de reglas por TI y el código fuente LN4 (M4RCH_RULES3)."
    requerido: false
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_m4object`

### Propósito
Esta skill permite a los agentes consultar la estructura jerárquica completa de un m4object (canal) de PeopleNet. Un m4object es la unidad funcional que define cómo la aplicación opera sobre los datos de la BDL.

La jerarquía real de un m4object es:

```
T3 (canal)
├─ Herencia (T3_INHERIT)
├─ Conectores (T3_CONNTORS)
└─ Nodos (NODES)
     └─ TI (Technical Instance) — entidad pivotal
          ├─ Items (campos/métodos, vinculados a la BDL)
          │    └─ Argumentos de métodos (ITEM_ARGS) — siempre incluidos
          ├─ Conceptos de nómina (CONCEPTS) — siempre incluidos
          └─ Reglas (RULES) — lógica de negocio en LN4
               └─ Código fuente LN4 (RULES3) — con --include-rules
```

**Nota importante:** La TI (Technical Instance) es una entidad de primer nivel, no un simple passthrough. Tiene sus propios objetos BDL de lectura/escritura, herencia propia, y puede ser reutilizada por diferentes canales a través de nodos distintos.

### Flujo de Trabajo
La skill invoca el script `tools/m4object/get_m4object.py`, que realiza los siguientes pasos:
1. **Cabecera del canal**: Consulta `M4RCH_T3S` para los metadatos principales (categoría, stream type, seguridad, etc.).
2. **Comentarios**: Consulta `M4RCH_T3S1..T3S7` para los comentarios multilingüe.
3. **Herencia**: Consulta `M4RCH_T3_INHERIT` para la cadena de herencia entre canales.
4. **Conectores**: Consulta `M4RCH_T3_CONNTORS` para las conexiones entre canales.
5. **Nodos con TIs**: Consulta `M4RCH_NODES` JOIN `M4RCH_TIS` para los nodos y sus instancias técnicas.
6. **Items por TI**: Consulta `M4RCH_ITEMS` para los campos y métodos de cada TI.
7. **Argumentos de métodos**: Consulta `M4RCH_ITEM_ARGS` para los parámetros de entrada/salida de items tipo Method (siempre incluidos).
8. **Conceptos de nómina**: Consulta `M4RCH_CONCEPTS` para los conceptos de nómina asociados a cada TI (siempre incluidos).
9. **Reglas**: Consulta `M4RCH_RULES` para el conteo (siempre) y detalle (con `--include-rules`) de reglas por TI.
10. **Código fuente LN4**: Consulta `M4RCH_RULES3` para el código fuente de las reglas (solo con `--include-rules`, truncado a 3000 chars).
11. **Ensamblaje**: Estructura todo en un JSON jerárquico con un resumen (totales de nodos, TIs, items, conceptos, reglas).

### Datos Disponibles
- **Canal (T3)**: ID, nombre ESP/ENG, categoría, subcategoría, stream type, tipo de ejecución, flags de seguridad/externo/cacheable/separable, servicio, tipo de organización, fechas.
- **Herencia**: Canales base y tipo de herencia.
- **Conectores**: Identificador, nodo origen, nodo conector, item conector, tipo.
- **Nodos**: ID, posición, nombre, tipo, root flag, autoload, filas únicas, visibilidad, afecta BD, DMD, RSM, filtro dinámico.
- **TI**: ID, nombre, TI base (herencia), objetos BDL de lectura/escritura, sentencias, flags de sistema y generación SQL.
- **Items**: ID, tipo, M4 type, objetos y campos de lectura/escritura, visibilidad, PK, posición, nombre, tipo interno, tipo CS, método.
- **Argumentos de métodos** (nuevos en v2): Para items de tipo Method, se incluyen automáticamente: ID argumento, posición, tipo M4, tipo de argumento (1=input, 2=output), flag is_output.
- **Conceptos de nómina** (nuevos en v2): Para TIs que tengan conceptos en M4RCH_CONCEPTS: ID concepto, ID item asociado, tipo, scope, flag sistema.
- **Reglas**: Conteo por TI (siempre), y opcionalmente: ID regla, item, tipo de regla, tipo de disparo, orden de ejecución.
- **Código fuente LN4** (nuevo en v2): Con `--include-rules`, cada regla incluye su campo `source_code` con el código LN4 (truncado a 3000 chars).
- **Resumen**: Conteos totales de nodos, TIs, items, conceptos y reglas.

### Listado de M4Objects
Para obtener un listado de todos los m4objects disponibles:
```bash
python -m tools.m4object.list_m4objects
```

Para filtrar por categoría:
```bash
python -m tools.m4object.list_m4objects --category PAYROLL
```

Para buscar por texto:
```bash
python -m tools.m4object.list_m4objects --search "employee"
```

### Generación de Diccionario
Para generar la documentación Markdown completa de todos los m4objects:
```bash
python -m tools.m4object.build_m4object_dictionary
```
Los ficheros se generan en `docs/02_m4object/channels/`.

### Ejemplos de Uso
**Comando básico:**
```bash
python -m tools.m4object.get_m4object "ABC"
```

**Con detalle de reglas y código fuente LN4:**
```bash
python -m tools.m4object.get_m4object "SCO_MNG_DEV_PRODUCT" --include-rules
```

**Resultado esperado (ejemplo simplificado):**
```json
{
  "status": "success",
  "id_t3": "ABC",
  "name_esp": "Canal ABC",
  "name_eng": "ABC Channel",
  "category": "HR_ADMIN",
  "stream_type": "Normal",
  "nodes": [
    {
      "id_node": "MAIN_NODE",
      "position": 1,
      "is_root": true,
      "ti": {
        "id_ti": "ABC_TI",
        "read_object": "EMPLOYEES",
        "write_object": "EMPLOYEES",
        "items": [
          {"id_item": "ID_EMPLOYEE", "is_pk": true, "m4_type": "STRING"},
          {
            "id_item": "GET_DATA", "item_type": 3, "m4_type": "VARIANT",
            "arguments": [
              {"id_argument": "AI_PARAM1", "position": 1, "m4_type": "STRING", "is_output": false},
              {"id_argument": "AO_RESULT", "position": 2, "m4_type": "VARIANT", "is_output": true}
            ]
          }
        ],
        "concepts": [
          {"id_concept": "CVE_SALARY", "id_item": "CVE_SALARY", "concept_type": 1}
        ],
        "rules_count": 5
      }
    }
  ],
  "summary": {
    "node_count": 1,
    "ti_count": 1,
    "total_items": 15,
    "total_concepts": 1,
    "total_rules": 5
  }
}
```
