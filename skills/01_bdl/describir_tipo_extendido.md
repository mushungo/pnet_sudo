---
# Metadata estructurada de la Skill
nombre: "describir_tipo_extendido"
version: "1.0.0"
descripcion: "Describe las propiedades y la lógica de comportamiento de un Tipo Extendido de la BDL."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_type"
    tipo: "string"
    descripcion: "El identificador del Tipo Extendido a describir. Ej: 'AGE'."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_tipo_extendido`

### Propósito
Esta skill permite a los agentes y desarrolladores entender la lógica completa detrás de un tipo de dato de dominio.

### Flujo de Trabajo
La skill invoca el script `tools.bdl.get_bdl_extended_type_details.py`.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.get_bdl_extended_type_details "AGE"
```
