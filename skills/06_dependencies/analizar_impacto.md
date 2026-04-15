---
nombre: "analizar_impacto"
version: "1.0.0"
descripcion: "Análisis de impacto: dado un TI + ITEM, traza todas las dependencias internas, externas y de canal que lo referencian o que él usa."
parametros:
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "Identificador del TI."
    requerido: true
  - nombre: "id_item"
    tipo: "string"
    descripcion: "Identificador del item."
    requerido: true
  - nombre: "direction"
    tipo: "string"
    descripcion: "Dirección: 'dependents' (quién depende de mí), 'uses' (de quién dependo), 'both'. Default: dependents."
    requerido: false
herramienta: "tools.dependencies.find_dependents"
---

## Documentación de la Skill: `analizar_impacto`

### Propósito
Herramienta de análisis de impacto que responde a la pregunta: "si cambio este item, ¿qué se ve afectado?" o "¿de qué depende este item?". Busca en las tres tablas de dependencias:
- **INTERNAL_DEP**: Dependencias dentro del mismo TI.
- **EXTERNAL_DEP**: Dependencias cruzando TIs (via alias).
- **CHANNEL_DEP**: Dependencias cruzando canales (T3s).

### Flujo de Trabajo
1. **Dependencias internas**: Busca en M4RCH_INTERNAL_DEP items que usan o son usados por el item dado.
2. **Dependencias externas**: Busca en M4RCH_EXTERNAL_DEP con TI cruzado.
3. **Dependencias de canal**: Busca en M4RCH_CHANNEL_DEP con T3 cruzado.
4. **Resumen**: Devuelve conteos por tipo y la lista detallada.

### Ejemplos de Uso

**¿Quién depende de mi item?**
```bash
python -m tools.dependencies.find_dependents "MI_TI" "MI_ITEM"
```

**¿De quién dependo yo?**
```bash
python -m tools.dependencies.find_dependents "MI_TI" "MI_ITEM" --direction uses
```

**Ambas direcciones:**
```bash
python -m tools.dependencies.find_dependents "MI_TI" "MI_ITEM" --direction both
```
