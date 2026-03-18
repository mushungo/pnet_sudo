---
# Metadata estructurada de la Skill
nombre: "encontrar_usos_bdl_object"
version: "1.0.0"
descripcion: "Encuentra todos los m4objects (canales) que utilizan un Objeto Lógico (BDL) específico."
# Parámetros
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "El identificador único del Objeto Lógico (BDL) cuyos usos se quieren encontrar."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `encontrar_usos_bdl_object`

### Propósito
Esencial para evaluar las consecuencias de un cambio en la BDL.

### Flujo de Trabajo
Invoca el script `tools.bdl.find_bdl_usages.py`.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.find_bdl_usages "STD_PERSON"
```
