---
nombre: "describir_menu"
version: "1.2.0"
descripcion: "Obtiene el detalle completo de una opción de menú de PeopleNet: definición, árbol, argumentos, uso y favoritos."
parametros:
  - nombre: "id_menu"
    tipo: "string"
    requerido: true
    descripcion: "Identificador lógico del menú (ej: HRM_EMPLOYEES)"
  - nombre: "include_children"
    tipo: "boolean"
    requerido: false
    descripcion: "Incluir hijos directos en el árbol"
  - nombre: "include_hits"
    tipo: "boolean"
    requerido: false
    descripcion: "Incluir detalle de contadores de uso por usuario"
  - nombre: "include_bp"
    tipo: "boolean"
    requerido: false
    descripcion: "Incluir definición del BP vinculado y sus presentaciones asociadas"
---

## Documentacion de la Skill: `describir_menu`

### Proposito
Obtiene la definición completa de una opción de menú de PeopleNet, incluyendo: textos multilingue, tareas vinculadas, posiciones en el árbol jerárquico, argumentos configurados, estadísticas de uso y favoritos.

### Datos Recuperados
| Sección | Tabla | Descripción |
|---|---|---|
| Definición | `M4RMN_OPTIONS` | Textos en 7 idiomas, BP, icono, rol, versión, keywords, PNet+ |
| URLs | `M4RMN_OPTIONS1` | Páginas JSP/HTTP por idioma |
| Árbol (padres) | `M4RMN_TREE` | En qué nodos del árbol aparece esta opción |
| Hijos | `M4RMN_TREE` | Opciones hijas directas (con --include-children) |
| Argumentos | `M4RMN_ARGUMENTS` | Pares clave-valor por entrada de árbol |
| Uso | `M4RMN_MENU_HITS` | Contadores de visitas por usuario |
| Favoritos | `M4RMN_FAVORIT_TREE` | Conteo de usuarios que tienen esta opción como favorita |

### Campos Clave de M4RMN_OPTIONS
- **ID_MENU**: identificador lógico único
- **TRANS_MENU{ESP,ENG,...}**: texto corto del menú (7 idiomas)
- **N_MENU{ESP,ENG,...}**: descripción larga (VARCHAR 2000)
- **ID_BP / ID_BP_AUX_1 / ID_BP_AUX_2**: tareas de negocio vinculadas (seguridad ACL)
- **ID_APPROLE**: rol de aplicación requerido
- **ID_DEPENDING_MENU**: padre en la peineta PNet+ (modo red)
- **ID_SCREEN**: identificador de pantalla asociada
- **KEYWORDS{ESP,ENG,...}**: palabras clave de búsqueda
- **OWNER_FLAG**: nivel de herencia (rango numérico, ver decodificación)

### Decodificación de OWNER_FLAG (por rangos)
| Rango | Significado |
|---|---|
| 0 | Sin propietario |
| 1 | Standard |
| 2 | Standard Extendido |
| 3-9 | Reservado |
| 10-19 | Standard Premium |
| 20 | Corporate |
| 21 | Corporate Extendido |
| 22-29 | Reservado Corporate |
| 40-49 | Country |
| 50-99 | Client |
| >99 | Custom |

### Arquitectura de Seguridad: ID_APPROLE en Cascada
El campo `ID_APPROLE` aparece en todas las tablas de menú, controlando visibilidad en cada nivel:

| Tabla | Controla |
|---|---|
| `SMN_OPTIONS.ID_APPROLE` | Quién ve la opción en el catálogo |
| `SMN_TREE.ID_APPROLE` | Quién ve la opción en esa posición del árbol (puede diferir por padre) |
| `SMN_FAVOURITES` / `SMN_FAVORIT_TREE` | Contexto de rol en favoritos |
| `SMN_MENU_HITS` | Contexto de rol en tracking de uso |

Una misma opción puede tener roles distintos en cada nivel: visible en el catálogo pero restringida en cierto nodo del árbol.

### Transporte RAMDL
Los menús se transportan entre entornos (desarrollo, testing, producción) mediante paquetes RAMDL:

| Objeto RAMDL | Versiones | Qué transporta |
|---|---|---|
| `MENU OPTION` | v60250+ (2 versiones) | Opciones de menú individuales |
| `APP_ROLE` | v60250+ | Roles de aplicación (la FK maestra de acceso a menús) |

Los menús se generan como archivos `.js` en el App Server y se transfieren al cliente por sesión HTTP.

### Gap: CCT No Audita Menus
Las tablas `M4RMN_*` tienen campos auditables (`ID_SECUSER`, `DT_LAST_UPDATE`, `ID_APPROLE`), pero el CCT (Change Control Tool) **no cubre menús** en su ciclo estándar. Los objetos auditados por CCT son: FIELD, ITEM, PAYROLL ITEM, PRESENTATION, RULE, CONCEPT, SENTENCE. Esto implica que las modificaciones a menús no quedan trazadas en el control de cambios formal.

### Gotchas
- El campo `VALUE` del objeto `SMN_ARGUMENTS` se almacena en la columna SQL `ZVALUE` (no `VALUE`).
- El campo `ID_APP_USER` se almacena como `ID_SECUSER` en todas las tablas `M4RMN_*`.
- Una misma opción puede aparecer en múltiples posiciones del árbol (clave compuesta `ID_MENU + ID_PARENT_MENU` en `SMN_TREE`).

### Cadena Completa: Menú → BP → Presentación
Cada opción de menú está vinculada a un Business Process (`ID_BP`), y cada BP puede tener presentaciones asociadas. La cadena completa de trazabilidad es:

```
M4RMN_OPTIONS (menú)
    ↓ ID_BP
M4RBP_DEF (Business Process)
    ↓ ID_BP
M4RCH_TASK_PRESENTATION (presentaciones vinculadas)
    ↓ ID_PRESENTATION
M4RPT_PRESENTATION (definición de presentación)
```

Para recuperar la cadena completa con `--include-bp`:
- Se consulta el BP vinculado en `ID_BP`
- Se obtiene la definición básica desde `M4RBP_DEF`
- Se listan las presentaciones desde `M4RCH_TASK_PRESENTATION`

### Flujo de Trabajo
1. Conecta a la BD de metadatos.
2. Consulta la definición principal en M4RMN_OPTIONS.
3. Obtiene URLs de M4RMN_OPTIONS1.
4. Recupera las posiciones en el árbol (padres) desde M4RMN_TREE.
5. Opcionalmente lista hijos directos (--include-children).
6. Consulta argumentos de M4RMN_ARGUMENTS.
7. Obtiene estadísticas de uso de M4RMN_MENU_HITS.
8. Cuenta usuarios que la tienen en favoritos via M4RMN_FAVORIT_TREE.
9. Opcionalmente obtiene el BP vinculado y sus presentaciones (--include-bp).

### Ejemplo de Uso
```bash
# Detalle basico
python -m tools.menus.get_menu HRM_EMPLOYEES

# Con hijos directos
python -m tools.menus.get_menu PEOPLENET --include-children

# Con detalle de uso por usuario
python -m tools.menus.get_menu HRM_EMPLOYEES --include-hits

# Con BP vinculado y presentaciones
python -m tools.menus.get_menu HRM_EMPLOYEES --include-bp
```

**Resultado esperado (resumido):**
```json
{
  "id_menu": "HRM_EMPLOYEES",
  "names": {"esp": "Empleados", "eng": "Employees", "fra": "Employés"},
  "business_process": {"id_bp": "HRM_EMPLOYEES_BP", "id_bp_aux_1": null, "id_bp_aux_2": null},
  "owner_flag": 1,
  "owner_flag_name": "Standard",
  "tree_positions": [
    {"id_parent_menu": "HRM_MAIN", "parent_name_esp": "Recursos Humanos", "position": 3}
  ],
  "arguments": [],
  "hit_summary": {"distinct_users": 45, "total_hits": 1230},
  "favourites_count": 12
}
```
