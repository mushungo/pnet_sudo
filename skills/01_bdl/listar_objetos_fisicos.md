---
nombre: "listar_objetos_fisicos"
version: "1.0.0"
descripcion: "Lista los objetos físicos (tablas SQL reales) del repositorio BDL de PeopleNet, mostrando el mapeo entre objetos lógicos y sus tablas SQL."
parametros:
  - nombre: "object"
    tipo: "string"
    descripcion: "Filtrar por objeto lógico específico. Ej: 'EMPLOYEE'."
    requerido: false
  - nombre: "type"
    tipo: "integer"
    descripcion: "Filtrar por tipo de objeto (1=table, 3=overflow, 4=view, 5=master_overflow, 7=custom_m4, 8=hash_temp)."
    requerido: false
  - nombre: "search"
    tipo: "string"
    descripcion: "Buscar en nombres de objetos físicos o lógicos. Ej: 'EMPLOYEE'."
    requerido: false
herramienta: "tools.bdl.list_real_objects"
---

## Documentación de la Skill: `listar_objetos_fisicos`

### Propósito
Lista todos los objetos físicos (REAL_OBJECTS) de la BDL de PeopleNet. Muestra el mapeo entre cada objeto lógico y sus tablas SQL físicas, incluyendo el tipo de objeto y si es la tabla principal.

### Contexto
En PeopleNet, un objeto lógico puede tener múltiples objetos físicos: tabla principal, tablas de overflow, vistas, etc. Esta skill permite navegar ese mapeo.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con filtros**: Ejecuta un SELECT sobre `M4RDC_REAL_OBJECTS` con filtros opcionales.
3. **Resultado JSON**: Devuelve la lista con tipo, tabla principal y PK name.

### Ejemplos de Uso

**Listar todos:**
```bash
python -m tools.bdl.list_real_objects
```

**Filtrar por objeto lógico:**
```bash
python -m tools.bdl.list_real_objects --object "EMPLOYEE"
```

**Filtrar por tipo (solo tablas):**
```bash
python -m tools.bdl.list_real_objects --type 1
```

**Buscar:**
```bash
python -m tools.bdl.list_real_objects --search "SALARY"
```
