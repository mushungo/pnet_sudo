---
nombre: "describir_rol_aplicacion"
version: "1.0.0"
descripcion: "Obtiene el detalle completo de un rol de aplicación de PeopleNet, incluyendo usuarios asignados y permisos de cliente."
parametros:
  - nombre: "id_app_role"
    tipo: "string"
    descripcion: "Identificador del rol de aplicación. Ej: 'M4ADM', 'ADMIN_NOMINA'."
    requerido: true
---

## Documentación de la Skill: `describir_rol_aplicacion`

### Propósito
Obtiene la información completa de un rol del subsistema de seguridad de PeopleNet. Incluye los usuarios asignados al rol y los permisos de cliente (CLIENT_USE) que controlan acceso a T3s, nodos e items.

### Flujo de Trabajo
1. **Rol principal**: Consulta M4RSC_APPROLE para datos descriptivos.
2. **Usuarios**: Consulta M4RSC_APP_USR_ROLE + APPUSER para usuarios asignados con fechas y organización.
3. **Permisos**: Consulta M4RSC_CLIENT_USE para permisos granulares (read/write/execute/authenticate/encrypted).

### Ejemplos de Uso

**Obtener detalle de un rol:**
```bash
python -m tools.security.get_role "M4ADM"
```

**Listar todos los roles:**
```bash
python -m tools.security.list_roles
```

**Buscar roles:**
```bash
python -m tools.security.list_roles --search "ADMIN"
```
