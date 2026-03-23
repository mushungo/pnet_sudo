---
nombre: "describir_rol_rsm"
version: "1.0.0"
descripcion: "Obtiene la definición completa de un Rol RSM (Role Security Model) de PeopleNet, incluyendo sus permisos sobre objetos lógicos y campos."
parametros:
  - nombre: "id_rsm"
    tipo: "string"
    descripcion: "El identificador único del Rol RSM a describir. Ej: '_DEFAULT_VALUES', 'ADMIN_COMPENSACION'."
    requerido: true
herramienta: "tools.bdl.get_rsm_role"
---

## Documentación de la Skill: `describir_rol_rsm`

### Nota Organizacional
> La herramienta reside en `tools/bdl/` porque los roles RSM se almacenan en tablas de metadatos de la capa BDL (`M4RSC_RSM`, `M4RSC_RSM1`, `M4RDC_SEC_LOBJ`, `M4RDC_SEC_FIELDS`). La skill se organiza bajo `03_security/` por afinidad de dominio (los roles RSM son entidades del modelo de seguridad).

### Propósito
Esta skill permite introspeccionar los Roles de Seguridad (RSM - Role Security Model) del repositorio de metadatos de PeopleNet. Los roles RSM definen qué permisos (SELECT, INSERT, UPDATE, DELETE y sus variantes de corrección) tiene cada perfil sobre los objetos lógicos de la BDL. Hay 50 roles con 9,465 permisos sobre objetos y 2 permisos sobre campos específicos.

La skill consulta las tablas `M4RSC_RSM`, `M4RSC_RSM1`, `M4RDC_SEC_LOBJ` y `M4RDC_SEC_FIELDS`.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_rsm_role.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Rol**: Ejecuta una consulta sobre `M4RSC_RSM` y `M4RSC_RSM1` para obtener los detalles y comentarios del rol.
3.  **Consulta de Permisos sobre Objetos**: Ejecuta una consulta sobre `M4RDC_SEC_LOBJ` con JOIN a `M4RDC_LOGIC_OBJECT` para obtener todos los permisos CRUD sobre objetos.
4.  **Consulta de Permisos sobre Campos**: Ejecuta una consulta sobre `M4RDC_SEC_FIELDS` para obtener permisos a nivel de campo (lectura/escritura).
5.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON.
6.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar.

### Datos Disponibles
- **Rol**: ID, nombre (ESP/ENG), rol padre (herencia), ownership, usability, comentario.
- **Permisos sobre objetos**: SELECT/INSERT/UPDATE/DELETE + corrección, seguridad a nivel de campo, operaciones en cascada, herencia.
- **Permisos sobre campos**: Lectura/Escritura por campo específico.

### Listado de Roles
Para obtener un listado de todos los roles RSM:
```bash
python -m tools.bdl.list_rsm_roles
```

### Generación de Diccionario
Para generar la documentación Markdown completa de todos los roles:
```bash
python -m tools.bdl.build_rsm_dictionary
```
Los ficheros se generan en `docs/03_security/rsm_roles/`.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.get_rsm_role "ADMIN_COMPENSACION"
```

**Resultado esperado (ejemplo):**
```json
{
  "status": "success",
  "role": {
    "id_rsm": "ADMIN_COMPENSACION",
    "name": "ADMINISTRADOR DE COMPENSACIÓN SALARIAL",
    "name_eng": null,
    "parent_rsm": null,
    "ownership": null,
    "usability": null,
    "comment": null,
    "object_permissions_count": 150,
    "field_permissions_count": 0,
    "object_permissions": [
      {
        "id_object": "CCO_ANIO_SED",
        "description": "Año SED",
        "select": true,
        "insert": true,
        "update": true,
        "delete": true,
        "corr_insert": null,
        "corr_update": null,
        "corr_delete": null,
        "has_field_security": false,
        "cascade_oper": null,
        "inherited_from": null
      }
    ],
    "field_permissions": []
  }
}
```
