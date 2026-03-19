---
nombre: "describir_objeto_fisico"
version: "1.0.0"
descripcion: "Obtiene el detalle de un objeto físico de la BDL — la tabla SQL real con sus campos y el mapeo a campos lógicos."
parametros:
  - nombre: "id_real_object"
    tipo: "string"
    descripcion: "Nombre de la tabla SQL física. Ej: 'M4ACO_CR_SAL_STRUC'."
    requerido: true
---

## Documentación de la Skill: `describir_objeto_fisico`

### Propósito
Complementa la skill `describir_bdl_object` mostrando el lado físico: cómo un objeto lógico se materializa en tablas SQL reales. Incluye el mapeo campo-a-campo entre lógico y físico, y los índices con sus propiedades de tuning (unique, clustered, fill factor).

### Flujo de Trabajo
1. **Objeto principal**: Consulta M4RDC_REAL_OBJECTS para obtener tipo y objeto lógico padre.
2. **Campos físicos**: Consulta M4RDC_REAL_FIELDS para el mapeo campo físico → campo lógico.
3. **Índices**: Consulta M4RDC_REAL_INDEX para propiedades de tuning de SQL Server.

### Ejemplos de Uso

**Obtener detalle de una tabla física:**
```bash
python -m tools.bdl.get_real_object "M4ACO_CR_SAL_STRUC"
```

**Listar todas las tablas físicas de un objeto lógico:**
```bash
python -m tools.bdl.list_real_objects --object "ACO_CR_SAL_STRUC"
```

**Listar solo vistas:**
```bash
python -m tools.bdl.list_real_objects --type 4
```
