---
nombre: "describir_usuario"
version: "1.0.0"
descripcion: "Obtiene el detalle completo de un usuario de aplicación de PeopleNet, incluyendo roles, alias de dominio y permisos."
parametros:
  - nombre: "id_app_user"
    tipo: "string"
    descripcion: "Identificador del usuario de aplicación. Ej: 'M4ADM'."
    requerido: true
---

## Documentación de la Skill: `describir_usuario`

### Propósito
Obtiene la información completa de un usuario del subsistema de seguridad de PeopleNet (M4RSC). Incluye datos del usuario, roles asignados con validez temporal, y alias de dominio para autenticación LDAP/AD.

### Flujo de Trabajo
1. **Usuario principal**: Consulta M4RSC_APPUSER para datos base.
2. **Roles**: Consulta M4RSC_APP_USR_ROLE + APPROLE para roles asignados con fechas de validez y organización.
3. **Alias**: Consulta M4RSC_USER_ALIAS para mapeos usuario→dominio.

### Ejemplos de Uso

**Obtener detalle de un usuario:**
```bash
python -m tools.security.get_user "M4ADM"
```

**Listar todos los usuarios:**
```bash
python -m tools.security.list_users
```

**Buscar usuarios bloqueados:**
```bash
python -m tools.security.list_users --locked
```

**Buscar por nombre:**
```bash
python -m tools.security.list_users --search "ADMIN"
```
