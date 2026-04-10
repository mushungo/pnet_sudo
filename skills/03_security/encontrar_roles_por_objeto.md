---
nombre: "encontrar_roles_por_objeto"
version: "1.0.0"
descripcion: "Encuentra todos los roles de aplicación que tienen permisos explícitos sobre un M4Object (canal/nodo/item)."
herramienta: "tools.security.find_roles_for_object"
parametros:
  - nombre: "id_t3"
    tipo: "string"
    descripcion: "Identificador del canal (ID_T3) a consultar."
    requerido: true
  - nombre: "id_node"
    tipo: "string"
    descripcion: "Filtrar por nodo específico dentro del canal."
    requerido: false
  - nombre: "id_item"
    tipo: "string"
    descripcion: "Filtrar por item específico (requiere --node)."
    requerido: false
---

## Documentación de la Skill: `encontrar_roles_por_objeto`

### Propósito

Traza la relación inversa de seguridad: dado un M4Object (canal), responde "¿Qué roles tienen permisos sobre este canal?". Es el complemento inverso de `describir_rol_aplicacion` (que va de rol -> permisos sobre objetos).

Consulta `M4RSC_CLIENT_USE` con JOIN a `M4RSC_APPROLE` para resolver los nombres de los roles.

### Flujo de Trabajo

1. **Búsqueda base**: Filtra `M4RSC_CLIENT_USE` por `ID_T3 = ?`.
2. **Filtros opcionales**: Si se especifica `--node`, añade filtro por `ID_NODE`. Si se especifica `--item`, añade filtro por `ID_ITEM`.
3. **Resolución de nombres**: JOIN con `M4RSC_APPROLE` para obtener el nombre ESP/ENG de cada rol.
4. **Agrupación**: Los permisos se agrupan por rol, mostrando cada permiso individual (nodo/item + flags R/W/X).

### Datos Disponibles

- **Rol**: ID, nombre ESP/ENG.
- **Permisos por nodo/item**: can_read, can_write, can_execute, must_authenticate, encrypted.
- **Conteos**: Total de roles distintos y total de registros de permisos.

### Ejemplos de Uso

**Todos los roles con permisos sobre un canal:**
```bash
python -m tools.security.find_roles_for_object "SCO_MNG_DEV_PRODUCT"
```

**Filtrar por nodo:**
```bash
python -m tools.security.find_roles_for_object "SCO_MNG_DEV_PRODUCT" --node "MAIN_NODE"
```

**Filtrar por item específico:**
```bash
python -m tools.security.find_roles_for_object "SCO_MNG_DEV_PRODUCT" --node "MAIN_NODE" --item "CVE_STATUS"
```

### Resultado Esperado (ejemplo simplificado)

```json
{
  "status": "success",
  "object_searched": {"id_t3": "SCO_MNG_DEV_PRODUCT", "id_node": null, "id_item": null},
  "count": 2,
  "total_permissions": 15,
  "roles": [
    {
      "id_role": "ADMIN",
      "name_esp": "Administrador",
      "permissions": [
        {"id_node": "MAIN_NODE", "id_item": null, "can_read": true, "can_write": true, "can_execute": true}
      ]
    }
  ]
}
```
