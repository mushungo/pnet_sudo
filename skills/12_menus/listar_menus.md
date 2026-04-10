---
nombre: "listar_menus"
version: "1.1.0"
descripcion: "Lista las opciones de menú de PeopleNet con filtros por texto, rol de aplicación o menú padre."
parametros:
  - nombre: "search"
    tipo: "string"
    requerido: false
    descripcion: "Texto a buscar en ID, nombre ESP/ENG o palabras clave"
  - nombre: "role"
    tipo: "string"
    requerido: false
    descripcion: "Filtrar por ID_APPROLE"
  - nombre: "parent"
    tipo: "string"
    requerido: false
    descripcion: "Mostrar hijos directos de un ID_PARENT_MENU"
---

## Documentacion de la Skill: `listar_menus`

### Proposito
Lista las opciones de menú registradas en el catálogo SMN_OPTIONS (tabla física M4RMN_OPTIONS) de PeopleNet. Permite buscar por texto libre, filtrar por rol de aplicación, o navegar el árbol mostrando hijos directos de un nodo padre.

### Contexto del Sistema de Menus
PeopleNet implementa un sistema de menús con dos capas:
- **SMN_OPTIONS** (M4RMN_OPTIONS) = catálogo de opciones (qué existe)
- **SMN_TREE** (M4RMN_TREE) = árbol jerárquico (dónde aparece cada opción)

Cada opción de menú se vincula a una **tarea** (Business Process = ID_BP) que determina la seguridad ACL. Los menús se generan como archivos `.js` en el App Server y se transfieren al cliente por sesión.

### Case Module MENUS
El módulo lógico `MENUS` agrupa los siguientes objetos BDL:

| Objeto | Tabla Física | Descripción |
|---|---|---|
| `SMN_OPTIONS` | `M4RMN_OPTIONS` + `M4RMN_OPTIONS1` | Catálogo de opciones (textos, BP, icono, rol, URLs) |
| `SMN_TREE` | `M4RMN_TREE` | Árbol jerárquico padre-hijo con posición y rol |
| `SMN_ARGUMENTS` | `M4RMN_ARGUMENTS` | Argumentos clave-valor por entrada de árbol |
| `SMN_MENU_HITS` | `M4RMN_MENU_HITS` | Tracking de visitas por usuario |
| `SMN_FAVOURITES` | `M4RMN_FAVOURITES` | Menús favoritos por usuario |
| `SMN_FAVORIT_TREE` | `M4RMN_FAVORIT_TREE` | Árbol de favoritos por sociedad/usuario |

### Tablas Consultadas por la Herramienta
- `M4RMN_OPTIONS` — Catálogo de opciones de menú (ID, nombres multilingue, BP, icono, rol, versión)
- `M4RMN_TREE` — Árbol jerárquico (usado cuando se filtra por --parent o --role)

### Niveles de Herencia (OWNER_FLAG)
| Nivel | Rango de menú |
|---|---|
| Standard | 1 - 39 |
| Corporate | 40 - 49 |
| Country | Rangos específicos por país |

### Arquitectura de Seguridad: ID_APPROLE
Al filtrar por `--role`, la herramienta busca el `ID_APPROLE` en dos niveles:
- **SMN_OPTIONS.ID_APPROLE** — restricción a nivel de catálogo (la opción completa)
- **SMN_TREE.ID_APPROLE** — restricción a nivel de posición en el árbol (puede diferir por padre)

Esto significa que un menú puede ser visible para un rol en un nodo del árbol pero no en otro. La tarea BP vinculada (`ID_BP`) añade un tercer nivel de control vía `M4RBP_APPROLE` (roles autorizados por tarea).

### Transporte RAMDL
Las opciones de menú se transportan entre entornos mediante paquetes RAMDL:

| Objeto RAMDL | Versiones | Qué transporta |
|---|---|---|
| `MENU OPTION` | v60250+ (2 versiones) | Opciones de menú individuales |
| `APP_ROLE` | v60250+ | Roles de aplicación (la FK maestra de acceso) |

### Flujo de Trabajo
1. Conecta a la BD de metadatos de PeopleNet.
2. Consulta M4RMN_OPTIONS con JOIN a M4RMN_TREE si se filtra por padre o rol.
3. Devuelve JSON con ID, nombres ESP/ENG, tarea BP, icono, rol, versión y timestamps.

### Ejemplo de Uso
```bash
# Listar todos los menus (hasta 200)
python -m tools.menus.list_menus

# Buscar menus por texto
python -m tools.menus.list_menus --search "empleado"

# Menus visibles para un rol
python -m tools.menus.list_menus --role HRM_MANAGER

# Hijos directos de un nodo del arbol
python -m tools.menus.list_menus --parent PEOPLENET
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 15,
  "filters": {"search": "empleado", "role": null, "parent": null, "limit": 200},
  "menus": [
    {
      "id_menu": "HRM_EMPLOYEES",
      "name_esp": "Empleados",
      "name_eng": "Employees",
      "id_bp": "HRM_EMPLOYEES_BP",
      "icon": "employee_icon",
      "owner_flag": 1,
      "id_approle": "HRM_MANAGER",
      "available_version": "60250",
      "id_depending_menu": null,
      "show_in_map": true,
      "dt_last_update": "2025-01-15 10:30:00"
    }
  ]
}
```
