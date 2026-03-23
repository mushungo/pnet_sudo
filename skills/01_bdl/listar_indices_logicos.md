---
nombre: "listar_indices_logicos"
version: "1.0.0"
descripcion: "Lista todos los índices lógicos de la BDL de PeopleNet con conteos de columnas y columnas INCLUDE."
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "Filtrar por objeto lógico específico. Ej: 'EMPLOYEE'."
    requerido: false
herramienta: "tools.bdl.list_indexes"
---

## Documentación de la Skill: `listar_indices_logicos`

### Propósito
Lista todos los índices lógicos definidos en la BDL. Cada índice está asociado a un objeto lógico y contiene columnas de clave y columnas INCLUDE.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con subconsultas**: Ejecuta un SELECT sobre `M4RDC_INDEX` con JOINs a `M4RDC_LOGIC_OBJECT` y subconsultas de conteo sobre `M4RDC_INDEX_COLS` e `M4RDC_INDEX_INCLUDE_COLS`.
3. **Filtrado opcional**: Permite filtrar por `ID_OBJECT`.
4. **Resultado JSON**: Devuelve la lista con identificador, objeto, unicidad, conteos de columnas.

### Ejemplos de Uso

**Listar todos los índices:**
```bash
python -m tools.bdl.list_indexes
```

**Filtrar por objeto:**
```bash
python -m tools.bdl.list_indexes "EMPLOYEE"
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 150,
  "indexes": [
    {
      "id_index": "IX_EMP_NAME",
      "id_object": "EMPLOYEE",
      "object_description": "Empleado",
      "is_unique": false,
      "real_name": "M4IX_EMP_NAME",
      "column_count": 3,
      "include_column_count": 0
    }
  ]
}
```
