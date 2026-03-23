---
nombre: "listar_roles_rsm"
version: "1.0.0"
descripcion: "Lista todos los roles RSM (Role Security Model) de PeopleNet con conteos de permisos a nivel de objeto y campo."
parametros: []
herramienta: "tools.bdl.list_rsm_roles"
---

## Documentación de la Skill: `listar_roles_rsm`

### Propósito
Lista todos los roles RSM del repositorio de seguridad. Los roles RSM definen los permisos de acceso a objetos lógicos y campos de la BDL, controlando qué datos puede ver y modificar cada perfil.

### Nota Organizacional
> La herramienta reside en `tools/bdl/` porque los roles RSM operan sobre objetos de la capa BDL (`M4RSC_RSM`, `M4RDC_SEC_LOBJ`, `M4RDC_SEC_FIELDS`). La skill se organiza bajo `03_security/` por afinidad de dominio.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con subconsultas**: Ejecuta un SELECT sobre `M4RSC_RSM` con conteos de permisos de `M4RDC_SEC_LOBJ` (objetos) y `M4RDC_SEC_FIELDS` (campos).
3. **Resultado JSON**: Devuelve la lista con nombre, RSM padre, ownership, usability y conteos de permisos.

### Ejemplos de Uso

**Listar todos los roles RSM:**
```bash
python -m tools.bdl.list_rsm_roles
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 15,
  "roles": [
    {
      "id_rsm": "RSM_ADMIN",
      "name": "Administrador",
      "parent_rsm": null,
      "ownership": "META4",
      "usability": "STANDARD",
      "object_permissions": 250,
      "field_permissions": 1200
    }
  ]
}
```
