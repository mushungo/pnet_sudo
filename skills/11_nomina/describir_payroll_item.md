---
nombre: "describir_payroll_item"
version: "1.0.0"
descripcion: "Lista y describe items de nómina (payroll items) de PeopleNet desde M4RCH_PAYROLL_ITEM."
herramienta: "tools.m4object.get_payroll_item"
parametros:
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "Filtrar por TI específico (ej: ID_TI_PAYROLL)."
    requerido: false
  - nombre: "id_item"
    tipo: "string"
    descripcion: "ID del item específico a detallar (requiere --ti)."
    requerido: false
  - nombre: "search"
    tipo: "string"
    descripcion: "Buscar por texto en ID_ITEM, ID_CONCEPT o ID_TI."
    requerido: false
---

## Documentación de la Skill: `describir_payroll_item`

### Propósito

Expone la tabla `M4RCH_PAYROLL_ITEM`, que contiene las definiciones de conceptos de nómina dentro de los TIs de canales payroll. Esta tabla es distinta de `M4RCH_ITEMS` (que contiene items genéricos) y de `M4RCH_CONCEPTS` (que vincula conceptos a items).

Es especialmente útil para:
- Verificar que un concepto de nómina está correctamente registrado.
- Listar todos los conceptos de un canal de payroll.
- Obtener el detalle completo de un payroll item con su contexto en M4RCH_ITEMS.

### Flujo de Trabajo

1. **Descubrimiento de esquema**: La herramienta descubre dinámicamente las columnas disponibles en `M4RCH_PAYROLL_ITEM` (el esquema puede variar entre instalaciones).
2. **Listado/búsqueda**: Filtra por TI, por texto, o lista todo. Excluye columnas de código fuente del listado.
3. **Detalle**: Para un item específico, devuelve todas las columnas incluyendo un JOIN contextual con `M4RCH_ITEMS` para enriquecer con tipo, nombre y campo BDL asociado.

### Ejemplos de Uso

**Listar todos los payroll items:**
```bash
python -m tools.m4object.get_payroll_item --list
```

**Listar payroll items de un TI específico:**
```bash
python -m tools.m4object.get_payroll_item --list --ti "<ID_TI_PAYROLL>"
```

**Buscar un concepto por texto:**
```bash
python -m tools.m4object.get_payroll_item --list --search "<TEXTO_BUSQUEDA>"
```

**Obtener detalle completo de un payroll item:**
```bash
python -m tools.m4object.get_payroll_item --ti "<ID_TI_PAYROLL>" --item "<ID_ITEM_CONCEPTO>"
```

### Relación con otras herramientas

- `describir_m4object` ahora incluye conceptos (`M4RCH_CONCEPTS`) por TI automáticamente.
- `verificar_concepto_nomina` (skill de nómina) realiza una verificación cruzada completa de un concepto de nómina a través de múltiples tablas.
- Esta herramienta se enfoca exclusivamente en `M4RCH_PAYROLL_ITEM`.
