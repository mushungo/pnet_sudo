---
# Metadata estructurada de la Skill
nombre: "describir_m4object"
version: "1.0.0"
descripcion: "Obtiene la definición completa de un m4object (canal) de PeopleNet, incluyendo su herencia, nodos, TIs, items y reglas."
parametros:
  - nombre: "id_t3"
    tipo: "string"
    descripcion: "El identificador del m4object (canal) a describir. Ej: ABC, SCO_MNG_DEV_PRODUCT."
    requerido: true
  - nombre: "include_rules"
    tipo: "boolean"
    descripcion: "Si true, incluye el detalle de reglas por TI (no solo el conteo)."
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
          │    └─ Argumentos (ITEM_ARGS)
          └─ Reglas (RULES) — lógica de negocio en LN4
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
7. **Reglas**: Consulta `M4RCH_RULES` para el conteo (y opcionalmente detalle) de reglas por TI.
8. **Ensamblaje**: Estructura todo en un JSON jerárquico con un resumen (totales de nodos, TIs, items, reglas).

### Datos Disponibles
- **Canal (T3)**: ID, nombre ESP/ENG, categoría, subcategoría, stream type, tipo de ejecución, flags de seguridad/externo/cacheable/separable, servicio, tipo de organización, fechas.
- **Herencia**: Canales base y tipo de herencia.
- **Conectores**: Identificador, nodo origen, nodo conector, item conector, tipo.
- **Nodos**: ID, posición, nombre, tipo, root flag, autoload, filas únicas, visibilidad, afecta BD, DMD, RSM, filtro dinámico.
- **TI**: ID, nombre, TI base (herencia), objetos BDL de lectura/escritura, sentencias, flags de sistema y generación SQL.
- **Items**: ID, tipo, M4 type, objetos y campos de lectura/escritura, visibilidad, PK, posición, nombre, tipo interno, tipo CS, método.
- **Reglas**: Conteo por TI (siempre), y opcionalmente: ID regla, item, tipo de regla, tipo de disparo, orden de ejecución.
- **Resumen**: Conteos totales de nodos, TIs, items y reglas.

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

**Con detalle de reglas:**
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
  "stream_type": "STANDARD",
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
          {"id_item": "ID_EMPLOYEE", "is_pk": true, "m4_type": "STRING"}
        ],
        "rules_count": 5
      }
    }
  ],
  "summary": {
    "node_count": 1,
    "ti_count": 1,
    "total_items": 15,
    "total_rules": 5
  }
}
```
