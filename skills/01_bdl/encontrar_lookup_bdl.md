---
# Metadata estructurada de la Skill
nombre: "encontrar_lookup_bdl"
version: "1.0.0"
descripcion: "Encuentra la tabla maestra (lookup) que provee los valores válidos para un campo específico de un objeto de la BDL."
# Parámetros
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "El identificador del Objeto Lógico (BDL) que contiene el campo."
    requerido: true
  - nombre: "id_field"
    tipo: "string"
    descripcion: "El identificador del campo cuya tabla maestra se quiere encontrar."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `encontrar_lookup_bdl`

### Propósito
Responde a la pregunta: "¿De dónde saca este campo sus opciones?".

### Flujo de Trabajo
Invoca el script `tools.bdl.find_bdl_lookup.py`.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.find_bdl_lookup "SCH_ITEMS" "ID_M4_TYPE"
```
