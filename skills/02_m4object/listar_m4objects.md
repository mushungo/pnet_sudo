---
# Metadata estructurada de la Skill
nombre: "listar_m4objects"
version: "1.0.0"
descripcion: "Lista todos los m4objects (canales) disponibles en PeopleNet, con filtros opcionales por categoría o texto libre."
parametros:
  - nombre: "category"
    tipo: "string"
    descripcion: "Filtrar por categoría del canal (ej: PAYROLL, HR_ADMIN)."
    requerido: false
  - nombre: "search"
    tipo: "string"
    descripcion: "Texto libre para buscar en ID_T3, nombre ESP o nombre ENG."
    requerido: false
---

# (Documentación para humanos)

## Documentación de la Skill: `listar_m4objects`

### Propósito
Esta skill permite a los agentes obtener un listado de todos los m4objects (canales) disponibles en el repositorio de PeopleNet, con información resumida de cada uno. Es útil para descubrir canales, filtrar por categoría funcional o buscar por nombre.

Hay aproximadamente **6,386 canales** en el repositorio.

### Flujo de Trabajo
La skill invoca el script `tools/m4object/list_m4objects.py`, que:
1. Consulta `M4RCH_T3S` JOIN `M4RCH_NODES` para obtener los canales con conteo de nodos.
2. Aplica filtros opcionales por categoría o texto libre.
3. Devuelve un JSON con la lista y el total.

### Datos Disponibles por Canal
- **id_t3**: Identificador único del canal.
- **name_esp / name_eng**: Nombres descriptivos en español e inglés.
- **category / subcategory**: Categoría y subcategoría funcional.
- **stream_type**: Tipo de stream (STANDARD, etc.).
- **exe_type**: Tipo de ejecución (CLIENT, SERVER, etc.).
- **has_security**: Si tiene control de seguridad.
- **is_external**: Si es un canal externo.
- **node_count**: Número de nodos del canal.

### Ejemplos de Uso

**Listar todos los m4objects:**
```bash
python -m tools.m4object.list_m4objects
```

**Filtrar por categoría:**
```bash
python -m tools.m4object.list_m4objects --category PAYROLL
```

**Buscar por texto:**
```bash
python -m tools.m4object.list_m4objects --search "employee"
```

**Resultado esperado (ejemplo):**
```json
{
  "status": "success",
  "total": 6386,
  "m4objects": [
    {
      "id_t3": "ABC",
      "name_esp": "Canal ABC",
      "name_eng": "ABC Channel",
      "category": "HR_ADMIN",
      "subcategory": null,
      "stream_type": "STANDARD",
      "exe_type": "CLIENT",
      "has_security": true,
      "is_external": false,
      "node_count": 3
    }
  ]
}
```

### Skill Relacionada
Para obtener los detalles completos de un canal específico, usar la skill `describir_m4object`.
