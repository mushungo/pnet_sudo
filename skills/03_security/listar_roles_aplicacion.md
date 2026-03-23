---
nombre: "listar_roles_aplicacion"
version: "1.0.0"
descripcion: "Lista todos los roles de aplicación (APPROLE) del repositorio de seguridad de PeopleNet, con conteo de usuarios asignados."
parametros:
  - nombre: "search"
    tipo: "string"
    descripcion: "Buscar en ID o nombres del rol. Ej: 'ADMIN'."
    requerido: false
herramienta: "tools.security.list_roles"
---

## Documentación de la Skill: `listar_roles_aplicacion`

### Propósito
Lista todos los roles de aplicación (APPROLE) del repositorio de seguridad. Los APPROLE determinan qué funcionalidades y menús puede acceder un usuario, a diferencia de los RSM que controlan permisos a nivel de datos.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con JOIN**: Ejecuta un SELECT sobre `M4RSC_APPROLE` con LEFT JOIN a `M4RSC_APP_USR_ROLE` para contar usuarios asignados.
3. **Filtrado opcional**: Permite buscar por `--search` en ID y nombres.
4. **Resultado JSON**: Devuelve la lista con ID, nombres bilingues y conteo de usuarios.

### Ejemplos de Uso

**Listar todos:**
```bash
python -m tools.security.list_roles
```

**Buscar:**
```bash
python -m tools.security.list_roles --search "ADMIN"
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 30,
  "roles": [
    {
      "id_app_role": "ADMIN_GENERAL",
      "name_esp": "Administrador General",
      "name_eng": "General Administrator",
      "user_count": 5
    }
  ]
}
```
