---
nombre: "listar_modulos_datos"
version: "1.0.0"
descripcion: "Lista todos los módulos de datos (Case Modules) disponibles en el repositorio de metadatos de PeopleNet."
parametros: []
herramienta: "tools.bdl.list_case_modules"
---

## Documentación de la Skill: `listar_modulos_datos`

### Propósito
Lista todos los módulos de datos (Case Modules) del repositorio. Un Case Module agrupa objetos lógicos y relaciones en una unidad lógica de negocio, controlando ownership y usabilidad.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con subconsultas**: Ejecuta un SELECT sobre `M4RDD_CASE_MODULES` con conteos de objetos (`M4RDD_CMOD_OBJS`) y relaciones (`M4RDD_CMOD_RELS`).
3. **Resultado JSON**: Devuelve la lista con nombre, flags de ownership/usability y conteos.

### Ejemplos de Uso

**Listar todos los módulos:**
```bash
python -m tools.bdl.list_case_modules
```

**Resultado esperado:**
```json
{
  "status": "success",
  "count": 25,
  "modules": [
    {
      "id_module": "MOD_PAYROLL",
      "name": "Módulo de Nómina",
      "owner_flag": 1,
      "ownership": "META4",
      "usability": "STANDARD",
      "object_count": 15,
      "relation_count": 8
    }
  ]
}
```
