---
nombre: "listar_vistas_sql"
version: "1.0.0"
descripcion: "Lista todas las vistas SQL definidas en la BDL de PeopleNet con un resumen de cada una."
parametros: []
herramienta: "tools.bdl.list_views"
---

## Documentación de la Skill: `listar_vistas_sql`

### Propósito
Lista todas las vistas SQL del repositorio de metadatos BDL. Cada vista está registrada en `M4RDC_VIEW_CODE` y asociada a un objeto lógico de `M4RDC_LOGIC_OBJECT`.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con JOIN**: Ejecuta un SELECT sobre `M4RDC_VIEW_CODE` con JOIN a `M4RDC_LOGIC_OBJECT` para obtener la descripción.
3. **Resultado JSON**: Devuelve la lista con identificador, descripción, nombre real, si es real (materializada) y fechas de creación/modificación.

### Ejemplos de Uso

**Listar todas las vistas:**
```bash
python -m tools.bdl.list_views
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 42,
  "views": [
    {
      "id_object": "VW_EMPLOYEE_SUMMARY",
      "description": "Vista resumen de empleados",
      "real_name": "M4VW_EMPLOYEE_SUMMARY",
      "is_real": true,
      "dt_create": "2020-01-15",
      "dt_mod": "2023-06-20"
    }
  ]
}
```
