---
# Metadata estructurada de la Skill
nombre: "describir_m4object"
version: "0.1.0"
descripcion: "Obtiene la definición completa de un m4object (canal) de PeopleNet, incluyendo sus nodos, items y presentaciones."
parametros:
  - nombre: "id_t3"
    tipo: "string"
    descripcion: "El identificador del m4object (canal) a describir."
    requerido: true
---

## Documentación de la Skill: `describir_m4object`

### Propósito
Esta skill permite a los agentes consultar la estructura jerárquica de un m4object (canal) de PeopleNet. Un m4object es la unidad funcional que define cómo la aplicación opera sobre los datos de la BDL.

### Flujo de Trabajo
La skill invocará el script `tools/m4object/get_m4object.py`, que realizará los siguientes pasos:
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta de Metadatos**: Ejecuta consultas sobre las tablas `M4RCH_T3S`, `M4RCH_NODES`, `M4RCH_ITEMS`.
3. **Estructuración de Datos**: Formatea los resultados en un objeto JSON jerárquico.
4. **Devolución de Resultados**: Imprime el JSON a la salida estándar.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.m4object.get_m4object "MI_M4OBJECT_ID"
```

### Estado
**No implementada.** El script `get_m4object.py` aún no contiene la lógica de consulta.
