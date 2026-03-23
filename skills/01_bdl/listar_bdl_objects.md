---
nombre: "listar_bdl_objects"
version: "1.0.0"
descripcion: "Lista todos los objetos lógicos (BDL) disponibles en el repositorio de metadatos de PeopleNet."
parametros: []
herramienta: "tools.bdl.list_bdl_objects"
---

## Documentación de la Skill: `listar_bdl_objects`

### Propósito
Lista todos los identificadores de objetos lógicos de la Base de Datos Lógica (BDL) de PeopleNet. Es el punto de entrada para explorar el catálogo completo de entidades de datos del repositorio.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta de Metadatos**: Ejecuta un SELECT sobre `M4RDC_LOGIC_OBJECT` ordenado por `ID_OBJECT`.
3. **Resultado JSON**: Devuelve un array de identificadores de objeto.

### Ejemplos de Uso

**Listar todos los objetos:**
```bash
python -m tools.bdl.list_bdl_objects
```

**Resultado esperado:**
```json
{
  "status": "success",
  "objects": [
    "ACO_CR_SAL_STRUC",
    "EMPLOYEE",
    "..."
  ]
}
```
