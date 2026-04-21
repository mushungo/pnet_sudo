---
nombre: "describir_paquete_presentacion"
version: "1.0.0"
descripcion: "Extrae los metadatos de compilación y los binarios OBL de una presentación de PeopleNet (tablas M4RPT_PRESENT_PKG*)."
parametros:
  - nombre: "id_presentation"
    tipo: "string"
    requerido: true
    descripcion: "Identificador de la presentación (ej: SCO_EMPLOYEE)"
  - nombre: "lang"
    tipo: "string"
    requerido: false
    descripcion: "Variante de idioma a exportar: neutral | eng | esp | fra | ger | bra | ita | gen"
  - nombre: "export_dir"
    tipo: "string"
    requerido: false
    descripcion: "Directorio donde volcar los archivos .bin (uno por variante)"
  - nombre: "metadata_only"
    tipo: "boolean"
    requerido: false
    descripcion: "Si true, solo devuelve fechas de compilación sin leer los blobs binarios"
---

## Documentacion de la Skill: `describir_paquete_presentacion`

### Proposito
Recupera el código OBL compilado de una presentación de PeopleNet. El bytecode se almacena distribuido en 9 tablas físicas separadas: una de metadatos y ocho de binarios (una por variante de idioma). Esta skill permite inspeccionar qué variantes están compiladas, su tamaño, y exportarlas a disco para análisis externo.

### Arquitectura de Almacenamiento OBL

El paquete compilado de una presentación se divide en las siguientes tablas:

| Tabla | Columna binaria | Contenido |
|---|---|---|
| `M4RPT_PRESENT_PKG` | *(sin binario)* | Fechas: DT_CREATE, DT_LAST_COMPILE, DT_LAST_UPDATE, DT_LAST_UPDATE1 |
| `M4RPT_PRESENT_PKG1` | `XPACKAGE` | **Paquete principal** — bytecode OBL neutro (sin traducciones literales) |
| `M4RPT_PRESENT_PKG2` | `PKG_LNGENG` | Variante en inglés |
| `M4RPT_PRESENT_PKG3` | `PKG_LNGESP` | Variante en español |
| `M4RPT_PRESENT_PKG4` | `PKG_LNGFRA` | Variante en francés |
| `M4RPT_PRESENT_PKG5` | `PKG_LNGGER` | Variante en alemán |
| `M4RPT_PRESENT_PKG6` | `PKG_LNGBRA` | Variante en portugués brasileño |
| `M4RPT_PRESENT_PKG7` | `PKG_LNGITA` | Variante en italiano |
| `M4RPT_PRESENT_PKG8` | `PKG_LNGGEN` | Variante genérica / neutral extendida |

> **Nota:** No todas las presentaciones tienen todas las variantes compiladas. Una presentación sin uso internacional típicamente solo tiene `XPACKAGE` (neutral) y `PKG_LNGESP`. La ausencia de una variante devuelve `present: false` con `size_bytes: 0`.

### Por qué la división en 9 tablas

SQL Server impone un límite de 8.060 bytes por fila en tablas estándar. Los blobs OBL pueden alcanzar varios MB. PeopleNet resuelve esto colocando cada columna `image`/`varbinary(max)` en su propia tabla física, con la misma PK (`ID_PRESENTATION`), evitando el límite de tamaño de fila.

### Estructura del Bytecode OBL (parcialmente inferida)

Los binarios son propietarios y no están documentados públicamente. Del análisis de trazas del LDB Inspector se observa que el blob contiene:
- Marcadores de tipo de clase: `ClassnameIncludepanel`, `ClassnameRefSeqAlias*`
- Descriptores de formato: `Stretch`, `ÿ` como byte terminador de secciones
- Los strings de etiquetas multilingues están embebidos en las variantes de idioma (PKG2–PKG8), no en el XPACKAGE neutro

### Fechas de Compilación (M4RPT_PRESENT_PKG)

| Campo | Significado |
|---|---|
| `DT_CREATE` | Fecha de primera compilación de la presentación |
| `DT_LAST_COMPILE` | Última vez que se compiló correctamente |
| `DT_LAST_UPDATE` | Última modificación de la definición fuente |
| `DT_LAST_UPDATE1` | Última modificación de metadatos auxiliares |

Si `DT_LAST_UPDATE > DT_LAST_COMPILE`, la presentación tiene cambios sin compilar.

### Ejemplo de Uso

```bash
# Solo metadatos de compilación (rápido, sin leer blobs)
python -m tools.presentations.get_presentation_pkg SCO_EMPLOYEE --metadata-only

# Resumen de todas las variantes (tamaños, sin exportar)
python -m tools.presentations.get_presentation_pkg SCO_EMPLOYEE

# Exportar todas las variantes a disco
python -m tools.presentations.get_presentation_pkg SCO_EMPLOYEE --export-dir ./output/pkg

# Exportar solo la variante española
python -m tools.presentations.get_presentation_pkg SCO_EMPLOYEE --lang esp --export-dir ./output/pkg
```

**Resultado esperado (sin exportar):**
```json
{
  "id_presentation": "SCO_EMPLOYEE",
  "compilation": {
    "dt_create": "2020-01-15 10:23:00",
    "dt_last_compile": "2024-11-20 14:05:12",
    "dt_last_update": "2024-11-20 13:58:44",
    "dt_last_update1": null
  },
  "packages": {
    "neutral": {
      "table": "M4RPT_PRESENT_PKG1",
      "column": "XPACKAGE",
      "lang": "neutral",
      "present": true,
      "size_bytes": 184320
    },
    "eng": {
      "table": "M4RPT_PRESENT_PKG2",
      "column": "PKG_LNGENG",
      "lang": "eng",
      "present": true,
      "size_bytes": 12288
    },
    "esp": {
      "table": "M4RPT_PRESENT_PKG3",
      "column": "PKG_LNGESP",
      "lang": "esp",
      "present": true,
      "size_bytes": 11776
    },
    "fra": { "present": false, "size_bytes": 0 },
    "ger": { "present": false, "size_bytes": 0 },
    "bra": { "present": false, "size_bytes": 0 },
    "ita": { "present": false, "size_bytes": 0 },
    "gen": { "present": false, "size_bytes": 0 }
  },
  "total_size_bytes": 208384,
  "packages_present": 3
}
```

### Ver también
- `describir_presentacion` — definición, herencia, canales y BPs vinculados
- `listar_presentaciones` — búsqueda en el catálogo de presentaciones
- `describir_business_process` — Business Processes que usan la presentación
