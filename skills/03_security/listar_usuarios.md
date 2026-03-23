---
nombre: "listar_usuarios"
version: "1.0.0"
descripcion: "Lista todos los usuarios de aplicación (APPUSER) del repositorio de seguridad de PeopleNet, con filtros por tipo, búsqueda y estado de bloqueo."
parametros:
  - nombre: "type"
    tipo: "string"
    descripcion: "Filtrar por tipo de usuario. Ej: 'Person', 'System'."
    requerido: false
  - nombre: "search"
    tipo: "string"
    descripcion: "Buscar en ID o nombre de usuario. Ej: 'ADMIN'."
    requerido: false
  - nombre: "locked"
    tipo: "boolean"
    descripcion: "Si es true, solo muestra usuarios bloqueados."
    requerido: false
herramienta: "tools.security.list_users"
---

## Documentación de la Skill: `listar_usuarios`

### Propósito
Lista todos los usuarios de aplicación (APPUSER) del repositorio de seguridad de PeopleNet. Incluye información sobre tipo de usuario, rol por defecto, estado de bloqueo, sesiones máximas y conteo de roles asignados.

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con JOIN**: Ejecuta un SELECT sobre `M4RSC_APPUSER` con LEFT JOIN a `M4RSC_APP_USR_ROLE` para contar roles.
3. **Filtrado opcional**: Permite filtrar por `--type`, `--search` y `--locked`.
4. **Resultado JSON**: Devuelve la lista con todos los campos del usuario y conteo de roles.

### Ejemplos de Uso

**Listar todos:**
```bash
python -m tools.security.list_users
```

**Filtrar por tipo:**
```bash
python -m tools.security.list_users --type Person
```

**Buscar:**
```bash
python -m tools.security.list_users --search "ADMIN"
```

**Solo bloqueados:**
```bash
python -m tools.security.list_users --locked
```
