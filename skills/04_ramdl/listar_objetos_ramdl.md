---
nombre: "listar_objetos_ramdl"
version: "1.0.0"
descripcion: "Lista todos los objetos RAMDL (transporte) del repositorio de PeopleNet, agrupados por versión, o lista las versiones disponibles."
parametros:
  - nombre: "versions"
    tipo: "boolean"
    descripcion: "Si se pasa --versions, lista solo las versiones RAMDL disponibles en vez de los objetos."
    requerido: false
herramienta: "tools.bdl.list_ramdl_objects"
---

## Documentación de la Skill: `listar_objetos_ramdl`

### Propósito
Lista todos los objetos RAMDL del repositorio. RAMDL (Repository Administration and Meta-Data Language) es el sistema de transporte de metadatos de PeopleNet: permite exportar e importar definiciones de objetos entre entornos.

### Nota Organizacional
> La herramienta reside en `tools/bdl/` porque los objetos RAMDL se almacenan en tablas de la capa BDL (`M4RDC_RAMDL_OBJECTS`, `M4RDC_RAMDL_VER`). La skill se organiza bajo `04_ramdl/` por afinidad de dominio.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta agrupada**: Ejecuta un SELECT sobre `M4RDC_RAMDL_OBJECTS` agrupando versiones por objeto.
3. **Modo versiones**: Con `--versions`, consulta `M4RDC_RAMDL_VER` para listar las versiones disponibles.
4. **Resultado JSON**: Devuelve la lista con nombre, rango de versiones y conteo de versiones.

### Ejemplos de Uso

**Listar todos los objetos:**
```bash
python -m tools.bdl.list_ramdl_objects
```

**Listar solo versiones:**
```bash
python -m tools.bdl.list_ramdl_objects --versions
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 200,
  "objects": [
    {
      "id_object": "EMPLOYEE",
      "name": "Empleado",
      "min_version": "7.0.0",
      "max_version": "8.1.7",
      "version_count": 5
    }
  ]
}
```
